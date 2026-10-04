CH05 candidate-03 CLI回放入口：

TS：cd ts && npm run ch05:offline -- workspace <workspace-dir> <mode>
Rust：CARGO_TARGET_DIR=/private/tmp/rein-candidate03-build cargo run --manifest-path rust/Cargo.toml --example ch05_loop -- workspace <workspace-dir> <mode>
统一比较：npm run ch05:compare-all

mode：single、multi（默认行为）；recovery（先 missing.md，收到 path_invalid 后读取 README.md 并回答实际内容）；empty（空白最终回答，empty_final）；exhausted（工具调用后 replay exhausted，model_error）；limit（持续工具调用，maxTurns=2，max_turns）。live 仍需 --live 且最多4轮。

四模式实际结果与原始 JSON 位于 four-modes.json 及 ts-*.json/rust-*.json；workspace 含 README.md 与 notes.md。
