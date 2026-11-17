"""Check release snapshots against FILE_MANIFEST.json (no network or mutations)."""
from pathlib import Path
import hashlib,json,sys
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'FILE_MANIFEST.json').read_text(encoding='utf-8'))
errors=[]
for e in manifest['files']:
    p=root/e['path']
    if not p.is_file(): errors.append('MISSING '+e['path']);continue
    if hashlib.sha256(p.read_bytes()).hexdigest()!=e['sha256']:errors.append('CHANGED '+e['path'])
if errors: print('\n'.join(errors));sys.exit(1)
print(f"PASS: {len(manifest['files'])} files match release hashes. Rebuilding results after release can legitimately change hashes; record a new revision.")
