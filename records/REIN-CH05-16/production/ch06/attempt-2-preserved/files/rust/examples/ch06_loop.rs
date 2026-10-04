use rein_ch01_helloworld::rein::{
    run_agent_loop_with_options, ControlSignal, LoopOptions, Message, ModelAdapter, ModelTurn,
    ToolCall, ToolDefinition, ToolError, Workspace,
};
use std::{future::Future, path::PathBuf, pin::Pin, time::Duration};

struct Replay {
    mode: String,
}
impl ModelAdapter for Replay {
    fn complete<'a>(
        &'a self,
        messages: &'a [Message],
        _: &'a [ToolDefinition],
    ) -> Pin<Box<dyn Future<Output = Result<ModelTurn, ToolError>> + Send + 'a>> {
        let mode = self.mode.clone();
        let tool_count = messages.iter().filter(|m| m.role == "tool").count();
        Box::pin(async move {
            if mode == "timeout" || mode == "cancel" {
                tokio::time::sleep(Duration::from_millis(40)).await;
            }
            let calls = if mode == "duplicate" || (mode == "budget" && tool_count == 0) {
                vec![
                    ToolCall {
                        id: format!("call-{tool_count}"),
                        name: "read_file".into(),
                        arguments: serde_json::json!({"path":"README.md"}),
                    },
                    ToolCall {
                        id: "second".into(),
                        name: "read_file".into(),
                        arguments: serde_json::json!({"path":"README.md"}),
                    },
                ]
            } else if tool_count == 0 {
                vec![ToolCall {
                    id: "read".into(),
                    name: "read_file".into(),
                    arguments: serde_json::json!({"path":"README.md"}),
                }]
            } else {
                vec![]
            };
            Ok(ModelTurn {
                message: Message {
                    role: "assistant".into(),
                    content: if calls.is_empty() {
                        "完成".into()
                    } else {
                        String::new()
                    },
                    tool_call_id: None,
                    tool_calls: calls.clone(),
                },
                tool_calls: calls,
            })
        })
    }
}

#[tokio::main]
async fn main() {
    let mode = std::env::args().nth(1).unwrap_or_else(|| "normal".into());
    let root = std::env::temp_dir().join(format!("rein-ch06-rust-{}", std::process::id()));
    let _ = std::fs::remove_dir_all(&root);
    std::fs::create_dir_all(&root).unwrap();
    std::fs::write(root.join("README.md"), "marker: ch06\n").unwrap();
    let signal = ControlSignal::new();
    if mode == "cancel" {
        let cancel = signal.clone();
        tokio::spawn(async move {
            tokio::time::sleep(Duration::from_millis(5)).await;
            cancel.cancel();
        });
    }
    let result = run_agent_loop_with_options(
        &Replay { mode: mode.clone() },
        &Workspace {
            root: PathBuf::from(&root),
        },
        "读取 README.md",
        LoopOptions {
            max_turns: if mode == "zero" { 0 } else { 3 },
            max_tool_calls: if mode == "budget" { 1 } else { usize::MAX },
            duplicate_limit: if mode == "duplicate" { 1 } else { usize::MAX },
            timeout: if mode == "timeout" {
                Some(Duration::from_millis(5))
            } else {
                None
            },
            signal: if mode == "cancel" { Some(signal) } else { None },
        },
    )
    .await;
    println!(
        "{}",
        serde_json::to_string_pretty(&serde_json::json!({"mode":mode,"result":result})).unwrap()
    );
    let _ = std::fs::remove_dir_all(root);
}
