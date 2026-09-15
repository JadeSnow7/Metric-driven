import { spawnSync } from 'node:child_process'
import { readFileSync } from 'node:fs'
const fixture = JSON.parse(readFileSync(new URL('../fixtures/cases/ch06-control.json', import.meta.url)))
function run(command, args, env = {}) {
  const result = spawnSync(command, args, { cwd: new URL('..', import.meta.url), encoding: 'utf8', env: { ...process.env, ...env } })
  if (result.status !== 0) throw new Error(`${command} ${args.join(' ')} exited ${result.status}: ${result.stderr}`)
  const start = result.stdout.indexOf('{')
  return JSON.parse(result.stdout.slice(start))
}
for (const mode of fixture.modes) {
  const ts = run('npm', ['run', 'ch06:offline', '--workspace', 'ts', '--', mode])
  const rust = run('cargo', ['run', '--quiet', '--manifest-path', 'rust/Cargo.toml', '--example', 'ch06_loop', '--', mode], { CARGO_TARGET_DIR: '/private/tmp/rein-candidate03-build' })
  if (ts.result.reason !== fixture.expectedReasons[mode] || rust.result.reason !== fixture.expectedReasons[mode]) throw new Error(`${mode}: ${ts.result.reason}/${rust.result.reason}`)
  console.log(JSON.stringify({ mode, typescript: ts.result.reason, rust: rust.result.reason }))
}
