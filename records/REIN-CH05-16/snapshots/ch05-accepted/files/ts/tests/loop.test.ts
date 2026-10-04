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

  it('feeds unknown, bad arguments, and missing files back so the model can recover', async () => {
    const root = await mkdtemp(join(tmpdir(), 'rein-loop-recover-'))
    try {
      await writeFile(join(root, 'ok.txt'), 'recovered')
      let turnNumber = 0
      const received: any[][] = []
      const adapter: ChatAdapter = { async complete(messages) {
        turnNumber++
        received.push(structuredClone(messages) as any)
        if (turnNumber === 1) return turn('', [tool('u', 'unknown', {}), tool('a', 'read_file', { path: 3 }), tool('m', 'read_file', { path: 'missing.txt' })])
        if (turnNumber === 2) return turn('', [tool('r', 'read_file', { path: 'ok.txt' })])
        return turn('recovered')
      } }
      const result = await runAgentLoop(adapter, { root }, 'recover')
      expect(result).toMatchObject({ state: 'completed', reason: 'final_answer', answer: 'recovered' })
      expect(result.events.filter(e => e.type === 'tool_result').map(e => e.result.error?.code)).toEqual(['unknown_tool', 'arguments_invalid', 'path_invalid', undefined])
      expect(received[1]?.filter(m => m.role === 'tool').map(m => JSON.parse(m.content).error.code)).toEqual(['unknown_tool', 'arguments_invalid', 'path_invalid'])
      expect(received[2]?.filter(m => m.role === 'tool').slice(-1).map(m => m.toolCallId)).toEqual(['r'])
    } finally { await rm(root, { recursive: true, force: true }) }
  })

  it('uses the default 32-turn protection and records every request', async () => {
    const root = await mkdtemp(join(tmpdir(), 'rein-loop-max-'))
    try {
      const adapter: ChatAdapter = { async complete() { return turn('', [tool('u', 'unknown', {})]) } }
      const result = await runAgentLoop(adapter, { root }, 'max')
      expect(result.reason).toBe('max_turns')
      expect(result.events.filter(e => e.type === 'model_requested')).toHaveLength(32)
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

  it('uses the search result to choose reads in either workspace and records reconstructable events', async () => {
    const cases: Array<Array<[string, string]>> = [[['a.md', 'marker: blue'], ['b.md', 'marker: sea']], [['changed.md', 'marker: gold'], ['other.md', 'marker: wind']]]
    for (const files of cases) {
      const root = await mkdtemp(join(tmpdir(), 'rein-loop-workspace-'))
      try {
        for (const [path, content] of files) await writeFile(join(root, path), content)
        const seen: any[] = []
        const adapter: ChatAdapter = { async complete(messages) {
          seen.push(structuredClone(messages))
          const toolMessages = messages.filter(m => m.role === 'tool')
          if (!toolMessages.length) return turn('', [tool('search', 'search_files', { needle: 'marker:' })])
          if (toolMessages.length === 1) return turn('', (toolMessages[0]?.content ?? '').split('\n').filter(Boolean).map((path, i) => tool(`read-${i}`, 'read_file', { path })))
          return turn(toolMessages.slice(1).map(m => m.content).join('|'))
        } }
        const result = await runAgentLoop(adapter, { root }, 'inspect')
        expect(result.answer).toContain(files[0]?.[1])
        expect(seen[2]?.filter((m: any) => m.role === 'tool').slice(1).map((m: any) => m.content)).toEqual(files.map(f => f[1]))
        const request = result.events.find((event) => event.type === 'model_requested')
        expect(request).toMatchObject({ type: 'model_requested', tools: expect.any(Array), messages: expect.any(Array) })
      } finally { await rm(root, { recursive: true, force: true }) }
    }
  })

  it('returns a model_error when replay responses are exhausted after a tool call', async () => {
    const root = await mkdtemp(join(tmpdir(), 'rein-loop-exhausted-'))
    try {
      const result = await runAgentLoop({ async complete(messages) { if (messages.length === 1) return turn('', [tool('x', 'search_files', { needle: 'x' })]); throw new Error('replay exhausted') } }, { root }, 'inspect')
      expect(result).toMatchObject({ state: 'failed', reason: 'model_error', error: 'replay exhausted' })
      expect(result.events.some(e => e.type === 'tool_result' && e.toolCallId === 'x')).toBe(true)
    } finally { await rm(root, { recursive: true, force: true }) }
  })
})
