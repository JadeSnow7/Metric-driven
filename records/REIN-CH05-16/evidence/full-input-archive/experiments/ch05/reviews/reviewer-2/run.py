import subprocess,sys,os,json,time,hashlib,pathlib
label,cwd,*argv=sys.argv[1:]
out=pathlib.Path('/private/tmp/rein-ch05-review-evidence-2')
pkg=next((p for p in [pathlib.Path(cwd),*pathlib.Path(cwd).parents] if p.name in ['package-17','package-42']),None)
files={}
if pkg:
 for section in ['ts/src','ts/tests','ts/examples','rust/src','rust/tests','rust/examples','docs/chapters','fixtures','task-inputs']:
  base=pkg/section
  if base.exists():
   for f in sorted(base.rglob('*')):
    if f.is_file(): files[str(f.relative_to(pkg))]=hashlib.sha256(f.read_bytes()).hexdigest()
 for name in ['package.json','package-lock.json','ts/package.json','ts/tsconfig.json','ts/vitest.config.ts','rust/Cargo.toml','rust/Cargo.lock']:
  f=pkg/name
  if f.exists():files[name]=hashlib.sha256(f.read_bytes()).hexdigest()
env={k:v for k,v in os.environ.items() if not k.startswith('REIN_')}
env['CARGO_TARGET_DIR']='/private/tmp/rein-ch05-review-20260914/targets/reviewer-2/'+(pkg.name if pkg else 'probes')
meta={'label':label,'cwd':cwd,'argv':argv,'environment_overrides':{'CARGO_TARGET_DIR':env['CARGO_TARGET_DIR'],'REIN_*':'removed'},'source_sha256':files,'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
(out/(label+'.meta.json')).write_text(json.dumps(meta,ensure_ascii=False,indent=2))
t=time.monotonic()
with (out/(label+'.stdout.txt')).open('wb') as so,(out/(label+'.stderr.txt')).open('wb') as se:
 try: code=subprocess.run(argv,cwd=cwd,env=env,stdout=so,stderr=se,timeout=240).returncode
 except subprocess.TimeoutExpired: code='timeout_240_seconds'
meta.update(exit_code=code,wall_seconds=round(time.monotonic()-t,3))
(out/(label+'.meta.json')).write_text(json.dumps(meta,ensure_ascii=False,indent=2))
print(json.dumps({'label':label,'cwd':cwd,'argv':argv,'exit_code':code,'wall_seconds':meta['wall_seconds'],'stdout':str(out/(label+'.stdout.txt')),'stderr':str(out/(label+'.stderr.txt'))},ensure_ascii=False))
print((out/(label+'.stdout.txt')).read_text(errors='replace')[-6500:])
print((out/(label+'.stderr.txt')).read_text(errors='replace')[-3500:])
