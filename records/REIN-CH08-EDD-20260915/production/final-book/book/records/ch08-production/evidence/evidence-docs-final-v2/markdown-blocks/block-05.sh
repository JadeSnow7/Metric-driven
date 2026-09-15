export CARGO_TARGET_DIR="${CARGO_TARGET_DIR:-$PWD/rust/target}"
BAD_ROOT="$(mktemp -d /tmp/rein-ch08-bad-metadata.XXXXXX)"
cp -R fixtures/ch08-context/. "$BAD_ROOT/"
node -e 'const fs=require("fs"); const p=process.argv[1]+"/index.json"; const x=JSON.parse(fs.readFileSync(p)); x.documents[1].order=x.documents[0].order; fs.writeFileSync(p,JSON.stringify(x));' "$BAD_ROOT"
if npm run --silent ch08:compare -- --data-root "$BAD_ROOT" >"$BAD_ROOT/invalid.out" 2>"$BAD_ROOT/invalid.err"; then exit 1; fi
rg -n "duplicate|invalid|metadata|order" "$BAD_ROOT/invalid.err"
