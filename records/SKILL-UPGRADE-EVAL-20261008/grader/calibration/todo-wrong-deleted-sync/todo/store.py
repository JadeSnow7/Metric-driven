import json
import os
from pathlib import Path


def data_path():
    return Path(os.environ.get("TODO_FILE", "todo.json"))


def load():
    path = data_path()
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def save(items):
    data_path().write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
