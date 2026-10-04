import { mkdtemp, writeFile, rm } from 'node:fs/promises'
import { join } from 'node:path'
import { tmpdir } from 'node:os'
import { replayAdapter, runAgentLoop } from '/private/tmp/rein-ch05-review-20260914/reviewer-1/package-17/ts/src/rein/loop.ts'
import type { ModelTurn } from '/private/tmp/rein-ch05-review-20260914/reviewer-1/package-17/ts/src/rein/contracts.ts'

const turn = (content: string, toolCalls: ModelTurn['toolCalls'] = []): ModelTurn => ({ message: { role: 'assistant', content, toolCalls }, toolCalls })
const root = await mkdtemp(join(tmpdir(), 'rein-ch05-demo-'))
try {
  await writeFile(join(root, 'guide.md'), '# Loop\n工具结果：AZURE apples\n')
  const result = await runAgentLoop(replayAdapter([
    turn('', [{ id: 'search-1', name: 'search_files', arguments: { needle: '工具结果' } }]),
    turn('', [{ id: 'read-1', name: 'read_file', arguments: { path: 'guide.md' } }]),
    turn('读取完成：工具结果会进入下一轮。'),
  ]), [{ role: 'user', content: '搜索并读取 guide.md' }], { root })
  console.log(JSON.stringify({ answer: result.answer, reason: result.reason, events: result.events }, null, 2))
} finally { await rm(root, { recursive: true, force: true }) }
