extern crate product as rein_ch01_helloworld;
mod supplied_demo {
    include!("/private/tmp/rein-ch05-review-20260914/reviewer-2/package-42/rust/examples/ch05_loop.rs");
    pub async fn reproduce() {
        let replay = Replay { responses: Arc::new(Mutex::new(vec![r#"{"choices":[{"message":{"role":"assistant","content":null,"tool_calls":[{"id":"once","type":"function","function":{"name":"no_such_tool","arguments":"{}"}}]}}]}"#.into()])) };
        let root = std::path::PathBuf::from("/private/tmp/rein-ch05-review-evidence-2");
        println!("Input: one tool response, no second replay response; max_turns=4");
        let result = run_agent_loop(&replay,"offline://replay","offline","demo",&Workspace{root},"exhaust replay",4).await;
        println!("LoopResult: {:?}",result);
    }
}
#[tokio::main]
async fn main() { supplied_demo::reproduce().await; }
