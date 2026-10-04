#!/usr/bin/env python3
"""Seal a selected run with content hashes and exact session evidence."""
import argparse, hashlib, json, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
EXCLUDE={".git","node_modules","target","cargo-target","build","cache",".cache","dist"}
RUN_FILES={"argv.json","run.json","stdout.jsonl","stderr.txt","final.md","classification","classification.json"}
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""): h.update(b)
 return h.hexdigest()
def listing(r): return {p.relative_to(r).as_posix():p for p in r.rglob("*") if p.is_file() and not any(x in EXCLUDE for x in p.relative_to(r).parts)}
def main(argv=None):
 p=argparse.ArgumentParser();
 for n in ("source","work","run","output"): p.add_argument("--"+n,type=Path,required=True)
 p.add_argument("--source-manifest",type=Path); p.add_argument("--session-path",type=Path); p.add_argument("--thread-id",required=True); a=p.parse_args(argv)
 s,w,r,o=[x.resolve() for x in (a.source,a.work,a.run,a.output)]; created=False
 try:
  if o.exists(): raise RuntimeError("refusing to overwrite existing seal")
  if len({s,w,r,o})<4 or not all(x.is_dir() for x in (s,w,r)): raise RuntimeError("source/work/run/output must differ and exist")
  src={k:sha(v) for k,v in listing(s).items()}; prod={k:sha(v) for k,v in listing(w).items()}
  if a.source_manifest:
   exp=json.loads(a.source_manifest.read_text()); exp=exp.get("source",exp)
   if isinstance(exp,dict) and isinstance(exp.get("files"),list): exp={x["path"]:x["sha256"] for x in exp["files"]}
   if exp!=src: raise RuntimeError("common source manifest mismatch")
  o.mkdir(); created=True; (o/"source-manifest.json").write_text(json.dumps({"source":src,"work":prod,"added":sorted(set(prod)-set(src)),"deleted":sorted(set(src)-set(prod)),"modified":sorted(k for k in set(src)&set(prod) if src[k]!=prod[k])},indent=2)+"\n")
  shutil.copytree(w,o/"work",ignore=shutil.ignore_patterns(*EXCLUDE)); (o/"run").mkdir()
  for f in r.iterdir():
   if f.is_dir() and f.name in EXCLUDE: continue
   if f.name not in RUN_FILES: raise RuntimeError("run file not allowed: "+f.name)
   shutil.copy2(f,o/"run"/f.name)
  sm={"thread_id":a.thread_id,"token_events":[],"token_count":{"total":None,"last":None,"cache":None,"reasoning":None},"turn_context":[],"elapsed":None}
  if a.session_path:
   found=False
   for line in a.session_path.read_text(errors="replace").splitlines():
    try:x=json.loads(line)
    except json.JSONDecodeError: continue
    if x.get("type")=="session_meta" and x.get("payload",{}).get("id")==a.thread_id: found=True
    if x.get("type")=="event_msg" and x.get("payload",{}).get("type")=="token_count": sm["token_events"].append(x.get("payload",{})); sm["token_count"]=x.get("payload",{}).get("info",{})
    if x.get("type")=="turn_context": sm["turn_context"].append({"model":x.get("payload",{}).get("model"),"effort":x.get("payload",{}).get("effort")})
   if not found: raise RuntimeError("session path does not contain exact thread id")
   shutil.copy2(a.session_path,o/"session.jsonl")
  try: sm["elapsed"]=json.loads((r/"run.json").read_text()).get("elapsed_seconds")
  except Exception: pass
  (o/"git.json").write_text(json.dumps({"head":subprocess.run(["git","rev-parse","HEAD"],cwd=w,text=True,capture_output=True).stdout.strip(),"diff":subprocess.run(["git","diff","--binary"],cwd=w,text=True,capture_output=True).stdout},indent=2)+"\n")
  (o/"meta.json").write_text(json.dumps({"sealed_at":datetime.now(timezone.utc).isoformat(),"argv":sys.argv,"session":sm,"exclusions":sorted(EXCLUDE)},indent=2)+"\n"); print(json.dumps({"ok":True,"output":str(o)})); return 0
 except Exception as e:
  if created: (o/"error.json").write_text(json.dumps({"ok":False,"error":str(e)})+"\n")
  print(json.dumps({"ok":False,"error":str(e)})); return 1
if __name__=="__main__": raise SystemExit(main())
