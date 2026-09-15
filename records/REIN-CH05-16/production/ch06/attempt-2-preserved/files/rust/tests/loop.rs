use rein_ch01_helloworld::rein::{
    run_agent_loop_with_adapter, run_agent_loop_with_options, ControlSignal, LoopEvent,
    LoopOptions, LoopState, Message, ModelAdapter, ModelTurn, StopReason, ToolCall, ToolDefinition,
    ToolError, Workspace,
};
use std::{
    collections::VecDeque,
    future::Future,
    pin::Pin,
    sync::{Arc, Mutex},
    time::Duration,
};

fn turn(content: &str, calls: Vec<ToolCall>) -> ModelTurn {
    ModelTurn {
        message: Message {
            role: "assistant".into(),
            content: content.into(),
            tool_call_id: None,
            tool_calls: calls.clone(),
        },
        tool_calls: calls,
    }
}
fn call(id: &str, name: &str, args: serde_json::Value) -> ToolCall {
    ToolCall {
        id: id.into(),
        name: name.into(),
        arguments: args,
    }
}
struct Replay(Arc<Mutex<VecDeque<Result<ModelTurn, ToolError>>>>);
impl ModelAdapter for Replay {
    fn complete<'a>(
        &'a self,
        _: &'a [Message],
        _: &'a [ToolDefinition],
    ) -> Pin<Box<dyn Future<Output = Result<ModelTurn, ToolError>> + Send + 'a>> {
        let value = self.0.lock().unwrap().pop_front().unwrap_or_else(|| {
            Err(ToolError {
                code: "replay_exhausted".into(),
                message: "replay exhausted".into(),
            })
        });
        Box::pin(async move { value })
    }
}

struct SearchReplay {
    requests: Arc<Mutex<Vec<Vec<Message>>>>,
}
impl ModelAdapter for SearchReplay {
    fn complete<'a>(
        &'a self,
        messages: &'a [Message],
        _: &'a [ToolDefinition],
    ) -> Pin<Box<dyn Future<Output = Result<ModelTurn, ToolError>> + Send + 'a>> {
        self.requests.lock().unwrap().push(messages.to_vec());
        let tool_messages: Vec<&Message> = messages.iter().filter(|m| m.role == "tool").collect();
        let response = if tool_messages.is_empty() {
            turn(
                "",
                vec![call(
                    "search",
                    "search_files",
                    serde_json::json!({"needle":"marker:"}),
                )],
            )
        } else if tool_messages.len() == 1 {
            let calls = tool_messages[0]
                .content
                .lines()
                .enumerate()
                .map(|(i, path)| {
                    call(
                        &format!("read-{i}"),
                        "read_file",
                        serde_json::json!({"path":path}),
                    )
                })
                .collect();
            turn("", calls)
        } else {
            turn(
                &tool_messages[1..]
                    .iter()
                    .map(|m| m.content.trim())
                    .collect::<Vec<_>>()
                    .join(" | "),
                vec![],
            )
        };
        Box::pin(async move { Ok(response) })
    }
}
fn workspace(label: &str, files: &[(&str, &str)]) -> Workspace {
    let root = std::env::temp_dir().join(format!("rein-ch05-{label}-{}", std::process::id()));
    let _ = std::fs::remove_dir_all(&root);
    std::fs::create_dir_all(&root).unwrap();
    for (path, content) in files {
        std::fs::write(root.join(path), content).unwrap();
    }
    Workspace { root }
}

struct ControlledReplay;
impl ModelAdapter for ControlledReplay {
    fn complete<'a>(
        &'a self,
        _: &'a [Message],
        _: &'a [ToolDefinition],
    ) -> Pin<Box<dyn Future<Output = Result<ModelTurn, ToolError>> + Send + 'a>> {
        Box::pin(async { Ok(turn("late", vec![])) })
    }
    fn complete_controlled<'a>(
        &'a self,
        _: &'a [Message],
        _: &'a [ToolDefinition],
        signal: &'a ControlSignal,
    ) -> Pin<Box<dyn Future<Output = Result<ModelTurn, ToolError>> + Send + 'a>> {
        let signal = signal.clone();
        Box::pin(async move {
            tokio::time::sleep(Duration::from_millis(40)).await;
            if signal.is_cancelled() {
                Ok(turn("late", vec![]))
            } else {
                Ok(turn("done", vec![]))
            }
        })
    }
}

