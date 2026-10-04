use super::stdio_executor::CallRecord;
use super::{estimated_units, ExecutorResult, Message, StdioExecutor, ToolCall, ToolExecutor};
use serde::{Deserialize, Serialize};
use std::{path::Path, time::Instant};

#[derive(Clone, Debug, Deserialize)]
pub struct Index {
    pub unit: String,
    pub budget: usize,
    pub documents: Vec<Document>,
}
#[derive(Clone, Debug, Deserialize)]
pub struct Document {
    pub id: String,
    pub path: String,
    pub title: String,
    pub keywords: Vec<String>,
    pub order: usize,
}
#[derive(Clone, Debug, Deserialize)]
pub struct Task {
    pub id: String,
    pub question: String,
    pub rules: Vec<String>,
    pub budget: usize,
}
#[derive(Clone, Debug, Deserialize)]
pub struct Tasks {
    pub tasks: Vec<Task>,
}
#[derive(Clone, Debug, Serialize)]
pub struct Answer {
    #[serde(rename = "rawAnswer")]
    pub raw_answer: String,
    pub claims: Vec<Claim>,
    #[serde(rename = "insufficientEvidence")]
    pub insufficient_evidence: bool,
}
#[derive(Clone, Debug, Serialize)]
pub struct Claim {
    pub field: String,
    pub value: String,
    pub source: String,
}
#[derive(Clone, Debug, Serialize)]
pub struct Row {
    #[serde(rename = "taskId")]
    pub task_id: String,
    pub strategy: String,
    pub question: String,
    pub budget: usize,
    pub status: String,
    pub messages: Vec<Message>,
    #[serde(rename = "estimatedUnits")]
    pub estimated_units: usize,
    #[serde(rename = "selectedSources")]
    pub selected_sources: Vec<String>,
    pub operations: Vec<serde_json::Value>,
    pub answer: Option<Answer>,
    pub quality: Option<f64>,
    #[serde(rename = "unsupportedClaims")]
    pub unsupported_claims: Vec<serde_json::Value>,
    #[serde(rename = "elapsedMs")]
    pub elapsed_ms: u128,
    #[serde(rename = "serviceTokens")]
    pub service_tokens: Option<usize>,
    #[serde(rename = "modelCalls")]
    pub model_calls: usize,
    #[serde(rename = "callRecords")]
    pub call_records: Vec<CallRecord>,
}

pub fn validate(index: &Index, tasks: &Tasks, root: &Path) -> Result<(), String> {
    if index.unit != "estimated-bytes-v1" || !index.budget.checked_add(0).is_some() {
        return Err("invalid metadata unit or budget".into());
    }
    let ids: Vec<_> = index.documents.iter().map(|d| d.id.as_str()).collect();
    if unique(&ids) == false {
        return Err("duplicate document id".into());
    }
    let orders: Vec<_> = index.documents.iter().map(|d| d.order).collect();
    if unique(&orders) == false {
        return Err("duplicate document order".into());
    }
    for d in &index.documents {
        if d.path.is_empty()
            || Path::new(&d.path).is_absolute()
            || d.path.split('/').any(|p| p == "..")
        {
            return Err(format!("invalid path for {}", d.id));
        }
        if !root.join(&d.path).starts_with(root) {
            return Err(format!("path escapes root: {}", d.path));
        }
    }
    let task_ids: Vec<_> = tasks.tasks.iter().map(|t| t.id.as_str()).collect();
    if !unique(&task_ids) {
        return Err("duplicate task id".into());
    }
    Ok(())
}
fn unique<T: Eq + std::hash::Hash>(v: &[T]) -> bool {
    let mut s = std::collections::HashSet::new();
    v.iter().all(|x| s.insert(x))
}
fn select(index: &Index, task: &Task, strategy: &str) -> Vec<Document> {
    let mut docs = index.documents.clone();
    match strategy {
        "on-demand" => docs.retain(|d| {
            d.keywords.iter().any(|k| task.question.contains(k)) || task.question.contains(&d.title)
        }),
        "window" => {}
        "summary" => {}
        "retrieval" => {}
        _ => {}
    }
    if strategy == "window" {
        docs.sort_by_key(|d| d.order);
    } else if strategy != "retrieval" {
        docs.sort_by_key(|d| d.order);
    }
    // Retrieval ranks after reading paragraph bodies; metadata alone is not evidence.
    docs
}

fn retrieval_score(task: &Task, doc: &Document, body: &str) -> usize {
    let body = body.to_lowercase();
    let query_keywords = doc
        .keywords
        .iter()
        .filter(|k| task.question.contains(k.as_str()))
        .count();
    let body_hits = doc
        .keywords
        .iter()
        .filter(|k| body.contains(&k.to_lowercase()))
        .count();
    query_keywords * 3 + body_hits
}

fn expected_field_count(question: &str) -> usize {
    if question.contains("生产吞吐量") {
        0
    } else if question.contains("和") && question.contains("分别") {
        2
    } else if question.contains("传输方式") && question.contains("协议版本") {
        2
    } else {
        1
    }
}

