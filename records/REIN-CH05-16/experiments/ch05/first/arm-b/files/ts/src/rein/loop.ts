import type { ChatAdapter, Message, ToolDefinition, ToolResult } from './contracts'
import type { Workspace } from './readonly'
import { dispatchReadonly } from './readonly'

export type LoopState = 'running' | 'completed' | 'failed'
export type StopReason = 'final_answer' | 'empty_final' | 'model_error' | 'max_turns'
export type LoopEvent =
  | { readonly type: 'model_requested'; readonly turn: number; readonly messageCount: number }
  | { readonly type: 'model_received'; readonly turn: number; readonly toolCallIds: readonly string[]; readonly text: string }
  | { readonly type: 'tool_result'; readonly turn: number; readonly toolCallId: string; readonly result: ToolResult }
  | { readonly type: 'stopped'; readonly state: Exclude<LoopState, 'running'>; readonly reason: StopReason }

export interface LoopOptions {
  readonly maxTurns?: number
  readonly tools?: readonly ToolDefinition[]
}

export interface LoopResult {
  readonly state: LoopState
  readonly reason: StopReason
  readonly answer?: string
  readonly messages: readonly Message[]
  readonly events: readonly LoopEvent[]
  readonly error?: string
}

export const readonlyToolDefinitions: readonly ToolDefinition[] = [
  { name: 'search_files', description: 'Search text in workspace files.', inputSchema: { type: 'object', properties: { needle: { type: 'string' } }, required: ['needle'], additionalProperties: false } },
  { name: 'read_file', description: 'Read one UTF-8 file in the workspace.', inputSchema: { type: 'object', properties: { path: { type: 'string' } }, required: ['path'], additionalProperties: false } },
]

/** Runs the small, replayable tool loop. One model turn may produce many tools. */
export async function runAgentLoop(adapter: ChatAdapter, workspace: Workspace, prompt: string, options: LoopOptions = {}): Promise<LoopResult> {
  const maxTurns = options.maxTurns ?? 32
  const tools = options.tools ?? readonlyToolDefinitions
  const messages: Message[] = [{ role: 'user', content: prompt }]
  const events: LoopEvent[] = []
  for (let turn = 1; turn <= maxTurns; turn++) {
    events.push({ type: 'model_requested', turn, messageCount: messages.length })
    let model
    try { model = await adapter.complete(messages, tools) }
    catch (error) { return finish(messages, events, 'failed', 'model_error', undefined, error instanceof Error ? error.message : 'model error') }
    messages.push(model.message)
    events.push({ type: 'model_received', turn, toolCallIds: model.toolCalls.map(call => call.id), text: model.message.content })
    if (model.toolCalls.length === 0) {
      if (model.message.content.trim().length === 0) return finish(messages, events, 'failed', 'empty_final')
      return finish(messages, events, 'completed', 'final_answer', model.message.content)
    }
    for (const call of model.toolCalls) {
      const result = await dispatchReadonly(call, workspace)
      events.push({ type: 'tool_result', turn, toolCallId: call.id, result })
      messages.push({ role: 'tool', toolCallId: result.toolCallId, content: result.ok ? result.output ?? '' : JSON.stringify({ ok: false, error: result.error }) })
    }
  }
  return finish(messages, events, 'failed', 'max_turns')
}

function finish(messages: Message[], events: LoopEvent[], state: Exclude<LoopState, 'running'>, reason: StopReason, answer?: string, error?: string): LoopResult {
  events.push({ type: 'stopped', state, reason })
  return { state, reason, ...(answer === undefined ? {} : { answer }), messages, events, ...(error === undefined ? {} : { error }) }
}
