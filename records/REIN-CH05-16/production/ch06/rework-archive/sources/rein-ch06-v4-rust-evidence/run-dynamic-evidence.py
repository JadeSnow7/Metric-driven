import json, os, pathlib, subprocess, tempfile, time

root = pathlib.Path('/private/tmp/rein-production-candidate-03')
out = pathlib.Path('/private/tmp/rein-ch06-v4-rust-evidence/dynamic')
out.mkdir(parents=True, exist_ok=True)
target = '/private/tmp/rein-candidate03-build'
records = []

def run(name, argv, cwd=None):
    started = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    p = subprocess.run(argv, cwd=cwd, env={**os.environ, 'CARGO_TARGET_DIR': target}, text=True, capture_output=True)
    ended = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    record = {'name': name, 'argv': argv, 'cwd': str(cwd or pathlib.Path.cwd()), 'start': started,
              'end': ended, 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
    (out / f'{name}.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    records.append(record)

run('fmt-check', ['cargo', 'fmt', '--manifest-path', str(root / 'rust/Cargo.toml'), '--', '--check'])
run('check-examples', ['cargo', 'check', '--manifest-path', str(root / 'rust/Cargo.toml'), '--examples'])
for name, files in [('zero-files', []), ('one-file', [('README.md', 'marker: ch06 one')]),
                    ('three-files', [('a.md', 'marker: ch06 alpha'), ('b.md', 'marker: ch06 beta'), ('c.md', 'marker: ch06 gamma')])]:
    with tempfile.TemporaryDirectory(prefix=f'rein-ch06-{name}-') as directory:
        workspace = pathlib.Path(directory)
        for filename, content in files:
            (workspace / filename).write_text(content + '\n')
        run(name, ['cargo', 'run', '--quiet', '--manifest-path', str(root / 'rust/Cargo.toml'),
                   '--example', 'ch06_loop', '--', 'normal', str(workspace)])
(out / 'index.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n')
