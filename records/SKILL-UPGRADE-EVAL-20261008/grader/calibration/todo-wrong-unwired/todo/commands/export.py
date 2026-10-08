import csv

from todo.registry import command
from todo.store import load


@command("export")
def run(args):
    if len(args) != 1:
        print("usage: todo export <path>")
        return 2
    with open(args[0], "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["title", "done"])
        for item in load():
            writer.writerow([item["title"], "true" if item["done"] else "false"])
    print(f"exported: {args[0]}")
    return 0
