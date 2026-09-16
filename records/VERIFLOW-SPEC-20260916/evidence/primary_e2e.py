#!/usr/bin/env python3
"""Primary-thread actual, local-only integration check; creates no production actions."""
import argparse, copy, hashlib, json, os, subprocess, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / 'skill/veriflow/scripts'
PYTHON = sys.executable

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    logs=[]; checks=[]
    hashes={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'skill/veriflow').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    (out/'inputs.json').write_text(json.dumps({'python':sys.version,'inputs':hashes,'spec':sha(ROOT/'records/VERIFLOW-SPEC-20260916/SPEC.md')},indent=2))
    def run(argv,cwd,label,expected=0,codes=()):
        start=time.time(); r=subprocess.run([str(x) for x in argv],cwd=cwd,text=True,capture_output=True,timeout=45,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
        entry={'label':label,'argv':[str(x) for x in argv],'cwd':str(cwd),'started_at_epoch':start,'ended_at_epoch':time.time(),'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'expected_exit':expected,'expected_codes':list(codes)}
        logs.append(entry)
        with (out/'commands.jsonl').open('a') as f:f.write(json.dumps(entry,ensure_ascii=False)+'\n')
        assert r.returncode==expected,(label,entry)
        if codes:
            got={e['code'] for e in json.loads(r.stdout)['errors']}
            assert set(codes)<=got,(label,got)
        return r
    with tempfile.TemporaryDirectory(prefix='veriflow-primary-e2e-') as td:
        repo=Path(td).resolve(); record=repo/'records/TASK-001';record.mkdir(parents=True);statepath=record/'task-state.json'
        def save():statepath.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
        def gate(name,label,expected=0,codes=(),extra=()):
            save();r=run([PYTHON,SCRIPTS/'validate_task.py',statepath,'--repo',repo,'--gate',name,*extra],repo,label,expected,codes)
            (out/(label+'-state.json')).write_text(statepath.read_text());return json.loads(r.stdout)
        def revision():
            save();return run([PYTHON,SCRIPTS/'validate_task.py',statepath,'--repo',repo,'--print-revision'],repo,'revision').stdout.strip()
        run(['git','init','-q','-b','main'],repo,'git-init')
        run(['git','config','user.name','Isolated Veriflow'],repo,'git-name')
        run(['git','config','user.email','test@example.invalid'],repo,'git-email')
        (repo/'app.py').write_text("print('baseline')\n")
        run(['git','add','app.py'],repo,'git-add');run(['git','-c','commit.gpgsign=false','commit','--no-verify','-qm','baseline'],repo,'git-baseline')
        base=run(['git','rev-parse','HEAD'],repo,'git-head').stdout.strip()
        state=json.loads((ROOT/'skill/veriflow/assets/templates/task-state.example.json').read_text())
        state['schema_version']='1.3';state['task'].update(id='TASK-001',title='隔离行数工具',status='in_progress')
        state['discovery'].update(status='ready',expected_outcome='UTF-8 行数为 2',scope='README/app/sample/result')
        state['sources'][0].update(reference='fixture:primary-e2e-request',summary='构建隔离行数示例并验证，不操作外部服务')
        state['sources'].append({'id':'SRC-002','kind':'user_requirement','reference':'fixture:local-simulation-authorization','summary':'只允许临时仓库内写入模拟迁移标记','adoption':'accepted'})
        state['baseline'].update(git_ref=base,prepared_at='2026-09-16T00:00:00Z',foreign_paths=[])
        files=['README.md','app.py','sample.txt','result.txt'];specfile='records/TASK-001/SPEC.md'
        state['spec']={'version':'DEMO-1','authority':specfile,'source_ids':['SRC-001'],'goal_ref':'discovery.expected_outcome','scope_ref':'discovery.scope','constraints':['only local temp files'],'exceptions':['empty input yields 0'],'conditions':[{'id':'SC-001','metric_ids':['MET-001'],'deliverables':files}],'contracts':[specfile],'open_items':[]}
        state['binding']={'receipt_paths':['records/TASK-001/STATUS.md','records/TASK-001/action-marker.txt']}
        state['main_tasks']=state['main_tasks'][:1];state['main_tasks'][0].update(goal='行数示例',metric_ids=['MET-001'])
        state['metrics']=state['metrics'][:1];state['metrics'][0].update(name='行数等于2',target='stdout is 2 newline',method='run actual program and compare saved result',environment_data='local Python with UTF-8 two-line sample',verification='execution')
        state['implementation_tasks'][0].update(file_scope=files+[specfile],acceptance=['MET-001'],scope='实现并核验本地示例')
        for key in state['authorization']:state['authorization'][key]={'status':'not_authorized','source_id':None}
        state['authorization']['migrate']={'status':'authorized','source_id':'SRC-002','scope':['temp:one','temp:two']}
        state['recovery_strategy'].update(trigger='local simulation interrupted',steps=['read action marker before retry'],owner='primary')
        state['overall_acceptance']={'metric_ids':['MET-001'],'evidence_ids':[],'status':'undetermined'}
        (record/'SPEC.md').write_text('# DEMO-1\nREADME、程序、样本和真实结果齐全，实际输出2。\n')
        gate('implementation','01-ready')
        (repo/'app.py').write_text("import pathlib,sys\nprint(len(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8').splitlines()))\n")
        (repo/'README.md').write_text('# 行数示例\n运行 `python app.py sample.txt`，输出 2。\n')
        (repo/'sample.txt').write_text('苹果\n香蕉\n')
        r=run([PYTHON,'app.py','sample.txt'],repo,'02-generate-result');assert r.stdout=='2\n';(repo/'result.txt').write_text(r.stdout)
        def evidence(eid,name):
            save();path=record/'evidence'/name
            run([PYTHON,SCRIPTS/'record_execution.py','--output',path,'--repo',repo,'--state',statepath,'--cwd',repo,'--source','app.py','--fixture','sample.txt','--require-stdout','--',PYTHON,'-c',"import subprocess,sys,pathlib; p=subprocess.run([sys.executable,'app.py','sample.txt'],capture_output=True,text=True,check=True); assert p.stdout=='2\\n'; assert pathlib.Path('result.txt').read_text()==p.stdout; print(p.stdout,end='')"],repo,'record-'+eid)
            raw=json.loads(path.read_text());assert raw['result']=='passed';assert raw['spec_version']=='DEMO-1';assert raw['spec_sha256']
            (out/name).write_text(path.read_text())
            item={'id':eid,'path':str(path.relative_to(repo)),'kind':'execution','supports':['MET-001'],'revision':raw['revision'],'spec_version':raw['spec_version'],'spec_sha256':raw['spec_sha256'],'sha256':sha(path),'status':'current','result':'passed','observed_at':raw['ended_at']}
            state['evidence'].append(item);state['metrics'][0].update(status='passed',evidence_ids=[eid]);state['implementation_tasks'][0].update(status='verified',evidence_ids=[eid]);state['main_tasks'][0]['status']='verified'
            state['overall_acceptance'].update(status='passed',evidence_ids=[eid]);state['delivery']['local_validation']='passed'
            state['changes']=[{'id':'CHG-001','implementation_task_ids':['IT-001'],'paths':files+[specfile,'records/TASK-001/evidence'],'evidence_ids':[eid],'revision':raw['revision'],'status':'reviewed'}];save();return item
        first=evidence('EVD-001','first-execution.json')
        gate('record','03-record');accepted=gate('acceptance','04-acceptance');assert accepted['spec_version']=='DEMO-1'
        before=revision();(record/'STATUS.md').write_text('追加运行回执\n');assert revision()==before
        state=json.loads(statepath.read_text());state['task']['mode']='resume';gate('acceptance','05-resume')
        checks.append('record -> acceptance -> reload/resume; appended receipt preserves binding')
        (record/'SPEC.md').write_text((record/'SPEC.md').read_text()+'复核实际保存的结果。\n')
        gate('acceptance','06-spec-changed',1)
        first=state['evidence'][0];first.update(status='stale',stale_reason='同版本Spec正文补充验证说明，保留旧运行')
        second=evidence('EVD-002','second-execution.json');gate('acceptance','07-new-with-history')
        checks.append('same-label Spec bytes invalidate old execution; new execution works beside preserved history')
        snapshot_result=run([PYTHON,SCRIPTS/'authorization_snapshot.py','--state',statepath,'--action','migrate','--target','temp:one','--revision',second['revision']],repo,'08-capture-authorization')
        snapshot=json.loads(snapshot_result.stdout)
        gate('action','09-before-action',extra=['--action','migrate','--target','temp:one','--revision',second['revision']])
        action={'id':'ACT-001','kind':'local-simulation','authorization_action':'migrate','status':'in_progress','target':'temp:one','revision':second['revision'],'idempotency_key':'simulation-once','authorization_snapshot':snapshot,'receipt':''}
        state['actions'].append(action);save()
        run([PYTHON,'-c',"from pathlib import Path;Path('records/TASK-001/action-marker.txt').write_text('completed once\\n')"],repo,'10-local-action')
        action['status']='unknown';gate('action','11-unknown-blocks',1,['ACTION_OUTCOME_UNKNOWN'],['--action','migrate','--target','temp:one','--revision',second['revision']])
        marker=run([PYTHON,'-c',"from pathlib import Path; print(Path('records/TASK-001/action-marker.txt').read_text(),end='')"],repo,'12-read-receipt');assert marker.stdout=='completed once\n'
        action.update(status='completed',receipt='records/TASK-001/action-marker.txt')
        gate('action','13-duplicate-blocks',1,['DELIVERY_ALREADY_COMPLETED'],['--action','migrate','--target','temp:one','--revision',second['revision']])
        state['authorization']['migrate']['status']='not_authorized';state['sources'][1]['adoption']='superseded'
        gate('record','14-history-after-revoke');gate('acceptance','15-acceptance-after-revoke')
        gate('action','16-new-action-revoked',1,['AUTH_ACTION'],['--action','migrate','--target','temp:two','--revision',second['revision']])
        checks.append('actual local action -> unknown -> readback -> completed; duplicate and revoked next action blocked; history remains auditable')
        (out/'final-state.json').write_text(statepath.read_text())
        for rel in files+[specfile]:
            dest=out/'products'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((repo/rel).read_bytes())
    (out/'result.json').write_text(json.dumps({'ok':True,'checks':checks,'command_count':len(logs),'source_hashes_unchanged':hashes=={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'skill/veriflow').rglob('*') if p.is_file() and '__pycache__' not in p.parts}},ensure_ascii=False,indent=2))
    print(json.dumps({'ok':True,'checks':checks,'output':str(out)},ensure_ascii=False))
if __name__=='__main__':main()
