from pathlib import Path
import subprocess,sys,json,datetime
R=Path(__file__).resolve().parents[1]
p=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(R/'tests'),'-v'],cwd=R,capture_output=True,text=True,errors='replace')
text=p.stdout+p.stderr;(R/'evidence/unit_tests.log').write_text(text,encoding='utf-8')
status=dict(scope='Python structural/model tests only; not native ERC/DRC or bench',returncode=p.returncode,result='PASS' if p.returncode==0 else 'FAIL',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),manufacture='BLOCKED')
(R/'evidence/test_summary.json').write_text(json.dumps(status,indent=2));print(text);sys.exit(p.returncode)
