import { describe, expect, it } from 'vitest'
import { runAgentLoop } from '../src/rein/loop'
import type { ChatAdapter, ModelTurn } from '../src/rein/contracts'
import { mkdtemp, writeFile, rm } from 'node:fs/promises'
import { join } from 'node:path'
import { tmpdir } from 'node:os'

const turn = (content: string, toolCalls: ModelTurn['toolCalls'] = []): ModelTurn => ({ message: { role: 'assistant', content, toolCalls }, toolCalls })
const tool = (id: string, name: string, args: Record<string, unknown>) => ({ id, name, arguments: args })

describe('ch05 agent loop', () => {
  it('searches and reads real content, then sends both results to the next model turn', async () => {
    const root = await mkdtemp(join(tmpdir(), 'rein-loop-'))
    try {
      await writeFile(join(root, 'a.txt'), 'alpha secret')
      await writeFile(join(root, 'b.txt'), 'beta')
      const received: any[][] = []
      const adapter: ChatAdapter = { async complete(messages) { received.push(structuredClone(messages) as any); return received.length === 1 ? turn('', [tool('s', 'search_files', { needle: 'secret' }), tool('r', 'read_file', { path: 'a.txt' })]) : turn('总结：alpha secret') } }
      const result = await runAgentLoop(adapter, { root }, 'inspect')
      expect(result.answer).toBe('总结：alpha secret')
      expect(received[1]?.filter(m => m.role === 'tool').map(m => m.content)).toEqual(['a.txt', 'alpha secret'])
      expect(result.events.filter(e => e.type === 'tool_result').map(e => e.toolCallId)).toEqual(['s', 'r'])
    } finally { await rm(root, { recursive: true, force: true }) }
  })

  it('returns structured failures and protects the turn budget', async () => {
    const root = await mkdtemp(join(tmpdir(), 'rein-loop-'))
    try {
      const adapter: ChatAdapter = { async complete() { return turn('', [tool('bad', 'unknown', {})]) } }
      const result = await runAgentLoop(adapter, { root }, 'inspect', { maxTurns: 2 })
      expect(result.reason).toBe('max_turns')
      expect(result.events.some(e => e.type === 'tool_result' && !e.result.ok && e.result.error?.code === 'unknown_tool')).toBe(true)
    } finally { await rm(root, { recursive: true, force: true }) }
  })

  it('does not invent an answer for model errors or empty final messages', async () => {
    const root = await mkdtemp(join(tmpdir(), 'rein-loop-'))
    try {
      const failed = await runAgentLoop({ async complete() { throw new Error('offline failure') } }, { root }, 'x')
      expect(failed).toMatchObject({ state: 'failed', reason: 'model_error', error: 'offline failure' })
      const empty = await runAgentLoop({ async complete() { return turn('   ') } }, { root }, 'x')
      expect(empty).toMatchObject({ state: 'failed', reason: 'empty_final' })
    } finally { await rm(root, { recursive: true, force: true }) }
  })
})
