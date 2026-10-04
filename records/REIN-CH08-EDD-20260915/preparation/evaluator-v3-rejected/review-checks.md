# Chapter 08 independent review checks

This checklist is frozen for two independent reviewers. Run every check; record commands and raw evidence in `evidence/`. Do not award a synthetic precise score.

## Functional checks

- Run the public full check and strategy-filtered check. Verify 16 unique rows, stable IDs, all required fields, messages/rules/question retention, exact UTF-8 estimate, `serviceTokens: null`, source-backed claims, frozen-fact quality, explicit unknown, and no unsupported claims.
- Exercise budget 0: assert `context_budget_exhausted`, zero model calls, zero operations/records, and no document I/O.
- Exercise duplicate metadata, invalid path escape, missing document, duplicate rows, missing rows, wrong estimate, unsupported claim, stale/oracle-dependent value, and accepted duplicate metadata. Assert the specific check ID and response, not merely process exit.

## Regression checks

- Run TypeScript typecheck/all tests, Rust fmt/check/test, and existing 05–07 compare checks.
- Run the real 16-row ch08 command and verify the root protocol, including failures and `callRecords`.

## Architecture checks

- Inspect that Rust owns method selection, budget and evidence adoption, while the real `StdioExecutor` launches Node. Exercise an actual Node failure and assert an error response with a retained failed record.
- Confirm four real methods and parameter/data changes; Rust budget is authoritative. Confirm no expectedFacts/EDD record is read by the product.
- Confirm calibration is a data-driven toy only and is not described as Rust/Node or model validation.

## Reproducing the body

- Extract and run every key bash code block from the final chapter, then run all three independent exercises using copied temporary data.
- Run the README standalone example with its complete absolute paths and inputs.
- Check anchors `methods-entry`, `fixed-dataset`, `four-methods`, `compare-results`, `method-failure`, `practice-08-1`, `practice-08-2`, `practice-08-3`; verify navigation links and docs build.

## First-pass completeness

- List any implementation claim that says “passed” while the command or response actually fails, and attach the raw command output.
- Product scoring must not penalize absent EDD formatting; report process/evidence gaps separately. For each of functionality, regression, architecture, body reproduction, and first-pass completeness, record facts and pass/fail only.

Automation observes the external protocol. It cannot prove a real process boundary, real algorithm, Rust authority, or authentic four-method implementation; those require source inspection and actual execution evidence.
