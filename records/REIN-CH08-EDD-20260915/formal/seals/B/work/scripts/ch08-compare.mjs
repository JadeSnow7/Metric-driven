import { spawnSync } from 'node:child_process'
import { resolve } from 'node:path'
const root=resolve(new URL('..', import.meta.url).pathname)
const args=process.argv.slice(2); const strategies=args.includes('--strategy') ? [args[args.indexOf('--strategy')+1]] : ['on-demand','window','summary','retrieval']
const all=[]; let unit='estimated-bytes-v1'
for(const strategy of strategies){ const run=spawnSync('cargo',['run','--quiet','--locked','--manifest-path',resolve(root,'rust/Cargo.toml'),'--example','ch08_context','--',...args,'--strategy',strategy],{cwd:root,encoding:'utf8'}); if(run.error||run.status!==0){process.stderr.write(run.stderr||'ch08 failed\n');process.exit(run.status||2)} const out=JSON.parse(run.stdout); unit=out.unit; all.push(...out.results) }
process.stdout.write(JSON.stringify({unit,serviceTokens:null,results:all})+'\n')
