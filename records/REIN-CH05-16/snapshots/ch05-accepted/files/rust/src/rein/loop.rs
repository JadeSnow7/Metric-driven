//! Chapter 05's typed, provider-independent agent loop.
use super::{
    dispatch_readonly, openai_complete, Message, ModelTurn, OpenAiHttp, ToolCall, ToolDefinition,
    ToolError, ToolResult, Workspace,
};
use serde::{Deserialize, Serialize};
use std::{future::Future, pin::Pin};

pub trait ModelAdapter {
    fn complete<'a>(
        &'a self,
        messages: &'a [Message],
        tools: &'a [ToolDefinition],
    ) -> Pin<Box<dyn Future<Output = Result<ModelTurn, ToolError>> + Send + 'a>>;
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
    for turn in 1..=max_turns {
        events.push(LoopEvent::ModelRequested {
            turn,
            messages: messages.clone(),
            tools: definitions.clone(),
        });
        let response = match adapter.complete(&messages, &definitions).await {
            Ok(value) => value,
            Err(error) => {
                return finish_loop(
                    messages,
                    events,
                    LoopState::Failed,
                    StopReason::ModelError,
                    None,
                    Some(error.message),
                )
            }
        };
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
        for call in response.tool_calls {
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
    finish_loop(
        messages,
        events,
        LoopState::Failed,
        StopReason::MaxTurns,
        None,
        None,
    )
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
