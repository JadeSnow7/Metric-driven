from pathlib import Path
root=Path('/private/tmp/rein-ch05-review-evidence-2')
source=r'''
use product::rein::*;
use serde_json::{json,Value};
use std::{future::Future,pin::Pin,sync::Mutex,path::PathBuf};
struct Fake { mode: String, requests: Mutex<Vec<Value>> }
impl Fake { fn new(mode:&str)->Self { Self {mode:mode.into(),requests:Mutex::new(vec![])} } }
fn call(id:&str,name:&str,args:Value)->Value { json!({"id":id,"type":"function","function":{"name":name,"arguments":args.to_string()}}) }
fn response(text:&str,calls:Vec<Value>)->String { json!({"choices":[{"message":{"role":"assistant","content":text,"tool_calls":calls}}]}).to_string() }
impl OpenAiHttp for Fake {
 fn post<'a>(&'a self,_:&'a str,_:&'a str,body:Value)->Pin<Box<dyn Future<Output=Result<String,ToolError>>+Send+'a>> {
  let mut requests=self.requests.lock().unwrap(); requests.push(body.clone()); let n=requests.len();
  let toolmessages:Vec<_>=body["messages"].as_array().unwrap().iter().filter(|v|v["role"]=="tool").collect();
  let result=match self.mode.as_str() {
   "search"=>if n==1 {Ok(response("",vec![call("search-1","search_files",json!({"needle":"marker"}))]))} else if n==2 {let names=toolmessages[0]["content"].as_str().unwrap(); Ok(response("先读搜索命中",names.split('\n').enumerate().map(|(i,p)|call(&format!("read-{}",i+1),"read_file",json!({"path":p}))).collect()))} else { Ok(response(&toolmessages.iter().filter(|m|m["tool_call_id"].as_str().unwrap().starts_with("read-")).map(|m|m["content"].as_str().unwrap()).collect::<Vec<_>>().join(" | "),vec![]))},
   "errors"=>if n==1{Ok(response("pending",vec![call("unknown","no_such_tool",json!({})),call("args","read_file",json!({"path":42})),call("missing","read_file",json!({"path":"missing.md"})),call("directory","read_file",json!({"path":"."}))]))}else {let codes:Vec<String>=toolmessages.iter().map(|m|serde_json::from_str::<Value>(m["content"].as_str().unwrap()).unwrap()["error"]["code"].as_str().unwrap().to_owned()).collect(); assert_eq!(codes,vec!["unknown_tool","arguments_invalid","path_invalid","read_failed"]);Ok(response("已收到结构化失败，可继续",vec![]))},
   "empty"=>Ok(response(" \n ",vec![])),
   "model_error"=>if n==1{Ok(response("",vec![call("read-before-error","read_file",json!({"path":"a.txt"}))]))}else{Err(ToolError {code:"review_model_failure".into(),message:"review model failed".into()})},
   "repeat"=>Ok(response("",vec![call(&format!("repeat-{n}"),"read_file",json!({"path":"a.txt"}))])),
   s if s.starts_with("event-")=>if n==1{Ok(response("",vec![call("same-id","search_files",json!({"needle":s}))]))}else{Ok(response("done",vec![]))},
   _=>Ok(response("完成",vec![]))
  };
  Box::pin(async move{result})
 }
}
#[cfg(feature="p17")]
struct Bridge<'a>(&'a Fake);
#[cfg(feature="p17")]
impl LoopAdapter for Bridge<'_>{
 fn complete<'a>(&'a mut self,messages:&'a[Message],tools:&'a[ToolDefinition])->Pin<Box<dyn Future<Output=Result<ModelTurn,ToolError>>+Send+'a>> { Box::pin(async move {openai_complete(self.0,"http://offline.invalid","review-placeholder","offline-review",messages,tools).await}) }
}
async fn run(fake:&Fake,root:PathBuf,limit:usize)->Value {
 #[cfg(feature="p17")]
 let r={
  let tools=vec![ToolDefinition {name:"search_files".into(),description:"搜索文本文件".into(),input_schema:json!({"type":"object"})},ToolDefinition{name:"read_file".into(),description:"读取文本文件".into(),input_schema:json!({"type":"object"})}];
  run_agent_loop(&mut Bridge(fake),&[Message {role:"user".into(),content:"查找 marker 并读取所有命中文件".into(),tool_call_id:None,tool_calls:vec![]}],&Workspace{root},&tools,limit).await
 };
 #[cfg(not(feature="p17"))]
 let r=run_agent_loop(fake,"http://offline.invalid","review-placeholder","offline-review",&Workspace{root},"查找 marker 并读取所有命中文件",limit).await;
 #[cfg(feature="p17")]
 let result=json!({"ok":r.ok,"answer":r.answer,"reason":r.reason,"messages":r.messages,"events":r.events});
 #[cfg(not(feature="p17"))]
 let result=serde_json::to_value(r).unwrap();
 result
}
#[tokio::main]
async fn main(){
 let base=PathBuf::from(format!("/private/tmp/rein-ch05-review-evidence-2/rust-workspaces-{}",std::process::id()));
 let mut output=vec![];
 for (label,files) in [("A",vec![("a.txt","marker: 蓝色 17"),("nested/b.txt","marker: 山海 31")]),("B",vec![("changed.txt","marker: 金色 29"),("other.md","marker: 风声 47")])]{
  let root=base.join(label);std::fs::create_dir_all(&root).unwrap();for (p,text) in &files {std::fs::create_dir_all(root.join(p).parent().unwrap()).unwrap();std::fs::write(root.join(p),text).unwrap();}
  let fake=Fake::new("search");let result=run(&fake,root.clone(),32).await;let requests=fake.requests.lock().unwrap().clone();assert_eq!(requests.len(),3);assert_eq!(result["answer"],files.iter().map(|(_,t)|*t).collect::<Vec<_>>().join(" | "));
  let tools:Vec<_>=requests[2]["messages"].as_array().unwrap().iter().filter(|m|m["role"]=="tool").collect();assert_eq!(tools.iter().map(|m|m["tool_call_id"].as_str().unwrap()).collect::<Vec<_>>(),vec!["search-1","read-1","read-2"]);
  output.push(json!({"test":format!("search_then_multi_read_{label}"),"status":"passed","root":root,"requests":requests,"result":result}));
 }
 let root=base.join("A");
 for mode in ["normal","errors","empty","model_error","repeat"] {let fake=Fake::new(mode);let result=run(&fake,root.clone(),32).await; let requests=fake.requests.lock().unwrap().clone();if mode=="empty" || mode=="model_error" || mode=="repeat" {assert!(result["answer"].is_null());}if mode=="repeat"{assert_eq!(requests.len(),32);}if mode=="model_error" {assert_eq!(requests.len(),2);assert!(result["events"].as_array().unwrap().iter().any(|e|!e["result"].is_null()));}output.push(json!({"test":mode,"status":"passed","request_count":requests.len(),"requests":requests,"result":result}));}
 let fake=Fake::new("repeat");let result=run(&fake,root.clone(),4).await;assert_eq!(fake.requests.lock().unwrap().len(),4);output.push(json!({"test":"explicit_4_cap","status":"passed","request_count":4,"result":result}));
 let a=Fake::new("event-A");let ar=run(&a,root.clone(),32).await;let b=Fake::new("event-B");let br=run(&b,root.clone(),32).await;
 output.push(json!({"test":"event_only_reconstruction_counterexample","events_equal":ar["events"]==br["events"],"requests_equal":*a.requests.lock().unwrap()==*b.requests.lock().unwrap(),"first":{"result":ar,"requests":*a.requests.lock().unwrap()},"second":{"result":br,"requests":*b.requests.lock().unwrap()}}));
 println!("{}",serde_json::to_string_pretty(&output).unwrap());
}
'''
for p in ['17','42']:
 d=root/('rust-probe-'+p);(d/'src').mkdir(parents=True,exist_ok=True)
 (d/'Cargo.toml').write_text('[package]\nname = "review-probe-'+p+'"\nversion = "0.1.0"\nedition = "2021"\n[features]\np17 = []\n[dependencies]\nproduct = { package = "rein-ch01-helloworld", path = "/private/tmp/rein-ch05-review-20260914/reviewer-2/package-'+p+'/rust" }\nserde_json = "1"\ntokio = { version = "1", features = ["macros", "rt-multi-thread"] }\n')
 (d/'src/main.rs').write_text(source)
