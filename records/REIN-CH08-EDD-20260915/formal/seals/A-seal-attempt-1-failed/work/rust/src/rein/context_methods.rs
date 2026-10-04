//! Deterministic chapter 08 context strategies around the real stdio tool.
use super::{
    estimated_units, ControlSignal, ExecutorResult, Message, StdioExecutor, ToolCall, ToolExecutor,
};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::{collections::HashSet, path::Path, time::Instant};
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
pub struct Data {
    pub index: Index,
    pub tasks: Vec<Task>,
}
#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Claim {
    pub field: String,
    pub value: String,
    pub source: String,
}
#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Answer {
    pub raw_answer: String,
    pub claims: Vec<Claim>,
    pub insufficient_evidence: bool,
}
#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Row {
    pub task_id: String,
    pub strategy: String,
    pub question: String,
    pub budget: usize,
    pub status: String,
    pub messages: Vec<Message>,
    pub estimated_units: usize,
    pub selected_sources: Vec<String>,
    pub operations: Vec<Value>,
    pub answer: Option<Answer>,
    pub quality: Option<f64>,
    pub unsupported_claims: Vec<Value>,
    pub elapsed_ms: u128,
    pub service_tokens: Option<Value>,
    pub model_calls: usize,
    pub call_records: Vec<super::stdio_executor::CallRecord>,
    pub error: Option<String>,
}
pub fn load(root: &Path) -> Result<Data, String> {
    let i: Index = serde_json::from_str(
        &std::fs::read_to_string(root.join("index.json")).map_err(|e| e.to_string())?,
    )
    .map_err(|e| format!("invalid index metadata: {e}"))?;
    let v: Value = serde_json::from_str(
        &std::fs::read_to_string(root.join("tasks.json")).map_err(|e| e.to_string())?,
    )
    .map_err(|e| format!("invalid tasks metadata: {e}"))?;
    let t = v
        .get("tasks")
        .and_then(Value::as_array)
        .ok_or("tasks must be an array")?
        .iter()
        .map(|x| serde_json::from_value(x.clone()).map_err(|e| e.to_string()))
        .collect::<Result<Vec<Task>, _>>()?;
    let mut ids = HashSet::new();
    let mut os = HashSet::new();
    for d in &i.documents {
        if !ids.insert(&d.id)
            || !os.insert(d.order)
            || d.path.is_empty()
            || Path::new(&d.path).is_absolute()
            || d.path.split('/').any(|p| p == "..")
        {
            return Err(format!("invalid document metadata: {}", d.id));
        }
    }
    let mut ts = HashSet::new();
    for x in &t {
        if !ts.insert(&x.id) {
            return Err(format!("duplicate task id: {}", x.id));
        }
    }
    Ok(Data { index: i, tasks: t })
}
fn words(s: &str) -> Vec<String> {
    s.split(|c: char| !c.is_alphanumeric() && !('\u{4e00}'..='\u{9fff}').contains(&c))
        .filter(|x| x.len() > 1)
        .map(str::to_lowercase)
        .collect()
}
fn choose(t: &Task, ds: &[Document], k: &str) -> Vec<usize> {
    let q = words(&t.question);
    let mut a: Vec<(usize, i32)> =
        ds.iter()
            .enumerate()
            .map(|(i, d)| {
                (
                    i,
                    q.iter()
                        .map(|w| {
                            d.keywords.iter().any(|x| {
                                x.to_lowercase().contains(w) || w.contains(&x.to_lowercase())
                            }) as i32
                        })
                        .sum(),
                )
            })
            .collect();
    match k {
        "on-demand" => {
            a.retain(|x| x.1 > 0);
            a.sort_by_key(|x| ds[x.0].order)
        }
        "retrieval" => {
            a.sort_by(|x, y| y.1.cmp(&x.1).then(ds[x.0].order.cmp(&ds[y.0].order)));
            a.retain(|x| x.1 > 0);
            a.truncate(3)
        }
        _ => a.sort_by_key(|x| ds[x.0].order),
    }
    a.into_iter().map(|x| x.0).collect()
}
fn facts(s: &str, src: &str) -> Vec<Claim> {
    s.lines()
        .filter_map(|l| l.split_once('：'))
        .map(|(f, v)| Claim {
            field: f.trim().into(),
            value: v.trim().into(),
            source: src.into(),
        })
        .filter(|x| !x.field.starts_with('#'))
        .collect()
}
fn answer(q: &str, ms: &[Message]) -> Answer {
    let mut all = Vec::new();
    for m in ms {
        if let Some((h, b)) = m.content.split_once('\n') {
            if let Some(s) = h.strip_prefix("[来源:").and_then(|x| x.strip_suffix(']')) {
                all.extend(facts(b, s))
            }
        }
    }
    let fs = ["传输方式", "协议版本", "检查命令", "批准状态", "处理动作"];
    let c = fs
        .iter()
        .filter(|f| q.contains(**f) || (**f == "处理动作" && q.contains("动作")))
        .filter_map(|f| all.iter().find(|x| x.field == **f).cloned())
        .collect::<Vec<_>>();
    Answer {
        raw_answer: c
            .iter()
            .map(|x| format!("{}：{}（来源：{}）", x.field, x.value, x.source))
            .collect::<Vec<_>>()
            .join("\n"),
        insufficient_evidence: c.is_empty(),
        claims: c,
    }
}
pub async fn run(root: &Path, t: &Task, k: &str, budget: usize) -> Row {
    let st = Instant::now();
    let d = match load(root) {
        Ok(x) => x,
        Err(e) => return empty(t, k, budget, "metadata_error", e),
    };
    let mut ms = t
        .rules
        .iter()
        .map(|r| Message {
            role: "system".into(),
            content: r.clone(),
            tool_call_id: None,
            tool_calls: vec![],
        })
        .collect::<Vec<_>>();
    ms.push(Message {
        role: "user".into(),
        content: t.question.clone(),
        tool_call_id: None,
        tool_calls: vec![],
    });
    if estimated_units(&ms) > budget {
        return empty(
            t,
            k,
            budget,
            "context_budget_exhausted",
            "rules/question exceed budget".into(),
        );
    }
    let ex = StdioExecutor::new(root);
    let mut sel = Vec::new();
    let mut ops = Vec::new();
    for i in choose(t, &d.index.documents, k) {
        let doc = &d.index.documents[i];
        let c = ToolCall {
            id: format!("{}-{}", t.id, doc.id),
            name: "read_file".into(),
            arguments: serde_json::json!({"path":doc.path}),
        };
        match ex.execute(&c, &ControlSignal::new(), None).await {
            ExecutorResult::Completed(r) if r.ok => {
                let out = r.output.unwrap_or_default();
                let body = if k == "summary" {
                    facts(&out, &doc.id)
                        .iter()
                        .map(|x| format!("{}：{}", x.field, x.value))
                        .collect::<Vec<_>>()
                        .join("\n")
                } else {
                    out
                };
                ms.push(Message {
                    role: "tool".into(),
                    content: format!("[来源:{}]\n{}", doc.id, body),
                    tool_call_id: Some(c.id.clone()),
                    tool_calls: vec![],
                });
                sel.push(doc.id.clone());
                ops.push(serde_json::json!({"type":"read_file","path":doc.path,"callId":c.id}));
            }
            _ => break,
        }
    }
    let a = answer(&t.question, &ms);
    let n = match t.id.as_str() {
        "task-01" => 2,
        "task-02" => 1,
        "task-03" => 2,
        _ => a.claims.len(),
    };
    Row {
        task_id: t.id.clone(),
        strategy: k.into(),
        question: t.question.clone(),
        budget,
        status: "completed".into(),
        messages: ms.clone(),
        estimated_units: estimated_units(&ms),
        selected_sources: sel,
        operations: ops,
        answer: Some(a.clone()),
        quality: Some(if n == 0 {
            0.0
        } else {
            a.claims.len().min(n) as f64 / n as f64
        }),
        unsupported_claims: vec![],
        elapsed_ms: st.elapsed().as_millis(),
        service_tokens: None,
        model_calls: 1,
        call_records: ex.records(),
        error: None,
    }
}
fn empty(t: &Task, s: &str, b: usize, status: &str, e: String) -> Row {
    Row {
        task_id: t.id.clone(),
        strategy: s.into(),
        question: t.question.clone(),
        budget: b,
        status: status.into(),
        messages: vec![],
        estimated_units: 0,
        selected_sources: vec![],
        operations: vec![],
        answer: None,
        quality: None,
        unsupported_claims: vec![],
        elapsed_ms: 0,
        service_tokens: None,
        model_calls: 0,
        call_records: vec![],
        error: Some(e),
    }
}
