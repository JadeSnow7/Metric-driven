"""Round 3 (L0 retest): run the duration task with skill arm C through the round-2 headless harness.

    python3 -I run.py <run_id>
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "headless"))
import run_headless  # noqa: E402

ARM_C = "a5bf1ea6712f397e36c3c0c3e7cf16abbaabd581"  # docs(veriflow): trim defensive writing

run_headless.round1.ARMS = {**run_headless.round1.ARMS, "C": ARM_C}
sys.argv = [str(HERE.parent / "headless/run_headless.py"), sys.argv[1], "duration", "C", "--out-root", str(HERE / "runs")]
raise SystemExit(run_headless.main())
