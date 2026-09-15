import { readFile, writeFile, lstat, mkdir, copyFile, chmod } from 'node:fs/promises'
import { createHash } from 'node:crypto'
import { execFileSync } from 'node:child_process'
import { resolve, dirname, relative, sep } from 'node:path'

const planPath = new URL('./plan.json', import.meta.url)
const plan = JSON.parse(await readFile(planPath, 'utf8'))
const manifest = JSON.parse(await readFile(new URL('../bootstrap/original-file-manifest.json', import.meta.url), 'utf8'))
const original = resolve('/Users/huaodong/workspace/Agent-Learning')
const source = resolve(plan.source)
const digest = async path => createHash('sha256').update(await readFile(path)).digest('hex')
const mode = async path => (await lstat(path)).mode & 0o777
const exists = async path => { try { await lstat(path); return true } catch (error) { if (error.code === 'ENOENT') return false; throw error } }
const inside = (root, path) => {
  const rel = relative(root, path)
  return rel === '' || (rel !== '..' && !rel.startsWith(`..${sep}`) && !rel.startsWith('/') && !rel.startsWith('\\'))
}
const pathIsSafe = path => path && !path.startsWith('/') && !path.startsWith('\\') && !path.split('/').includes('..') && !path.split('\\').includes('..')
const sourceRoot = source
const destinationRoot = original
const conflictPath = new URL('./conflicts.json', import.meta.url)
const actualHead = execFileSync('git', ['-C', original, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim()
if (actualHead !== manifest.head) throw new Error(`original HEAD drift: ${actualHead} != ${manifest.head}`)
for (const [path, expected] of Object.entries(manifest.files)) {
  const target = resolve(original, path)
  let actual
  try { actual = { sha256: await digest(target), bytes: (await lstat(target)).size, mode: await mode(target) } }
  catch { throw new Error(`original file missing: ${path}`) }
  if (actual.sha256 !== expected.sha256 || actual.bytes !== expected.bytes || actual.mode !== expected.mode) throw new Error(`original file drift: ${path}`)
}
const baselinePaths = new Set(Object.keys(manifest.files))
const conflicts = []
const preflight = []
for (const entry of plan.entries) {
  if (!pathIsSafe(entry.path)) throw new Error(`unsafe relative path: ${entry.path}`)
  const from = resolve(sourceRoot, entry.path)
  const to = resolve(destinationRoot, entry.path)
  if (!inside(sourceRoot, from) || !inside(destinationRoot, to)) throw new Error(`path escapes transfer roots: ${entry.path}`)
  const sourceInfo = await lstat(from).catch(() => null)
  if (!sourceInfo?.isFile() || sourceInfo.isSymbolicLink()) throw new Error(`source is not a regular file: ${entry.path}`)
  const sourceActual = { sha256: await digest(from), bytes: sourceInfo.size, mode: sourceInfo.mode & 0o777 }
  if (sourceActual.sha256 !== entry.sha256 || sourceActual.bytes !== entry.bytes || sourceActual.mode !== entry.mode) {
    throw new Error(`source changed after plan: ${entry.path}`)
  }
  let parent = dirname(to)
  while (inside(destinationRoot, parent) && parent !== destinationRoot) {
    const parentInfo = await lstat(parent).catch(() => null)
    if (parentInfo?.isSymbolicLink()) throw new Error(`destination parent is symlink: ${entry.path}`)
    parent = dirname(parent)
  }
  if (!inside(destinationRoot, parent)) throw new Error(`destination parent escapes root: ${entry.path}`)
  const targetExists = await exists(to)
  if (targetExists && !baselinePaths.has(entry.path)) {
    const targetInfo = await lstat(to)
    conflicts.push({
      path: entry.path,
      reason: 'new destination already exists',
      source: { path: from, sha256: sourceActual.sha256, bytes: sourceActual.bytes, mode: sourceActual.mode },
      destination: { path: to, sha256: targetInfo.isFile() ? await digest(to) : null, bytes: targetInfo.size, mode: targetInfo.mode & 0o777, type: targetInfo.isDirectory() ? 'directory' : targetInfo.isSymbolicLink() ? 'symlink' : 'other' }
    })
  }
  preflight.push({ entry, from, to })
}
await writeFile(conflictPath, `${JSON.stringify({ generatedAt: new Date().toISOString(), conflicts }, null, 2)}\n`)
const apply = process.argv.includes('--apply')
console.log(JSON.stringify({ checkedHead: actualHead, checkedFiles: Object.keys(manifest.files).length, preflightEntries: preflight.length, conflicts: conflicts.length, apply }, null, 2))
if (conflicts.length) throw new Error(`backwrite conflicts recorded in ${conflictPath.pathname}`)
if (!apply) process.exit(0)
for (const { entry, from, to } of preflight) {
  await mkdir(dirname(to), { recursive: true })
  await copyFile(from, to)
  await chmod(to, entry.mode)
}
