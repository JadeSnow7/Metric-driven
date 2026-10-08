"""Measure the final report of one run: python3 -I report_metrics.py <process.json>

Fields: chars, bold or heading lines, caveat sentences (things not done /
not checked), and whether it explains an unchanged README/doc.
"""

import json
import re
import sys

CAVEAT = re.compile(r"没有|未运行|未覆盖|没做|没测|未做|不确定|没改|没动|未更新|没更新|没碰|didn't|did not|not run|haven't|no other")
DOC_UNCHANGED = re.compile(r"(README|文档|docs?)[^。\n]{0,40}((没有|没|未)(改|更新|变化|动)|unchanged|not (changed|updated)|didn't change)"
                           r"|(didn't|did not) (change|update) the (README|docs?)", re.I)


def measure(text: str) -> dict:
    sentences = [s for s in re.split(r"[。\n；]|(?<=[.!?])\s", text) if s.strip()]
    return {
        "chars": len(text),
        "headings": len(re.findall(r"^\s*(\*\*|#+ )", text, re.M)),
        "caveat_sentences": sum(1 for s in sentences if CAVEAT.search(s)),
        "doc_unchanged_note": bool(DOC_UNCHANGED.search(text)),
    }


if __name__ == "__main__":
    process = json.load(open(sys.argv[1], encoding="utf-8"))
    print(json.dumps(measure(process.get("final_text") or ""), ensure_ascii=False))
