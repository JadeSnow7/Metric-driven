//! Chapter 05's typed, provider-independent agent loop.
use super::{
    dispatch_readonly, openai_complete, Message, ModelTurn, OpenAiHttp, ToolCall, ToolDefinition,
    ToolError, ToolResult, Workspace,
};
use serde::{Deserialize, Serialize};
use std::{
    future::Future,
    pin::Pin,
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc,
    },
    time::{Duration, Instant},
};

pub trait ModelAdapter {
    fn complete<'a>(
        &'a self,
        messages: &'a [Message],
        tools: &'a [ToolDefinition],
    ) -> Pin<Box<dyn Future<Output = Result<ModelTurn, ToolError>> + Send + 'a>>;
    fn complete_controlled<'a>(
        &'a self,
        messages: &'a [Message],
        tools: &'a [ToolDefinition],
        _signal: &'a ControlSignal,
    ) -> Pin<Box<dyn Future<Output = Result<ModelTurn, ToolError>> + Send + 'a>> {
        self.complete(messages, tools)
    }
}

#[derive(Clone, Debug, Default)]
pub struct ControlSignal(Arc<AtomicBool>);
impl ControlSignal {
    pub fn new() -> Self {
        Self::default()
    }
    pub fn cancel(&self) {
        self.0.store(true, Ordering::Release);
    }
    pub fn is_cancelled(&self) -> bool {
        self.0.load(Ordering::Acquire)
    }
}

