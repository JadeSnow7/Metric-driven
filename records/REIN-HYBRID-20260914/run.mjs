import { cp, mkdir, readdir, readFile, stat, writeFile } from 'node:fs/promises'
import { createHash } from 'node:crypto'
import { join, relative, dirname } from 'node:path'
import { execFileSync } from 'node:child_process'

const startedAt = new Date().toISOString()
const argv = process.argv
const cwd = process.cwd()
const original = '/Users/huaodong/workspace/Agent-Learning'
const candidate = '/private/tmp/rein-production-candidate-03'
const output = '/private/tmp/rein-hybrid-work-20260914'
const record = '/Users/huaodong/Documents/evidence-driven-development/records/REIN-HYBRID-20260914/bootstrap'
const baselinePath = '/Users/huaodong/Documents/evidence-driven-development/records/REIN-CH05-16/evidence/inputs/rein-restored/manifest.json'
for (const p of [output, record]) { try { await stat(p); throw new Error(`refusing existing output: ${p}`) } catch (e) { if (e.code !== 'ENOENT') throw e } }
const excluded = (p) => p === '.git' || p === 'node_modules' || p === 'target' || p === 'build' || p === 'dist' || (p.startsWith('.env') && p !== '.env.example')
const hash = b => createHash('sha256').update(b).digest('hex')
async function walk(root, dir = '') { const out = new Map(); for (const name of await readdir(join(root, dir))) { if (excluded(name)) continue; const rel = join(dir, name); const info = await stat(join(root, rel)); if (info.isDirectory()) for (const [p, v] of await walk(root, rel)) out.set(p, v); else { const b = await readFile(join(root, rel)); out.set(rel, { sha256: hash(b), bytes: b.byteLength, mode: info.mode & 0o777 }); } } return out }
const baseline = JSON.parse(await readFile(baselinePath, 'utf8')); const baselineMap = new Map(baseline.files.map(x => [x.path, x]))
const originalMap = await walk(original); const candidateMap = await walk(candidate)
const originalDiff = execFileSync('git', ['-C', original, 'diff', '--binary'], { encoding: 'buffer' });
const originalDiffStat = execFileSync('git', ['-C', original, 'diff', '--stat'], { encoding: 'utf8' });
const originalStatus = execFileSync('git', ['-C', original, 'status', '--short', '--untracked-files=all'], { encoding: 'utf8' });
await mkdir(output, { recursive: true }); await mkdir(record, { recursive: true })
await writeFile(join(record, 'original-git-diff.patch'), originalDiff); await writeFile(join(record, 'original-git-diff.stat'), originalDiffStat); await writeFile(join(record, 'original-status.txt'), originalStatus)
const originalHead = execFileSync('git', ['-C', original, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim()
const originalMetadata = Object.fromEntries([...originalMap].map(([p, v]) => [p, v])); await writeFile(join(record, 'original-file-manifest.json'), JSON.stringify({ root: original, head: originalHead, files: originalMetadata }, null, 2) + '\n')
await cp(original, output, { recursive: true, errorOnExist: true, filter: source => !excluded(source.split('/').pop() ?? '') })
const conflicts = []
for (const [path, candidateFile] of candidateMap) {
  const base = baselineMap.get(path); const current = originalMap.get(path)
  const candidateEqualsBase = base && candidateFile.sha256 === base.sha256
  const currentEqualsBase = base && current && current.sha256 === base.sha256
  const candidateEqualsCurrent = current && candidateFile.sha256 === current.sha256
  if (candidateEqualsBase || candidateEqualsCurrent) continue
  if (!current || currentEqualsBase) { const from = join(candidate, path); const to = join(output, path); await mkdir(dirname(to), { recursive: true }); await cp(from, to); continue }
  conflicts.push({ path, original: current, candidate: candidateFile, baseline: base ?? null })
  const side = join(record, 'conflicts', path); await mkdir(dirname(side), { recursive: true }); await cp(join(candidate, path), `${side}.candidate`); await cp(join(original, path), `${side}.original`)
}
const mergedMap = await walk(output); const sourceManifest = { root: output, sourceOriginal: original, sourceCandidate: candidate, files: Object.fromEntries([...mergedMap].map(([p, v]) => [p, v])) }
await writeFile(join(record, 'hybrid-tree-manifest.json'), JSON.stringify(sourceManifest, null, 2) + '\n')
const authorPaths = ['docs/chapters/01.md', 'docs/chapters/02.md', 'docs/chapters/03.md', 'docs/chapters/04.md', 'reports/ch01-author-style.md', 'docs/.vitepress/config.mts', 'docs/.vitepress/theme/SourceVersionSwitch.vue', 'docs/.vitepress/theme/sourceVersionState.ts']
const author = Object.fromEntries(authorPaths.filter(p => originalMap.has(p)).map(p => [p, originalMap.get(p)])); await writeFile(join(record, 'author-retained.json'), JSON.stringify(author, null, 2) + '\n')
const before01 = baselineMap.get('docs/chapters/01.md')?.sha256 ?? null; const after01 = mergedMap.get('docs/chapters/01.md')?.sha256 ?? null
const endedAt = new Date().toISOString(); const report = { argv, cwd, startedAt, endedAt, exit: 0, stdout: `merged ${candidateMap.size} candidate paths; conflicts: ${conflicts.length}\n`, stderr: '', originalHead, baselinePath, output, record, candidatePaths: candidateMap.size, conflicts, authorPaths, chapter01: { beforeHash: before01, afterHash: after01, originalCurrentHash: originalMap.get('docs/chapters/01.md')?.sha256 ?? null }, sourceManifestPath: join(record, 'hybrid-tree-manifest.json') }
await writeFile(join(record, 'integration-report.json'), JSON.stringify(report, null, 2) + '\n')
console.log(report.stdout.trim())
