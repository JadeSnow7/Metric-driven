from todo.registry import command
from todo.store import load


@command("export")
def run(args):
    lines = ["title,done"] + [f"{item['title']},{str(item['done']).lower()}" for item in load()]
    open(args[0], "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return 0
