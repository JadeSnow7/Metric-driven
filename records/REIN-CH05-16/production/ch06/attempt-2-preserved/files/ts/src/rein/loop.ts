import type { ChatAdapter, Message, ToolCall, ToolDefinition, ToolResult } from './contracts'
import type { Workspace } from './readonly'
import { dispatchReadonly } from './readonly'

export type LoopState = 'running' | 'completed' | 'failed'
export type StopReason = 'final_answer' | 'empty_final' | 'model_error' | 'max_turns' | 'tool_budget_exhausted' | 'duplicate_action' | 'cancelled' | 'timeout'
export type LoopEvent =
  | { readonly type: 'model_requested'; readonly turn: number; readonly messages: readonly Message[]; readonly tools: readonly ToolDefinition[] }
  | { readonly type: 'model_received'; readonly turn: number; readonly message: Message; readonly toolCallIds: readonly string[]; readonly text: string }
  | { readonly type: 'tool_result'; readonly turn: number; readonly call: ToolCall; readonly toolCallId: string; readonly result: ToolResult }
  | { readonly type: 'action_skipped'; readonly turn: number; readonly action: 'model' | 'tool'; readonly callId?: string; readonly reason: StopReason }
  | { readonly type: 'stopped'; readonly state: Exclude<LoopState, 'running'>; readonly reason: StopReason }

export interface LoopOptions {
  readonly maxTurns?: number
  /** Maximum number of tool calls actually started. */
  readonly maxToolCalls?: number
  /** Number of equal (tool name + canonical arguments) dispatches allowed. */
  readonly duplicateLimit?: number
  readonly signal?: AbortSignal
  /** Whole-loop deadline, including model and tool work. */
  readonly timeoutMs?: number
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
  const maxToolCalls = options.maxToolCalls ?? Number.POSITIVE_INFINITY
  const duplicateLimit = options.duplicateLimit ?? Number.POSITIVE_INFINITY
  const tools = options.tools ?? readonlyToolDefinitions
  const messages: Message[] = [{ role: 'user', content: prompt }]
  const events: LoopEvent[] = []
  const startedAt = Date.now()
  const deadline = options.timeoutMs === undefined ? undefined : startedAt + Math.max(0, options.timeoutMs)
  const controlReason = (): StopReason | undefined => {
    if (options.signal?.aborted) return 'cancelled'
    if (deadline !== undefined && Date.now() >= deadline) return 'timeout'
    return undefined
  }
  let toolStarted = 0
  const seen = new Map<string, number>()
  if (maxTurns <= 0) return finish(messages, events, 'failed', 'max_turns')
  const initialReason = controlReason()
  if (initialReason) return finish(messages, events, 'failed', initialReason)
  for (let turn = 1; turn <= maxTurns; turn++) {
    const beforeModel = controlReason()
    if (beforeModel) return finish(messages, events, 'failed', beforeModel)
    events.push({ type: 'model_requested', turn, messages: structuredClone(messages), tools: structuredClone(tools) })
    let model
    try {
      const remaining = deadline === undefined ? undefined : Math.max(0, deadline - Date.now())
      model = await raceControl(() => adapter.complete(messages, tools, { timeoutMs: remaining, signal: options.signal }), options.signal, remaining)
    }
    catch (error) {
      const reason = controlReason()
      if (reason) return finish(messages, events, 'failed', reason)
      return finish(messages, events, 'failed', 'model_error', undefined, error instanceof Error ? error.message : 'model error')
    }
    const afterModel = controlReason()
    if (afterModel) return finish(messages, events, 'failed', afterModel)
    messages.push(model.message)
    events.push({ type: 'model_received', turn, message: structuredClone(model.message), toolCallIds: model.toolCalls.map(call => call.id), text: model.message.content })
    if (model.toolCalls.length === 0) {
      if (model.message.content.trim().length === 0) return finish(messages, events, 'failed', 'empty_final')
      return finish(messages, events, 'completed', 'final_answer', model.message.content)
    }
    if (model.toolCalls.length > 0 && maxToolCalls <= toolStarted) {
      for (const call of model.toolCalls) events.push({ type: 'action_skipped', turn, action: 'tool', callId: call.id, reason: 'tool_budget_exhausted' })
      return finish(messages, events, 'failed', 'tool_budget_exhausted')
    }
    for (let index = 0; index < model.toolCalls.length; index++) {
      const call = model.toolCalls[index]!
      const reason = controlReason()
      if (reason) {
        for (const skipped of model.toolCalls.slice(index)) events.push({ type: 'action_skipped', turn, action: 'tool', callId: skipped.id, reason })
        return finish(messages, events, 'failed', reason)
      }
      if (toolStarted >= maxToolCalls) {
        for (const skipped of model.toolCalls.slice(index)) events.push({ type: 'action_skipped', turn, action: 'tool', callId: skipped.id, reason: 'tool_budget_exhausted' })
        return finish(messages, events, 'failed', 'tool_budget_exhausted')
      }
      const identity = `${call.name}\0${canonicalJson(call.arguments)}`
      const occurrences = (seen.get(identity) ?? 0) + 1
      if (occurrences > duplicateLimit) {
        for (const skipped of model.toolCalls.slice(index)) events.push({ type: 'action_skipped', turn, action: 'tool', callId: skipped.id, reason: 'duplicate_action' })
        return finish(messages, events, 'failed', 'duplicate_action')
      }
      seen.set(identity, occurrences)
      toolStarted++
      const result = await dispatchReadonly(call, workspace)
      events.push({ type: 'tool_result', turn, call: structuredClone(call), toolCallId: call.id, result })
      messages.push({ role: 'tool', toolCallId: result.toolCallId, content: result.ok ? result.output ?? '' : JSON.stringify({ ok: false, error: result.error }) })
    }
  }
  const finalControl = controlReason()
  return finish(messages, events, 'failed', finalControl ?? 'max_turns')
}

function canonicalJson(value: unknown): string {
  if (value === null || typeof value !== 'object') return JSON.stringify(value)
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(',')}]`
  return `{${Object.keys(value as Record<string, unknown>).sort().map(key => `${JSON.stringify(key)}:${canonicalJson((value as Record<string, unknown>)[key])}`).join(',')}}`
}

async function raceControl<T>(start: () => Promise<T>, signal: AbortSignal | undefined, timeoutMs: number | undefined): Promise<T> {
  if (signal === undefined && timeoutMs === undefined) return start()
  let timer: ReturnType<typeof setTimeout> | undefined
  let onAbort: (() => void) | undefined
  const control = new Promise<never>((_, reject) => {
    onAbort = () => reject(new Error('cancelled'))
    signal?.addEventListener('abort', onAbort, { once: true })
    if (timeoutMs !== undefined) timer = setTimeout(() => reject(new Error('timeout')), timeoutMs)
  })
  if (signal?.aborted) throw new Error('cancelled')
  const work = start()
  try { return await Promise.race([work, control]) }
  finally {
    if (timer !== undefined) clearTimeout(timer)
    if (onAbort) signal?.removeEventListener('abort', onAbort)
  }
}

function finish(messages: Message[], events: LoopEvent[], state: Exclude<LoopState, 'running'>, reason: StopReason, answer?: string, error?: string): LoopResult {
  events.push({ type: 'stopped', state, reason })
  return { state, reason, ...(answer === undefined ? {} : { answer }), messages, events, ...(error === undefined ? {} : { error }) }
}
