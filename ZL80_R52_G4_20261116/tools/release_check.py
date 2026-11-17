"""Conservative release gate. Does not create Gerbers or allow auto-release."""
import json,csv,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
reasons=['B01 only critical nets routed; 43 remaining connectivity links in current audit','B02/B03/B04/B05 circuits not closed','Native KiCad parse/ERC/DRC and filled zones not verified','Real MPNs, mating connectors and PMT socket not frozen','G1 photodiode alignment changes need sign-off','No physical bench, EMC, thermal or DFM qualification','No responsible human manufacturing approval']
audit=R/'validation/results/native_tools.json'
if audit.exists() and json.loads(audit.read_text()).get('status')=='EXECUTED_REVIEW_REQUIRED':reasons[2]='Native reports exist but need signed violation review, zone refill proof and design hash match'
result=dict(status='BLOCKED',reasons=reasons,scope='Engineering review package only. No manufacturing release implied.')
(R/'validation/results/release_gate.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False,indent=2));sys.exit(2)
