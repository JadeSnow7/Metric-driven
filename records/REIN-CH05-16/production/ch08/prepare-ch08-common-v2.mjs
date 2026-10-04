import { cp, mkdir, readFile, readdir, stat, writeFile } from 'node:fs/promises'
import { createHash } from 'node:crypto'
import { resolve, join, relative } from 'node:path'
import { register } from 'node:module'
register('./ts-resolve-loader.mjs', { parentURL: import.meta.url })

const argv = process.argv.slice(2)
const startedAt = new Date().toISOString()
const cwd = process.cwd()
const sourceSnapshot = '/private/tmp/rein-ch07-main-snapshot-review/tar-recovered/rein-ch07'
const { estimateMessages } = await import(`${sourceSnapshot}/ts/src/rein/loop.ts`)
const outputRoot = '/private/tmp/rein-ch08-common-input-v2'
const recordRoot = resolve('records/REIN-CH05-16/production/ch08/common-preparation-v2')
const fixtureRoot = join(outputRoot, 'fixtures/ch08-context')
const sourceManifest = 'records/REIN-CH05-16/snapshots/ch07-accepted/manifest.json'
const budget = 2400

for (const path of [outputRoot, recordRoot]) {
  try { await stat(path); throw new Error(`refusing to overwrite existing output: ${path}`) } catch (error) {
    if (error?.code !== 'ENOENT') throw error
  }
}

function bytes(value) { return Buffer.byteLength(value, 'utf8') }
function sha256(value) { return createHash('sha256').update(value).digest('hex') }
function makeDoc(title, field, value, background) {
  let text = `# ${title}\n\n${field}：${value}\n\n${background}\n`
  const filler = '这段背景用于说明资料的组织方式与阅读边界，帮助读者在连续阅读时保持上下文，并且让示例拥有稳定的篇幅。'
  while (bytes(text) < 700) text += `${filler}\n`
  if (bytes(text) > 850) throw new Error(`${title} exceeds document size: ${bytes(text)}`)
  return text
}

const documents = [
  { id: '01-runtime', title: '运行配置', path: 'docs/01-runtime.md', keywords: ['运行', '传输', '协议', '文档检索服务'], text: makeDoc('运行配置', '传输方式', 'stdio\n协议版本：2025-06-18', '本页描述一个小型服务在启动阶段需要知道的背景信息。配置内容按主题排列，便于维护者从索引进入具体说明，并在变更时留下清晰的阅读路径。') },
  { id: '02-cache', title: '缓存配置', path: 'docs/02-cache.md', keywords: ['缓存', '目录', '有效期'], text: makeDoc('缓存配置', '缓存目录', '.rein/cache\n缓存有效期：600秒', '本页记录运行过程中一类辅助数据的保存约定。背景说明关注文件组织、清理时机和维护习惯，读者可以据此理解资料之间的分工以及查阅顺序。') },
  { id: '03-approval', title: '批准规则', path: 'docs/03-approval.md', keywords: ['批准', '基线', '文件', '审查'], text: makeDoc('批准规则', '基线变化后的批准状态', '失效', '本页说明变更审查所处的背景。内容强调记录之间的关联和复核职责，使维护者能够沿着资料中的线索理解一次修改为何需要重新确认。') },
  { id: '04-index', title: '文档索引', path: 'docs/04-index.md', keywords: ['索引', '导航', '入口'], text: makeDoc('文档索引', '索引入口', 'docs/index.md', '本页介绍资料导航的组织背景。索引把分散的说明聚合成可追踪的入口，读者可以先确定主题，再进入对应页面完成查阅。') },
  { id: '05-failure', title: '失败处理', path: 'docs/05-failure.md', keywords: ['失败', '批准', '失效', '处理', '基线'], text: makeDoc('失败处理', '旧批准失效后的处理动作', '重新生成补丁并重新审查', '本页描述出现异常结果时的处置背景。叙述围绕恢复顺序和复核责任展开，帮助维护者把一次失败看作可追踪的工作过程。') },
  { id: '06-release', title: '发布操作', path: 'docs/06-release.md', keywords: ['发布', '检查', '命令'], text: makeDoc('发布操作', '发布前检查命令', 'npm run verify', '本页说明发布阶段的工作背景。检查步骤被放在发布动作之前，便于维护者在交付前形成一致的确认节奏，并保留可复查的操作记录。') },
]
for (const document of documents) {
  const size = bytes(document.text)
  if (size < 700 || size > 850) throw new Error(`${document.id} must be 700-850 UTF8 bytes, got ${size}`)
}

const tasks = [
  { id: 'runtime', question: '运行文档检索服务使用什么传输方式和协议版本？', requiredFields: ['传输方式', '协议版本'], expectedFacts: { '传输方式': 'stdio', '协议版本': '2025-06-18' }, relevantSources: ['01-runtime'] },
  { id: 'release', question: '发布前应该运行哪条检查命令？', requiredFields: ['发布前检查命令'], expectedFacts: { '发布前检查命令': 'npm run verify' }, relevantSources: ['06-release'] },
  { id: 'approval', question: '文件基线变化后，批准状态是什么，接下来如何处理？', requiredFields: ['基线变化后的批准状态', '旧批准失效后的处理动作'], expectedFacts: { '基线变化后的批准状态': '失效', '旧批准失效后的处理动作': '重新生成补丁并重新审查' }, relevantSources: ['03-approval', '05-failure'] },
  { id: 'unknown', question: '生产环境每秒可以处理多少请求？', requiredFields: [], expectedFacts: {}, relevantSources: [], requiresInsufficientEvidence: true },
]

