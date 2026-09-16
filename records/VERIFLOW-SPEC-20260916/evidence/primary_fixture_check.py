#!/usr/bin/env python3
import hashlib,json,os,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];S=ROOT/'skill/veriflow/scripts'
def main():
 out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False); logs=[]
 def run(argv,cwd,label,expected=0):
  start=time.time();r=subprocess.run([str(x) for x in argv],cwd=cwd,capture_output=True,text=True,timeout=30,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
  entry={'label':label,'argv':[str(x) for x in argv],'cwd':str(cwd),'start':start,'end':time.time(),'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'expected_exit':expected};logs.append(entry)
  with (out/'commands.jsonl').open('a') as f:f.write(json.dumps(entry)+'\n')
  assert r.returncode==expected,entry
  return r
 with tempfile.TemporaryDirectory(prefix='veriflow-fixtures-') as t:
  parent=Path(t).resolve();repo=parent/'repo';repo.mkdir();ext=parent/'fixture.txt';ext.write_text('fixture\n');marker=repo/'marker'
  run(['git','init','-q'],repo,'init');(repo/'app.txt').write_text('baseline\n');run(['git','add','app.txt'],repo,'add');run(['git','-c','user.name=Test','-c','user.email=test@example.invalid','-c','commit.gpgsign=false','commit','--no-verify','-qm','base'],repo,'commit');base=run(['git','rev-parse','HEAD'],repo,'head').stdout.strip()
  state=json.loads((ROOT/'skill/veriflow/assets/templates/task-state.example.json').read_text());state['schema_version']='1.2';state.pop('spec',None);state.pop('binding',None);state['baseline'].update(git_ref=base,prepared_at='2026-09-16T00:00:00Z');state['sources'][0]['reference']='fixture:primary';state['recovery_strategy']['owner']='primary';state['authorization']['push'].pop('scope',None)
  record=repo/'records/TASK-001';record.mkdir(parents=True);manifest=record/'task-state.json'
  def save():manifest.write_text(json.dumps(state))
  def record_input(path,name,expected):
   save();return run([sys.executable,S/'record_execution.py','--repo',repo,'--state',manifest,'--cwd',repo,'--output',record/'evidence'/name,'--fixture',path,'--',sys.executable,'-c',f"from pathlib import Path;Path({str(marker)!r}).write_text('ran')"],repo,name,expected)
  record_input(ext,'undeclared.json',2);assert not marker.exists()
  state['baseline']['external_inputs']=[{'path':str(ext),'sha256':hashlib.sha256(ext.read_bytes()).hexdigest(),'identity':'fixture:v1','reproduction':'UTF-8 fixture followed by newline'}]
  for alias in [repo/'alias.txt',parent/'alias.txt']:
   alias.symlink_to(ext);record_input(alias,'alias-'+str(len(logs))+'.json',2);assert not marker.exists()
  # The allowed control only reads the fixture; it does not create a product during recording.
  save();raw=record/'evidence/canonical.json';run([sys.executable,S/'record_execution.py','--repo',repo,'--state',manifest,'--cwd',repo,'--output',raw,'--fixture',ext,'--',sys.executable,'-c',f"from pathlib import Path;print(Path({str(ext)!r}).read_text(),end='')"],repo,'canonical')
  data=json.loads(raw.read_text());state['evidence']=[{'id':'EVD-001','path':str(raw.relative_to(repo)),'kind':'execution','supports':['MET-001'],'revision':data['revision'],'sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'status':'current','result':'passed','observed_at':data['ended_at']}];save()
  run([sys.executable,S/'validate_task.py',manifest,'--repo',repo,'--gate','record'],repo,'canonical-validates')
  ext.unlink();state['evidence'][0].update(status='stale',stale_reason='external fixture removed after original run');save();run([sys.executable,S/'validate_task.py',manifest,'--repo',repo,'--gate','record'],repo,'historical-missing-input')
  raw.write_text(raw.read_text()+' ');r=run([sys.executable,S/'validate_task.py',manifest,'--repo',repo,'--gate','record'],repo,'tamper-detected',1);assert 'EVIDENCE_HASH_MISMATCH' in {x['code'] for x in json.loads(r.stdout)['errors']}
 (out/'result.json').write_text(json.dumps({'ok':True,'checks':['undeclared denied before command','repository/external aliases denied before command','declared canonical fixture records and validates','missing stale input retained','raw tamper detected'],'script_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in S.glob('*.py')}},indent=2));print('fixture checks passed')
if __name__=='__main__':main()
