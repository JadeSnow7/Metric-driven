import hashlib, importlib.util, pathlib, subprocess, tempfile
root=pathlib.Path('/Users/huaodong/Documents/evidence-driven-development')
spec=importlib.util.spec_from_file_location('candidate',root/'tools/validate_repository.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with tempfile.TemporaryDirectory() as tmp:
    parent=pathlib.Path(tmp);repo=parent/'repo';repo.mkdir();doc=repo/'test.md';outside=parent/'existing.md';outside.write_text('real file');(repo/'inside.md').write_text('inside')
    text=f'[ordinary]({outside}) [angle](<{outside}>) [inside](inside.md) [web](https://example.com) [fragment](#section) `[{outside}]({outside})`'
    assert (doc.parent/str(outside)).resolve().exists(), 'old existence-only check must accept this fixture'
    assert m.broken_local_links(repo,doc,text)==[str(outside),f'<{outside}>']
    print('DISTINGUISHING CHECK PASSED: old existence-only rule accepts real external file; new Markdown entry rejects both ordinary and angle links while retaining valid targets.')
sealed='records/REIN-CH08-EDD-20260915/formal/seals/C/run/final.md'
original=subprocess.check_output(['git','show','HEAD:'+sealed],cwd=root)
assert (root/sealed).read_bytes()==original
print('SEALED FINAL BYTE IDENTITY',hashlib.sha256(original).hexdigest())
paths={n:f'records/REIN-CH05-16/evidence/{n}/final.md' for n in ['evaluator-v3','evaluator-v4','preparation-operator','prerequisites-v3','prerequisites-v4']}
paths['evaluator-v3-rejected']='records/REIN-CH08-EDD-20260915/preparation/evaluator-v3-rejected/run/final.md'
for name,p in paths.items():
    b=subprocess.check_output(['git','show','HEAD:'+p],cwd=root)
    saved=root/'records/CI-PORTABILITY-20260916/evidence/coder'/f'{name}.final.md.original.txt'
    assert saved.read_bytes()==b
    print('ORIGINAL PRESERVED',p,hashlib.sha256(b).hexdigest())
assert subprocess.check_output(['git','diff','--name-only','--','skill'],cwd=root)==b''
print('SKILL UNCHANGED')
