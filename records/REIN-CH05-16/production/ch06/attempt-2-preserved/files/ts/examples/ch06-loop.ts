import { mkdtemp, writeFile, rm } from 'node:fs/promises'
import { join } from 'node:path'
import { tmpdir } from 'node:os'
import { runAgentLoop } from '../src/rein/loop'
import type { ChatAdapter, ModelTurn, ToolCall } from '../src/rein/contracts'

const mode = process.argv[2] ?? 'normal'
const root = await mkdtemp(join(tmpdir(), 'rein-ch06-'))
await writeFile(join(root, 'README.md'), 'marker: ch06\n')
const call = (id: string, name: string, arguments_: Record<string, unknown>): ToolCall => ({ id, name, arguments: arguments_ })
const turn = (content: string, toolCalls: ToolCall[] = []): ModelTurn => ({ message: { role: 'assistant', content, toolCalls }, toolCalls })
let requests = 0
const adapter: ChatAdapter = { async complete(messages) {
  requests++
  const tools = messages.filter(message => message.role === 'tool')
  if (mode === 'duplicate') return turn('', [call(`duplicate-${requests}`, 'read_file', { path: 'README.md' })])
  if (mode === 'budget') return turn('', [call('one', 'read_file', { path: 'README.md' }), call('two', 'read_file', { path: 'README.md' })])
  if (mode === 'timeout' || mode === 'cancel') { await new Promise(resolve => setTimeout(resolve, 40)); return turn('late') }
  if (tools.length === 0) return turn('', [call('read', 'read_file', { path: 'README.md' })])
  return turn(`完成：${tools.at(-1)?.content.trim()}`)
} }
const controller = new AbortController()
if (mode === 'cancel') setTimeout(() => controller.abort(), 5)
const result = await runAgentLoop(adapter, { root }, '读取 README.md', {
  maxTurns: mode === 'zero' ? 0 : 3,
  maxToolCalls: mode === 'budget' ? 1 : undefined,
  duplicateLimit: mode === 'duplicate' ? 1 : undefined,
  timeoutMs: mode === 'timeout' ? 5 : undefined,
  signal: mode === 'cancel' ? controller.signal : undefined,
})
console.log(JSON.stringify({ mode, requests, result }, null, 2))
await rm(root, { recursive: true, force: true })
