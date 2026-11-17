"""SHA-256 manifest of this folder (excluding the manifest itself and caches)."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parent
files=sorted(p for p in R.rglob('*') if p.is_file() and p.name!='manifest_sha256.json' and '__pycache__' not in p.parts and p.name!='.DS_Store')
m=dict(revision='ADF50-V0.6-PDR',date='2026-11-16',file_count=len(files),
       files={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
(R/'manifest_sha256.json').write_text(json.dumps(m,ensure_ascii=False,indent=1));print(len(files),'files')
