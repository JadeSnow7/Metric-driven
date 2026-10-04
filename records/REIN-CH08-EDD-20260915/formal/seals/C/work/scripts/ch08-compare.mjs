import { spawnSync } from 'node:child_process'
import { resolve } from 'node:path'
const root = resolve(new URL('..', import.meta.url).pathname)
const args = process.argv.slice(2)
const data = args.includes('--data-root') ? args[args.indexOf('--data-root') + 1] : resolve(root, 'fixtures/ch08-context')
const budget = args.includes('--budget') ? args[args.indexOf('--budget') + 1] : null
const strategy = args.includes('--strategy') ? args[args.indexOf('--strategy') + 1] : null
const rustArgs = [ 'run', '--quiet', '--locked', '--manifest-path', resolve(root, 'rust/Cargo.toml'), '--example', 'ch08_context', '--', data ]
if (budget !== null) rustArgs.push(`--budget=${budget}`)
if (strategy !== null) rustArgs.push(`--strategy=${strategy}`)
const result = spawnSync('cargo', rustArgs, { cwd: root, encoding: 'utf8' })
if (result.status !== 0) { process.stderr.write(result.stderr); process.exit(result.status ?? 1) }
process.stdout.write(result.stdout)
