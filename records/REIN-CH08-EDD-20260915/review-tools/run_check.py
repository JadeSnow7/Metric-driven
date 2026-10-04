#!/usr/bin/env python3
import argparse,hashlib,json,os,signal,subprocess,tempfile,time
from datetime import datetime,timezone
from pathlib import Path
EXCLUDE={'.git','node_modules','target','cache','records'}
def ts(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def hashes(root):
 out={}
 for base,dirs,names in os.walk(root,topdown=True):
  base=Path(base); relbase=base.relative_to(root)
  dirs[:]=[d for d in dirs if d not in EXCLUDE and not (d=='dist' and '.vitepress' in relbase.parts)]
  for name in names:
   p=base/name; rel=p.relative_to(root)
   out[rel.as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
 return out
def main():
 p=argparse.ArgumentParser(); p.add_argument('--cwd',type=Path,required=True); p.add_argument('--output',type=Path,required=True); p.add_argument('--timeout',type=float,default=180); p.add_argument('command',nargs=argparse.REMAINDER); a=p.parse_args(); cmd=a.command[1:] if a.command[:1]==['--'] else a.command; cwd=a.cwd.resolve(); out=a.output.resolve()
 if not cmd: p.error('command required after --')
 if out.exists(): print(json.dumps({'ok':False,'error':'output already exists'})); return 1
 out.mkdir(parents=True); start=ts(); mono=time.monotonic(); code=None; timed=False; launch_error=None; stdout=b''; stderr=b''; wrapper=0; before=hashes(cwd)
 try:
  proc=subprocess.Popen(cmd,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
  try: stdout,stderr=proc.communicate(timeout=a.timeout); code=proc.returncode; wrapper=code
  except subprocess.TimeoutExpired:
   timed=True; wrapper=124; os.killpg(proc.pid,signal.SIGKILL); stdout,stderr=proc.communicate(); code=proc.returncode
 except FileNotFoundError as e: launch_error=str(e); wrapper=127
 except OSError as e: launch_error=str(e); wrapper=127
 rec={'argv':cmd,'cwd':str(cwd),'started_at':start,'ended_at':ts(),'elapsed_seconds':time.monotonic()-mono,'exit_code':code,'timed_out':timed,'wrapper_exit_code':wrapper,'launch_error':launch_error,'stdout':stdout.decode('utf-8','replace'),'stderr':stderr.decode('utf-8','replace'),'stdout_base64':__import__('base64').b64encode(stdout).decode(),'stderr_base64':__import__('base64').b64encode(stderr).decode(),'source_hashes_before':before,'source_hashes_after':hashes(cwd)}
 (out/'stdout.bin').write_bytes(stdout); (out/'stderr.bin').write_bytes(stderr)
 with tempfile.NamedTemporaryFile('w',dir=out,delete=False) as f: json.dump(rec,f,indent=2); f.write('\n'); tmp=Path(f.name)
 tmp.replace(out/'run.json'); return wrapper or (code if code is not None else 127)
if __name__=='__main__': raise SystemExit(main())
