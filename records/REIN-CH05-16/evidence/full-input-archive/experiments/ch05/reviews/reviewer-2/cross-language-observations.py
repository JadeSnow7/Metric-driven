import json,pathlib
p=pathlib.Path('/private/tmp/rein-ch05-review-evidence-2')
r={}
for pkg in ['17','42']:
 d=json.loads((p/f'p{pkg}-ts-independent.stdout.txt').read_text())
 r[pkg]={'ts_cases':[{k:x[k] for k in ['test','status','request_count','events_equal','requests_equal'] if k in x} for x in d]}
print(json.dumps(r,ensure_ascii=False,indent=2))
(p/'independent-summary.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
