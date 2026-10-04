import { spawn } from 'node:child_process'
import { mkdir, writeFile } from 'node:fs/promises'

const root = '/Users/huaodong/workspace/Agent-Learning'
const outDir = new URL('./', import.meta.url)
await mkdir(outDir, { recursive: true })
const commands = [
  ['build', 'npm', ['run', 'build'], {}],
  ['checker', 'node', ['scripts/check-book-links.mjs'], {}],
  ['typecheck', 'npm', ['run', 'typecheck'], {}],
  ['nav5', 'npm', ['test', '--workspace', 'ts'], {}],
  ['hybrid-verify', 'npm', ['run', 'hybrid:verify'], { CARGO_TARGET_DIR: '/private/tmp/rein-hybrid-target' }]
]

const run = (name, command, args, extraEnv) => new Promise(resolve => {
  const startedAt = new Date().toISOString()
  const child = spawn(command, args, { cwd: root, env: { ...process.env, ...extraEnv }, stdio: ['ignore', 'pipe', 'pipe'] })
  let stdout = ''; let stderr = ''
  child.stdout.on('data', chunk => { stdout += chunk })
  child.stderr.on('data', chunk => { stderr += chunk })
  child.on('close', (code, signal) => resolve({ name, argv: [command, ...args], cwd: root, startedAt, endedAt: new Date().toISOString(), exit: code, signal, stdout, stderr }))
  child.on('error', error => resolve({ name, argv: [command, ...args], cwd: root, startedAt, endedAt: new Date().toISOString(), exit: null, signal: null, stdout, stderr: `${stderr}${error.stack}\n` }))
})

const results = []
for (const [name, command, args, env] of commands) results.push(await run(name, command, args, env))
await writeFile(new URL('./commands.json', outDir), JSON.stringify(results, null, 2) + '\n')
console.log(JSON.stringify(results.map(({ name, exit, signal }) => ({ name, exit, signal })), null, 2))
if (results.some(result => result.exit !== 0)) process.exitCode = 1
