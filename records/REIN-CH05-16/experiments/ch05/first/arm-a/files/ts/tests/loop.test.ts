import { describe, expect, it } from 'vitest'
import { mkdtemp, writeFile, rm } from 'node:fs/promises'
import { join } from 'node:path'
import { tmpdir } from 'node:os'
import { replayAdapter, runAgentLoop } from '../src/rein/loop'
import type { Message, ModelTurn } from '../src/rein/contracts'

const assistant = (content: string, toolCalls: ModelTurn['toolCalls'] = []): ModelTurn => ({ message: { role: 'assistant', content, toolCalls }, toolCalls })

describe('core agent loop', () => {
  it('returns a normal final answer', async () => {
    const root = await mkdtemp(join(tmpdir(), 'rein-loop-'))
    try { const result = await runAgentLoop(replayAdapter([assistant('完成')]), [{ role: 'user', content: 'hi' }], { root }); expect(result).toMatchObject({ ok: true, answer: '完成', reason: 'completed' }); expect(result.events.at(-1)).toEqual({ type: 'stopped', reason: 'completed' }) } finally { await rm(root, { recursive: true, force: true }) }
  })

  it('searches and then reads real file contents before answering', async () => {
    const root = await mkdtemp(join(tmpdir(), 'rein-loop-'))
    try {
      await writeFile(join(root, 'notes.txt'), '真实内容：蓝色书签')
      const result = await runAgentLoop(replayAdapter([
        assistant('', [{ id: 's1', name: 'search_files', arguments: { needle: '蓝色' } }]),
        assistant('', [{ id: 'r1', name: 'read_file', arguments: { path: 'notes.txt' } }]),
        assistant('蓝色书签'),
      ]), [{ role: 'user', content: '找蓝色并总结' }], { root })
      expect(result.ok).toBe(true); expect(result.answer).toBe('蓝色书签')
      expect(result.messages.some(message => message.content.includes('notes.txt'))).toBe(true)
      expect(result.messages.some(message => message.content.includes('真实内容'))).toBe(true)
    } finally { await rm(root, { recursive: true, force: true }) }
  })

  it('keeps multiple call order and ids, and feeds failures back', async () => {
    const root = await mkdtemp(join(tmpdir(), 'rein-loop-'))
    try {
      await writeFile(join(root, 'a.txt'), 'a')
      const result = await runAgentLoop(replayAdapter([
        assistant('', [{ id: 'a', name: 'read_file', arguments: { path: 'a.txt' } }, { id: 'b', name: 'no_such_tool', arguments: {} }]),
        assistant('已说明失败'),
      ]), [{ role: 'user', content: '读文件' }], { root })
      expect(result.ok).toBe(true)
      expect(result.events.filter(event => event.type === 'tool').map(event => event.toolCallId)).toEqual(['a', 'b'])
      expect(result.messages.filter(message => message.role === 'tool').map(message => message.toolCallId)).toEqual(['a', 'b'])
      expect(result.messages.at(-1)?.content).toBe('已说明失败')
    } finally { await rm(root, { recursive: true, force: true }) }
  })

  it('records model errors, empty answers, and max-round protection', async () => {
    const root = await mkdtemp(join(tmpdir(), 'rein-loop-'))
    try {
      await expect(runAgentLoop(replayAdapter([new Error('down')]), [], { root })).resolves.toMatchObject({ ok: false, reason: 'model_error' })
      await expect(runAgentLoop(replayAdapter([assistant('')]), [], { root })).resolves.toMatchObject({ ok: false, reason: 'empty_final' })
      await expect(runAgentLoop(replayAdapter([assistant('', [{ id: 'x', name: 'nope', arguments: {} }])]), [], { root }, { maxRounds: 1 })).resolves.toMatchObject({ ok: false, reason: 'max_rounds' })
    } finally { await rm(root, { recursive: true, force: true }) }
  })
})
