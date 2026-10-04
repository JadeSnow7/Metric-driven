import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

root = Path('/private/tmp/veriflow-spec-20260916')
docs = [root / 'skill/veriflow/references/workflow.md']
checks = []
commands = [
    ['git', 'diff', '--check'],
    ['python3.11', '-c', "from pathlib import Path; import re; p=Path('skill/veriflow/references/workflow.md'); missing=[x for x in re.findall(r'\\[[^]]+\\]\\(([^)#]+)', p.read_text()) if not (p.parent/x).resolve().exists()]; print({'missing': missing}); raise SystemExit(bool(missing))"],
]
for argv in commands:
    started = datetime.now(timezone.utc)
    result = subprocess.run(argv, cwd=root, capture_output=True, text=True)
    ended = datetime.now(timezone.utc)
    checks.append({'argv': argv, 'cwd': str(root), 'started_at': started.isoformat(), 'ended_at': ended.isoformat(), 'stdout': result.stdout, 'stderr': result.stderr, 'exit_code': result.returncode})
payload = {'generated_at': datetime.now(timezone.utc).isoformat(), 'scope': [str(p.relative_to(root)) for p in docs], 'checks': checks}
(root / 'records/VERIFLOW-SPEC-20260916/evidence/docs-coder/v4-checks.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
