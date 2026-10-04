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
    p=subprocess.Popen(argv,cwd=repo,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    timed=False
    try: rawout,rawerr=p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed=True
        try: os.killpg(p.pid,9)
        except ProcessLookupError: pass
        rawout,rawerr=p.communicate()
    end=time.time()
    def hashes(root):
        return {str(x.relative_to(root)):digest(x) for x in sorted(root.rglob('*')) if x.is_file() and not any(part in {'.git','node_modules','target','dist','cache'} for part in x.relative_to(root).parts)}
    run={'label':label,'argv':argv,'cwd':str(repo),'started_at':started,'ended_at':end,'elapsed_seconds':time.monotonic()-start,'exit_code':p.returncode,'timed_out':timed,'stdout':rawout.decode('utf-8','replace'),'stderr':rawerr.decode('utf-8','replace'),'input_hashes':hashes(data),'source_hashes':hashes(repo)}
    (output/f'{label}.json').write_text(json.dumps(run,ensure_ascii=False,indent=2)+'\n')
    return run
def parse_output(run):
    if run['exit_code']!=0: return None
    try: return json.loads(run['stdout'])
    except json.JSONDecodeError as e: raise AssertionError(f"CHECK_JSON_OUTPUT: {e}")
def check_messages(row, tasks):
    assert isinstance(row['messages'],list), 'CHECK_MESSAGES_TYPE'
    task=next(t for t in tasks if t['id']==row['taskId'])
    expected=[('system',x) for x in task['rules']]+[('user',task['question'])]
    assert [(m.get('role'),m.get('content')) for m in row['messages'][:len(expected)]]==expected, 'CHECK_RULES_QUESTION_PRESERVED'
    return expected
def check_row(row,tasks,index,scenario,data_root,quality_exact=True):
    for key in REQUIRED: assert key in row, f'CHECK_FIELD_{key}'
    assert row['strategy'] in STRATEGIES, 'CHECK_STRATEGY'
    assert row['serviceTokens'] is None, 'CHECK_SERVICE_TOKENS_NULL'
    assert row['budget']==scenario['budget'], 'CHECK_REQUEST_BUDGET'
    assert isinstance(row['selectedSources'],list) and isinstance(row['operations'],list) and isinstance(row['callRecords'],list) and isinstance(row['unsupportedClaims'],list), 'CHECK_ROW_LIST_TYPES'
    if row['status']=='context_budget_exhausted':
        assert scenario['budget']==0, 'CHECK_EXHAUSTION_ONLY_ZERO_BUDGET'
        assert row['messages']==[] and row['operations']==[] and row['callRecords']==[] and row['answer'] is None and row['quality'] is None and row['estimatedUnits']==0 and row['modelCalls']==0, 'CHECK_BUDGET_ZERO_EMPTY'
        return
    check_messages(row,tasks)
    assert row['status']=='completed', 'CHECK_STATUS_COMPLETED'
    assert isinstance(row['messages'],list) and row['estimatedUnits']==estimate(row['messages']) and row['estimatedUnits']<=row['budget'], 'CHECK_ESTIMATE'
    assert row['modelCalls']==1, 'CHECK_MODEL_CALL_COUNT'
    answer=row['answer']; assert isinstance(answer,dict) and isinstance(answer.get('rawAnswer'),str) and isinstance(answer.get('claims'),list) and isinstance(answer.get('insufficientEvidence'),bool), 'CHECK_ANSWER_SHAPE'
    source_text={}; source_ids={d['id'] for d in index['documents']}; source_paths={d['id']:data_root/d['path'] for d in index['documents']}
    for m in row['messages']:
        if m.get('role')=='user' and m.get('content','').startswith('[来源:'):
            sid=m['content'].split(']',1)[0][4:]; assert sid in source_ids, 'CHECK_SOURCE_ID'; source_text.setdefault(sid,[]).extend(m['content'].splitlines()[1:])
    for claim in answer['claims']:
        assert all(isinstance(claim.get(k),str) and claim[k] for k in ('field','value','source')), 'CHECK_CLAIM_SHAPE'
        assert f"{claim['field']}：{claim['value']}" in source_text.get(claim['source'],[]), 'CHECK_CLAIM_GROUNDED'
        current=source_paths[claim['source']]
        assert f"{claim['field']}：{claim['value']}" in current.read_text().splitlines(), 'CHECK_CLAIM_CURRENT_SOURCE'
    assert 0<=row['quality']<=1, 'CHECK_QUALITY_RANGE'
    task=next(t for t in tasks if t['id']==row['taskId'])
    grounded=sum(1 for fact in task['expectedFacts'] if any(c.get('field')==fact['field'] and c.get('value')==fact['value'] and c.get('source')==fact['source'] for c in answer['claims']))
    expected_quality=1 if not task['expectedFacts'] and not answer['claims'] else (grounded/len(task['expectedFacts']) if task['expectedFacts'] else 0)
    if quality_exact: assert row['quality']==expected_quality, 'CHECK_QUALITY_EXACT'
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
    for row in rows: check_row(row,tasks,index,{'budget':budget},data)
    return value
def _main():
    p=argparse.ArgumentParser(); p.add_argument('--repo',type=Path,required=True); p.add_argument('--data',type=Path,required=True); p.add_argument('--output',type=Path,required=True); p.add_argument('--command-json',type=Path); p.add_argument('--calibration-toy',type=Path); a=p.parse_args()
    assert not a.output.exists(), 'CHECK_OUTPUT_MUST_BE_NEW'; a.output.mkdir(parents=True)
    command=json.loads(a.command_json.read_text()) if a.command_json else ['npm','run','--silent','ch08:compare','--']
    assert isinstance(command,list) and all(isinstance(x,str) and x for x in command), 'CHECK_COMMAND_SHAPE'
    tasks=json.loads((a.data/'tasks.json').read_text())['tasks']; index=json.loads((a.data/'index.json').read_text())
    result={"scenarios":[]}
    result['scenarios'].append({'name':'default','rows':len(suite(command,a.repo,a.data,a.output/'default')['results'])})
    result['scenarios'].append({'name':'budget0','rows':len(suite(command,a.repo,a.data,a.output/'budget0','budget0')['results'])})
    # Dynamic data mutation: preserve tasks/oracle and require the new value when it is sent.
    with tempfile.TemporaryDirectory() as td:
        mutated=Path(td); shutil.copytree(a.data,mutated,dirs_exist_ok=True); f=mutated/'docs/early-runtime.md'; f.write_text(f.read_text().replace('传输方式：JSON Lines','传输方式：CBOR'))
        run=execute(command,a.repo,mutated,a.output/'mutated', 'mutated'); value=parse_output(run); assert value
        rows=[r for r in value['results'] if r.get('taskId')=='task-01']; assert rows
        assert len(value.get('results',[]))==16, 'CHECK_MUTATED_4X4'
        for r in value['results']: check_row(r,tasks,index,{'budget':2400},mutated)
        assert {(r.get('taskId'),r.get('strategy')) for r in value['results']}=={(t['id'],s) for t in tasks for s in STRATEGIES}, 'CHECK_MUTATED_4X4_SET'
        for r in rows:
            if any('传输方式：CBOR' in m.get('content','') for m in r.get('messages',[])):
                assert any(c.get('field')=='传输方式' and c.get('value')=='CBOR' for c in r['answer'].get('claims',[])), 'CHECK_MUTATION_FOLLOWS_MESSAGES'
        result['scenarios'].append({'name':'mutated','rows':len(value['results'])})
    # Metadata duplicate must be a nonzero CLI failure, not evaluator self-generated failure.
    with tempfile.TemporaryDirectory() as td:
        bad=Path(td); shutil.copytree(a.data,bad,dirs_exist_ok=True); idx=json.loads((bad/'index.json').read_text()); idx['documents'].append(dict(idx['documents'][0])); (bad/'index.json').write_text(json.dumps(idx,ensure_ascii=False))
        run=execute(command,a.repo,bad,a.output/'duplicate','duplicate'); assert run['exit_code']!=0, 'CHECK_DUPLICATE_METADATA_REJECTED'
        result['scenarios'].append({'name':'duplicate','exit_code':run['exit_code']})
    with tempfile.TemporaryDirectory() as td:
        bad=Path(td); shutil.copytree(a.data,bad,dirs_exist_ok=True); (bad/'docs/early-runtime.md').unlink()
        run=execute(command,a.repo,bad,a.output/'missing','missing',strategy='summary'); value=parse_output(run); assert value and len(value['results'])==4, 'CHECK_MISSING_RESULT_ROWS'
        row=next(r for r in value['results'] if r.get('taskId')=='task-01'); assert row['status']=='error' and row['answer'] is None and row['modelCalls']==0, 'CHECK_MISSING_ERROR_ROW'
        result['scenarios'].append({'name':'missing','rows':len(value['results'])})
    with tempfile.TemporaryDirectory() as td:
        bad=Path(td); shutil.copytree(a.data,bad,dirs_exist_ok=True); idx=json.loads((bad/'index.json').read_text()); idx['documents'][0]['path']='../escape.md'; (bad/'index.json').write_text(json.dumps(idx,ensure_ascii=False))
        run=execute(command,a.repo,bad,a.output/'path-escape','path-escape'); assert run['exit_code']!=0, 'CHECK_PATH_ESCAPE_REJECTED'
        result['scenarios'].append({'name':'path-escape','exit_code':run['exit_code']})
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result))
def main():
    output_preexisted=False
    for i,arg in enumerate(os.sys.argv):
        if arg=='--output' and i+1<len(os.sys.argv):
            output_preexisted=Path(os.sys.argv[i+1]).exists(); break
    try: return _main()
    except AssertionError as exc:
        output=None
        for i,arg in enumerate(os.sys.argv):
            if arg=='--output' and i+1<len(os.sys.argv): output=Path(os.sys.argv[i+1]); break
        if output is not None and not output_preexisted:
            output.mkdir(parents=True,exist_ok=True)
            payload={'status':'failed','failed_checks':[{'check_id':str(exc)}]}
            (output/'summary.json').write_text(json.dumps(payload,indent=2)+'\n')
            print(json.dumps(payload),file=os.sys.stderr)
        raise SystemExit(1)
if __name__=='__main__': main()
