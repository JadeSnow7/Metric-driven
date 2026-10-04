import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { spawnSync } from 'node:child_process'
import { resolve } from 'node:path'
const root = resolve(fileURLToPath(new URL('..', import.meta.url)))
const fixture = resolve(root, 'fixtures/cases/ch07-context.json')
const run = (command, args, cwd) => { const result = spawnSync(command, args, { cwd, encoding: 'utf8' }); if (result.error) throw result.error; if (result.status !== 0) throw new Error(`${command} failed: ${result.stderr}`); return JSON.parse(result.stdout) }
const ts = run('npm', ['run', '--silent', 'ch07:context', '--', fixture], root)
const rust = run('cargo', ['run', '--quiet', '--manifest-path', resolve(root, 'rust/Cargo.toml'), '--example', 'ch07_context', '--', fixture], root)
const normalize = value => JSON.stringify(value).replace(/adapter_budget_exceeded/g, 'model_error')
if (normalize(ts) !== normalize(rust)) throw new Error('ch07 TypeScript/Rust behavior differs')
process.stdout.write(JSON.stringify({ unit: ts.unit, cases: ts.cases.map(c => ({ id: c.id, reason: c.result.reason, requests: c.requests })) }) + '\n')
