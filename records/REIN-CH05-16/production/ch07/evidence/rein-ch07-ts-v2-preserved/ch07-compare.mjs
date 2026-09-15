import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { spawnSync } from 'node:child_process'
import { resolve } from 'node:path'
import { isDeepStrictEqual } from 'node:util'
const root = resolve(fileURLToPath(new URL('..', import.meta.url)))
const fixture = resolve(root, 'fixtures/cases/ch07-context.json')
const run = (command, args, cwd) => { const result = spawnSync(command, args, { cwd, encoding: 'utf8' }); if (result.error) throw result.error; if (result.status !== 0) throw new Error(`${command} failed: ${result.stderr}`); return JSON.parse(result.stdout) }
const ts = run('npm', ['run', '--silent', 'ch07:context', '--', fixture], root)
const rust = run('cargo', ['run', '--quiet', '--manifest-path', resolve(root, 'rust/Cargo.toml'), '--example', 'ch07_context', '--', fixture], root)
const normalize = value => {
  if (Array.isArray(value)) return value.map(normalize)
  if (!value || typeof value !== 'object') return value
  const out = {}
  for (const [key, child] of Object.entries(value)) {
    if (key === 'error' && child && typeof child === 'object') out[key] = { code: child.code ?? null }
    else if (key === 'error' && typeof child === 'string') out[key] = null
    else out[key] = normalize(child)
  }
  return out
}
const fixtureCases = JSON.parse(readFileSync(fixture, 'utf8')).cases
for (const implementation of [ts, rust]) {
  if (implementation.unit !== 'estimated-bytes-v1' || implementation.cases.length !== fixtureCases.length) throw new Error('invalid ch07 output envelope')
  for (const actual of implementation.cases) {
    const expected = fixtureCases.find(item => item.id === actual.id)
    if (!expected) throw new Error(`unknown case ${actual.id}`)
    if (actual.result.reason !== expected.expected.reason || actual.requests !== expected.expected.requests) throw new Error(`${actual.id} does not satisfy fixture expectation`)
    const requested = actual.result.events.filter(event => event.type === 'model_requested')
    if (requested.length !== actual.requests || requested.length !== actual.sentMessages.length) throw new Error(`${actual.id} request/event mismatch`)
    for (let i = 0; i < requested.length; i++) if (!isDeepStrictEqual(requested[i].messages, actual.sentMessages[i])) throw new Error(`${actual.id} sent message audit mismatch`)
  }
}
if (!isDeepStrictEqual(normalize(ts), normalize(rust))) throw new Error('ch07 TypeScript/Rust behavior differs')
process.stdout.write(JSON.stringify({ unit: ts.unit, cases: ts.cases.map(c => ({ id: c.id, reason: c.result.reason, requests: c.requests })) }) + '\n')
