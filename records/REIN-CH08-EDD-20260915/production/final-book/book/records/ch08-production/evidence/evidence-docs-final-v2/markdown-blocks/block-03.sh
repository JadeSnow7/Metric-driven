export CARGO_TARGET_DIR="${CARGO_TARGET_DIR:-$PWD/rust/target}"
npm run --silent ch08:compare | node -e 'let x="";process.stdin.on("data",d=>x+=d).on("end",()=>{const o=JSON.parse(x); if(o.unit!=="estimated-bytes-v1"||o.serviceTokens!==null||o.results.length!==16) process.exit(1); console.log(`rows=${o.results.length} unit=${o.unit} serviceTokens=${o.serviceTokens}`)})'
