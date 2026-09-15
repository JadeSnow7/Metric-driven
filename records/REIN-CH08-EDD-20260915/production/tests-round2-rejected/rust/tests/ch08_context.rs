use rein_ch01_helloworld::rein::context_methods::{
    run_one_with_executor, validate, Document, Index, Row, Task, Tasks,
};
use rein_ch01_helloworld::rein::{estimated_units, Message, StdioExecutor};
use std::{
    fs,
    path::{Path, PathBuf},
    process,
    sync::atomic::{AtomicUsize, Ordering},
};
static SEQ: AtomicUsize = AtomicUsize::new(0);
fn root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .to_path_buf()
}
fn dir() -> PathBuf {
    let p = std::env::temp_dir().join(format!(
        "rein-ch08-contract-{}-{}",
        process::id(),
        SEQ.fetch_add(1, Ordering::Relaxed)
    ));
    fs::create_dir(&p).unwrap_or_else(|e| panic!("unique temp dir: {p:?}: {e}"));
    fs::create_dir(p.join("docs")).unwrap();
    p
}
fn fixture() -> (PathBuf, Index, Vec<Task>) {
    let p = dir();
    let docs = [
        (
            "early",
            "背景旧段落\n\n传输方式：JSON Lines\n协议版本：rein-extension/0.1\n",
        ),
        ("latest", "检查命令：npm test\n"),
        ("approved", "批准状态：approved\n处理动作：deploy\n"),
        ("failed", "批准状态：failed\n处理动作：rollback\n"),
        ("background", "背景自然段\n"),
        ("other", "无关事实：never\n"),
    ];
    for (id, body) in docs {
        fs::write(p.join("docs").join(format!("{id}.md")), body).unwrap();
    }
    let index = Index {
        unit: "estimated-bytes-v1".into(),
        budget: 2400,
        documents: [
            ("early", vec!["传输", "协议"]),
            ("latest", vec!["检查", "命令"]),
            ("approved", vec!["批准", "处理"]),
            ("failed", vec!["批准", "处理"]),
            ("background", vec!["背景"]),
            ("other", vec!["无关"]),
        ]
        .into_iter()
        .enumerate()
        .map(|(i, (id, ks))| Document {
            id: id.into(),
            path: format!("docs/{id}.md"),
            title: id.into(),
            keywords: ks.into_iter().map(str::to_string).collect(),
            order: i + 1,
        })
        .collect(),
    };
    let rules = vec![
        "只根据实际读取的资料回答".into(),
        "每个事实必须给出来源".into(),
    ];
    let tasks = vec![
        Task {
            id: "task-01".into(),
            question: "早期文档的传输方式和协议版本是什么？".into(),
            rules: rules.clone(),
            budget: 2400,
        },
        Task {
            id: "task-02".into(),
            question: "最新发布文档的检查命令是什么？".into(),
            rules: rules.clone(),
            budget: 2400,
        },
        Task {
            id: "task-03".into(),
            question: "批准与失败文档的批准状态与处理动作是什么？".into(),
            rules: rules.clone(),
            budget: 2400,
        },
        Task {
            id: "task-04".into(),
            question: "生产吞吐量是多少？".into(),
            rules: vec!["资料没有证据时明确说明不足".into()],
            budget: 2400,
        },
    ];
    fs::write(
        p.join("tasks.json"),
        r#"{"tasks":[{"id":"task-01","expectedFacts":[{"field":"传输方式","value":"JSON Lines","source":"early"},{"field":"协议版本","value":"rein-extension/0.1","source":"early"}]},{"id":"task-02","expectedFacts":[{"field":"检查命令","value":"npm test","source":"latest"}]},{"id":"task-03","expectedFacts":[{"field":"批准状态","value":"approved","source":"approved"},{"field":"处理动作","value":"deploy","source":"approved"}]},{"id":"task-04","expectedFacts":[]}] }"#,
    )
    .unwrap();
    let oracle = fs::read_to_string(p.join("tasks.json")).unwrap().replace("\"task-04\",\"expectedFacts\"", "\"task-04\",\"unknown\":true,\"expectedFacts\"");
    fs::write(p.join("tasks.json"), oracle).unwrap();
    (p, index, tasks)
}
fn exec(p: &Path, mode: Option<&str>) -> StdioExecutor {
    let mut e = StdioExecutor::new(p);
    e.code_root = root();
    if let Some(m) = mode {
        e.host_script = root().join("ts/tests/fixtures/hybrid-fault-host.ts");
        e.env.push(("REIN_HYBRID_FAULT_MODE".into(), m.into()));
    }
    e
}
async fn run(i: &Index, t: &Task, s: &str, p: &Path, b: Option<usize>) -> Row {
    run_one_with_executor(i, t, s, p, b, exec(p, None)).await
}

