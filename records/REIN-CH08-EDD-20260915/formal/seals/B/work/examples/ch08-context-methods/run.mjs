import { cp, mkdtemp, rm } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { spawnSync } from 'node:child_process'
const here=dirname(fileURLToPath(import.meta.url)); const temp=await mkdtemp('/tmp/rein-ch08-example-'); await cp(resolve(here,'input'),temp,{recursive:true})
try { for(const strategy of ['on-demand','window','summary','retrieval']) { const r=spawnSync('npm',['run','--silent','ch08:compare','--','--data-root',temp,'--strategy',strategy],{cwd:resolve(here,'../..'),encoding:'utf8'}); if(r.status!==0)throw new Error(r.stderr); const row=JSON.parse(r.stdout).results[0]; if(row.status!=='completed'||!row.operations.length||!row.messages.some(m=>m.content.startsWith('[来源:local-01]')))throw new Error(`${strategy} contract failed`); } console.log(JSON.stringify({passed:true,entry:'Rust -> Node read_file',strategies:4})) } finally { await rm(temp,{recursive:true,force:true}) }
