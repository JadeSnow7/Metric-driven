#!/usr/bin/env python3
import argparse,json,re,sys,os
from pathlib import Path
def main():
 p=argparse.ArgumentParser(); p.add_argument('--data-root',type=Path,required=True); p.add_argument('--budget',type=int,default=2400); p.add_argument('--strategy',choices=['on-demand','window','summary','retrieval']); a=p.parse_args(); root=a.data_root; idx=json.loads((root/'index.json').read_text()); tasks=json.loads((root/'tasks.json').read_text())['tasks']; docs=idx['documents']; ids={d['id'] for d in docs}
 if (len(ids)!=len(docs) or len({d['order'] for d in docs})!=len(docs) or any(Path(d['path']).is_absolute() or '..' in Path(d['path']).parts for d in docs)) and os.environ.get('EDD_MUTANT')!='accept-duplicate-metadata': raise SystemExit('invalid metadata')
 out=[]; strategies=[a.strategy] if a.strategy else ['on-demand','window','summary','retrieval']
 for t in tasks:
  for s in strategies:
   if a.budget==0: out.append({'taskId':t['id'],'strategy':s,'question':t['question'],'budget':0,'status':'context_budget_exhausted','messages':[],'estimatedUnits':0,'selectedSources':[],'operations':[],'answer':None,'quality':None,'unsupportedClaims':[],'elapsedMs':0,'serviceTokens':None,'modelCalls':0,'callRecords':[]}); continue
   selected=[]
   terms=[x for x in ['传输','协议','检查命令','批准','失败','基线','状态','动作','吞吐量'] if x in t['question']]
   for d in sorted(docs,key=lambda x:x['order']):
    hay=' '.join([d['title'],*d['keywords']])
    if s in ('on-demand','summary','retrieval') and not any(x in hay for x in terms): continue
    if s=='window' and d['id'] not in {'doc-03','doc-05','doc-06'}: continue
    p=(root/d['path']).resolve()
    if not p.is_relative_to(root.resolve()) or not p.is_file(): out.append({'taskId':t['id'],'strategy':s,'question':t['question'],'budget':a.budget,'status':'error','messages':[],'estimatedUnits':0,'selectedSources':[],'operations':[],'answer':None,'quality':None,'unsupportedClaims':[],'elapsedMs':0,'serviceTokens':None,'modelCalls':0,'callRecords':[]}); break
    text=p.read_text(); selected.append((d,text))
   else:
    ms=[{'role':'system','content':x} for x in t['rules']]+[{'role':'user','content':t['question']}]
    for d,text in selected: ms.append({'role':'user','content':f'[来源:{d["id"]}]\n'+text})
    claims=[]
    fields=['传输方式','协议版本','检查命令','批准状态','处理动作','生产吞吐量']
    for field in fields:
     if field not in t['question']: continue
     for d,text in selected:
      m=re.search(re.escape(field)+r'：([^\n]+)',text)
      if m: claims.append({'field':field,'value':m.group(1),'source':d['id']}); break
    ans={'rawAnswer':'；'.join(c['field']+'：'+c['value'] for c in claims) if claims else '证据不足','claims':claims,'insufficientEvidence':not claims}
    quality=1 if claims or '吞吐量' in t['question'] else 0
    out.append({'taskId':t['id'],'strategy':s,'question':t['question'],'budget':a.budget,'status':'completed','messages':ms,'estimatedUnits':sum(8+len(m['role'].encode())+len(m['content'].encode()) for m in ms),'selectedSources':[d['id'] for d,_ in selected],'operations':[{'op':'read_file','path':d['path']} for d,_ in selected],'answer':ans,'quality':quality,'unsupportedClaims':[],'elapsedMs':0,'serviceTokens':None,'modelCalls':1,'callRecords':[]})
 mutant=os.environ.get('EDD_MUTANT','')
 if mutant=='missing-row': out.pop()
 elif mutant=='duplicate-replacement' and len(out)>1: out[1]=dict(out[0])
 elif mutant=='wrong-estimate' and out: out[0]['estimatedUnits']+=1
 elif mutant=='larger-budget' and out: out[0]['budget']=9999
 elif mutant=='unsupported-claim' and out: out[0]['answer']['claims'].append({'field':'伪造','value':'x','source':'doc-01'})
 elif mutant=='frozen-original-value':
  for row in out:
   if row.get('taskId')=='task-01': row['answer']['rawAnswer']=row['answer']['rawAnswer'].replace('CBOR','JSON Lines'); break
 elif mutant=='budget0-dispatch' and a.budget==0: out.append({'taskId':'bad','strategy':'on-demand','status':'completed'})
 print(json.dumps({'unit':'estimated-bytes-v1','serviceTokens':None,'results':out},ensure_ascii=False))
if __name__=='__main__': main()
