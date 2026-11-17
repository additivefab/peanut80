"""Inspect/parse a completed local archive. No USB/Ethernet/FPGA control implied."""
from pathlib import Path
import argparse,csv,json
from zlraw import inspect,iter_records,read_metadata,file_hash,FormatError
from geometry import map_samples

def main():
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['inspect','map']);ap.add_argument('file',type=Path)
    ap.add_argument('--out',type=Path);a=ap.parse_args()
    report=inspect(a.file);report['sha256']=file_hash(a.file)
    print(json.dumps(report,indent=2,ensure_ascii=False))
    if a.command=='map':
        if not report['digital_integrity_eligible']:raise FormatError('mapping blocked: digital integrity failed')
        if not a.out:ap.error('map requires --out')
        m=read_metadata(a.file)
        if not m.get('synthetic') and m.get('sensor_delay_ticks') is None:
            raise FormatError('real data mapping requires approved sensor delay calibration')
        rows=map_samples(list(iter_records(a.file)),m.get('sync_span_mm',92),m.get('film_width_mm',80),m.get('sensor_delay_ticks',0))
        if not rows:raise FormatError('no complete mapped scan lines')
        with a.out.open('x',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        print('DIAGNOSTIC ONLY; not optical density / not a calibrated Master:',a.out)
if __name__=='__main__':
    try:main()
    except (FormatError,ValueError,OSError) as e:raise SystemExit('ERROR: '+str(e))
