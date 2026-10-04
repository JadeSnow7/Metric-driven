#!/usr/bin/env python3
"""Independent black-box evaluator for the chapter 08 external protocol."""
from __future__ import annotations

import argparse, hashlib, json, os, shutil, subprocess, tempfile, time
from pathlib import Path
from typing import Any

STRATEGIES = ("on-demand", "window", "summary", "retrieval")
REQUIRED = ("taskId", "strategy", "question", "budget", "status", "messages",
            "estimatedUnits", "selectedSources", "operations", "answer", "quality",
            "unsupportedClaims", "elapsedMs", "serviceTokens", "modelCalls", "callRecords")

def sha(path: Path) -> str:
    h = hashlib.sha256()
    if path.is_file():
        h.update(path.read_bytes())
    elif path.is_dir():
        for p in sorted(x for x in path.rglob("*") if x.is_file()):
            h.update(str(p.relative_to(path)).encode()); h.update(p.read_bytes())
    return h.hexdigest()

def load_data(root: Path) -> tuple[dict, dict]:
    return json.loads((root / "index.json").read_text()), json.loads((root / "tasks.json").read_text()).get("tasks", [])

def valid_metadata(index: dict, data: Path) -> list[str]:
    errors=[]; docs=index.get("documents", [])
    ids=[d.get("id") for d in docs]; orders=[d.get("order") for d in docs]
    if len(ids)!=len(set(ids)): errors.append("duplicate document id")
    if len(orders)!=len(set(orders)): errors.append("duplicate document order")
    if index.get("unit") != "estimated-bytes-v1": errors.append("wrong unit")
    for d in docs:
        p=Path(str(d.get("path", "")))
        if p.is_absolute() or ".." in p.parts: errors.append(f"path_escape:{d.get('id')}")
        elif not (data / p).is_file(): errors.append(f"missing_document:{d.get('id')}")
    tasks=json.loads((data / "tasks.json").read_text()).get("tasks", [])
    tids=[t.get("id") for t in tasks]
    if len(tids)!=len(set(tids)): errors.append("duplicate task id")
    return errors

def estimate(messages: list[dict]) -> int:
    return sum(8 + len(str(m.get("role", "")).encode()) + len(str(m.get("content", "")).encode()) for m in messages)

def source_messages(messages: list[dict]) -> dict[str, str]:
    return {m["content"].split("\n",1)[0][4:-1]: m["content"] for m in messages
            if isinstance(m, dict) and isinstance(m.get("content"), str) and m["content"].startswith("[来源:")}

def check_row(row: dict, task: dict, strategy: str, index: dict, *, budget_zero=False) -> list[tuple[str,bool,str]]:
    out=[]
    def add(cid, ok, why): out.append((cid, bool(ok), why))
    for k in REQUIRED: add(f"schema.{k}", k in row, "present" if k in row else "missing")
    if any(k not in row for k in REQUIRED): return out
    add("schema.status", row["status"] in ("completed", "context_budget_exhausted", "error"), "recognized status")
    add("schema.serviceTokens-null", row["serviceTokens"] is None, "must be null")
    add("messages.rules-question", len(row["messages"]) >= 3 and [m.get("content") for m in row["messages"][:3]] == task["rules"] + [task["question"]], "rules and question retained")
    add("messages.utf8-estimate", row["estimatedUnits"] == estimate(row["messages"]), "exact UTF-8 estimate")
    add("budget.within-request", row["estimatedUnits"] <= row["budget"] or row["status"] == "context_budget_exhausted", "within budget or explicit exhaustion")
    if row["status"] == "context_budget_exhausted":
        add("budget.exhausted-shape", row["answer"] is None and row["modelCalls"] == 0 and not row["messages"] and not row["operations"] and not row["callRecords"], "zero-I/O exhaustion shape")
        return out
    if row["status"] == "error":
        add("errors.no-answer", row["answer"] is None and row["modelCalls"] == 0, "error has no answer/model call")
        return out
    add("completed.model-call", row["modelCalls"] == 1, "one offline answer call")
    add("completed.answer-shape", isinstance(row["answer"], dict) and isinstance(row["answer"].get("claims"), list), "answer object")
    src=source_messages(row["messages"])
    answer=row["answer"] if isinstance(row["answer"], dict) else {}
    claims=answer.get("claims", [])
    for i,c in enumerate(claims):
        source=c.get("source"); value=c.get("value"); field=c.get("field")
        evidence=source in src and (f"{field}：{value}" in src[source] or f"{field}: {value}" in src[source])
        add(f"claims.source-evidence.{i}", evidence, "claim has matching source fact")
    expected=task.get("expectedFacts", [])
    matched=sum(1 for e in expected if any(c.get("field")==e["field"] and c.get("value")==e["value"] and c.get("source")==e["source"] and c.get("source") in src and (f"{c.get('field')}：{c.get('value')}" in src[c.get("source")] or f"{c.get('field')}: {c.get('value')}" in src[c.get("source")]) for c in claims))
    add("quality.frozen-facts", row["quality"] == (matched/len(expected) if expected else 1.0), "quality from expectedFacts and evidence claims")
    if expected:
        add("quality.all-required", matched == len(expected), "all required facts present")
    else:
        add("unknown.explicit", answer.get("insufficientEvidence") is True and not claims and row.get("quality") == 1.0, "unknown question is explicitly insufficient")
    add("unsupportedClaims.empty", not row["unsupportedClaims"], "no unsupported claims")
    return out

