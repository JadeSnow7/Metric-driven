import hashlib, json, subprocess, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_scenarios import ScenarioRepository

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts/validate_task.py"
RECORDER = ROOT / "scripts/record_execution.py"

class SpecBindingTests(unittest.TestCase):
    def prepare(self):
        repo = ScenarioRepository(); repo.make_completed()
        repo.state["schema_version"] = "1.3"
        repo.state["metrics"] = [repo.state["metrics"][0]]
        repo.state["main_tasks"][0]["metric_ids"] = ["MET-001"]
        repo.state["implementation_tasks"][0]["acceptance"] = ["MET-001"]
        repo.state["overall_acceptance"]["metric_ids"] = ["MET-001"]
        repo.state["evidence"][0]["supports"] = ["MET-001"]
        repo.state["evidence"] = []
        repo.state["implementation_tasks"][0]["evidence_ids"] = []
        repo.state["metrics"][0]["evidence_ids"] = []
        repo.state["overall_acceptance"]["evidence_ids"] = []
        repo.state["changes"][0]["evidence_ids"] = []
        (repo.root / "SPEC.md").write_text("contract-v1\n")
        (repo.root / "README.md").write_text("body\n")
        (repo.root / "records/TASK-001/evidence/run-result.txt").write_text("run\n")
        repo.state["spec"] = {"version":"SPEC-TEST","authority":"state.spec","source_ids":["SRC-001"],"goal_ref":"discovery.expected_outcome","scope_ref":"discovery.scope","constraints":["preserve behavior"],"exceptions":[],"conditions":[{"id":"SC-01","metric_ids":["MET-001"],"deliverables":["app.txt","README.md","records/TASK-001/evidence/run-result.txt"]}],"contracts":["SPEC.md"],"open_items":[]}
        repo.state["binding"] = {"receipt_paths":["records/TASK-001/STATUS.md"]}
        repo.state["changes"][0]["paths"].extend(["README.md", "records/TASK-001/evidence/run-result.txt", "records/TASK-001/STATUS.md"])
        repo.write_state(); repo.bind_current_revision(); return repo

    def record_raw(self, repo, name="raw.json", evidence_id="EVD-RAW"):
        out = repo.records / "evidence" / name
        result = subprocess.run([sys.executable,str(RECORDER),"--output",str(out),"--repo",str(repo.root),"--state",str(repo.manifest),"--cwd",str(repo.root),"--source","app.txt","--",sys.executable,"-c","print('ok')"], cwd=repo.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        item={"id":evidence_id,"path":str(out.relative_to(repo.root)),"kind":"execution","supports":["MET-001"],"status":"current","result":"passed","observed_at":"2026-01-01T00:00:00Z","sha256":hashlib.sha256(out.read_bytes()).hexdigest()}
        repo.state["evidence"].append(item); repo.state["implementation_tasks"][0]["evidence_ids"].append(evidence_id); repo.state["metrics"][0]["evidence_ids"].append(evidence_id); repo.state["overall_acceptance"]["evidence_ids"].append(evidence_id)
        repo.state["changes"][0]["evidence_ids"].append(evidence_id); repo.state["changes"][0]["paths"].append("SPEC.md")
        repo.write_state(); repo.bind_current_revision()

    def validate(self, repo):
        return subprocess.run([sys.executable,str(VALIDATOR),str(repo.manifest),"--repo",str(repo.root),"--gate","acceptance"], cwd=repo.root, capture_output=True, text=True)

    def test_control_and_receipt_append_keep_revision(self):
        repo=self.prepare()
        try:
            self.record_raw(repo); control=self.validate(repo); self.assertEqual(control.returncode,0,control.stdout+control.stderr); before=json.loads(control.stdout)["current_revision"]
            receipt=repo.root/"records/TASK-001/STATUS.md"; receipt.write_text("receipt\n"); after_result=self.validate(repo); self.assertEqual(after_result.returncode,0,after_result.stdout); after=json.loads(after_result.stdout)["current_revision"]; self.assertEqual(before,after)
        finally: repo.close()

    def test_contract_change_rejects_old_raw(self):
        repo=self.prepare()
        try:
            self.record_raw(repo); control=self.validate(repo); self.assertEqual(control.returncode,0,control.stdout); old=repo.root/"records/TASK-001/evidence/raw.json"; (repo.root/"SPEC.md").write_text("contract-v2\n"); failed=self.validate(repo); self.assertNotEqual(failed.returncode,0); self.assertIn("EXECUTION_SPEC_MISMATCH",failed.stdout)
            for item in repo.state["evidence"]:
                if item["id"] == "EVD-RAW": item["status"]="stale"; item["stale_reason"]="contract changed"
            repo.state["implementation_tasks"][0]["evidence_ids"] = []
            repo.state["metrics"][0]["evidence_ids"] = []
            repo.state["overall_acceptance"]["evidence_ids"] = []
            repo.write_state(); self.record_raw(repo,"new.json","EVD-NEW"); self.assertEqual(self.validate(repo).returncode,0)
        finally: repo.close()

    def test_missing_each_deliverable_is_rejected(self):
        for missing in ("app.txt","README.md","records/TASK-001/evidence/run-result.txt"):
            repo=self.prepare()
            try:
                self.record_raw(repo); self.assertEqual(self.validate(repo).returncode,0); (repo.root/missing).unlink(); failed=self.validate(repo); self.assertNotEqual(failed.returncode,0); self.assertIn("SPEC_DELIVERABLE",failed.stdout)
            finally: repo.close()

if __name__ == "__main__": unittest.main()
