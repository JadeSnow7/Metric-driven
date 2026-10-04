import json, os, pathlib, subprocess, tempfile, time

root = pathlib.Path('/private/tmp/rein-production-candidate-03')
out = pathlib.Path('/private/tmp/rein-ch06-v4-rust-evidence-search-error/raw')
target = '/private/tmp/rein-candidate03-build'
records = []

def run(name, argv):
    start = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    p = subprocess.run(argv, text=True, capture_output=True, env={**os.environ, 'CARGO_TARGET_DIR': target})
    end = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    record = {'name': name, 'argv': argv, 'cwd': str(pathlib.Path.cwd()), 'start': start, 'end': end,
              'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
    (out / f'{name}.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    records.append(record)

run('fmt-check', ['cargo', 'fmt', '--manifest-path', str(root / 'rust/Cargo.toml'), '--', '--check'])
run('check-examples', ['cargo', 'check', '--manifest-path', str(root / 'rust/Cargo.toml'), '--examples'])
with tempfile.TemporaryDirectory(prefix='rein-ch06-nonexistent-') as directory:
    run('nonexistent-workspace', ['cargo', 'run', '--quiet', '--manifest-path', str(root / 'rust/Cargo.toml'), '--example', 'ch06_loop', '--', 'normal', str(pathlib.Path(directory) / 'missing')])
with tempfile.TemporaryDirectory(prefix='rein-ch06-numeric-') as directory:
    workspace = pathlib.Path(directory)
    (workspace / '123').write_text('marker: ch06 numeric\n')
    run('numeric-filename', ['cargo', 'run', '--quiet', '--manifest-path', str(root / 'rust/Cargo.toml'), '--example', 'ch06_loop', '--', 'normal', str(workspace)])
(out / 'index.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n')