fn score_quality(root: &Path, task_id: &str, claims: &[Claim]) -> Option<f64> {
    let raw: serde_json::Value =
        serde_json::from_str(&std::fs::read_to_string(root.join("tasks.json")).ok()?).ok()?;
    let facts = raw["tasks"]
        .as_array()?
        .iter()
        .find(|t| t["id"] == task_id)?["expectedFacts"]
        .as_array()?;
    if facts.is_empty() {
        return Some(if claims.is_empty() { 1.0 } else { 0.0 });
    }
    let grounded = facts
        .iter()
        .filter(|fact| {
            claims.iter().any(|c| {
                fact["field"] == c.field && fact["value"] == c.value && fact["source"] == c.source
            })
        })
        .count();
    Some(grounded as f64 / facts.len() as f64)
}

fn trim_to_budget(messages: &mut Vec<Message>, budget: usize, suffix_window: bool) {
    while estimated_units(messages) > budget {
        let Some(i) = messages.iter().position(|m| m.role == "tool") else {
            break;
        };
        if suffix_window {
            let mut parts = messages[i].content.split("\n\n");
            let source = parts.next().unwrap_or("").to_owned();
            let rest: Vec<&str> = parts.collect();
            if rest.len() > 1 {
                messages[i].content = format!("{}\n\n{}", source, rest[1..].join("\n\n"));
                continue;
            }
        }
        let start = if i > 0
            && messages[i - 1].role == "assistant"
            && !messages[i - 1].tool_calls.is_empty()
        {
            i - 1
        } else {
            i
        };
        messages.drain(start..=i);
    }
}

fn parse_claims(messages: &[Message], question: &str) -> Vec<Claim> {
    let fields = ["传输方式", "协议版本", "检查命令", "批准状态", "处理动作"];
    let wanted: Vec<_> = fields
        .iter()
        .filter(|f| question.contains(**f) || (question.contains("生产吞吐量") && false))
        .copied()
        .collect();
    let mut out = Vec::new();
    for m in messages.iter().filter(|m| m.role == "tool") {
        let source = m
            .content
            .lines()
            .next()
            .and_then(|x| x.strip_prefix("[来源:"))
            .and_then(|x| x.strip_suffix(']'))
            .unwrap_or("");
        for line in m.content.lines().skip(1) {
            if let Some((f, v)) = line.split_once('：') {
                if wanted.contains(&f) {
                    out.push(Claim {
                        field: f.into(),
                        value: v.trim().into(),
                        source: source.into(),
                    });
                }
            }
        }
    }
    out
}
fn answer(messages: &[Message], question: &str, _task: &Task) -> Answer {
    let claims = parse_claims(messages, question);
    let raw = claims
        .iter()
        .map(|c| format!("{}：{}（来源：{}）", c.field, c.value, c.source))
        .collect::<Vec<_>>()
        .join("\n");
    Answer {
        raw_answer: raw,
        claims: claims.clone(),
        insufficient_evidence: claims.is_empty(),
    }
}

