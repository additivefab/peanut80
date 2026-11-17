from pathlib import Path
import sys,subprocess,json,datetime
R=Path(__file__).resolve().parents[1]
p=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=R,capture_output=True,text=True)
(R/'validation/unit_tests.log').write_text(p.stdout+p.stderr,encoding='utf-8')
summary={'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'python':sys.version,
 'unit_tests':'PASS' if p.returncode==0 else 'FAIL','native_freecad':'NOT_RUN',
 'actual_lens_raytrace':'NOT_RUN_NO_PRESCRIPTION','bench':'NOT_RUN',
 'G0':'DRAFT_PENDING_INTERFACE_APPROVAL','G1':'BLOCKED_APERTURE_RISK_AND_NO_PO_C_EVIDENCE','manufacturing':'NOT_RELEASED'}
(R/'validation/status.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(p.stdout+p.stderr);print(json.dumps(summary,ensure_ascii=False,indent=2));sys.exit(p.returncode)
