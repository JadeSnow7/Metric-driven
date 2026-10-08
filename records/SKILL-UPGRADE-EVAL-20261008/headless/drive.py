"""Run all round-2 cells with bounded concurrency: python3 -I drive.py"""

import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
CELLS = [(f"{t[0].upper()}-{arm}{rep}", t, arm) for rep in range(1, 6) for t in ("duration", "todo") for arm in ("A", "B")]


def run(cell):
    run_id, task, arm = cell
    done = subprocess.run([sys.executable, "-I", str(HERE / "run_headless.py"), run_id, task, arm], text=True, capture_output=True)
    line = (done.stdout.strip().splitlines() or [done.stderr.strip()[-300:]])[-1]
    print(line, flush=True)


with ThreadPoolExecutor(max_workers=4) as pool:
    list(pool.map(run, CELLS))
