import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

root = Path('/private/tmp/veriflow-spec-20260916')
checks = []
for argv in (['git', 'diff', '--check'], ['rg', '-n', 'Spec 要求的正文、示例或运行产物', 'skill/veriflow/SKILL.md', 'skill/veriflow/references/claude-code.md']):
    started = datetime.now(timezone.utc)
    result = subprocess.run(argv, cwd=root, capture_output=True, text=True)
    ended = datetime.now(timezone.utc)
    checks.append({'argv': argv, 'cwd': str(root), 'started_at': started.isoformat(), 'ended_at': ended.isoformat(), 'stdout': result.stdout, 'stderr': result.stderr, 'exit_code': result.returncode})
payload = {'generated_at': datetime.now(timezone.utc).isoformat(), 'scope': ['skill/veriflow/SKILL.md', 'skill/veriflow/references/design.md', 'skill/veriflow/references/claude-code.md'], 'checks': checks}
(root / 'records/VERIFLOW-SPEC-20260916/evidence/docs-coder/v5-checks.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
