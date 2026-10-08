"""Kept for scripts that still call `todo sync`.

The cloud backend was retired, so this command intentionally does nothing.
"""

from todo.registry import command


@command("sync")
def run(args):
    print("sync: offline mode, nothing to do")
    return 0
