#!/usr/bin/env python3
import argparse,copy,hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'skill/veriflow/tests'));sys.path.insert(0,str(ROOT/'skill/veriflow/scripts'))
from test_spec_binding import SpecBindingTests
from authorization_snapshot import capture_snapshot

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);helper=SpecBindingTests();repo=helper.prepare();logs=[]
 def gate(name,label,want=0,code=None,target='origin/isolated'):
  repo.write_state();argv=[sys.executable,str(ROOT/'skill/veriflow/scripts/validate_task.py'),str(repo.manifest),'--repo',str(repo.root),'--gate',name,'--target',target];t=time.time();r=subprocess.run(argv,cwd=repo.root,capture_output=True,text=True,timeout=30,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'});d={'label':label,'argv':argv,'cwd':str(repo.root),'start':t,'end':time.time(),'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'expected_exit':want,'expected_code':code};logs.append(d)
  with (out/'commands.jsonl').open('a') as f:f.write(json.dumps(d,ensure_ascii=False)+'\n')
  assert r.returncode==want,d
  if code:assert code in {x['code'] for x in json.loads(r.stdout)['errors']},d
 def completed(action,rev,target,receipt):
  snap=capture_snapshot(repo.state,action,target,rev);repo.record_action('ACT-'+str(len(repo.state['actions'])+1),action,receipt,revision=rev,target=target);repo.state['actions'][-1]['authorization_snapshot']=snap
 try:
  helper.record_raw(repo)
  for action in ['commit','push','merge','deploy']:repo.authorize(action)
  token=repo.revision();snap=capture_snapshot(repo.state,'commit','local',token);repo.write_state()
  t=time.time();sha=repo.commit_all('actual isolated commit for temporal gate tests');logs.append({'label':'real-local-commit','started_at_epoch':t,'ended_at_epoch':time.time(),'receipt':sha,'scope':'temporary repository only'})
  repo.record_action('ACT-1','commit',sha,revision=token,target='local');repo.state['actions'][-1]['authorization_snapshot']=snap;repo.state['authorization']['commit']['status']='not_authorized'
  gate('push','revoked-prior-commit-new-push')
  completed('push',sha,'origin/isolated','fixture:simulated remote receipt; no push performed');repo.state['authorization']['push']['status']='not_authorized';repo.state['delivery'].update(remote_ci='passed',remote_ci_revision=sha)
  gate('merge','revoked-prior-push-new-merge',target='isolated/main')
  completed('merge',sha,'isolated/main','fixture:simulated merge receipt; no merge performed');repo.state['authorization']['merge']['status']='not_authorized'
  gate('deploy','revoked-prior-merge-new-deploy',target='fixture:local-only')
  repo.state['authorization']['deploy']['status']='not_authorized';gate('deploy','current-deploy-revoked',1,'AUTH_DEPLOY',target='fixture:local-only')
  repo.state['authorization']['deploy']['status']='authorized';old=repo.state['actions'][1].pop('authorization_snapshot');gate('deploy','unknown-history-blocks',1,'AUTH_SNAPSHOT_UNKNOWN',target='fixture:local-only');repo.state['actions'][1]['authorization_snapshot']=old
  wrong=repo.state['actions'][2];wrong['revision']='different-revision';wrong['authorization_snapshot']['revision']='different-revision'
  # Use a genuine new snapshot for the deliberately different revision so
  # this counterexample tests version selection, not a broken digest.
  repo.state['authorization']['merge']['status']='authorized';wrong['authorization_snapshot']=capture_snapshot(repo.state,'merge','isolated/main','different-revision');repo.state['authorization']['merge']['status']='not_authorized'
  gate('deploy','unrelated-history-does-not-support',1,'AUTH_MERGE',target='fixture:local-only')
  (out/'state.json').write_text(json.dumps(repo.state,ensure_ascii=False,indent=2))
 finally:repo.close()
 (out/'result.json').write_text(json.dumps({'ok':True,'gate_count':6,'boundary':'only local Git commit actually performed; push/merge/remote CI receipts are explicitly simulated fixture state, no production or network action','tool_sha256':hashlib.sha256((ROOT/'skill/veriflow/scripts/validate_task.py').read_bytes()).hexdigest()},indent=2));print('temporal chain gates passed')
if __name__=='__main__':main()
