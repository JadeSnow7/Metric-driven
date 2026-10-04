import { cpSync, mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { resolve } from 'node:path'
import { spawnSync } from 'node:child_process'
const root = resolve(new URL('../..', import.meta.url).pathname)
const work = mkdtempSync(resolve(tmpdir(), 'rein-ch08-example-'))
cpSync(resolve(new URL('input', import.meta.url).pathname), resolve(work, 'input'), { recursive: true })
cpSync(resolve(new URL('docs', import.meta.url).pathname), resolve(work, 'input/docs'), { recursive: true })
const r = spawnSync('node', ['scripts/ch08-compare.mjs', '--data-root', resolve(work, 'input')], { cwd: root, encoding: 'utf8' })
if (r.status !== 0) { process.stderr.write(r.stderr); process.exit(r.status ?? 1) }
const out = JSON.parse(r.stdout); if (out.results.length !== 4) throw new Error('example must produce four strategies')
console.log(JSON.stringify({ example: 'ch08-context-methods', rows: out.results.length }))
