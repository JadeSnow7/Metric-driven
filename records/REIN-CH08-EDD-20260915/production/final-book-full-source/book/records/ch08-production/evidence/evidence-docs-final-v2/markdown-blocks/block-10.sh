export CARGO_TARGET_DIR="${CARGO_TARGET_DIR:-$PWD/rust/target}"
cargo test --locked --manifest-path rust/Cargo.toml --test ch08_context
npm run --silent ch08:verify