#[tokio::test]
async fn controls_stop_pending_model_and_zero_budget_without_dispatch() {
    let ws = workspace("controls", &[]);
    let signal = ControlSignal::new();
    let to_cancel = signal.clone();
    tokio::spawn(async move {
        tokio::time::sleep(Duration::from_millis(5)).await;
        to_cancel.cancel();
    });
    let cancelled = run_agent_loop_with_options(
        &ControlledReplay,
        &ws,
        "cancel",
        LoopOptions {
            signal: Some(signal),
            ..LoopOptions::default()
        },
    )
    .await;
    assert_eq!(cancelled.reason, StopReason::Cancelled);
    assert_eq!(
        cancelled
            .events
            .iter()
            .filter(|event| matches!(event, LoopEvent::ModelRequested { .. }))
            .count(),
        1
    );
    let zero = run_agent_loop_with_options(
        &ControlledReplay,
        &ws,
        "zero",
        LoopOptions {
            max_turns: 0,
            ..LoopOptions::default()
        },
    )
    .await;
    assert_eq!(zero.reason, StopReason::MaxTurns);
    assert_eq!(
        zero.events
            .iter()
            .filter(|event| matches!(event, LoopEvent::ModelRequested { .. }))
            .count(),
        0
    );
    let timed = run_agent_loop_with_options(
        &ControlledReplay,
        &ws,
        "timeout",
        LoopOptions {
            timeout: Some(Duration::from_millis(5)),
            ..LoopOptions::default()
        },
    )
    .await;
    assert_eq!(timed.reason, StopReason::Timeout);
    let _ = std::fs::remove_dir_all(ws.root);
}

#[tokio::test]
async fn two_workspaces_search_then_read_and_pair_multiple_calls() {
    for (label, files, expected) in [
        (
            "blue",
            vec![("a.txt", "marker: blue"), ("b.txt", "marker: sea")],
            "marker: blue | marker: sea",
        ),
        (
            "gold",
            vec![("x.txt", "marker: gold"), ("y.txt", "marker: wind")],
            "marker: gold | marker: wind",
        ),
    ] {
        let ws = workspace(label, &files);
        let requests = Arc::new(Mutex::new(Vec::new()));
        let result = run_agent_loop_with_adapter(
            &SearchReplay {
                requests: requests.clone(),
            },
            &ws,
            "inspect",
            32,
        )
        .await;
        assert_eq!(result.reason, StopReason::FinalAnswer);
        assert_eq!(result.answer.as_deref(), Some(expected));
        assert_eq!(
            result
                .events
                .iter()
                .filter_map(|event| match event {
                    LoopEvent::ToolResult { tool_call_id, .. } => Some(tool_call_id.as_str()),
                    _ => None,
                })
                .collect::<Vec<_>>(),
            vec!["search", "read-0", "read-1"]
        );
        assert!(result.messages.iter().any(|m| m.content == expected));
        let captured = requests.lock().unwrap();
        assert_eq!(captured.len(), 3);
        let third_tools: Vec<_> = captured[2]
            .iter()
            .filter(|m| m.role == "tool")
            .skip(1)
            .collect();
        assert_eq!(
            third_tools
                .iter()
                .map(|m| m.tool_call_id.as_deref())
                .collect::<Vec<_>>(),
            vec![Some("read-0"), Some("read-1")]
        );
        assert_eq!(
            third_tools
                .iter()
                .map(|m| m.content.as_str())
                .collect::<Vec<_>>(),
            files
                .iter()
                .map(|(_, content)| *content)
                .collect::<Vec<_>>()
        );
        let _ = std::fs::remove_dir_all(ws.root);
    }
}

