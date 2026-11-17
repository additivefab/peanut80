from pathlib import Path
import sys
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'src'))
from scan_model import run
run()
print('Updated results/*.csv and calculation_summary.json. CAD/XLSX/PDF are release snapshots, not silently regenerated.')
