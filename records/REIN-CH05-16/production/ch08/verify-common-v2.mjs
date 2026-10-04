import { readFile, stat, writeFile } from 'node:fs/promises'
import { createHash } from 'node:crypto'
import { join } from 'node:path'

const startedAt = new Date().toISOString()
const argv = process.argv
const cwd = process.cwd()
const sourceRoot = '/private/tmp/rein-ch08-common-input-v2/source'
const outputRoot = '/private/tmp/rein-ch08-common-input-v2'
const recordRoot = join(cwd, 'records/REIN-CH05-16/production/ch08/common-preparation-v2')
const accepted = JSON.parse(await readFile(join(cwd, 'records/REIN-CH05-16/snapshots/ch07-accepted/manifest.json'), 'utf8'))
const fixtureFiles = ['fixtures/ch08-context/docs/01-runtime.md', 'fixtures/ch08-context/docs/02-cache.md', 'fixtures/ch08-context/docs/03-approval.md', 'fixtures/ch08-context/docs/04-index.md', 'fixtures/ch08-context/docs/05-failure.md', 'fixtures/ch08-context/docs/06-release.md', 'fixtures/ch08-context/index.json', 'fixtures/ch08-context/tasks.json', 'fixtures/ch08-context/README.md', 'fixtures/ch08-context/manifest.json']
const entries = []
for (const item of accepted.files) {
  const content = await readFile(join(sourceRoot, item.path))
  const sha256 = createHash('sha256').update(content).digest('hex')
  if (sha256 !== item.sha256) throw new Error(`source mismatch: ${item.path}`)
  entries.push({ path: item.path, sha256, bytes: content.byteLength })
}
for (const path of fixtureFiles) {
  const content = await readFile(join(outputRoot, path))
  entries.push({ path, sha256: createHash('sha256').update(content).digest('hex'), bytes: content.byteLength })
}
if (entries.length !== 148) throw new Error(`expected 148 source files, got ${entries.length}`)
const endedAt = new Date().toISOString()
const result = { argv, cwd, startedAt, endedAt, exit: 0, stdout: `verified source manifest entries: ${entries.length}; ch07 mismatches: 0\n`, stderr: '', sourceRoot, sourceManifest: 'records/REIN-CH05-16/snapshots/ch07-accepted/manifest.json', files: entries }
await writeFile(join(recordRoot, 'source-tree-manifest.json'), `${JSON.stringify({ chapter: 'rein-ch08', unit: 'estimated-bytes-v1', files: entries }, null, 2)}\n`)
await writeFile(join(recordRoot, 'integration-verification.json'), `${JSON.stringify(result, null, 2)}\n`)
console.log(result.stdout.trim())
