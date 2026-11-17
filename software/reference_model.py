"""ZL80 PDR reference algorithms, not calibrated scanner firmware."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import json, math, struct, hashlib, os
@dataclass(frozen=True)
class Sample:
    tick: int
    facet: int
    x_mm: float
    y_mm: float
    raw: int
    flags: int = 0
    gain_id: int = 0

def transmission_to_density(signal: float, dark: float, flat: float, reference_ratio: float = 1.0) -> float:
    """Inputs must be linear-equivalent values. LOG input must first use its inverse LUT."""
    if not all(math.isfinite(v) for v in (signal,dark,flat,reference_ratio)):
        raise ValueError("non-finite input")
    if flat <= dark or reference_ratio <= 0:
        raise ValueError("invalid flat/dark/reference")
    t=(signal-dark)/(flat-dark)/reference_ratio
    if t <= 0:
        raise ValueError("nonpositive signal; mark invalid, never fabricate a density")
    return -math.log10(t)

def position_from_sync(tick: int, sos_tick: int, eos_tick: int, x_sos: float=-46.0, x_eos: float=46.0) -> float:
    """Affine per-line baseline; facet LUT replaces it after geometric calibration."""
    if eos_tick <= sos_tick:
        raise ValueError("invalid scan interval")
    return x_sos+(tick-sos_tick)/(eos_tick-sos_tick)*(x_eos-x_sos)

def quadrature(previous: int, current: int) -> tuple[int,bool]:
    if previous not in range(4) or current not in range(4):raise ValueError("2-bit state required")
    if previous==current:return 0,False
    delta={(0,1):1,(1,3):1,(3,2):1,(2,0):1,(1,0):-1,(3,1):-1,(2,3):-1,(0,2):-1}
    return (delta[(previous,current)],False) if (previous,current) in delta else (0,True)

def delay_tags(tags: Iterable[int], cycles: int) -> list[int | None]:
    if cycles < 0: raise ValueError("negative latency")
    tags=list(tags)
    return [None]*cycles+tags

class ChunkWriter:
    """Atomic local chunks, 64-bit row numbers, SHA256; reference format, not DICONDE."""
    def __init__(self, directory: str | Path, columns: int, revision: str):
        self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=True)
        if columns<=0:raise ValueError("columns must be positive")
        self.columns=columns;self.revision=revision
    def write(self, first_row: int, rows: list[list[int]], quality: dict) -> Path:
        if first_row<0 or first_row>=2**64:raise ValueError("invalid uint64 row")
        if not rows or any(len(row)!=self.columns for row in rows):raise ValueError("invalid row shape")
        if any(not isinstance(x,int) or not 0<=x<=65535 for row in rows for x in row):raise ValueError("uint16 data required")
        header=json.dumps(dict(version=1,first_row=first_row,rows=len(rows),columns=self.columns,revision=self.revision,quality=quality),ensure_ascii=False).encode()
        payload=struct.pack("<"+"H"*(len(rows)*self.columns),*(x for row in rows for x in row))
        content=b'ZL80R5\0\0'+struct.pack('<I',len(header))+header+payload
        path=self.directory/f'{first_row:020d}.zl80'
        if path.exists():raise FileExistsError("immutable master chunk already exists")
        tmp=path.with_suffix('.tmp')
        with open(tmp,'xb') as f:f.write(content);f.flush();os.fsync(f.fileno())
        os.link(tmp,path)
        tmp.unlink()
        path.with_suffix('.sha256').write_text(hashlib.sha256(content).hexdigest())
        return path
    @staticmethod
    def verify(path: str | Path) -> dict:
        path=Path(path);blob=path.read_bytes()
        if hashlib.sha256(blob).hexdigest()!=path.with_suffix('.sha256').read_text().strip():raise ValueError("checksum mismatch")
        if blob[:8]!=b'ZL80R5\0\0':raise ValueError("bad magic")
        n=struct.unpack('<I',blob[8:12])[0];meta=json.loads(blob[12:12+n]);expected=meta['rows']*meta['columns']*2
        if len(blob[12+n:])!=expected:raise ValueError("payload length mismatch")
        return meta
