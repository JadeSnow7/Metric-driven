import { describe, expect, it } from 'vitest'
import { runAgentLoop, estimateMessages } from '../src/rein/loop'
import type { ChatAdapter } from '../src/rein/contracts'

const answer = (content: string) => ({ message: { role: 'assistant' as const, content }, toolCalls: [] })

describe('ch07 context management', () => {
  it('keeps rules, goal, and the complete latest multi-tool group while removing old groups', async () => {
    const history = [
      { role: 'user' as const, content: 'old' },
      { role: 'assistant' as const, content: '', toolCalls: [{ id: 'a', name: 'read_file', arguments: { path: 'a' } }, { id: 'b', name: 'read_file', arguments: { path: 'b' } }] },
      { role: 'tool' as const, toolCallId: 'a', content: 'A' }, { role: 'tool' as const, toolCallId: 'b', content: 'B' },
    ]
    let received: any[] = []
    const adapter: ChatAdapter = { async complete(messages) { received = structuredClone(messages) as any; return answer('ok') } }
    const result = await runAgentLoop(adapter, { root: process.cwd() }, 'goal', { context: { rules: ['rule'], history, budget: 139 } })
    expect(result.reason).toBe('final_answer')
    expect(received.filter(m => m.role === 'system').map(m => m.content)).toEqual(['rule'])
    expect(received.filter(m => m.role === 'tool').map(m => m.toolCallId)).toEqual(['a', 'b'])
    expect(result.messages).toHaveLength(history.length + 2)
    expect(result.events.find(e => e.type === 'context_prepared')).toMatchObject({ removedGroups: ['g0'], requiredGroups: ['g1', 'g4'] })
  })

  it('does not dispatch when required content exceeds budget', async () => {
    let calls = 0
    const adapter: ChatAdapter = { async complete() { calls++; return answer('bad') } }
    const result = await runAgentLoop(adapter, { root: process.cwd() }, 'goal', { context: { rules: ['rule'], history: [], budget: 1 } })
    expect(result).toMatchObject({ reason: 'context_budget_exhausted', state: 'failed' })
    expect(calls).toBe(0)
  })

  it('rejects malformed history and protects audit history from adapter mutation', async () => {
    const malformed = await runAgentLoop({ async complete() { return answer('never') } }, { root: process.cwd() }, 'goal', { context: { rules: [], history: [{ role: 'tool', toolCallId: 'orphan', content: 'x' }], budget: 100 } })
    expect(malformed.reason).toBe('invalid_context_history')
    const history = [{ role: 'user' as const, content: 'source' }]
    const result = await runAgentLoop({ async complete(messages) { (messages as any).push({ role: 'system', content: 'tampered' }); return answer('ok') } }, { root: process.cwd() }, 'goal', { context: { rules: [], history, budget: 100 } })
    expect(result.messages.map(message => message.content)).toEqual(['source', 'goal', 'ok'])
  })

  it('counts UTF-8 bytes deterministically', () => {
    expect(estimateMessages([{ role: 'user', content: '你好 🌏' }])).toBe(8 + 4 + 11)
  })
})
