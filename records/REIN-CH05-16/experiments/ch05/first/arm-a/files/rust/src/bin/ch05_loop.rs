use rein_ch01_helloworld::rein::{
    run_agent_loop, LoopAdapter, Message, ModelTurn, ToolCall, ToolDefinition, ToolError, Workspace,
};
use std::{future::Future, pin::Pin};
struct OfflineModel {
    round: usize,
}
impl LoopAdapter for OfflineModel {
    fn complete<'a>(
        &'a mut self,
        messages: &'a [Message],
        _tools: &'a [ToolDefinition],
    ) -> Pin<Box<dyn Future<Output = Result<ModelTurn, ToolError>> + Send + 'a>> {
        self.round += 1;
        let make = |id: &str, name: &str, args: serde_json::Value| ToolCall {
            id: id.into(),
            name: name.into(),
            arguments: args,
        };
        let turn = match self.round {
            1 => {
                let calls = vec![make(
                    "search-1",
                    "search_files",
                    serde_json::json!({"needle":"工具结果"}),
                )];
                ModelTurn {
                    message: Message {
                        role: "assistant".into(),
                        content: String::new(),
                        tool_call_id: None,
                        tool_calls: calls.clone(),
                    },
                    tool_calls: calls,
                }
            }
            2 => {
                let calls = vec![make(
                    "read-1",
                    "read_file",
                    serde_json::json!({"path":"guide.md"}),
                )];
                ModelTurn {
                    message: Message {
                        role: "assistant".into(),
                        content: String::new(),
                        tool_call_id: None,
                        tool_calls: calls.clone(),
                    },
                    tool_calls: calls,
                }
            }
            _ => ModelTurn {
                message: Message {
                    role: "assistant".into(),
                    content: messages
                        .iter()
                        .find(|m| m.role == "tool")
                        .map(|m| format!("读取完成：{}", m.content.trim()))
                        .unwrap_or_else(|| "读取完成".into()),
                    tool_call_id: None,
                    tool_calls: vec![],
                },
                tool_calls: vec![],
            },
        };
        Box::pin(async move { Ok(turn) })
    }
}
#[tokio::main]
async fn main() {
    let root = std::env::temp_dir().join(format!("rein-ch05-demo-{}", std::process::id()));
    let _ = std::fs::remove_dir_all(&root);
    std::fs::create_dir_all(&root).unwrap();
    std::fs::write(root.join("guide.md"), "# Loop\n工具结果会进入下一轮。\n").unwrap();
    let tools = vec![
        ToolDefinition {
            name: "search_files".into(),
            description: "搜索文本文件".into(),
            input_schema: serde_json::json!({"type":"object"}),
        },
        ToolDefinition {
            name: "read_file".into(),
            description: "读取文本文件".into(),
            input_schema: serde_json::json!({"type":"object"}),
        },
    ];
    let mut model = OfflineModel { round: 0 };
    let result = run_agent_loop(
        &mut model,
        &[Message {
            role: "user".into(),
            content: "搜索并读取 guide.md".into(),
            tool_call_id: None,
            tool_calls: vec![],
        }],
        &Workspace { root: root.clone() },
        &tools,
        32,
    )
    .await;
    println!("{}", serde_json::to_string_pretty(&serde_json::json!({"answer": result.answer, "reason": result.reason, "events": result.events})).unwrap());
    let _ = std::fs::remove_dir_all(root);
}
