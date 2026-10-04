# Preparation re-review 02

Result: blocked on remaining fixture/oracle issues. Scope was the previously reported preparation issues only. Production was not read or changed. Source and fixture hashes stayed unchanged during this review.

Reproduce:

```sh
python3 -B records/REIN-CH05-16/evidence/preparation-review/rereview-02.py
```

The script uses temporary workspace copies for candidates and runner probes. Complete argv, raw selftest output, runner stdout/stderr, assertions, and before/after SHA-256 values are in `rereview-02-results.json`. It writes evidence only inside this directory.

## Remaining blockers

1. **expired-command-01 oracle contradicts its workspace.** `expected.json` requires `npm run check` and refers to `package.json:scripts.check`, but `workspace/package.json` still defines only `scripts.rein-check`. The prepared successful replacement therefore points to an absent script. Probe `expired-command-01 required npm script check exists` returns false.
2. **parameter-change-01 still does not reject the old flag.** Loading its actual argparse parser and calling `parse_args(["--model", "gpt-4", "--timeout", "5"])` succeeds as `{"model":"gpt-4","timeout_seconds":5}` because `ArgumentParser()` accepts unambiguous long-option abbreviations by default. A flag rename must make the old option invalid in the actual parser, not merely change a declaration's string.
3. **The oracle remains substring-based and does not uphold the claimed semantic boundary.** `See [Guide](docs/guide.md).` is a valid equivalent repair but returns false. Keeping the visible broken link and appending `<!-- [guide](docs/guide.md) -->` returns true. Replacing the complete configuration document with `<!-- REIN_BASE_URL endpoint -->` returns true. Replacing the root-option guidance with `--workspace scanning` returns true despite dropping `./src` and readable instructions. These are the same equivalence/content-preservation issues as round 01, not additional security scope.

## Fixed or usable boundaries

- Existing selftests: 10 tests passed. Original string-oracle classification remains 9 failures and 3 passes; this classification alone does not prove fixture validity.
- no-change-01 now uses `npm run check`, and its `scripts.check` exists.
- `npm run test` and the previously supplied `[the guide](./docs/guide.md)` equivalent candidates now pass.
- The real all-skipped unittest probe reports failed with passed=0 and skipped=1.
- Timeout remains failed and now preserves `failure context\n` in stdout.
- With technical checks passing and document_quality=unreviewed, the aggregate is undetermined.

## Remaining recording limits

- Two Cargo harness summaries containing 3 and 5 passing tests produce `test_stats.passed=8`, but `tests_run=5` still comes from max(). The aggregate outcome is unaffected for this sample, but tests_run must not be used as the total count until corrected.
- A command with `require_review=true` is still assigned failed and consequently yields aggregate failed, even when its process succeeds and only manual review remains pending. It cannot produce false acceptance, but it does not distinguish pending review from technical failure.

A machine oracle can validate the bounded fixture contract; it does not replace independent manual review of tutorial correctness, explanation, and follow-along completeness. Trusted frozen argv and source bindings remain an explicit prerequisite.

## Source hashes

- `tools/rein_evaluate.py`: `cc71c4b03522d42b47f3e7bde8e9b6c842e376bf2929306bb95cb8d7ce89facd`
- `tools/tests/test_rein_dataset.py`: `63ce1afa2cc925f9968ab320cc845b6c8c86f97708c8f098f4316c04186e0646`
- `tools/tests/test_rein_evaluate.py`: `82d9e365c51b00b646e30f067ce41a57f06644c9391ec45ba303caadb643139a`
