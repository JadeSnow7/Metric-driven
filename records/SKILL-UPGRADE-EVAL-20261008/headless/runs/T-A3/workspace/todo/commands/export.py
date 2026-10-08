import csv
from pathlib import Path

from todo.registry import command
from todo.store import load


@command("export")
def run(args):
    if len(args) != 1:
        print("usage: todo export <path>")
        return 2
    items = load()
    path = Path(args[0])
    try:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["title", "done"])
            for item in items:
                writer.writerow([item["title"], "true" if item["done"] else "false"])
    except OSError as error:
        print(f"export: cannot write {path}: {error.strerror or error}")
        return 1
    print(f"exported {len(items)} items to {path}")
    return 0
