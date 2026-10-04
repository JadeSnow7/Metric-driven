#!/usr/bin/env python3
"""Preparation-only bounded runner; formal arms are started only by the owner."""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

def utc(): return datetime.now(timezone.utc).isoformat()
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def route_args(coder, workspace, prompt, final):
    import tomllib
    cfg=tomllib.loads(coder.read_text())
    return ["codex","exec","--ignore-user-config","--json","--approve-for-me","--skip-git-repo-check",
            "-C",str(workspace),"-m",cfg["model"],"-c",f"model_reasoning_effort={cfg['model_reasoning_effort']}",
            "-c","developer_instructions="+json.dumps(cfg.get("developer_instructions","")),"-o",str(final),"-"]

def run(args):
    out=args.output; out.mkdir(parents=True,exist_ok=False)
    argv=route_args(args.coder,args.workspace,args.prompt,out/"final.md")
    started=utc(); t=time.monotonic(); env=os.environ.copy(); env.update({"CARGO_TARGET_DIR":str(out/"cargo-target"),"CARGO_INCREMENTAL":"0","CARGO_PROFILE_DEV_DEBUG":"0","CARGO_PROFILE_TEST_DEBUG":"0"})
    (out/"argv.json").write_text(json.dumps({"argv":argv,"cwd":str(args.workspace),"started_at":started,"prompt_sha256":sha(args.prompt)},indent=2)+"\n")
    stdout_file=(out/"stdout.jsonl").open("w"); stderr_file=(out/"stderr.txt").open("w")
    p=subprocess.Popen(argv,cwd=args.workspace,env=env,stdin=subprocess.PIPE,stdout=stdout_file,stderr=stderr_file,text=True,start_new_session=True)
    p.stdin.write(args.prompt.read_text()); p.stdin.close(); interrupted=False
    try: p.wait(timeout=args.timeout)
    except subprocess.TimeoutExpired:
        interrupted=True; os.killpg(p.pid,15)
        try: p.wait(timeout=10)
        except subprocess.TimeoutExpired: os.killpg(p.pid,9); p.wait(timeout=10)
    stdout_file.close(); stderr_file.close()
    stdout=(out/"stdout.jsonl").read_text(errors="replace"); stderr=(out/"stderr.txt").read_text(errors="replace")
    if interrupted: (out/"classification").write_text("resource_interruption\n")
    meta={"argv":argv,"cwd":str(args.workspace),"started_at":started,"ended_at":utc(),"elapsed_seconds":time.monotonic()-t,"exit_code":p.returncode,"usage":None,"session_audit":"stdout.jsonl","classification":(out/"classification").read_text().strip() if (out/"classification").exists() else ("completed" if p.returncode==0 else "process_exit")}
    for line in reversed(stdout.splitlines()):
        try:
            event=json.loads(line)
            if event.get("usage") is not None: meta["usage"]=event["usage"]; break
        except json.JSONDecodeError: pass
    (out/"run.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n")
    return p.returncode

def audit(args):
    run=json.loads(args.run.read_text()); required=("argv","cwd","started_at","ended_at","exit_code","usage")
    missing=[x for x in required if x not in run]
    if missing: raise SystemExit("missing run fields: "+",".join(missing))
    print(json.dumps({"run":str(args.run),"argv":run["argv"],"cwd":run["cwd"],"exit_code":run["exit_code"],"usage":run["usage"],"stdout_sha256":sha(args.run.parent/"stdout.jsonl"),"stderr_sha256":sha(args.run.parent/"stderr.txt")},ensure_ascii=False))

def main():
    p=argparse.ArgumentParser(); s=p.add_subparsers(dest="cmd",required=True)
    r=s.add_parser("run"); r.add_argument("--coder",type=Path,required=True); r.add_argument("--workspace",type=Path,required=True); r.add_argument("--prompt",type=Path,required=True); r.add_argument("--output",type=Path,required=True); r.add_argument("--timeout",type=int,default=2700); r.set_defaults(fn=run)
    a=s.add_parser("audit"); a.add_argument("--run",type=Path,required=True); a.set_defaults(fn=audit)
    x=p.parse_args(); return x.fn(x)
if __name__=="__main__": raise SystemExit(main())
