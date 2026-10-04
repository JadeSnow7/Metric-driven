#!/usr/bin/env python3
import argparse,json,re,sys
from pathlib import Path
def main():
 p=argparse.ArgumentParser(); p.add_argument('--data-root',type=Path,required=True); p.add_argument('--budget',type=int,default=2400); p.add_argument('--strategy',choices=['on-demand','window','summary','retrieval']); a=p.parse_args(); root=a.data_root; idx=json.loads((root/'index.json').read_text()); tasks=json.loads((root/'tasks.json').read_text())['tasks']; docs=idx['documents']; ids={d['id'] for d in docs}
 if len(ids)!=len(docs) or len({d['order'] for d in docs})!=len(docs) or any(Path(d['path']).is_absolute() or '..' in Path(d['path']).parts for d in docs): raise SystemExit('invalid metadata')
 out=[]; strategies=[a.strategy] if a.strategy else ['on-demand','window','summary','retrieval']
 for t in tasks:
  for s in strategies:
   if a.budget==0: out.append({'taskId':t['id'],'strategy':s,'question':t['question'],'budget':0,'status':'context_budget_exhausted','messages':[],'estimatedUnits':0,'selectedSources':[],'operations':[],'answer':None,'quality':None,'unsupportedClaims':[],'elapsedMs':0,'serviceTokens':None,'modelCalls':0,'callRecords':[]}); continue
   selected=[]
   terms=[x for x in re.findall(r'[\u4e00-\u9fffA-Za-z0-9]+',t['question']) if len(x)>1]
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
    for q in t['expectedFacts']:
     for d,text in selected:
      m=re.search(re.escape(q['field'])+r'：([^\n]+)',text)
      if m: claims.append({'field':q['field'],'value':m.group(1),'source':d['id']}); break
    ans={'rawAnswer':'；'.join(c['field']+'：'+c['value'] for c in claims) if claims else '证据不足','claims':claims,'insufficientEvidence':not claims}
    out.append({'taskId':t['id'],'strategy':s,'question':t['question'],'budget':a.budget,'status':'completed','messages':ms,'estimatedUnits':sum(8+len(m['role'].encode())+len(m['content'].encode()) for m in ms),'selectedSources':[d['id'] for d,_ in selected],'operations':[{'op':'read_file','path':d['path']} for d,_ in selected],'answer':ans,'quality':1,'unsupportedClaims':[],'elapsedMs':0,'serviceTokens':None,'modelCalls':1,'callRecords':[]})
 print(json.dumps({'unit':'estimated-bytes-v1','serviceTokens':None,'results':out},ensure_ascii=False))
if __name__=='__main__': main()
