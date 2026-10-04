use rein_ch01_helloworld::rein::context_methods::{run_one, validate, Index, Row, Task, Tasks};
use serde::Serialize;
use std::{env, fs, path::PathBuf};

#[derive(Serialize)]
struct Output {
    unit: String,
    #[serde(rename = "serviceTokens")]
    service_tokens: Option<usize>,
    results: Vec<Row>,
}
fn main() {
    let mut args = env::args().skip(1);
    let root = PathBuf::from(
        args.next()
            .unwrap_or_else(|| "fixtures/ch08-context".into()),
    );
    let budget = args
        .next()
        .and_then(|x| x.strip_prefix("--budget=").map(|v| v.parse().unwrap()));
    let strategy = args
        .next()
        .and_then(|x| x.strip_prefix("--strategy=").map(str::to_owned));
    let index: Index =
        serde_json::from_str(&fs::read_to_string(root.join("index.json")).expect("read index"))
            .expect("valid index");
    let tasks: Tasks =
        serde_json::from_str(&fs::read_to_string(root.join("tasks.json")).expect("read tasks"))
            .expect("valid tasks");
    validate(&index, &tasks, &root).expect("invalid metadata");
    let strategies: Vec<&str> = strategy
        .as_deref()
        .map(|s| vec![s])
        .unwrap_or_else(|| vec!["on-demand", "window", "summary", "retrieval"]);
    let rt = tokio::runtime::Runtime::new().unwrap();
    let results = rt.block_on(async {
        let mut out = Vec::new();
        for task in &tasks.tasks {
            for s in &strategies {
                out.push(run_one(&index, task, s, &root, budget).await);
            }
        }
        out
    });
    println!(
        "{}",
        serde_json::to_string(&Output {
            unit: index.unit,
            service_tokens: None,
            results
        })
        .unwrap()
    );
}
