use rein_ch01_helloworld::rein::{run_agent_loop, OpenAiHttp, StopReason, ToolError, Workspace};
use std::{
    future::Future,
    pin::Pin,
    sync::{Arc, Mutex},
};

struct Replay(Arc<Mutex<Vec<String>>>);
impl OpenAiHttp for Replay {
    fn post<'a>(
        &'a self,
        _: &'a str,
        _: &'a str,
        _: serde_json::Value,
    ) -> Pin<Box<dyn Future<Output = Result<String, ToolError>> + Send + 'a>> {
        let response = self.0.lock().unwrap().remove(0);
        Box::pin(async move { Ok(response) })
    }
}

#[tokio::test]
async fn tools_are_real_and_results_are_paired_in_order() {
    let root = std::env::temp_dir().join(format!("rein-loop-{}", std::process::id()));
    let _ = std::fs::remove_dir_all(&root);
    std::fs::create_dir(&root).unwrap();
    std::fs::write(root.join("note.txt"), "rust evidence").unwrap();
    let responses = vec![
        r#"{"choices":[{"message":{"role":"assistant","content":null,"tool_calls":[{"id":"s","type":"function","function":{"name":"search_files","arguments":"{\"needle\":\"evidence\"}"}},{"id":"r","type":"function","function":{"name":"read_file","arguments":"{\"path\":\"note.txt\"}"}}]}}]}"#.into(),
        r#"{"choices":[{"message":{"role":"assistant","content":"done"}}]}"#.into(),
    ];
    let result = run_agent_loop(
        &Replay(Arc::new(Mutex::new(responses))),
        "offline://replay",
        "x",
        "m",
        &Workspace { root: root.clone() },
        "inspect",
        2,
    )
    .await;
    assert_eq!(result.reason, StopReason::FinalAnswer);
    assert_eq!(
        result
            .messages
            .iter()
            .filter(|m| m.role == "tool")
            .map(|m| m.tool_call_id.as_deref())
            .collect::<Vec<_>>(),
        vec![Some("s"), Some("r")]
    );
    assert_eq!(result.messages[2].content, "note.txt");
    assert_eq!(result.messages[3].content, "rust evidence");
    std::fs::remove_dir_all(root).unwrap();
}