await mkdir(outputRoot, { recursive: true })
await mkdir(recordRoot, { recursive: true })
await cp(sourceSnapshot, join(outputRoot, 'source'), { recursive: true, errorOnExist: true })
await mkdir(join(outputRoot, 'source/fixtures/ch08-context/docs'), { recursive: true })
await mkdir(join(fixtureRoot, 'docs'), { recursive: true })
for (const document of documents) {
  await writeFile(join(fixtureRoot, document.path), document.text, 'utf8')
  await writeFile(join(outputRoot, 'source/fixtures/ch08-context', document.path), document.text, 'utf8')
}
const index = { unit: 'estimated-bytes-v1', documents: documents.map(({ text, ...item }, order) => ({ ...item, order: order + 1 })) }
await writeFile(join(fixtureRoot, 'index.json'), `${JSON.stringify(index, null, 2)}\n`, 'utf8')
await writeFile(join(fixtureRoot, 'tasks.json'), `${JSON.stringify({ rules: ['仅根据提供材料回答；没有依据时明确说明证据不足。'], budget: 2400, tasks }, null, 2)}\n`, 'utf8')

const proof = tasks.map(task => {
  const chosen = documents.filter(document => task.relevantSources.includes(document.id))
  const messages = [
    { role: 'system', content: '仅根据提供材料回答；没有依据时明确说明证据不足。' },
    { role: 'user', content: task.question },
    ...chosen.map(document => ({ role: 'user', content: `[来源:${document.id}]\n${document.text}` })),
  ]
  return { taskId: task.id, selectedSources: chosen.map(document => document.id), messages, estimatedUnits: estimateMessages(messages), unit: 'estimated-bytes-v1', budget, fitsBudget: estimateMessages(messages) <= budget }
})
if (proof.some(item => !item.fitsBudget)) throw new Error(`shared material does not fit budget: ${JSON.stringify(proof)}`)

const files = {}
async function collect(dir) {
  for (const name of await readdir(dir)) {
    const path = join(dir, name)
    const info = await stat(path)
    if (info.isDirectory()) await collect(path)
    else { const content = await readFile(path); files[relative(outputRoot, path)] = { bytes: content.byteLength, sha256: sha256(content) } }
  }
}
await collect(fixtureRoot)
const readme = `# 第08章实验材料\n\n本目录提供固定的六篇 Markdown 资料、文档索引和四个问题。资料使用 UTF-8 保存，索引包含稳定 id、标题、相对路径、关键词与顺序；任务文件在顶层提供统一规则和 2400 的 estimated-bytes-v1 预算。\n\nrunner 将顶层 rules、budget 与每个 task 的 question 组成策略视图，再由策略从资料根和 index 选择上下文。每条规则作为 system 消息，问题作为 user 消息，资料作为带 [来源:id] 前缀的 user 消息。tasks.json 中的 expectedFacts、requiredFields、relevantSources 只供后置评估器使用；它们不属于策略或回答器输入。\n\n没有资料依据的问题应明确说明证据不足。完整消息和估算证明位于共同准备记录，不属于资料索引。\n`
await writeFile(join(fixtureRoot, 'README.md'), readme, 'utf8')
await collect(fixtureRoot)
const manifest = { unit: 'estimated-bytes-v1', budget: 2400, files: Object.fromEntries(Object.entries(files).map(([path, value]) => [path.replace('fixtures/ch08-context/', ''), value])) }
await writeFile(join(fixtureRoot, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`, 'utf8')
for (const name of ['index.json', 'tasks.json', 'README.md', 'manifest.json']) await cp(join(fixtureRoot, name), join(outputRoot, 'source/fixtures/ch08-context', name))

const endedAt = new Date().toISOString()
const report = { argv, cwd, startedAt, endedAt, exit: 0, stdout: 'prepared common input; no model or formal execution started\n', stderr: '', sourceSnapshot, sourceManifest, outputRoot, manifestPath: join(fixtureRoot, 'manifest.json'), newFiles: { ...files, [`fixtures/ch08-context/manifest.json`]: { bytes: bytes(JSON.stringify(manifest, null, 2) + '\n'), sha256: sha256(JSON.stringify(manifest, null, 2) + '\n') }, [`fixtures/ch08-context/README.md`]: { bytes: bytes(readme), sha256: sha256(readme) } } }
await writeFile(join(recordRoot, 'preparation-report.json'), `${JSON.stringify(report, null, 2)}\n`, 'utf8')
await writeFile(join(recordRoot, 'proof.json'), `${JSON.stringify({ manifest, readme, startedAt, endedAt }, null, 2)}\n`, 'utf8')
console.log(JSON.stringify({ outputRoot, recordRoot, startedAt, endedAt, proof }, null, 2))
