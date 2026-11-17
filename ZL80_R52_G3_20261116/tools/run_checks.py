from pathlib import Path
import unittest,json,datetime,sys,io,shutil
R=Path(__file__).resolve().parents[1];out=io.StringIO();suite=unittest.defaultTestLoader.discover(str(R/'tests'));res=unittest.TextTestRunner(stream=out,verbosity=2).run(suite)
(R/'validation/results/unit_test_log.txt').write_text(out.getvalue());print(out.getvalue())
summary={'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'tests_run':res.testsRun,'failures':len(res.failures),'errors':len(res.errors),'passed':res.wasSuccessful(),'scope':'calculation/data consistency and static geometry audit; includes synthetic analyzer unit test, NOT physical transport evidence','native_FreeCAD':'AVAILABLE_NOT_EXECUTED' if shutil.which('FreeCAD') else 'NOT_AVAILABLE','bench':'NOT_RUN','manufacturing_release':'BLOCKED'}
(R/'validation/results/test_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));sys.exit(0 if res.wasSuccessful() else 1)
