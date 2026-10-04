use rein_ch01_helloworld::rein::context_methods::{run_one, Index, Task};
use std::path::Path;

#[tokio::test]
async fn reads_real_node_and_unknown_stays_empty() {
    let root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .join("fixtures/ch08-context");
    let index: Index =
        serde_json::from_str(&std::fs::read_to_string(root.join("index.json")).unwrap()).unwrap();
    let task = Task {
        id: "task-01".into(),
        question: "早期运行文档中的传输方式和协议版本是什么？".into(),
        rules: vec!["只根据实际读取的资料回答".into()],
        budget: 2400,
    };
    let row = run_one(&index, &task, "on-demand", &root, None).await;
    assert_eq!(row.status, "completed");
    assert_eq!(row.answer.as_ref().unwrap().claims.len(), 2);
    assert!(row
        .call_records
        .iter()
        .all(|r| r.dispatched && r.reaped && r.child_pid.is_some()));
    let unknown = Task {
        id: "task-04".into(),
        question: "生产吞吐量是多少？".into(),
        rules: task.rules.clone(),
        budget: 2400,
    };
    let row = run_one(&index, &unknown, "retrieval", &root, None).await;
    assert!(row.answer.unwrap().insufficient_evidence);
}

#[tokio::test]
async fn zero_budget_does_not_dispatch() {
    let root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .join("fixtures/ch08-context");
    let index: Index =
        serde_json::from_str(&std::fs::read_to_string(root.join("index.json")).unwrap()).unwrap();
    let task = Task {
        id: "x".into(),
        question: "任何问题".into(),
        rules: vec!["规则".into()],
        budget: 2400,
    };
    let row = run_one(&index, &task, "summary", &root, Some(0)).await;
    assert_eq!(row.status, "context_budget_exhausted");
    assert_eq!(row.model_calls, 0);
    assert!(row.operations.is_empty());
}