def run_one(argv: list[str], cwd: Path, env: dict, record: Path, hashes: dict, timeout=30) -> tuple[int,dict]:
    start=time.time(); t0=time.monotonic()
    try:
        p=subprocess.run(argv,cwd=cwd,env=env,text=True,capture_output=True,timeout=timeout)
        timed=False
    except subprocess.TimeoutExpired as e:
        p=subprocess.CompletedProcess(argv,124,e.stdout or "",e.stderr or ""); timed=True
    end=time.time()
    rec={"argv":argv,"cwd":str(cwd),"start":start,"end":end,"exit":p.returncode,"timeout":timed,
         "stdout":p.stdout,"stderr":p.stderr,"durationMs":int((time.monotonic()-t0)*1000), **hashes}
    record.write_text(json.dumps(rec,ensure_ascii=False,indent=2))
    return p.returncode, rec

def parse_rows(stdout: str) -> tuple[dict|None,str|None]:
    try: return json.loads(stdout), None
    except json.JSONDecodeError as e: return None, f"invalid JSON stdout: {e}"

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--repo",required=True); ap.add_argument("--data",required=True); ap.add_argument("--output",required=True); ap.add_argument("--strategy",choices=STRATEGIES); ap.add_argument("--command-json")
    args=ap.parse_args(); repo=Path(args.repo).resolve(); data=Path(args.data).resolve(); output=Path(args.output).resolve(); output.mkdir(parents=True,exist_ok=True); (output/"runs").mkdir(exist_ok=True)
    index,tasks=load_data(data); checks=[]
    def result(cid,passed,reason): checks.append({"id":cid,"passed":bool(passed),"reason":reason})
    meta=valid_metadata(index,data)
    result("metadata.valid", not meta, "; ".join(meta) if meta else "metadata valid")
    # The real default command is one invocation producing all 16 rows. The
    # calibration toy has a one-strategy interface, so it is invoked once per
    # strategy only when explicitly supplied through --command-json.
    strategies=[args.strategy] if args.strategy else (list(STRATEGIES) if args.command_json else [None])
    cmd=json.loads(args.command_json) if args.command_json else ["npm","run","--silent","ch08:compare","--","--data-root",str(data)]
    hashes={"evaluatorHash":sha(Path(__file__).resolve()),"inputHash":sha(data),"sourceHash":sha(repo)}
    for strategy in strategies:
        av=cmd + ([] if args.command_json is None else [])
        if args.command_json is None and strategy is not None: av += ["--strategy",strategy]
        else:
            if "--data-root" not in av: av += ["--data-root",str(data)]
            if "--strategy" not in av: av += ["--strategy",strategy]
        env=os.environ.copy(); env["CH08_EVALUATOR_DATA_HASH"]=sha(data); env["CH08_EVALUATOR_SOURCE_HASH"]=sha(repo)
        rc,rec=run_one(av,repo,env,output/"runs"/f"{strategy}.json",hashes)
        payload,err=parse_rows(rec["stdout"])
        result(f"run.{strategy}.exit", rc==0, "process completed" if rc==0 else f"exit {rc}: {rec['stderr'][-300:]}")
        if err: result(f"run.{strategy}.json",False,err); continue
        result(f"run.{strategy}.root", isinstance(payload,dict) and payload.get("serviceTokens") is None and isinstance(payload.get("results"),list), "root protocol")
        rows=payload.get("results",[]) if isinstance(payload,dict) else []
        expected=len(tasks)
        if not args.strategy: result(f"rows.{strategy or 'all'}.count",len(rows)==(expected if strategy else expected*4),f"expected {expected if strategy else expected*4}, got {len(rows)}")
        for row in rows:
            task=next((t for t in tasks if t["id"]==row.get("taskId")),None)
            row_strategy=row.get("strategy") or strategy or "all"
            if task: checks.extend({"id":f"{row_strategy}.{cid}","passed":p,"reason":why} for cid,p,why in check_row(row,task,row_strategy,index))
            else: result(f"{strategy}.row.task",False,"unknown task")
    summary={"evaluator":"ch08-independent-v3","repo":str(repo),"data":str(data),"inputHash":sha(data),"sourceHash":sha(repo),"checks":checks,"passed":all(c["passed"] for c in checks),"checkCount":len(checks),"failedCount":sum(not c["passed"] for c in checks)}
    (output/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
    return 0 if summary["passed"] else 1

if __name__ == "__main__": raise SystemExit(main())
