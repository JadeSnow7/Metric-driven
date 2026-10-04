#!/usr/bin/env python3
"""Data-driven toy external protocol used only to calibrate the evaluator."""
import argparse, json, os, sys
from pathlib import Path

def estimate(ms): return sum(8+len(m["role"].encode())+len(m["content"].encode()) for m in ms)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data-root",required=True); ap.add_argument("--strategy",choices=["on-demand","window","summary","retrieval"],required=True); ap.add_argument("--budget",type=int)
    a=ap.parse_args(); root=Path(a.data_root); idx=json.loads((root/"index.json").read_text()); tasks=json.loads((root/"tasks.json").read_text())["tasks"]; mutant=os.getenv("CALIBRATION_MUTANT","")
    if mutant=="accept-duplicate-metadata": idx["documents"][1]["id"]=idx["documents"][0]["id"]
    if mutant=="path-escape": idx["documents"][0]["path"]="../outside"
    if mutant in ("accept-duplicate-metadata", "path-escape"):
        print("invalid metadata", file=sys.stderr); return 2
    results=[]
    for task in tasks:
        budget=0 if mutant=="budget0-dispatch" else (a.budget if a.budget is not None else task["budget"])
        ms=[{"role":"system","content":r} for r in task["rules"]]+[{"role":"user","content":task["question"]}]
        docs=idx["documents"]
        wanted=[d for d in docs if d["id"] in {e["source"] for e in task["expectedFacts"]}]
        if a.strategy=="summary": wanted=wanted[:]
        elif a.strategy=="on-demand": wanted=wanted
        elif a.strategy=="window": wanted=wanted
        else: wanted=wanted
        for d in wanted:
            p=root/d["path"]
            if not p.is_file():
                results.append({"taskId":task["id"],"strategy":a.strategy,"question":task["question"],"budget":budget,"status":"error","messages":ms,"estimatedUnits":estimate(ms),"selectedSources":[d["id"]],"operations":[{"op":"read","path":d["path"]}],"answer":None,"quality":None,"unsupportedClaims":[],"elapsedMs":0,"serviceTokens":None,"modelCalls":0,"callRecords":[]}); break
            ms.append({"role":"user","content":f"[来源:{d['id']}]\n"+p.read_text()})
        if results and results[-1].get("taskId")==task["id"] and results[-1]["status"]=="error": continue
        if estimate(ms)>budget:
            results.append({"taskId":task["id"],"strategy":a.strategy,"question":task["question"],"budget":budget,"status":"context_budget_exhausted","messages":[],"estimatedUnits":0,"selectedSources":[],"operations":[],"answer":None,"quality":None,"unsupportedClaims":[],"elapsedMs":0,"serviceTokens":None,"modelCalls":0,"callRecords":[]}); continue
        text="\n".join(m["content"] for m in ms); claims=[]
        for e in task["expectedFacts"]:
            marker=f"{e['field']}："; val=next((line.split(marker,1)[1] for line in text.splitlines() if marker in line),None)
            if val is not None: claims.append({"field":e["field"],"value":val,"source":e["source"]})
        if mutant=="unsupported-claim" and task["id"]=="task-01": claims.append({"field":"伪造","value":"invented","source":"doc-01"})
        if mutant=="wrong-estimate": est=estimate(ms)+1
        else: est=estimate(ms)
        if mutant=="frozen-original" and task["id"]=="task-01": claims=[dict(c,value="JSON Lines") if c["field"]=="传输方式" else c for c in claims]
        if mutant=="missing-row" and task["id"]=="task-04": continue
        if mutant=="duplicate-row" and task["id"]=="task-04": results.append(dict(results[-1] if results else {})) if results else None
        results.append({"taskId":task["id"],"strategy":a.strategy,"question":task["question"],"budget":budget,"status":"completed","messages":ms,"estimatedUnits":est,"selectedSources":[d["id"] for d in wanted],"operations":[{"op":"read","path":d["path"]} for d in wanted],"answer":{"rawAnswer":"; ".join(c["value"] for c in claims),"claims":claims,"insufficientEvidence":not claims},"quality":len(claims)/len(task["expectedFacts"]) if task["expectedFacts"] else 1.0,"unsupportedClaims":[],"elapsedMs":0,"serviceTokens":None,"modelCalls":1,"callRecords":[{"child_pid":1,"dispatched":True,"reaped":True,"exit_code":0,"terminal":"completed"}]})
    if mutant=="duplicate-row" and results: results.append(dict(results[-1]))
    if mutant=="budget0-dispatch":
        for r in results: r["status"]="completed"; r["modelCalls"]=1; r["messages"]=[]
    print(json.dumps({"unit":idx.get("unit"),"serviceTokens":None,"results":results},ensure_ascii=False))
if __name__=="__main__": raise SystemExit(main())
