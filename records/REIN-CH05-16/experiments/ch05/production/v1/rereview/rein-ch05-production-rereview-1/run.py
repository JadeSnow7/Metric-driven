import sys, subprocess, pathlib, json, time, os
outdir = pathlib.Path('/private/tmp/rein-ch05-production-rereview-1')
label, cwd, *argv = sys.argv[1:]
record = {'label': label, 'cwd': cwd, 'argv': argv, 'started_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
env = os.environ.copy()
env['CARGO_TARGET_DIR']='/private/tmp/rein-production-rereview-build'
record['environment_overrides']={'CARGO_TARGET_DIR':env['CARGO_TARGET_DIR']}
for name in list(env):
    if name.startswith('REIN_'): env.pop(name)
record['REIN_environment']='all inherited REIN_* removed; no credential files read'
try:
    p=subprocess.run(argv,cwd=cwd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=240)
    record.update(exit_code=p.returncode,output=p.stdout)
except subprocess.TimeoutExpired as e:
    record.update(exit_code=None,timeout=True,output=str(e.stdout))
(outdir/(label+'.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2))
(outdir/(label+'.txt')).write_text(record['output'])
print(json.dumps({k:v for k,v in record.items() if k!='output'},ensure_ascii=False,indent=2))
print(record['output'] if len(record['output'])<16000 else record['output'][:10000]+'\n[display clipped; raw output saved]\n'+record['output'][-3000:])
sys.exit(record.get('exit_code') or 0)
