import csv
import sys

from todo.registry import command
from todo.store import load


@command("export")
def run(args):
    if len(args) != 1:
        print("usage: todo export <path>", file=sys.stderr)
        return 2
    items = load()
    try:
        # newline="" lets the csv module control line endings (embedded newlines stay intact).
        with open(args[0], "w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["title", "done"])
            for item in items:
                writer.writerow([item["title"], "true" if item["done"] else "false"])
    except OSError as error:
        print(f"export: cannot write {args[0]}: {error.strerror or error}", file=sys.stderr)
        return 1
    print(f"exported {len(items)} item(s) to {args[0]}")
    return 0
