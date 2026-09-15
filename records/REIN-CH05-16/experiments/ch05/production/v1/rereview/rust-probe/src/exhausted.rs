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


#[tokio::main]
async fn main(){let responses=vec![r#"{"choices":[{"message":{"role":"assistant","content":null,"tool_calls":[{"id":"search","type":"function","function":{"name":"search_files","arguments":"{\"needle\":\"marker:\"}"}}]}}]}"#.into()];let result=run_agent_loop(&Replay(Arc::new(Mutex::new(responses))),"offline://replay","x","m",&Workspace{root:"/private/tmp/rein-production-20260914/fixtures/workspaces/prerequisites".into()},"inspect",2).await;println!("{}",serde_json::to_string(&result).unwrap());}