pub struct OpenAiModelAdapter<'a, H: OpenAiHttp> {
    http: &'a H,
    base_url: &'a str,
    api_key: &'a str,
    model: &'a str,
}
impl<'a, H: OpenAiHttp> OpenAiModelAdapter<'a, H> {
    pub fn new(http: &'a H, base_url: &'a str, api_key: &'a str, model: &'a str) -> Self {
        Self {
            http,
            base_url,
            api_key,
            model,
        }
    }
}
impl<'a, H: OpenAiHttp> ModelAdapter for OpenAiModelAdapter<'a, H> {
    fn complete<'b>(
        &'b self,
        messages: &'b [Message],
        tools: &'b [ToolDefinition],
    ) -> Pin<Box<dyn Future<Output = Result<ModelTurn, ToolError>> + Send + 'b>> {
        Box::pin(openai_complete(
            self.http,
            self.base_url,
            self.api_key,
            self.model,
            messages,
            tools,
        ))
    }
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum LoopState {
    Running,
    Completed,
    Failed,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum StopReason {
    FinalAnswer,
    EmptyFinal,
    ModelError,
    MaxTurns,
    ToolBudgetExhausted,
    DuplicateAction,
    Cancelled,
    Timeout,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum LoopEvent {
    ModelRequested {
        turn: usize,
        messages: Vec<Message>,
        tools: Vec<ToolDefinition>,
    },
    ModelReceived {
        turn: usize,
        message: Message,
        #[serde(rename = "toolCallIds")]
        tool_call_ids: Vec<String>,
        text: String,
    },
    ToolResult {
        turn: usize,
        call: ToolCall,
        #[serde(rename = "toolCallId")]
        tool_call_id: String,
        result: ToolResult,
    },
    ActionSkipped {
        turn: usize,
        action: String,
        #[serde(rename = "callId", skip_serializing_if = "Option::is_none")]
        call_id: Option<String>,
        reason: StopReason,
    },
    Stopped {
        state: LoopState,
        reason: StopReason,
    },
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct LoopResult {
    pub state: LoopState,
    pub reason: StopReason,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub answer: Option<String>,
    pub messages: Vec<Message>,
    pub events: Vec<LoopEvent>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
}
pub const READONLY_TOOLS: &[(&str, &str)] = &[
    ("search_files", "Search text in workspace files."),
    ("read_file", "Read one UTF-8 file in the workspace."),
];

pub async fn run_agent_loop<H: OpenAiHttp>(
    http: &H,
    base_url: &str,
    api_key: &str,
    model: &str,
    workspace: &Workspace,
    prompt: &str,
    max_turns: usize,
) -> LoopResult {
    run_agent_loop_with_adapter(
        &OpenAiModelAdapter::new(http, base_url, api_key, model),
        workspace,
        prompt,
        max_turns,
    )
    .await
}
pub async fn run_agent_loop_with_adapter<A: ModelAdapter>(
    adapter: &A,
    workspace: &Workspace,
    prompt: &str,
    max_turns: usize,
) -> LoopResult {
    run_agent_loop_with_options(
        adapter,
        workspace,
        prompt,
        LoopOptions {
            max_turns,
            ..LoopOptions::default()
        },
    )
    .await
}

#[derive(Clone, Debug)]
pub struct LoopOptions {
    pub max_turns: usize,
    pub max_tool_calls: usize,
    pub duplicate_limit: usize,
    pub timeout: Option<Duration>,
    pub signal: Option<ControlSignal>,
}
impl Default for LoopOptions {
    fn default() -> Self {
        Self {
            max_turns: 32,
            max_tool_calls: usize::MAX,
            duplicate_limit: usize::MAX,
            timeout: None,
            signal: None,
        }
    }
}

pub async fn run_agent_loop_with_options<A: ModelAdapter>(
    adapter: &A,
    workspace: &Workspace,
    prompt: &str,
    options: LoopOptions,
) -> LoopResult {
    let mut messages = vec![Message {
        role: "user".into(),
        content: prompt.into(),
        tool_call_id: None,
        tool_calls: vec![],
    }];
    let mut events = Vec::new();
    let definitions = READONLY_TOOLS.iter().map(|(name, description)| ToolDefinition { name: (*name).into(), description: (*description).into(), input_schema: match *name {
        "read_file" => serde_json::json!({"type":"object","properties":{"path":{"type":"string"}},"required":["path"],"additionalProperties":false}),
        "search_files" => serde_json::json!({"type":"object","properties":{"needle":{"type":"string"}},"required":["needle"],"additionalProperties":false}), _ => serde_json::json!({"type":"object"}),
    }}).collect::<Vec<_>>();
    let signal = options.signal.unwrap_or_default();
    let deadline = options.timeout.map(|d| Instant::now() + d);
    if options.max_turns == 0 {
        return finish_loop(
            messages,
            events,
            LoopState::Failed,
            StopReason::MaxTurns,
            None,
            None,
        );
    }
    if let Some(reason) = control_reason(&signal, deadline) {
        return finish_loop(messages, events, LoopState::Failed, reason, None, None);
    }
    let mut tool_started = 0usize;
    let mut seen = std::collections::HashMap::<String, usize>::new();
    for turn in 1..=options.max_turns {
        if let Some(reason) = control_reason(&signal, deadline) {
            return finish_loop(messages, events, LoopState::Failed, reason, None, None);
        }
        events.push(LoopEvent::ModelRequested {
            turn,
            messages: messages.clone(),
            tools: definitions.clone(),
        });
        let remaining = deadline.map(|d| d.saturating_duration_since(Instant::now()));
        let response = match await_control(
            adapter.complete_controlled(&messages, &definitions, &signal),
            &signal,
            remaining,
        )
        .await
        {
            Ok(value) => value,
            Err(error) => {
                if let Some(reason) = control_reason(&signal, deadline) {
                    return finish_loop(messages, events, LoopState::Failed, reason, None, None);
                }
                return finish_loop(
                    messages,
                    events,
                    LoopState::Failed,
                    StopReason::ModelError,
                    None,
                    Some(error.message),
                );
            }
        };
        if let Some(reason) = control_reason(&signal, deadline) {
            return finish_loop(messages, events, LoopState::Failed, reason, None, None);
        }
        let ids = response
            .tool_calls
            .iter()
            .map(|call| call.id.clone())
            .collect();
        events.push(LoopEvent::ModelReceived {
            turn,
            message: response.message.clone(),
            tool_call_ids: ids,
            text: response.message.content.clone(),
        });
        messages.push(response.message.clone());
        if response.tool_calls.is_empty() {
            if response.message.content.trim().is_empty() {
                return finish_loop(
                    messages,
                    events,
                    LoopState::Failed,
                    StopReason::EmptyFinal,
                    None,
                    None,
                );
            }
            return finish_loop(
                messages,
                events,
                LoopState::Completed,
                StopReason::FinalAnswer,
                Some(response.message.content),
                None,
            );
        }
        if !response.tool_calls.is_empty() && tool_started >= options.max_tool_calls {
            for call in &response.tool_calls {
                events.push(LoopEvent::ActionSkipped {
                    turn,
                    action: "tool".into(),
                    call_id: Some(call.id.clone()),
                    reason: StopReason::ToolBudgetExhausted,
                });
            }
            return finish_loop(
                messages,
                events,
                LoopState::Failed,
                StopReason::ToolBudgetExhausted,
                None,
                None,
            );
        }
        let calls = response.tool_calls.clone();
        for (index, call) in calls.into_iter().enumerate() {
            if let Some(reason) = control_reason(&signal, deadline) {
                for skipped in response.tool_calls.iter().skip(index) {
                    events.push(LoopEvent::ActionSkipped {
                        turn,
                        action: "tool".into(),
                        call_id: Some(skipped.id.clone()),
                        reason: reason.clone(),
                    });
                }
                return finish_loop(messages, events, LoopState::Failed, reason, None, None);
            }
            if tool_started >= options.max_tool_calls {
                for skipped in response.tool_calls.iter().skip(index) {
                    events.push(LoopEvent::ActionSkipped {
                        turn,
                        action: "tool".into(),
                        call_id: Some(skipped.id.clone()),
                        reason: StopReason::ToolBudgetExhausted,
                    });
                }
                return finish_loop(
                    messages,
                    events,
                    LoopState::Failed,
                    StopReason::ToolBudgetExhausted,
                    None,
                    None,
                );
            }
            let identity = format!("{}\0{}", call.name, canonical_json(&call.arguments));
            let occurrence = seen.get(&identity).copied().unwrap_or(0) + 1;
            if occurrence > options.duplicate_limit {
                for skipped in response.tool_calls.iter().skip(index) {
                    events.push(LoopEvent::ActionSkipped {
                        turn,
                        action: "tool".into(),
                        call_id: Some(skipped.id.clone()),
                        reason: StopReason::DuplicateAction,
                    });
                }
                return finish_loop(
                    messages,
                    events,
                    LoopState::Failed,
                    StopReason::DuplicateAction,
                    None,
                    None,
                );
            }
            seen.insert(identity, occurrence);
            tool_started += 1;
            let result = dispatch_readonly(&call, workspace);
            events.push(LoopEvent::ToolResult {
                turn,
                call: call.clone(),
                tool_call_id: call.id.clone(),
                result: result.clone(),
            });
            let content = if result.ok {
                result.output.unwrap_or_default()
            } else {
                serde_json::json!({"ok":false,"error":result.error}).to_string()
            };
            messages.push(Message {
                role: "tool".into(),
                content,
                tool_call_id: Some(result.tool_call_id),
                tool_calls: vec![],
            });
        }
    }
    let reason = control_reason(&signal, deadline).unwrap_or(StopReason::MaxTurns);
    finish_loop(messages, events, LoopState::Failed, reason, None, None)
}

fn control_reason(signal: &ControlSignal, deadline: Option<Instant>) -> Option<StopReason> {
    if signal.is_cancelled() {
        Some(StopReason::Cancelled)
    } else if deadline.is_some_and(|d| Instant::now() >= d) {
        Some(StopReason::Timeout)
    } else {
        None
    }
}

async fn await_control<T>(
    work: impl Future<Output = Result<T, ToolError>>,
    signal: &ControlSignal,
    timeout: Option<Duration>,
) -> Result<T, ToolError> {
    let watch = async {
        let start = Instant::now();
        loop {
            if signal.is_cancelled() {
                return Err(ToolError {
                    code: "cancelled".into(),
                    message: "cancelled".into(),
                });
            }
            if timeout.is_some_and(|d| start.elapsed() >= d) {
                return Err(ToolError {
                    code: "timeout".into(),
                    message: "deadline exceeded".into(),
                });
            }
            tokio::time::sleep(Duration::from_millis(2)).await;
        }
    };
    tokio::select! { value = work => value, value = watch => value }
}

fn canonical_json(value: &serde_json::Value) -> String {
    match value {
        serde_json::Value::Object(map) => {
            let mut keys: Vec<_> = map.keys().collect();
            keys.sort();
            format!(
                "{{{}}}",
                keys.into_iter()
                    .map(|k| format!(
                        "{}:{}",
                        serde_json::to_string(k).unwrap(),
                        canonical_json(&map[k])
                    ))
                    .collect::<Vec<_>>()
                    .join(",")
            )
        }
        serde_json::Value::Array(values) => format!(
            "[{}]",
            values
                .iter()
                .map(canonical_json)
                .collect::<Vec<_>>()
                .join(",")
        ),
        other => other.to_string(),
    }
}
fn finish_loop(
    messages: Vec<Message>,
    mut events: Vec<LoopEvent>,
    state: LoopState,
    reason: StopReason,
    answer: Option<String>,
    error: Option<String>,
) -> LoopResult {
    events.push(LoopEvent::Stopped {
        state: state.clone(),
        reason: reason.clone(),
    });
    LoopResult {
        state,
        reason,
        answer,
        messages,
        events,
        error,
    }
}
