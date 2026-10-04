#!/usr/bin/env python3
"""Dynamic, command-uniform evaluator for the frozen ch08 contract."""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, tempfile, time
from pathlib import Path

STRATEGIES=("on-demand","window","summary","retrieval")
REQUIRED=("taskId","strategy","question","budget","status","messages","estimatedUnits","selectedSources","operations","answer","quality","unsupportedClaims","elapsedMs","serviceTokens","modelCalls","callRecords")

def digest(path: Path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()
def estimate(messages):
    return sum(8+len(m['role'].encode())+len(m['content'].encode()) for m in messages)
def base_argv(command, data, *, budget=None, strategy=None):
    out=list(command)+["--data-root",str(data)]
    if budget is not None: out += ["--budget",str(budget)]
    if strategy is not None: out += ["--strategy",strategy]
    return out
def execute(command, repo, data, output, label, *, budget=None, strategy=None, timeout=180):
    output.mkdir(parents=True,exist_ok=True)
    argv=base_argv(command,data,budget=budget,strategy=strategy); start=time.monotonic(); started=time.time()
    p=subprocess.Popen(argv,cwd=repo,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    timed=False
    try: rawout,rawerr=p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        timed=True; rawout=exc.output or b''; rawerr=exc.stderr or b''; p.kill(); tailout,tailerr=p.communicate(); rawout+=tailout; rawerr+=tailerr
    end=time.time(); run={'label':label,'argv':argv,'cwd':str(repo),'started_at':started,'ended_at':end,'elapsed_seconds':time.monotonic()-start,'exit_code':p.returncode,'timed_out':timed,'stdout':rawout.decode('utf-8','replace'),'stderr':rawerr.decode('utf-8','replace'),'input_hashes':{str(x):digest(x) for x in sorted(data.rglob('*')) if x.is_file()}}
    (output/f'{label}.json').write_text(json.dumps(run,ensure_ascii=False,indent=2)+'\n')
    return run
def parse_output(run):
    if run['exit_code']!=0: return None
    try: return json.loads(run['stdout'])
    except json.JSONDecodeError as e: raise AssertionError(f"CHECK_JSON_OUTPUT: {e}")
def check_messages(row, tasks):
    assert isinstance(row['messages'],list), 'CHECK_MESSAGES_TYPE'
    task=next(t for t in tasks if t['id']==row['taskId'])
    expected=[{'role':'system','content':x} for x in task['rules']]+[{'role':'user','content':task['question']}]
    assert row['messages'][:len(expected)]==expected, 'CHECK_RULES_QUESTION_PRESERVED'
    return expected
def check_row(row,tasks,index,scenario):
    for key in REQUIRED: assert key in row, f'CHECK_FIELD_{key}'
    assert row['strategy'] in STRATEGIES, 'CHECK_STRATEGY'
    assert row['serviceTokens'] is None, 'CHECK_SERVICE_TOKENS_NULL'
    assert row['budget']==scenario['budget'], 'CHECK_REQUEST_BUDGET'
    if row['status']=='context_budget_exhausted':
        assert row['messages']==[] and row['operations']==[] and row['callRecords']==[] and row['answer'] is None and row['quality'] is None and row['estimatedUnits']==0 and row['modelCalls']==0, 'CHECK_BUDGET_ZERO_EMPTY'
        return
    check_messages(row,tasks)
    assert row['status']=='completed', 'CHECK_STATUS_COMPLETED'
    assert isinstance(row['messages'],list) and row['estimatedUnits']==estimate(row['messages']) and row['estimatedUnits']<=row['budget'], 'CHECK_ESTIMATE'
    assert row['modelCalls']==1, 'CHECK_MODEL_CALL_COUNT'
    answer=row['answer']; assert isinstance(answer,dict) and isinstance(answer.get('claims'),list), 'CHECK_ANSWER_SHAPE'
    source_text={}
    for m in row['messages']:
        if m.get('role')=='user' and m.get('content','').startswith('[来源:'):
            sid=m['content'].split(']',1)[0][4:]; source_text.setdefault(sid,''); source_text[sid]+=m['content']
    for claim in answer['claims']:
        assert all(isinstance(claim.get(k),str) and claim[k] for k in ('field','value','source')), 'CHECK_CLAIM_SHAPE'
        assert f"{claim['field']}：{claim['value']}" in source_text.get(claim['source'],''), 'CHECK_CLAIM_GROUNDED'
    assert 0<=row['quality']<=1, 'CHECK_QUALITY_RANGE'
    task=next(t for t in tasks if t['id']==row['taskId'])
    if task['unknown']:
        assert not answer['claims'] and answer['insufficientEvidence'] is True and row['quality']==1, 'CHECK_UNKNOWN'
    elif not answer['claims']:
        assert answer['insufficientEvidence'] is True, 'CHECK_NO_EVIDENCE_FLAG'
def suite(command,repo,data,output,scenario='default'):
    tasks=json.loads((data/'tasks.json').read_text())['tasks']; index=json.loads((data/'index.json').read_text())
    budget=0 if scenario=='budget0' else 2400
    run=execute(command,repo,data,output,scenario,budget=0 if scenario=='budget0' else None)
    value=parse_output(run); assert value and value.get('unit')=='estimated-bytes-v1', 'CHECK_ROOT_UNIT'
    assert value.get('serviceTokens') is None, 'CHECK_ROOT_SERVICE_TOKENS'
    rows=value.get('results'); assert isinstance(rows,list), 'CHECK_RESULTS_LIST'
    expected={(t['id'],s) for t in tasks for s in STRATEGIES}
    actual=[(r.get('taskId'),r.get('strategy')) for r in rows]
    assert set(actual)==expected and len(actual)==len(set(actual))==16, 'CHECK_EXACT_4X4'
    for row in rows: check_row(row,tasks,index,{'budget':budget})
    return value
def main():
    p=argparse.ArgumentParser(); p.add_argument('--repo',type=Path,required=True); p.add_argument('--data',type=Path,required=True); p.add_argument('--output',type=Path,required=True); p.add_argument('--command-json',type=Path); p.add_argument('--calibration-toy',type=Path); a=p.parse_args()
    assert not a.output.exists(), 'CHECK_OUTPUT_MUST_BE_NEW'; a.output.mkdir(parents=True)
    command=json.loads(a.command_json.read_text()) if a.command_json else ['npm','run','--silent','ch08:compare','--']
    assert isinstance(command,list) and all(isinstance(x,str) and x for x in command), 'CHECK_COMMAND_SHAPE'
    result={"scenarios":[]}
    result['scenarios'].append({'name':'default','rows':len(suite(command,a.repo,a.data,a.output/'default')['results'])})
    result['scenarios'].append({'name':'budget0','rows':len(suite(command,a.repo,a.data,a.output/'budget0','budget0')['results'])})
    # Dynamic data mutation: preserve tasks/oracle and require the new value when it is sent.
    with tempfile.TemporaryDirectory() as td:
        mutated=Path(td); shutil.copytree(a.data,mutated,dirs_exist_ok=True); f=mutated/'docs/early-runtime.md'; f.write_text(f.read_text().replace('传输方式：JSON Lines','传输方式：CBOR'))
        run=execute(command,a.repo,mutated,a.output/'mutated', 'mutated'); value=parse_output(run); assert value
        rows=[r for r in value['results'] if r.get('taskId')=='task-01']; assert rows
        for r in rows:
            if any('传输方式：CBOR' in m.get('content','') for m in r.get('messages',[])):
                assert any(c.get('field')=='传输方式' and c.get('value')=='CBOR' for c in r['answer'].get('claims',[])), 'CHECK_MUTATION_FOLLOWS_MESSAGES'
        result['scenarios'].append({'name':'mutated','rows':len(value['results'])})
    # Metadata duplicate must be a nonzero CLI failure, not evaluator self-generated failure.
    with tempfile.TemporaryDirectory() as td:
        bad=Path(td); shutil.copytree(a.data,bad,dirs_exist_ok=True); idx=json.loads((bad/'index.json').read_text()); idx['documents'].append(dict(idx['documents'][0])); (bad/'index.json').write_text(json.dumps(idx,ensure_ascii=False))
        run=execute(command,a.repo,bad,a.output/'duplicate','duplicate'); assert run['exit_code']!=0, 'CHECK_DUPLICATE_METADATA_REJECTED'
        result['scenarios'].append({'name':'duplicate','exit_code':run['exit_code']})
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result))
if __name__=='__main__': main()
