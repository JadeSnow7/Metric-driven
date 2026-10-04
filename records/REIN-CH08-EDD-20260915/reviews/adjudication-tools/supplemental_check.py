#!/usr/bin/env python3
import argparse,hashlib,json
from pathlib import Path
def j(v):
 if v is None:return 4
 if isinstance(v,bool):return 4 if v else 5
 if isinstance(v,(int,float)):return 8
 if isinstance(v,str):return 2+len(v.encode())
 if isinstance(v,list):return 2+sum(j(x) for x in v)+max(0,len(v)-1)
 return 2+sum(2+len(k.encode())+1+j(x) for k,x in v.items())+max(0,len(v)-1)
def est(ms):
 return sum(8+len(m['role'].encode())+len(m.get('content','').encode())+len(m.get('tool_call_id','').encode())+sum(8+len(c['id'].encode())+len(c['name'].encode())+j(c['arguments']) for c in m.get('tool_calls',[])) for m in ms)
def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--data',type=Path,required=True);p.add_argument('--budget',type=int,default=2400);a=p.parse_args(); run=json.loads(a.run.read_text()); out={'ok':True,'checks':[],'run_sha256':hashlib.sha256(a.run.read_bytes()).hexdigest()}
 def check(name,ok): out['checks'].append({'id':name,'status':'passed' if ok else 'failed'}); out['ok']&=ok
 check('RUN_EXIT_ZERO',run.get('exit_code')==0)
 try:value=json.loads(run['stdout']); rows=value['results']; check('EXACT_4X4',len(rows)==16 and len({(x.get('taskId'),x.get('strategy')) for x in rows})==16)
 except Exception: rows=[];check('JSON_OUTPUT',False)
 for row in rows:
  ms=row.get('messages',[]); norm=[dict(m,role='user') if (m.get('tool_call_id') or m.get('tool_calls')) and m.get('content','').startswith('[来源:') else m for m in ms]
  check('ESTIMATE',row.get('estimatedUnits')==est(ms)); check('BUDGET',row.get('budget')==a.budget)
  sources={m.get('content','').split(']',1)[0][4:]:m.get('content','') for m in norm if m.get('content','').startswith('[来源:')}
  for c in row.get('answer',{}).get('claims',[]): check('CLAIM_GROUNDED',f"{c.get('field')}：{c.get('value')}" in sources.get(c.get('source'),''))
 print(json.dumps(out,ensure_ascii=False,indent=2));return 0 if out['ok'] else 1
if __name__=='__main__':raise SystemExit(main())
