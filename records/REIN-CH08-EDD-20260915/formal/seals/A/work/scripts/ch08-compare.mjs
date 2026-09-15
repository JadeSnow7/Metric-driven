import { mkdirSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { spawnSync } from 'node:child_process'
const root=resolve(new URL('..',import.meta.url).pathname), args=process.argv.slice(2)
let dataRoot=resolve(root,'fixtures/ch08-context'), strategy=null, budget=null
for(let i=0;i<args.length;i++){if(args[i]==='--data-root')dataRoot=resolve(args[++i]);else if(args[i]==='--strategy')strategy=args[++i];else if(args[i]==='--budget')budget=args[++i]}
const rust=resolve(root,'rust/Cargo.toml'), cli=['run','--quiet','--locked','--manifest-path',rust,'--example','ch08_context','--',dataRoot]; if(strategy)cli.push('--strategy',strategy);if(budget!==null)cli.push('--budget',budget)
const p=spawnSync('cargo',cli,{cwd:root,encoding:'utf8'});const record={argv:['cargo',...cli],cwd:root,startedAt:new Date().toISOString(),stdout:p.stdout,stderr:p.stderr,exitCode:p.status,signal:p.signal};mkdirSync(resolve(root,'records/ch08'),{recursive:true});writeFileSync(resolve(root,'records/ch08/compare.json'),JSON.stringify(record,null,2));if(p.error||p.status!==0){process.stderr.write(p.stderr||p.error?.message||'compare failed');process.exit(p.status||1)}
process.stdout.write(p.stdout.split('\n').find(x=>x.startsWith('{'))+'\n')
