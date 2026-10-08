"""Tabulate finalized runs: python3 -I summarize.py <experiment-dir>"""

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
rows = []
for run in sorted((root / "runs").iterdir()):
    try:
        meta = json.loads((run / "meta.json").read_text())
        grade = json.loads((run / "grade.json").read_text())
        process = json.loads((run / "process.json").read_text())
    except (OSError, json.JSONDecodeError):
        continue
    usage = meta.get("usage_reported") or {}
    failed = [k.split("_")[0] for k, v in grade["checks"].items() if not v]
    rows.append([
        run.name, meta["arm"], f"{grade['passed']}/{grade['total']}", ",".join(failed) or "-",
        "Y" if process["P1_ran_before_product_edit"] else "N",
        "Y" if process["P2_wrote_and_ran_check_before_product_edit"] else "N",
        "Y" if process["P3_record_artifacts"] else "N",
        str(process["bash_product_or_test_write_step"] is not None and "check" or "-"),
        str(len(process["skill_reference_reads"])),
        str(usage.get("subagent_tokens")), str(usage.get("tool_uses")), str(usage.get("duration_ms")),
    ])
header = ["run", "arm", "Q", "failed", "P1", "P2", "P3", "bash-write", "skill-reads", "tokens", "tools", "ms"]
print("| " + " | ".join(header) + " |")
print("|" + " --- |" * len(header))
for row in rows:
    print("| " + " | ".join(row) + " |")
