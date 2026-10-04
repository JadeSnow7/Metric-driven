import json, os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
DATA=Path("/private/tmp/rein-ch08-preparation-product-v3/data")
CMD=[sys.executable, str(HERE/"calibration_cli.py")]

class EvaluatorCalibrationTests(unittest.TestCase):
    def run_eval(self, mutant="", data=DATA):
        out=Path(tempfile.mkdtemp(prefix="ch08-eval-test-"))
        env=os.environ.copy()
        if mutant: env["CALIBRATION_MUTANT"]=mutant
        p=subprocess.run([sys.executable,str(HERE/"evaluator.py"),"--repo",str(HERE),"--data",str(data),"--output",str(out),"--command-json",json.dumps(CMD)], env=env, text=True, capture_output=True)
        summary=json.loads((out/"summary.json").read_text())
        return p,summary,out

    def test_positive_all_four_strategies(self):
        p,s,_=self.run_eval()
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertTrue(s["passed"])
        self.assertEqual(s["failedCount"],0)

    def test_each_mutant_is_observed_by_specific_checks(self):
        mutants={
            "missing-row": "rows.on-demand.count",
            "duplicate-row": "rows.on-demand.count",
            "wrong-estimate": "on-demand.messages.utf8-estimate",
            "unsupported-claim": "on-demand.claims.source-evidence.2",
            "budget0-dispatch": "on-demand.messages.rules-question",
            "accept-duplicate-metadata": "run.on-demand.exit",
            "path-escape": "run.on-demand.exit",
        }
        for mutant, check_id in mutants.items():
            with self.subTest(mutant=mutant):
                p,s,_=self.run_eval(mutant)
                self.assertNotEqual(p.returncode,0)
                self.assertFalse(s["passed"])
                self.assertTrue(any(c["id"]==check_id and not c["passed"] for c in s["checks"]), (mutant, check_id))

    def test_frozen_original_value_is_rejected(self):
        tmp=Path(tempfile.mkdtemp(prefix="ch08-data-")); shutil.copytree(DATA,tmp,dirs_exist_ok=True)
        doc=tmp/"docs/early-runtime.md"; doc.write_text(doc.read_text().replace("JSON Lines","CBOR"))
        p,s,_=self.run_eval("frozen-original",tmp)
        self.assertNotEqual(p.returncode,0)
        self.assertTrue(any((not c["passed"]) and "claims.source-evidence" in c["id"] for c in s["checks"]))

if __name__ == "__main__": unittest.main()