#[tokio::test]
async fn default_matrix_and_message_contract() {
    let (p, i, ts) = fixture();
    let mut seen = std::collections::HashSet::new();
    for t in &ts {
        for s in ["on-demand", "window", "summary", "retrieval"] {
            let r = run(&i, t, s, &p, None).await;
            assert!(seen.insert((t.id.clone(), s)));
            assert_eq!(r.estimated_units, estimated_units(&r.messages));
            assert!(r.estimated_units <= t.budget);
            assert_eq!(
                r.messages.iter().filter(|m| m.role == "system").count(),
                t.rules.len()
            );
            assert_eq!(
                r.messages
                    .iter()
                    .find(|m| m.role == "user")
                    .unwrap()
                    .content,
                t.question
            );
            assert_eq!(r.service_tokens, None);
            assert!(r.answer.is_some());
            if t.id == "task-04" {
                let a = r.answer.unwrap();
                assert!(a.claims.is_empty() && a.insufficient_evidence);
                assert_eq!(r.quality, Some(1.0));
            }
        }
    }
    assert_eq!(seen.len(), 16);
}

#[tokio::test]
async fn mutation_changes_answer_and_summary_is_shorter() {
    let (p, mut i, ts) = fixture();
    fs::write(
        p.join("docs/early.md"),
        "背景旧段落\n\n传输方式：HTTP\n协议版本：rein-extension/0.1\n",
    )
    .unwrap();
    i.documents[0].keywords = vec!["传输".into(), "协议".into()];
    let r = run(&i, &ts[0], "summary", &p, None).await;
    let a = r.answer.unwrap();
    assert!(a.raw_answer.contains("HTTP") && a.raw_answer.contains("0.1"));
    assert!(a.claims.iter().all(|c| c.source == "early"));
    let body = fs::read_to_string(p.join("docs/early.md")).unwrap();
    let sources: Vec<_> = r.messages.iter().filter(|m| m.role == "user").collect();
    assert!(!sources.is_empty());
    assert!(sources.iter().all(|m| m.content.len() < body.len() + 20));
    assert_eq!(r.quality, Some(0.5));
}

#[tokio::test]
async fn budget_zero_and_base_boundary_never_dispatch() {
    let (p, i, mut ts) = fixture();
    ts[0].rules = vec!["r".into()];
    ts[0].question = "q".into();
    let req = vec![
        Message {
            role: "system".into(),
            content: "r".into(),
            tool_call_id: None,
            tool_calls: vec![],
        },
        Message {
            role: "user".into(),
            content: "q".into(),
            tool_call_id: None,
            tool_calls: vec![],
        },
    ];
    let base = estimated_units(&req);
    for s in ["on-demand", "window", "summary", "retrieval"] {
        for b in [0, base - 1] {
            let r = run(&i, &ts[0], s, &p, Some(b)).await;
            assert_eq!(r.status, "context_budget_exhausted");
            assert!(
                r.messages.is_empty()
                    && r.operations.is_empty()
                    && r.call_records.is_empty()
                    && r.answer.is_none()
            );
        }
        let r = run(&i, &ts[0], s, &p, Some(base)).await;
        assert!(r.estimated_units <= base);
    }
}

#[tokio::test]
async fn direct_entry_rejects_unsafe_budget_override() {
    let (p, i, ts) = fixture();
    let r = run(&i, &ts[0], "on-demand", &p, Some(usize::MAX)).await;
    assert_eq!(r.status, "error");
    assert!(r.answer.is_none() && r.model_calls == 0);
}

#[tokio::test]
async fn window_keeps_latest_complete_paragraph_suffix() {
    let (p, mut i, mut ts) = fixture();
    let body = "旧段落 alpha\n\n中间段落 beta\n\n最新段落 gamma\n\n尾段落 delta\n";
    fs::write(p.join("docs/early.md"), body).unwrap();
    i.documents.truncate(1);
    i.documents[0].keywords = vec!["不会命中".into()];
    ts[0].question = "窗口测试".into();
    ts[0].rules = vec!["保留完整段落".into()];
    let mut found = None;
    for budget in (100..=2000).step_by(100) {
        let r = run(&i, &ts[0], "window", &p, Some(budget)).await;
        if let Some(m) = r.messages.iter().find(|m| m.role == "tool") {
            if m.content.contains("最新段落 gamma")
                && m.content.contains("尾段落 delta")
                && !m.content.contains("旧段落 alpha")
            {
                found = Some(m.content.clone());
                break;
            }
        }
    }
    let content = found.expect("window must retain a complete latest suffix under a tight budget");
    assert!(!content.contains("中间段落 beta"));
    assert!(content.contains("最新段落 gamma\n\n尾段落 delta\n"));
}

