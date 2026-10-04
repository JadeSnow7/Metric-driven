#!/usr/bin/env python3
import argparse,copy,hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'skill/veriflow/tests'))
sys.path.insert(0,str(ROOT/'skill/veriflow/scripts'))
from test_spec_binding import SpecBindingTests
from authorization_snapshot import capture_snapshot

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);results=[]
 def gate(repo,label,gate='acceptance',extra=(),want=0,code=None):
  repo.write_state();argv=[sys.executable,str(ROOT/'skill/veriflow/scripts/validate_task.py'),str(repo.manifest),'--repo',str(repo.root),'--gate',gate,*extra];t=time.time();r=subprocess.run(argv,cwd=repo.root,capture_output=True,text=True,timeout=30,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'});d={'label':label,'argv':argv,'cwd':str(repo.root),'start':t,'end':time.time(),'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'expected_exit':want,'expected_code':code};results.append(d)
  with (out/'commands.jsonl').open('a') as f:f.write(json.dumps(d,ensure_ascii=False)+'\n')
  assert r.returncode==want,d
  data=json.loads(r.stdout)
  if code:assert code in {e['code'] for e in data['errors']},d
  if want:assert data.get('spec_satisfaction')!='satisfied',d
  return data
 helper=SpecBindingTests()
 for label,mutate,code in [
  ('target',lambda r:r.state['metrics'][0].update(target='different success condition'),'EXECUTION_SPEC_MISMATCH'),
  ('method',lambda r:r.state['metrics'][0].update(method='different verification method'),'EXECUTION_SPEC_MISMATCH'),
  ('main-goal',lambda r:r.state['main_tasks'][0].update(goal='different requested outcome'),'EXECUTION_SPEC_MISMATCH'),
  ('product',lambda r:(r.root/'app.txt').write_text('changed product\n'),'EXECUTION_REVISION_STALE'),
  ('metadata-product',lambda r:(r.root/'records/TASK-001/evidence/run-result.txt').write_text('changed artifact\n'),'EXECUTION_REVISION_STALE'),
 ]:
  repo=helper.prepare()
  try:
   helper.record_raw(repo);gate(repo,label+'-control');mutate(repo);repo.bind_current_revision();gate(repo,label+'-cannot-refresh-outer',want=1,code=code)
  finally:repo.close()
 repo=helper.prepare()
 try:
  helper.record_raw(repo);gate(repo,'review-control');repo.state['changes'][0]['paths'].remove('README.md');gate(repo,'missing-review',want=1,code='SPEC_DELIVERABLE_UNREVIEWED')
 finally:repo.close()
 repo=helper.prepare()
 try:
  helper.record_raw(repo);gate(repo,'stale-control');repo.state['evidence'][0].update(status='stale',stale_reason='cannot support current conclusion');gate(repo,'stale-cannot-satisfy',want=1,code='METRIC_EVIDENCE_NOT_CURRENT')
  raw=repo.root/repo.state['evidence'][0]['path'];raw.write_text(raw.read_text()+' ');gate(repo,'stale-tamper',want=1,code='EVIDENCE_HASH_MISMATCH')
 finally:repo.close()
 repo=helper.prepare()
 try:
  helper.record_raw(repo);gate(repo,'manual-control');e=repo.state['evidence'][0];e['kind']='test_report';gate(repo,'manual-no-spec',want=1,code='EVIDENCE_SPEC_MISMATCH')
 finally:repo.close()
 repo=helper.prepare()
 try:
  helper.record_raw(repo);gate(repo,'auth-control');rev=repo.revision();repo.state['authorization']['migrate']={'status':'authorized','source_id':'SRC-001','scope':['local:a','local:b']}
  snap=capture_snapshot(repo.state,'migrate','local:a',rev)
  item={'id':'ACT-001','kind':'simulation','status':'completed','authorization_action':'migrate','target':'local:a','revision':rev,'receipt':'fixture:simulated completed receipt','idempotency_key':'fixture:a','authorization_snapshot':snap};repo.state['actions']=[item];repo.state['authorization']['migrate']['status']='not_authorized'
  gate(repo,'auth-history-after-revoke');gate(repo,'new-revoked','action',['--action','migrate','--target','local:b','--revision',rev],1,'AUTH_ACTION')
  item.pop('authorization_snapshot');data=gate(repo,'history-unknown','record');assert 'AUTH_SNAPSHOT_UNKNOWN' in {x['code'] for x in data['warnings']}
  gate(repo,'unknown-blocks-action','action',['--action','migrate','--target','local:b','--revision',rev],1,'AUTH_SNAPSHOT_UNKNOWN')
  gate(repo,'unknown-blocks-commit','local-commit',want=1,code='AUTH_SNAPSHOT_UNKNOWN')
 finally:repo.close()
 (out/'result.json').write_text(json.dumps({'ok':True,'gate_count':len(results),'tool_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'skill/veriflow/scripts').glob('*.py')}},indent=2));print('adversarial checks passed',len(results))
if __name__=='__main__':main()
