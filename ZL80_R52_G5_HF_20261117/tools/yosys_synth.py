"""Yosys synthesis of zl80_capture_core for xc7 (synth_xilinx). NOT Vivado: no timing, no CDC, no constraints; LUT/FF/RAM counts are indicative.
Usage: python3 tools/yosys_synth.py --yosys <path>. Writes validation/results/yosys_synth.log and yosys_summary.json."""
import argparse,json,re,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
FILES=['rtl/core/record_fifo.sv','rtl/helpers/sync_bits.sv','rtl/core/quad_decoder.sv','rtl/core/record_to_axis64.sv','rtl/core/rr_record_merge.sv','rtl/core/zl80_capture_core.sv']
KEYS=['LUT1','LUT2','LUT3','LUT4','LUT5','LUT6','FDRE','FDCE','CARRY4','MUXF7','MUXF8','RAM32M','RAM64M','RAM32X1D','RAMB18E1','RAMB36E1','BUFG']
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--yosys',required=True);o=a.parse_args()
    script='read_verilog -sv %s; hierarchy -top zl80_capture_core; proc; flatten; opt; synth_xilinx -family xc7 -top zl80_capture_core; stat'%' '.join(FILES)
    p=subprocess.run([o.yosys,'-p',script],cwd=R,capture_output=True,text=True);log=R/'validation/results/yosys_synth.log';log.write_text(p.stdout+p.stderr)
    last=p.stdout.rsplit('Printing statistics.',1)[-1];cells={m.group(2):int(m.group(1)) for m in re.finditer(r'^\s+(\d+)\s+(\w+)\s*$',last,re.M) if m.group(2) in KEYS}
    out={'scope':'YOSYS_SYNTH_XILINX_INDICATIVE_NOT_VIVADO','returncode':p.returncode,'cells':cells,'lut_total':sum(cells.get(f'LUT{i}',0) for i in range(1,7)),
         'ff':cells.get('FDRE',0)+cells.get('FDCE',0),'bram36_equiv':cells.get('RAMB36E1',0)+0.5*cells.get('RAMB18E1',0),'abc_errors':len(re.findall(r'ABC: Error',p.stdout+p.stderr))}
    (R/'validation/results/yosys_summary.json').write_text(json.dumps(out,indent=1));print(json.dumps(out));sys.exit(p.returncode)
