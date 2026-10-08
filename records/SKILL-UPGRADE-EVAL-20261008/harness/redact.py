"""Keep only assistant tool calls/text and tool results from a subagent transcript.

Drops attachments (session context, environment, account details) and the
initial user prompt, which is already stored in meta.json.
Usage: python3 -I redact.py <raw.jsonl> <redacted.jsonl>
"""

import json
import sys

kept = []
for line in open(sys.argv[1], encoding="utf-8"):
    event = json.loads(line)
    message = event.get("message")
    if event.get("type") not in {"assistant", "user"} or not isinstance(message, dict):
        continue
    content = message.get("content")
    if not isinstance(content, list):
        continue
    if event["type"] == "user":
        content = [block for block in content if isinstance(block, dict) and block.get("type") == "tool_result"]
    else:
        content = [block for block in content if isinstance(block, dict) and block.get("type") in {"tool_use", "text"}]
    if content:
        kept.append({"type": event["type"], "message": {"role": message.get("role"), "model": message.get("model"), "content": content}})
with open(sys.argv[2], "w", encoding="utf-8") as handle:
    for event in kept:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
