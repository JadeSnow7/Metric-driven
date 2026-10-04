import json, subprocess, tempfile, unittest
from pathlib import Path

ROOT=Path('/private/tmp/rein-ch08-evaluator-v4'); DATA=Path('/private/tmp/rein-ch08-common-20260915/book/fixtures/ch08-context'); REPO=Path('/private/tmp/rein-ch08-common-20260915/book')
class EvalTests(unittest.TestCase):
  def run_eval(self):
    out=Path(tempfile.mkdtemp(prefix='eval-v4-'))/'run'; p=subprocess.run(['python3',str(ROOT/'evaluator.py'),'--repo',str(REPO),'--data',str(DATA),'--output',str(out),'--command-json',str(ROOT/'toy-command.json')],capture_output=True,text=True,timeout=180); self.assertEqual(p.returncode,0,p.stderr); return out,json.loads(p.stdout)
  def test_dynamic_known_good_suite_and_raw_records(self):
    out,summary=self.run_eval(); self.assertEqual([x['rows'] for x in summary['scenarios'][:3]],[16,16,16]); self.assertEqual(summary['scenarios'][3]['exit_code'],1); self.assertTrue((out/'default/default.json').is_file()); self.assertTrue((out/'duplicate/duplicate.json').is_file())
  def test_no_self_caught_duplicate_failure(self):
    out,summary=self.run_eval(); duplicate=json.loads((out/'duplicate/duplicate.json').read_text()); self.assertNotEqual(duplicate['exit_code'],0); self.assertIn('invalid metadata',duplicate['stderr'])
if __name__=='__main__': unittest.main()
