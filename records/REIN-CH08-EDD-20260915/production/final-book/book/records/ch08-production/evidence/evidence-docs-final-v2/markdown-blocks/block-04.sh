export CARGO_TARGET_DIR="${CARGO_TARGET_DIR:-$PWD/rust/target}"
npm run --silent ch08:compare | node -e 'let x="";process.stdin.on("data",d=>x+=d).on("end",()=>{const o=JSON.parse(x); for(const r of o.results) console.log([r.taskId,r.strategy,r.status,r.quality,r.estimatedUnits,r.selectedSources.join(","),r.answer?.claims.length??"null",r.modelCalls].join("\t"))})'
