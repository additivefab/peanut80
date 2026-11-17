"""Convert a simulator-produced 64-bit AXI dump to archive; not a hardware driver."""
import argparse,json
from pathlib import Path
from zlraw import Record,write_archive,inspect,FormatError

def convert(src:Path,dst:Path):
    records=[];lo=None;beats=0;lasts=[]
    for ln,line in enumerate(src.read_text().splitlines(),1):
        if not line.strip() or line.startswith('#'):continue
        h,keep,last=line.split();data=int(h,16);keep=int(keep,16);last=int(last)
        if keep!=255:raise FormatError(f'partial record byte mask at {ln}')
        if lo is None:
            if last:raise FormatError('TLAST on first half of record')
            lo=data
        else:
            records.append(Record.unpack(lo.to_bytes(8,'little')+data.to_bytes(8,'little')));lo=None
        beats+=1
        if last:lasts.append(beats)
    if lo is not None:raise FormatError('truncated AXI record')
    if not lasts or lasts[-1]!=beats:raise FormatError('missing final TLAST')
    write_archive(dst,{'synthetic':True,'source':'HDL simulator AXI dump; NOT bench','tick_hz':100000000},records)
    return inspect(dst)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    print(json.dumps(convert(a.input,a.output),indent=2))
