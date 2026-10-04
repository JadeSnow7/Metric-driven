# Review 01 historical transcript evidence

These results are transcribed from the first review's tool outputs in this task. The first review was read-only and did not persist a source hash before subsequent fixes. No current SHA-256 is attributed to that earlier version. The complete second review has separately captured before/after source hashes.

Original selfcheck command:

```sh
python3 -B -m unittest discover -s tools/tests -v
```

Observed: `Ran 9 tests in 0.195s`, `OK`.

Original temporary-candidate outputs from `assertions_hold`:

```jsonl
{"case":"expired-command-03","candidate":"Use `npm run test` for tests.\n","oracle_pass":false}
{"case":"expired-command-01","candidate":"rein-check\n","oracle_pass":true}
{"case":"parameter-change-02","candidate":"--root\n","oracle_pass":true}
{"case":"parameter-change-03","candidate":"The config key is `API_URL`.\n<!-- REIN_API_URL -->\n","oracle_pass":true}
{"case":"broken-relative-link-01","candidate":"See [the guide](./docs/guide.md).\n","oracle_pass":false}
{"case":"broken-relative-link-01","candidate":"See [guide](docs/missing.md).\n<!-- [guide](docs/guide.md) -->\n","oracle_pass":true}
```

Original runner probe: a real `python -B -m unittest discover` invocation with one @unittest.skip test produced `Ran 1 test`, `OK (skipped=1)`. The evaluation incorrectly returned `status=passed`, `tests_run=1`, `reasons=[]`.

Original timeout probe argv was `[python, "-u", "-c", "import time; print(\"failure context\",flush=True);time.sleep(2)"]`, timeout_seconds=0.1. It returned failed and recorded empty stdout and stderr.

Original parser probe input was `test result: ok. 3 passed; 0 failed; 0 ignored\ntest result: ok. 5 passed; 0 failed; 0 ignored`; `test_count` returned 5 although the summaries represent 8 passing tests.

The current executable reproducer `rereview-02.py` repeats the same issue classes against the revised fixtures and records exact current sources; it is not a replay of the old version.
