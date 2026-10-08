from todo.registry import command
from todo.store import load, save


@command("add")
def run(args):
    title = " ".join(args).strip()
    if not title:
        print("add: missing title")
        return 2
    items = load()
    items.append({"title": title, "done": False})
    save(items)
    print(f"added: {title}")
    return 0
