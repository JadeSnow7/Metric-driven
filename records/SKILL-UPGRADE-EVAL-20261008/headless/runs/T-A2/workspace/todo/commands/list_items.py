from todo.registry import command
from todo.store import load


@command("list")
def run(args):
    for index, item in enumerate(load(), start=1):
        mark = "x" if item["done"] else " "
        print(f"{index}. [{mark}] {item['title']}")
    return 0
