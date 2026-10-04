import { spawnSync } from 'node:child_process'
import { resolve } from 'node:path'
const root=resolve(new URL('..', import.meta.url).pathname)
const run=(args)=>spawnSync('node',[resolve(root,'scripts/ch08-compare.mjs'),...args],{cwd:root,encoding:'utf8'})
for(const strategy of ['on-demand','window','summary','retrieval']){const r=run(['--strategy',strategy]);if(r.status!==0)throw new Error(`${strategy}: ${r.stderr}`);const o=JSON.parse(r.stdout);if(o.results.length!==4)throw new Error(`${strategy}: wrong result count`);for(const row of o.results){if(row.status!=='completed')throw new Error(`${strategy}/${row.taskId}: ${row.status}`);if(row.modelCalls!==1)throw new Error(`${strategy}/${row.taskId}: modelCalls`);if(row.answer===null)throw new Error(`${strategy}/${row.taskId}: missing answer`)}}
const zero=run(['--budget','0']);if(zero.status!==0)throw new Error('budget zero command failed');for(const row of JSON.parse(zero.stdout).results){if(row.status!=='context_budget_exhausted'||row.modelCalls!==0||row.operations.length)throw new Error('budget zero contract failed')}
console.log(JSON.stringify({passed:true,strategies:4,budgetZero:true}))