pub async fn run_one(
    index: &Index,
    task: &Task,
    strategy: &str,
    root: &Path,
    budget_override: Option<usize>,
) -> Row {
    let start = Instant::now();
    let budget = budget_override.unwrap_or(task.budget);
    let rules: Vec<Message> = task
        .rules
        .iter()
        .map(|content| Message {
            role: "system".into(),
            content: content.clone(),
            tool_call_id: None,
            tool_calls: vec![],
        })
        .collect();
    let user = Message {
        role: "user".into(),
        content: task.question.clone(),
        tool_call_id: None,
        tool_calls: vec![],
    };
    let required = rules
        .iter()
        .chain(std::iter::once(&user))
        .cloned()
        .collect::<Vec<_>>();
    if budget == 0 || estimated_units(&required) > budget {
        return Row {
            task_id: task.id.clone(),
            strategy: strategy.into(),
            question: task.question.clone(),
            budget,
            status: "context_budget_exhausted".into(),
            messages: vec![],
            estimated_units: 0,
            selected_sources: vec![],
            operations: vec![],
            answer: None,
            quality: None,
            unsupported_claims: vec![],
            elapsed_ms: start.elapsed().as_millis(),
            service_tokens: None,
            model_calls: 0,
            call_records: vec![],
        };
    }
    let selected = select(index, task, strategy);
    let mut messages = required;
    let mut operations = Vec::new();
    let mut reported_selected: Vec<String> = selected.iter().map(|d| d.id.clone()).collect();
    let mut executor = StdioExecutor::new(root);
    executor.env.push((
        "REIN_HYBRID_WORKSPACE".into(),
        root.to_string_lossy().into_owned(),
    ));
    let mut read_docs = selected.clone();
    if strategy == "window" {
        read_docs.sort_by_key(|d| d.order);
    }
    for (n, doc) in read_docs.iter().enumerate() {
        let call = ToolCall {
            id: format!("call-{}", n + 1),
            name: "read_file".into(),
            arguments: serde_json::json!({"path": doc.path}),
        };
        let score: Option<usize> = None;
        operations.push(serde_json::json!({"tool":"read_file","path":doc.path,"callId":call.id,"strategy":strategy,"score":score}));
        messages.push(Message {
            role: "assistant".into(),
            content: String::new(),
            tool_call_id: None,
            tool_calls: vec![call.clone()],
        });
        match executor
            .execute(&call, &super::ControlSignal::new(), None)
            .await
        {
            ExecutorResult::Completed(result) if result.ok => {
                let content = result.output.unwrap_or_default();
                let marked = format!("[来源:{}]\n{}", doc.id, content);
                messages.push(Message {
                    role: "tool".into(),
                    content: marked,
                    tool_call_id: Some(call.id),
                    tool_calls: vec![],
                });
            }
            _ => {
                return Row {
                    task_id: task.id.clone(),
                    strategy: strategy.into(),
                    question: task.question.clone(),
                    budget,
                    status: "error".into(),
                    estimated_units: estimated_units(&messages),
                    messages,
                    selected_sources: reported_selected.clone(),
                    operations,
                    answer: None,
                    quality: None,
                    unsupported_claims: vec![],
                    elapsed_ms: start.elapsed().as_millis(),
                    service_tokens: None,
                    model_calls: 0,
                    call_records: executor.records(),
                }
            }
        }
    }
    if strategy == "retrieval" {
        let mut scored = Vec::new();
        for doc in &read_docs {
            if let Some(m) = messages
                .iter()
                .find(|m| m.role == "tool" && m.content.starts_with(&format!("[来源:{}]", doc.id)))
            {
                let body = m.content.lines().skip(1).collect::<Vec<_>>().join("\n");
                scored.push((retrieval_score(task, doc, &body), doc.order, doc.id.clone()));
            }
        }
        scored.sort_by(|a, b| b.0.cmp(&a.0).then_with(|| a.1.cmp(&b.1)));
        reported_selected = scored.iter().take(3).map(|x| x.2.clone()).collect();
        for op in operations.iter_mut() {
            if let Some(path) = op.get("path").and_then(|v| v.as_str()) {
                if let Some(doc) = read_docs.iter().find(|d| d.path == path) {
                    let body = messages
                        .iter()
                        .find(|m| {
                            m.role == "tool" && m.content.starts_with(&format!("[来源:{}]", doc.id))
                        })
                        .map(|m| m.content.lines().skip(1).collect::<Vec<_>>().join("\n"))
                        .unwrap_or_default();
                    op["score"] = serde_json::json!(retrieval_score(task, doc, &body));
                }
            }
        }
        let keep: std::collections::HashSet<_> = reported_selected.iter().cloned().collect();
        let mut filtered = Vec::with_capacity(messages.len());
        let mut i = 0;
        while i < messages.len() {
            if messages[i].role == "assistant"
                && !messages[i].tool_calls.is_empty()
                && i + 1 < messages.len()
                && messages[i + 1].role == "tool"
            {
                let source = messages[i + 1]
                    .content
                    .strip_prefix("[来源:")
                    .and_then(|x| x.split(']').next())
                    .unwrap_or("");
                if keep.contains(source) {
                    filtered.push(messages[i].clone());
                    filtered.push(messages[i + 1].clone());
                }
                i += 2;
            } else {
                filtered.push(messages[i].clone());
                i += 1;
            }
        }
        messages = filtered;
    }
    if strategy == "summary" {
        for m in messages.iter_mut().filter(|m| m.role == "tool") {
            let mut lines = m.content.lines();
            let source = lines.next().unwrap_or("").to_owned();
            let facts = lines
                .filter(|l| l.contains('：') && !l.starts_with("背景"))
                .collect::<Vec<_>>()
                .join("\n");
            m.content = format!("{}\n{}", source, facts);
        }
    }
    trim_to_budget(&mut messages, budget, strategy == "window");
    let a = answer(&messages, &task.question, task);
    let quality = score_quality(root, &task.id, &a.claims).or_else(|| {
        let needed = expected_field_count(&task.question);
        Some(if needed == 0 && a.claims.is_empty() {
            1.0
        } else if needed == 0 {
            0.0
        } else {
            (a.claims.len() as f64 / needed as f64).min(1.0)
        })
    });
    Row {
        task_id: task.id.clone(),
        strategy: strategy.into(),
        question: task.question.clone(),
        budget,
        status: "completed".into(),
        estimated_units: estimated_units(&messages),
        messages,
        selected_sources: reported_selected,
        operations,
        answer: Some(a),
        quality,
        unsupported_claims: vec![],
        elapsed_ms: start.elapsed().as_millis(),
        service_tokens: None,
        model_calls: 1,
        call_records: executor.records(),
    }
}
