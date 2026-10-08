import importlib
import sys
from pathlib import Path

from .registry import COMMANDS

PLUGINS = Path(__file__).with_name("plugins.cfg")


def load_commands():
    for line in PLUGINS.read_text(encoding="utf-8").splitlines():
        name = line.strip()
        if name and not name.startswith("#"):
            importlib.import_module(f"todo.commands.{name}")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    load_commands()
    if not argv or argv[0] not in COMMANDS:
        print(f"usage: todo {{{','.join(sorted(COMMANDS))}}} ...", file=sys.stderr)
        return 2
    return COMMANDS[argv[0]](argv[1:])