#[tokio::test]
async fn unknown_badargs_missing_file_are_feedback_and_can_recover() {
    let ws = workspace("recover", &[("ok.txt", "recovered")]);
    let replay = Replay(Arc::new(Mutex::new(VecDeque::from([
        Ok(turn(
            "",
            vec![
                call("u", "unknown", serde_json::json!({})),
                call("a", "read_file", serde_json::json!({"path": 3})),
                call("m", "read_file", serde_json::json!({"path":"missing"})),
            ],
        )),
        Ok(turn(
            "recovered",
            vec![call("r", "read_file", serde_json::json!({"path":"ok.txt"}))],
        )),
        Ok(turn("done", vec![])),
    ]))));
    let result = run_agent_loop_with_adapter(&replay, &ws, "recover", 32).await;
    assert_eq!(result.reason, StopReason::FinalAnswer);
    assert!(result.events.iter().any(|event| matches!(event, LoopEvent::ToolResult { result, .. } if result.error.as_ref().map(|e| e.code.as_str()) == Some("unknown_tool"))));
    assert!(result.events.iter().any(|event| matches!(event, LoopEvent::ToolResult { result, .. } if result.error.as_ref().map(|e| e.code.as_str()) == Some("arguments_invalid"))));
    assert!(result.events.iter().any(|event| matches!(event, LoopEvent::ToolResult { result, .. } if result.error.as_ref().map(|e| e.code.as_str()) == Some("path_invalid"))));
    let _ = std::fs::remove_dir_all(ws.root);
}

#[tokio::test]
async fn model_error_empty_final_max_turns_and_replay_exhaustion_are_structured() {
    let ws = workspace("boundaries", &[]);
    let failed = run_agent_loop_with_adapter(
        &Replay(Arc::new(Mutex::new(VecDeque::from([Err(ToolError {
            code: "model_error".into(),
            message: "offline".into(),
        })])))),
        &ws,
        "x",
        32,
    )
    .await;
    assert_eq!(failed.reason, StopReason::ModelError);
    assert_eq!(failed.state, LoopState::Failed);
    let empty = run_agent_loop_with_adapter(
        &Replay(Arc::new(Mutex::new(VecDeque::from([Ok(turn(
            "  ",
            vec![],
        ))])))),
        &ws,
        "x",
        32,
    )
    .await;
    assert_eq!(empty.reason, StopReason::EmptyFinal);
    let max_responses = (0..32)
        .map(|_| Ok(turn("", vec![call("u", "unknown", serde_json::json!({}))])))
        .collect();
    let max =
        run_agent_loop_with_adapter(&Replay(Arc::new(Mutex::new(max_responses))), &ws, "x", 32)
            .await;
    assert_eq!(max.reason, StopReason::MaxTurns);
    assert_eq!(
        max.events
            .iter()
            .filter(|e| matches!(e, LoopEvent::ModelRequested { .. }))
            .count(),
        32
    );
    let exhausted = run_agent_loop_with_adapter(
        &Replay(Arc::new(Mutex::new(VecDeque::from([Ok(turn(
            "",
            vec![call("s", "search_files", serde_json::json!({"needle":"x"}))],
        ))])))),
        &ws,
        "x",
        2,
    )
    .await;
    assert_eq!(exhausted.reason, StopReason::ModelError);
    assert_eq!(exhausted.error.as_deref(), Some("replay exhausted"));
    let _ = std::fs::remove_dir_all(ws.root);
}

#[test]
fn loop_wire_values_are_snake_case_and_fields_camel_case() {
    let value = serde_json::to_value(StopReason::MaxTurns).unwrap();
    assert_eq!(value, "max_turns");
    let value = serde_json::to_value(LoopEvent::ModelReceived {
        turn: 1,
        message: Message {
            role: "assistant".into(),
            content: "x".into(),
            tool_call_id: None,
            tool_calls: vec![],
        },
        tool_call_ids: vec!["a".into()],
        text: "x".into(),
    })
    .unwrap();
    assert_eq!(value["type"], "model_received");
    assert!(value.get("toolCallIds").is_some());
}
