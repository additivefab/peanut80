from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[1];manifest=json.loads((R/'MANIFEST_SHA256.json').read_text());bad=[]
for x in manifest['files']:
 p=R/x['path']
 if not p.exists():bad.append([x['path'],'MISSING']);continue
 if hashlib.sha256(p.read_bytes()).hexdigest()!=x['sha256']:bad.append([x['path'],'CHANGED'])
print('OK' if not bad else 'MISMATCH',len(manifest['files']),'files; modified/rebuilt outputs intentionally change their hashes.')
for x in bad:print(*x)
sys.exit(bool(bad))
