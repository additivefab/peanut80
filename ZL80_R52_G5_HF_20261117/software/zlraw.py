"""ZL80 G5 raw record/archive format. Standard library only; no hardware access."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, BinaryIO
import json, struct, zlib, hashlib
RECORD = struct.Struct('<IQHBB')  # payload32,tick64,flags16,version8,type8
BLOCK = struct.Struct('<4sIII')   # marker,sequence,length,CRC32
MAGIC=b'ZL80RAW1'; MAX_METADATA=1<<20; MAX_BLOCK=1<<24
SAMPLE=0x01;SOS_UP=0x10;SOS_DOWN=0x11;EOS_UP=0x12;EOS_DOWN=0x13
ENC_M=0x20;ENC_D=0x21;ENC_E=0x22;POLYGON_INDEX=0x30
START=0x70;STATUS=0x71;LOSS=0x72;END=0x7f
TYPES={SAMPLE,SOS_UP,SOS_DOWN,EOS_UP,EOS_DOWN,ENC_M,ENC_D,ENC_E,POLYGON_INDEX,START,STATUS,LOSS,END}
class FormatError(ValueError): pass
@dataclass(frozen=True)
class Record:
    kind:int
    tick:int
    payload:int=0
    flags:int=0
    version:int=1
    def pack(self)->bytes:
        if self.kind not in TYPES or self.version!=1: raise FormatError('unsupported record type/version')
        try: return RECORD.pack(self.payload,self.tick,self.flags,self.version,self.kind)
        except struct.error as exc: raise FormatError(str(exc)) from exc
    @classmethod
    def unpack(cls,data:bytes)->'Record':
        if len(data)!=16: raise FormatError('record must be exactly 16 bytes')
        p,t,f,v,k=RECORD.unpack(data)
        if k not in TYPES or v!=1: raise FormatError('unsupported record type/version')
        return cls(k,t,p,f,v)
    @property
    def a(self)->int: return self.payload & 0xffff
    @property
    def b(self)->int: return (self.payload>>16)&0xffff
    @property
    def signed_payload(self)->int:
        return self.payload if self.payload<0x80000000 else self.payload-(1<<32)
def _exact(f:BinaryIO,n:int)->bytes:
    b=f.read(n)
    if len(b)!=n: raise FormatError('truncated archive; data must not be padded')
    return b
def read_metadata(path:str|Path)->dict:
    with Path(path).open('rb') as f:
        if _exact(f,8)!=MAGIC: raise FormatError('bad file magic')
        n=struct.unpack('<I',_exact(f,4))[0]
        if n>MAX_METADATA: raise FormatError('metadata exceeds limit')
        try: m=json.loads(_exact(f,n))
        except (UnicodeError,json.JSONDecodeError) as e: raise FormatError('bad metadata') from e
        if not isinstance(m,dict): raise FormatError('metadata must be object')
        return m
def iter_records(path:str|Path)->Iterator[Record]:
    """Streaming CRC/sequence checked reader. Empty/truncated files are errors."""
    with Path(path).open('rb') as f:
        if _exact(f,8)!=MAGIC: raise FormatError('bad file magic')
        n=struct.unpack('<I',_exact(f,4))[0]
        if n>MAX_METADATA: raise FormatError('metadata exceeds limit')
        _exact(f,n); expected=0; saw=False
        while True:
            h=f.read(BLOCK.size)
            if not h: break
            if len(h)!=BLOCK.size: raise FormatError('truncated block header')
            marker,seq,length,crc=BLOCK.unpack(h)
            if marker!=b'BLK1' or seq!=expected: raise FormatError('block sequence/magic mismatch')
            if not length or length%16 or length>MAX_BLOCK: raise FormatError('invalid block length')
            body=_exact(f,length)
            if zlib.crc32(body)&0xffffffff != crc: raise FormatError('CRC mismatch')
            expected+=1;saw=True
            for i in range(0,length,16): yield Record.unpack(body[i:i+16])
        if not saw: raise FormatError('archive contains no records')
def write_archive(path:str|Path,metadata:dict,records:Iterable[Record],block_records:int=256)->None:
    if not 1<=block_records<=MAX_BLOCK//16: raise ValueError('invalid block_records')
    m=json.dumps(metadata,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
    if len(m)>MAX_METADATA: raise ValueError('metadata too large')
    # Exclusive creation: never overwrite a Raw Master or a previous synthetic example.
    with Path(path).open('xb') as f:
        f.write(MAGIC+struct.pack('<I',len(m))+m); buf=bytearray();seq=0
        def emit():
            nonlocal seq
            f.write(BLOCK.pack(b'BLK1',seq,len(buf),zlib.crc32(buf)&0xffffffff));f.write(buf)
            seq+=1;buf.clear()
        for r in records:
            buf.extend(r.pack())
            if len(buf)==16*block_records: emit()
        if buf:emit()
def inspect(path:str|Path)->dict:
    meta=read_metadata(path); counts={};session=None;ended=False;status=None;loss=None
    footer_phase=0;last_sample=None;sample_nonmonotonic=0;uncal=0;unpaired=0;upstream=0;testpat=0;rails=0
    for r in iter_records(path):
        counts[f'0x{r.kind:02X}']=counts.get(f'0x{r.kind:02X}',0)+1
        if ended: raise FormatError('records after END; one session per archive')
        if footer_phase and r.kind not in (LOSS,END):raise FormatError('record after footer began')
        if r.kind==LOSS and footer_phase!=1:raise FormatError('LOSS must follow STATUS')
        if r.kind==END and footer_phase!=2:raise FormatError('END must follow LOSS')
        if r.kind==START:
            if session is not None: raise FormatError('multiple START records')
            session=r.payload
        elif session is None: raise FormatError('missing START')
        if r.kind==SAMPLE:
            if last_sample is not None and r.tick<=last_sample:sample_nonmonotonic+=1
            last_sample=r.tick;uncal+=bool(r.flags&4);unpaired+=bool(r.flags&8);upstream+=bool(r.flags&32);testpat+=bool(r.flags&16)
            rails+=r.a in (0,65535) or r.b in (0,65535)
        elif r.kind==STATUS:
            if status is not None:raise FormatError('duplicate STATUS')
            status=r.payload;footer_phase=1
        elif r.kind==LOSS:
            if loss is not None:raise FormatError('duplicate LOSS')
            loss=r.payload;footer_phase=2
        elif r.kind==END:
            if r.payload!=session:raise FormatError('END session mismatch')
            ended=True
    if not ended or status is None or loss is None:raise FormatError('incomplete session/footer')
    ok=status==0 and loss==0 and sample_nonmonotonic==0 and uncal==0 and unpaired==0 and upstream==0
    if counts.get('0x01',0)==0:ok=False
    return {'session_id':session,'record_counts':counts,'status_word':status,'dropped_records':loss,
            'sample_time_errors':sample_nonmonotonic,'uncalibrated_samples':uncal,
            'unverified_pairs':unpaired,'test_pattern_samples':testpat,'upstream_loss_samples':upstream,'rail_samples_preserved':rails,
            'digital_integrity_eligible':ok,'synthetic':bool(meta.get('synthetic',False)),
            'metrology_release':False,
            'note':'CRC/digital checks do not prove optical, geometric or safety qualification'}
def file_hash(path:str|Path)->str:
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        while b:=f.read(1<<20):h.update(b)
    return h.hexdigest()
