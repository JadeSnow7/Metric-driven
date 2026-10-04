use rein_ch01_helloworld::rein::context_methods::{run, Index, Tasks};
use std::{fs, path::PathBuf};

#[tokio::test]
async fn ch08_default_tasks_are_evidence_based() {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../fixtures/ch08-context");
    let index: Index =
        serde_json::from_str(&fs::read_to_string(root.join("index.json")).unwrap()).unwrap();
    let tasks: Tasks =
        serde_json::from_str(&fs::read_to_string(root.join("tasks.json")).unwrap()).unwrap();
    let output = run(index, tasks, root, "retrieval", None, None)
        .await
        .unwrap();
    assert_eq!(output.results.len(), 4);
    assert_eq!(
        output.results[0].answer.as_ref().unwrap().claims[0].source,
        "doc-01"
    );
    assert!(
        output.results[3]
            .answer
            .as_ref()
            .unwrap()
            .insufficientEvidence
    );
}

#[tokio::test]
async fn ch08_zero_budget_does_not_read_or_call() {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../fixtures/ch08-context");
    let index: Index =
        serde_json::from_str(&fs::read_to_string(root.join("index.json")).unwrap()).unwrap();
    let tasks: Tasks =
        serde_json::from_str(&fs::read_to_string(root.join("tasks.json")).unwrap()).unwrap();
    let output = run(index, tasks, root, "on-demand", Some(0), None)
        .await
        .unwrap();
    assert!(output
        .results
        .iter()
        .all(|row| row.status == "context_budget_exhausted"
            && row.modelCalls == 0
            && row.operations.is_empty()));
}
