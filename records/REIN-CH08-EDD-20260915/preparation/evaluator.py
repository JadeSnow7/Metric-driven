#!/usr/bin/env python3
"""Independent dynamic evaluator for the frozen ch08 CLI envelope."""
from __future__ import annotations
import argparse, json, subprocess, tempfile
from pathlib import Path

STRATEGIES={"on-demand","window","summary","retrieval"}
def run_cli(command, root, strategy=None, budget=None):
    args=command+(["--data-root",str(root)] if root else [])
    if strategy: args += ["--strategy",strategy]
    if budget is not None: args += ["--budget",str(budget)]
    p=subprocess.run(args,capture_output=True,text=True,timeout=180)
    if p.returncode: raise AssertionError(f"CLI failed: {p.stderr}")
    return json.loads(p.stdout)
def validate_envelope(value):
    assert value.get("unit")=="estimated-bytes-v1"
    rows=value.get("results"); assert isinstance(rows,list) and rows
    seen=set()
    for row in rows:
        key=(row.get("taskId"),row.get("strategy")); assert key not in seen; seen.add(key)
        assert row["strategy"] in STRATEGIES and isinstance(row["messages"],list)
        assert isinstance(row["estimatedUnits"],int) and row["estimatedUnits"]>=0
        assert isinstance(row["operations"],list) and isinstance(row["callRecords"],list)
        assert row.get("serviceTokens") is None and row.get("quality") is None
        if row["status"]=="context_budget_exhausted": assert row["modelCalls"]==0 and row["answer"] is None and not row["operations"]
        if row["status"]=="completed":
            assert row["answer"] is not None
            claims=row["answer"].get("claims",[]); assert isinstance(claims,list)
            for claim in claims: assert all(isinstance(claim.get(k),str) and claim[k] for k in ("field","value","source"))
            if row["answer"].get("insufficientEvidence"): assert not claims
    return value
def main():
    p=argparse.ArgumentParser(); p.add_argument("--command",nargs="+",required=True); p.add_argument("--root",type=Path,required=True); p.add_argument("--negative",action="store_true"); a=p.parse_args()
    if a.negative:
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); import shutil; shutil.copytree(a.root,root,dirs_exist_ok=True)
            index=json.loads((root/"index.json").read_text()); index["documents"].append(index["documents"][0]); (root/"index.json").write_text(json.dumps(index))
            try: run_cli(a.command,root); raise AssertionError("duplicate metadata was silently accepted")
            except (AssertionError,subprocess.CalledProcessError): return 0
    value=validate_envelope(run_cli(a.command,a.root));
    if not any(r["strategy"] in STRATEGIES for r in value["results"]): raise AssertionError("missing strategies")
    print(json.dumps({"rows":len(value["results"]),"strategies":sorted({r["strategy"] for r in value["results"]})}))
if __name__=="__main__": main()
