# prerequisites-v3 verification

Observed 2026-09-14 in production cwd. No commit, tag, push, external model request, or secret read was performed.

## Commands

| command | exit | result | raw evidence |
| --- | ---: | --- | --- |
| `npm run typecheck` | 0 | passed | `npm-typecheck.stdout-stderr.txt` |
| `npm test` | 0 | passed; 7 files, 70 tests | `npm-test.stdout-stderr.txt` |
| `cargo fmt --manifest-path rust/Cargo.toml -- --check` | 0 | passed | `cargo-fmt.stdout-stderr.txt` |
| `CARGO_TARGET_DIR=/private/tmp/rein-ch05-cargo-target cargo check --manifest-path rust/Cargo.toml --locked --offline` | 0 | passed | `cargo-check.stdout-stderr.txt` |
| `CARGO_TARGET_DIR=/private/tmp/rein-ch05-cargo-target cargo test --manifest-path rust/Cargo.toml --locked --offline` | 0 | passed; 9 unit + 4 prerequisite tests | `cargo-test.stdout-stderr.txt` |

The Rust integration test uses the concrete Reqwest transport against a trusted local `127.0.0.1` loopback server. It captured two requests and checked the second request's assistant `tool_calls` and both `tool_call_id` values. No network outside loopback was used.

## Changed-file SHA-256

```text
e3d3fcf037527499fdf2518728466755d94f7d353363c2755761fe6ae33d4af2  ts/src/rein/adapters.ts
878809d4036113c1c8aba9a55788cba12615de87c15666a01c98588b57eec2ee  ts/src/rein/contracts.ts
d9c29b3fc3b1c03bc2c116569eadbfaac66da08121e05b2dad6e512b9fe4997b  ts/src/rein/readonly.ts
496eef9bb5b7c9d7d86abee95cce8318962986fb6003424495cc8f0a933475f9  ts/tests/rein-prerequisites.test.ts
1a8509993b8886463cbc760e9a89e3e3918bd013f6d4dd862fb9e26b171e078d  rust/src/rein/mod.rs
197175bcf31f9b4acf669eabc2b75aa95d96979bfffd904233b13530bcd62ede  rust/tests/prerequisites.rs
c86150d3f883c14715f6736ffd9d6dd2ca1f2339982133345a2a203219e79b2e  rust/Cargo.toml
4665aba2dfe3a3c83545b0a1df454fe554d99abf44b250fb276b421926bc6d0a  rust/Cargo.lock
5d24a462295c6676ab83ba0b29dd63d3b462ba319226881484b90c25cf52ef38  rust/src/lib.rs
716411206323b717d373903b81e9d462d4b01f81b5a395a912fad4c417e73beb  contracts/README.md
1b422c7f6798c9b3af9c1be246f7d1cdd7a1e8e23da910f3db2128cad892bbed  fixtures/cases/prerequisites.json
a2956b94b5b32bf6975fa325aa5c350f5e6eeaf5860378605ca4866e23b6ee7a  fixtures/workspaces/prerequisites/README.md
```

Existing unrelated dirty files remain untouched. `rust/src/lib.rs` was already dirty and is listed only because it is within the permitted scope; this task did not intentionally change it.
