use rein_ch01_helloworld::rein::{run_agent_loop, OpenAiHttp, ToolError, Workspace};
use std::{
    future::Future,
    pin::Pin,
    sync::{Arc, Mutex},
};

struct Replay {
    responses: Arc<Mutex<Vec<String>>>,
}
impl OpenAiHttp for Replay {
    fn post<'a>(
        &'a self,
        _: &'a str,
        _: &'a str,
        _: serde_json::Value,
    ) -> Pin<Box<dyn Future<Output = Result<String, ToolError>> + Send + 'a>> {
        let body = self.responses.lock().unwrap().remove(0);
        Box::pin(async move { Ok(body) })
    }
}

#[tokio::main]
async fn main() {
    let single = std::env::args().nth(1).as_deref() == Some("single");
    let responses = vec![
        if single { r#"{"choices":[{"message":{"role":"assistant","content":null,"tool_calls":[{"id":"read-1","type":"function","function":{"name":"read_file","arguments":"{\"path\":\"README.md\"}"}}]}}]}"#.into() } else { r#"{"choices":[{"message":{"role":"assistant","content":null,"tool_calls":[{"id":"search-1","type":"function","function":{"name":"search_files","arguments":"{\"needle\":\"前置\"}"}},{"id":"read-1","type":"function","function":{"name":"read_file","arguments":"{\"path\":\"README.md\"}"}}]}}]}"#.into() },
        r#"{"choices":[{"message":{"role":"assistant","content":"我找到了 README.md，并读取了真实内容。"}}]}"#.into(),
    ];
    let root = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../fixtures/workspaces/prerequisites");
    let result = run_agent_loop(
        &Replay {
            responses: Arc::new(Mutex::new(responses)),
        },
        "offline://replay",
        "offline",
        "demo",
        &Workspace { root },
        if single {
            "读取 README.md"
        } else {
            "检查 workspace"
        },
        32,
    )
    .await;
    println!("{}", serde_json::to_string_pretty(&result).unwrap());
}
