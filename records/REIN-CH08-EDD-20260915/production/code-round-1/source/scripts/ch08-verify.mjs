import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { spawnSync } from 'node:child_process'
const root = resolve(new URL('..', import.meta.url).pathname)
const run = (args) => { const r = spawnSync('node', args, { cwd: root, encoding: 'utf8' }); if (r.status !== 0) throw new Error(r.stderr); return r.stdout }
const out = JSON.parse(run(['scripts/ch08-compare.mjs']))
if (out.unit !== 'estimated-bytes-v1' || out.results.length !== 16) throw new Error('ch08 must produce 16 results')
for (const row of out.results) { if (!row.taskId || !row.strategy || !Array.isArray(row.messages) || row.serviceTokens !== null) throw new Error('invalid result row'); if (row.status === 'completed' && row.modelCalls !== 1) throw new Error('completed row must call offline answerer once'); if (row.taskId === 'task-04' && !row.answer?.insufficientEvidence) throw new Error('unknown task must be insufficient') }
const example = resolve(root, 'examples/ch08-context-methods/README.md')
if (readFileSync(example, 'utf8').includes('node examples')) run(['examples/ch08-context-methods/entry.mjs'])
process.stdout.write(JSON.stringify({ unit: out.unit, rows: out.results.length }) + '\n')
