import { readFile } from 'node:fs/promises'
import { join } from 'node:path'
import { createReplayAdapter } from '../src/rein/adapters'
import { runAgentLoop } from '../src/rein/loop'

const root = join(process.cwd(), '../fixtures/workspaces/prerequisites')
const fixture = JSON.parse(await readFile(join(process.cwd(), '../fixtures/cases/prerequisites.json'), 'utf8'))
const single = process.argv[2] === 'single'
const first = single ? { content: [{ type: 'tool_use', id: 'read-only', name: 'read_file', input: { path: 'README.md' } }] } : fixture.anthropic_response
const replay = createReplayAdapter([
  JSON.stringify(first),
  JSON.stringify(fixture.anthropic_followup_response ?? { content: [{ type: 'text', text: '已完成读取与搜索。' }] }),
])
const result = await runAgentLoop(replay, { root }, single ? '请读取 README.md。' : '请检查 workspace，并总结结果。')
console.log(JSON.stringify({ state: result.state, reason: result.reason, answer: result.answer, events: result.events }, null, 2))
