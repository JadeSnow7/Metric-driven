"""Main-thread clean delivery verification; no edits to source checkout."""
import hashlib, json, os, pathlib, shutil, subprocess, tempfile, time

root=pathlib.Path('/Users/huaodong/Documents/evidence-driven-development')
task=root/'records/CI-PORTABILITY-20260916'
state=json.loads((task/'task-state.json').read_text())
workspace=pathlib.Path(tempfile.mkdtemp(prefix='veriflow-ci-clean-',dir='/private/tmp'))
checkout=workspace/'repo';checkout.mkdir()
archive=subprocess.Popen(['git','archive','HEAD'],cwd=root,stdout=subprocess.PIPE)
subprocess.run(['tar','-xf','-','-C',str(checkout)],stdin=archive.stdout,check=True)
archive.stdout.close()
if archive.wait(): raise SystemExit('git archive failed')
owned=state['implementation_tasks'][0]['file_scope']
for rel in owned:
    src=root/rel; dst=checkout/rel
    if src.exists():
        dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    else: raise SystemExit(f'owned file missing: {rel}')
shutil.copytree(task,checkout/task.relative_to(root))
env=dict(os.environ,PYTHONPYCACHEPREFIX=str(workspace/'pycache'))
print('clean_checkout:',checkout,flush=True)
print('source_sha256:',json.dumps({p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in owned},sort_keys=True),flush=True)
commands=[['python3','tools/validate_repository.py'],['python3','-m','py_compile',*[str(p.relative_to(checkout)) for pattern in ('tools/*.py','skill/veriflow/scripts/*.py','skill/veriflow/tests/*.py') for p in sorted(checkout.glob(pattern))]],['python3','-m','unittest','discover','-s','skill/veriflow/tests','-v'],['python3','-m','unittest','tools/tests/test_validate_repository.py','-v']]
for argv in commands:
    print('RUN',json.dumps(argv),flush=True);start=time.monotonic()
    result=subprocess.run(argv,cwd=checkout,env=env)
    print('RESULT',result.returncode,'elapsed_seconds',round(time.monotonic()-start,3),flush=True)
    if result.returncode: raise SystemExit(result.returncode)
print('All workflow commands passed in a clean candidate checkout; no foreign untracked paths copied.',flush=True)
