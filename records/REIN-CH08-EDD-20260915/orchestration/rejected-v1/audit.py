#!/usr/bin/env python3
"""Summarize auditable model/prompt/tool references for one sealed run."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("seal",type=Path); p.add_argument("--session",type=Path); a=p.parse_args()
    root=a.seal.resolve(); meta=json.loads((root/"run-meta.json").read_text()); result={"argv":meta.get("argv"),"usage":meta.get("usage"),"token_count":meta.get("token_count"),"elapsed_seconds":meta.get("elapsed_seconds"),"session":meta.get("session"),"models":[],"efforts":[],"skill_references":[],"reads":[],"writes":[],"isolation_limit":"Shell-visible calls do not prove strict OS isolation."}
    if a.session and a.session.is_file():
        for line in a.session.read_text(errors="replace").splitlines():
            try: item=json.loads(line)
            except json.JSONDecodeError: continue
            if item.get("type")=="turn.started": result["models"].append(item.get("model")); result["efforts"].append(item.get("reasoning_effort"))
            text=json.dumps(item,ensure_ascii=False)
            if "evidence-driven-development" in text: result["skill_references"].append({"kind":"mentioned_or_read","text":text[:300]})
    print(json.dumps(result,ensure_ascii=False,indent=2)); return 0
if __name__ == "__main__": raise SystemExit(main())