#[tokio::test]
async fn retrieval_requires_body_and_unknown_query_is_empty() {
    let (p, mut i, mut ts) = fixture();
    ts[0].question = "zzqnomatch902 稀有词 传输方式".into();
    fs::write(p.join("docs/early.md"), "metadata-only\n").unwrap();
    fs::write(p.join("docs/other.md"), "正文稀有词\n传输方式：BODY\n").unwrap();
    i.documents[0].keywords = vec!["metadata-query".into()];
    i.documents[5].keywords = vec!["稀有词".into()];
    let r = run(&i, &ts[0], "retrieval", &p, None).await;
    assert!(r
        .answer
        .as_ref()
        .unwrap()
        .claims
        .iter()
        .any(|c| c.value == "BODY"));
    let retrieval_ops: Vec<_> = r
        .operations
        .iter()
        .filter(|x| x.get("type").and_then(|v| v.as_str()) == Some("retrieval"))
        .collect();
    assert!(!retrieval_ops.is_empty());
    let early_score = retrieval_ops
        .iter()
        .find(|x| x.get("source").and_then(|v| v.as_str()) == Some("early"))
        .and_then(|x| x.get("score"))
        .and_then(|v| v.as_u64())
        .unwrap();
    let other_score = retrieval_ops
        .iter()
        .find(|x| x.get("source").and_then(|v| v.as_str()) == Some("other"))
        .and_then(|x| x.get("score"))
        .and_then(|v| v.as_u64())
        .unwrap();
    assert!(
        early_score < other_score,
        "metadata-only document must not outrank body match"
    );
    assert!(other_score > early_score);
    assert!(r
        .operations
        .iter()
        .filter(|x| x.get("strategy").and_then(|v| v.as_str()) == Some("retrieval"))
        .all(|x| x.get("score").is_some()));
    let mut u = ts[3].clone();
    u.question = "zzqnomatch902".into();
    let r = run(&i, &u, "retrieval", &p, None).await;
    assert!(r.selected_sources.is_empty());
    let a = r.answer.unwrap();
    assert!(a.claims.is_empty() && a.insufficient_evidence);
    assert_eq!(r.quality, Some(1.0));
}

#[tokio::test]
async fn unknown_oracle_does_not_hide_real_throughput_fact() {
    let (p, mut i, mut ts) = fixture();
    fs::write(p.join("docs/latest.md"), "生产吞吐量：100 requests/s\n").unwrap();
    ts[3].question = "生产吞吐量是多少？".into();
    i.documents[1].keywords = vec!["生产".into(), "吞吐量".into()];
    let r = run(&i, &ts[3], "retrieval", &p, None).await;
    let a = r.answer.unwrap();
    assert!(!a.claims.is_empty(), "real fact must be parsed");
    assert!(!a.insufficient_evidence);
    assert_eq!(
        r.quality,
        Some(0.0),
        "unknown is an oracle scoring result, not a retrieval rule"
    );
}

#[tokio::test]
async fn node_faults_are_error_rows_with_real_records() {
    let (p, i, ts) = fixture();
    for m in ["invalid_json", "crash_after_invoke", "wrong_id"] {
        let r = run_one_with_executor(&i, &ts[0], "on-demand", &p, None, exec(&p, Some(m))).await;
        assert_eq!(r.status, "error", "{m}");
        assert!(r.answer.is_none() && r.model_calls == 0 && !r.call_records.is_empty());
        let c = r.call_records.last().unwrap();
        assert!(
            c.dispatched && c.reaped && c.child_pid.is_some(),
            "{m}: {c:?}"
        );
        assert!(c.terminal.is_some() || c.exit_code.is_some(), "{m}: {c:?}");
    }
}

#[test]
fn metadata_rejects_duplicate_and_escape() {
    let (_, mut i, ts) = fixture();
    i.documents[1].id = i.documents[0].id.clone();
    assert!(validate(&i, &Tasks { tasks: ts.clone() }, Path::new("/tmp")).is_err());
    let (_, mut i, ts) = fixture();
    i.documents[0].path = "../escape.md".into();
    assert!(validate(&i, &Tasks { tasks: ts }, Path::new("/tmp")).is_err());
}
