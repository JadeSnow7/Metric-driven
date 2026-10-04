import type { ChatAdapter, Message, ToolCall, ToolDefinition, ToolResult } from './contracts'
import { dispatchReadonly, type Workspace } from './readonly'

export type LoopEvent =
  | { readonly type: 'started'; readonly round: number }
  | { readonly type: 'model'; readonly round: number; readonly toolCallIds: readonly string[]; readonly text: string }
  | { readonly type: 'tool'; readonly round: number; readonly toolCallId: string; readonly name: string; readonly result: ToolResult }
  | { readonly type: 'stopped'; readonly reason: StopReason }

export type StopReason = 'completed' | 'empty_final' | 'model_error' | 'max_rounds'

export interface LoopResult {
  readonly ok: boolean
  readonly answer?: string
  readonly reason: StopReason
  readonly messages: readonly Message[]
  readonly events: readonly LoopEvent[]
}

export const readonlyToolDefinitions: readonly ToolDefinition[] = [
  { name: 'search_files', description: '在工作区文本文件中搜索关键词', inputSchema: { type: 'object', properties: { needle: { type: 'string' } }, required: ['needle'], additionalProperties: false } },
  { name: 'read_file', description: '读取工作区内的一个文本文件', inputSchema: { type: 'object', properties: { path: { type: 'string' } }, required: ['path'], additionalProperties: false } },
]

export async function runAgentLoop(
  adapter: ChatAdapter,
  initialMessages: readonly Message[],
  workspace: Workspace,
  options: { readonly maxRounds?: number; readonly tools?: readonly ToolDefinition[] } = {},
): Promise<LoopResult> {
  const maxRounds = options.maxRounds ?? 32
  const tools = options.tools ?? readonlyToolDefinitions
  const messages: Message[] = [...initialMessages]
  const events: LoopEvent[] = [{ type: 'started', round: 0 }]
  for (let round = 1; round <= maxRounds; round += 1) {
    let turn
    try { turn = await adapter.complete(messages, tools) }
    catch (error) {
      events.push({ type: 'stopped', reason: 'model_error' })
      return { ok: false, reason: 'model_error', messages, events }
    }
    messages.push(turn.message)
    events.push({ type: 'model', round, toolCallIds: turn.toolCalls.map(call => call.id), text: turn.message.content })
    if (turn.toolCalls.length === 0) {
      if (turn.message.content.trim().length === 0) {
        events.push({ type: 'stopped', reason: 'empty_final' })
        return { ok: false, reason: 'empty_final', messages, events }
      }
      events.push({ type: 'stopped', reason: 'completed' })
      return { ok: true, answer: turn.message.content, reason: 'completed', messages, events }
    }
    for (const call of turn.toolCalls) {
      const result = await dispatchReadonly(call, workspace)
      const content = result.ok ? result.output ?? '' : JSON.stringify({ error: result.error })
      messages.push({ role: 'tool', toolCallId: result.toolCallId, content })
      events.push({ type: 'tool', round, toolCallId: call.id, name: call.name, result })
    }
  }
  events.push({ type: 'stopped', reason: 'max_rounds' })
  return { ok: false, reason: 'max_rounds', messages, events }
}

export function replayAdapter(turns: readonly (Pick<import('./contracts').ModelTurn, 'message' | 'toolCalls'> | Error)[]): ChatAdapter & { readonly receivedMessages: readonly (readonly Message[])[] } {
  let index = 0
  const receivedMessages: (readonly Message[])[] = []
  return { receivedMessages, async complete(messages) {
    receivedMessages.push(structuredClone(messages))
    const turn = turns[index++]
    if (turn === undefined) throw new Error('replay exhausted')
    if (turn instanceof Error) throw turn
    return turn
  } }
}
