"""Tabulate round-2 runs and per-cell counts: python3 -I summarize.py"""

import json
import statistics
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows, cells = [], defaultdict(list)
for run in sorted((HERE / "runs").iterdir()):
    try:
        meta = json.loads((run / "meta.json").read_text())
        grade = json.loads((run / "grade.json").read_text())
        process = json.loads((run / "process.json").read_text())
    except (OSError, json.JSONDecodeError):
        continue
    result = meta.get("result") or {}
    completed = meta.get("exit_code") == 0 and not meta.get("timed_out") and result.get("subtype") == "success" and not result.get("is_error")
    record = {
        "run": run.name, "task": meta["task"], "arm": meta["arm"], "completed": completed,
        "q": grade.get("passed"), "q_total": grade.get("total"),
        "failed": [k.split("_")[0] for k, v in (grade.get("checks") or {}).items() if not v],
        "p1": process.get("P1_ran_before_product_edit"), "p2": process.get("P2_wrote_and_ran_check_before_product_edit"),
        "p3": process.get("P3_record_artifacts"), "reads": process.get("skill_reference_reads") or [],
        "turns": result.get("num_turns"), "cost": result.get("total_cost_usd"), "ms": result.get("duration_ms"),
        "models": result.get("model_usage_models"),
    }
    rows.append(record)
    cells[(record["task"], record["arm"])].append(record)

yn = lambda value: "Y" if value else "N"
print("| run | 完成 | Q | 未过 | P1 | P2 | P3 | 读取的 references | turns | cost_usd | duration_ms |")
print("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
for r in rows:
    refs = ", ".join(x for x in r["reads"] if x != "SKILL.md") or "-"
    print(f"| {r['run']} | {yn(r['completed'])} | {r['q']}/{r['q_total']} | {','.join(r['failed']) or '-'} | {yn(r['p1'])} | {yn(r['p2'])} | {yn(r['p3'])} | {refs} | {r['turns']} | {r['cost']} | {r['ms']} |")

print()
print("| 任务 | 组 | n | 完成 | 产品全过 | P1 | P2 | P3 | 读 references | cost 中位数 | turns 中位数 | duration_ms 中位数 |")
print("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
for (task, arm), group in sorted(cells.items()):
    count = lambda key: sum(1 for r in group if r[key])
    median = lambda key: statistics.median([r[key] for r in group if r[key] is not None]) if any(r[key] is not None for r in group) else None
    full = sum(1 for r in group if r["q"] == r["q_total"])
    refs = sum(1 for r in group if any(x != "SKILL.md" for x in r["reads"]))
    cost = median("cost")
    print(f"| {task} | {arm} | {len(group)} | {count('completed')} | {full} | {count('p1')} | {count('p2')} | {count('p3')} | {refs} | "
          f"{round(cost, 3) if cost is not None else None} | {median('turns')} | {median('ms')} |")
