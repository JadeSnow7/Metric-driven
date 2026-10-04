use rein_ch01_helloworld::rein::context_methods::{load, run, Row};
use serde::Serialize;
use std::path::PathBuf;
#[derive(Serialize)]
struct Out {
    unit: String,
    #[serde(rename = "serviceTokens")]
    service_tokens: Option<()>,
    results: Vec<Row>,
}
#[tokio::main]
async fn main() {
    let mut a = std::env::args().skip(1);
    let root = PathBuf::from(a.next().unwrap_or_else(|| "fixtures/ch08-context".into()));
    let mut b = None;
    let mut s = None;
    while let Some(x) = a.next() {
        match x.as_str() {
            "--budget" => b = a.next().and_then(|v| v.parse().ok()),
            "--strategy" => s = a.next(),
            _ => {}
        }
    }
    let d = load(&root).unwrap_or_else(|e| {
        eprintln!("{e}");
        std::process::exit(2)
    });
    let ss = s.map(|x| vec![x]).unwrap_or_else(|| {
        vec![
            "on-demand".into(),
            "window".into(),
            "summary".into(),
            "retrieval".into(),
        ]
    });
    let mut r = Vec::new();
    for t in &d.tasks {
        for x in &ss {
            r.push(run(&root, t, x, b.unwrap_or(t.budget)).await)
        }
    }
    println!(
        "{}",
        serde_json::to_string(&Out {
            unit: d.index.unit,
            service_tokens: None,
            results: r
        })
        .unwrap()
    )
}
