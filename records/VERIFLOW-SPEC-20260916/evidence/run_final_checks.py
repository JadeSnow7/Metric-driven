#!/usr/bin/env python3
import argparse,hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 files=list((ROOT/'skill/veriflow').rglob('*'))+[ROOT/'README.md',ROOT/'tools/validate_repository.py',ROOT/'tools/tests/test_validate_repository.py',ROOT/'records/VERIFLOW-SPEC-20260916/SPEC.md']
 before={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file() and '__pycache__' not in p.parts}
 commands=[('skill-tests',[sys.executable,'-m','unittest','discover','-s','skill/veriflow/tests','-v']),('repository-tests',[sys.executable,'-m','unittest','tools/tests/test_validate_repository.py','-v']),('repository-static',[sys.executable,'tools/validate_repository.py']),('diff-check',['git','diff','--check']),('syntax',[sys.executable,'-c',"from pathlib import Path; ps=list(Path('skill/veriflow').rglob('*.py')); [(compile(p.read_bytes(),str(p),'exec')) for p in ps]; print(f'compiled {len(ps)} Python files without writing pyc')"]),('skill-format',[sys.executable,'/Users/huaodong/.codex/skills/.system/skill-creator/scripts/quick_validate.py',str(ROOT/'skill/veriflow')])]
 results=[]
 for label,argv in commands:
  t=time.time();r=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True,timeout=180,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':'/private/tmp/veriflow-validation-deps'})
  data={'label':label,'argv':argv,'cwd':str(ROOT),'started_at_epoch':t,'ended_at_epoch':time.time(),'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
  (out/(label+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2));results.append({'label':label,'exit_code':r.returncode});print(label,r.returncode,flush=True)
 after={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file() and '__pycache__' not in p.parts}
 (out/'manifest.json').write_text(json.dumps({'python':sys.version,'before':before,'after':after,'unchanged':before==after,'results':results},ensure_ascii=False,indent=2))
 return int(before!=after or any(r['exit_code'] for r in results))
if __name__=='__main__':raise SystemExit(main())
