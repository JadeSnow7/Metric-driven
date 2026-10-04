import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

root = Path('/private/tmp/veriflow-spec-20260916')
docs = [
    root / 'skill/veriflow/SKILL.md',
    root / 'skill/veriflow/references/workflow.md',
    root / 'skill/veriflow/references/design.md',
    root / 'skill/veriflow/references/delegation-and-handoffs.md',
    root / 'skill/veriflow/references/writing.md',
    root / 'skill/veriflow/references/claude-code.md',
    root / 'skill/veriflow/agents/claude-code/veriflow-coder.md',
    root / 'skill/veriflow/agents/claude-code/veriflow-reviewer.md',
    root / 'skill/veriflow/assets/templates/handoff.md',
    root / 'skill/veriflow/assets/templates/task-summary.md',
    root / 'skill/veriflow/assets/templates/work-log.md',
    root / 'skill/veriflow/assets/templates/writing-handoff.md',
]
link_code = """from pathlib import Path
import json
import re
missing=[]
for p in %r:
    p=Path(p)
    for link in re.findall(r'\\[[^]]+\\]\\(([^)#]+)', p.read_text()):
        if not (p.parent/link).resolve().exists(): missing.append([str(p),link])
print(json.dumps({'missing': missing}, ensure_ascii=False))
raise SystemExit(bool(missing))""" % [str(p) for p in docs]
checks = []
for argv in (['git', 'diff', '--check'], ['python3.11', '-c', link_code]):
    started = datetime.now(timezone.utc)
    result = subprocess.run(argv, cwd=root, capture_output=True, text=True)
    ended = datetime.now(timezone.utc)
    checks.append({
        'argv': argv,
        'cwd': str(root),
        'started_at': started.isoformat(),
        'ended_at': ended.isoformat(),
        'stdout': result.stdout,
        'stderr': result.stderr,
        'exit_code': result.returncode,
    })
payload = {
    'generated_by': 'run_v3_checks.py',
    'generated_at': datetime.now(timezone.utc).isoformat(),
    'scope': [str(p.relative_to(root)) for p in docs],
    'sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in docs},
    'checks': checks,
}
(root / 'records/VERIFLOW-SPEC-20260916/evidence/docs-coder/v3-checks.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
