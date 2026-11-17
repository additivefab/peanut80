"""Run actual Python tests; clearly separate these from HDL/native/bench results."""
from pathlib import Path
import unittest,json,sys,platform,time,subprocess
R=Path(__file__).resolve().parents[1];out=R/'validation/results';out.mkdir(parents=True,exist_ok=True)
suite=unittest.defaultTestLoader.discover(str(R/'tests'))
with (out/'python_tests.log').open('w') as f:
    result=unittest.TextTestRunner(stream=f,verbosity=2).run(suite)
summary={'scope':'PYTHON_ALGORITHMS_AND_FORMAT_ONLY_NOT_RTL','tests':result.testsRun,
 'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
 'status':'PASS' if result.wasSuccessful() else 'FAIL','python':sys.version,'platform':platform.platform()}
(out/'python_tests.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2));sys.exit(0 if result.wasSuccessful() else 1)
