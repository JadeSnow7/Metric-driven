
use rein_ch01_helloworld::rein::*;
use serde_json::{json,Value};
use std::{future::Future,pin::Pin,sync::Mutex,path::PathBuf};
struct Probe {mode:String,received:Mutex<Vec<Value>>}
fn tool(id:&str,name:&str,args:Value)->Value {json!({"id":id,"type":"function","function":{"name":name,"arguments":args.to_string()}})}
fn response(text:String,calls:Vec<Value>)->String {json!({"choices":[{"message":{"role":"assistant","content":text,"tool_calls":calls}}]}).to_string()}
impl Probe {
 fn next(&self,messages:Value,tools:Value)->Result<String,ToolError>{
  let mut received=self.received.lock().unwrap();received.push(json!({"messages":messages,"tools":tools}));let n=received.len();
  let final_ = |s:&str| Ok(response(s.into(),vec![]));
  let calls = |v:Vec<Value>| Ok(response("".into(),v));
  match self.mode.as_str(){
   "search"=>match n{1=>calls(vec![tool("search","search_files",json!({"needle":"needle"}))]),2=>calls(messages.as_array().unwrap().last().unwrap()["content"].as_str().unwrap().split('\n').enumerate().map(|(i,path)|tool(&format!("read-{i}"),"read_file",json!({"path":path}))).collect()),_=>final_(&messages.as_array().unwrap().iter().filter(|m|m["role"]=="tool").skip(1).map(|m|m["content"].as_str().unwrap()).collect::<Vec<_>>().join("|"))},
   "failures"=>if n==1 {calls(vec![tool("unknown","no_such_tool",json!({})),tool("invalid","read_file",json!({"path":9})),tool("missing","read_file",json!({"path":"missing.md"}))])}else{final_("feedback received")},
   "error"=>if n==1{calls(vec![tool("before-error","read_file",json!({"path":"AZURE-a.txt"}))])}else{Err(ToolError{code:"network".into(),message:"probe network down".into()})},
   "empty"=>final_(" \n "),"normal"=>final_("normal"),
   "limit"=>calls(vec![tool(&format!("repeat-{n}"),"no_such_tool",json!({}))]),
   path=>if n==1{calls(vec![tool("read","read_file",json!({"path":path}))])}else{final_("done")}
  }
 }
}

impl OpenAiHttp for Probe {fn post<'a>(&'a self,_url:&'a str,_key:&'a str,body:Value)->Pin<Box<dyn Future<Output=Result<String,ToolError>>+Send+'a>> {let result=self.next(body["messages"].clone(),body["tools"].clone());Box::pin(async move{result})}}
async fn run(mode:&str,root:PathBuf,limit:usize)->(Value,Value){let p=Probe{mode:mode.into(),received:Mutex::new(vec![])};let r=run_agent_loop(&p,"offline://replay","offline","probe",&Workspace{root},"inspect",limit).await;let received=json!(*p.received.lock().unwrap());(serde_json::to_value(r).unwrap(),received)}

#[tokio::main]
async fn main(){
 let base=PathBuf::from("/private/tmp/rein-ch05-production-rereview-1").join(format!("rust-ws-{}",std::process::id()));std::fs::create_dir_all(&base).unwrap();
 let mut evidence=json!({"cases":{},"checks":{}});
 for variant in ["AZURE","OCHRE"]{
  let root=base.join(variant);std::fs::create_dir_all(&root).unwrap();for suffix in ["a","b"]{std::fs::write(root.join(format!("{variant}-{suffix}.txt")),format!("needle {variant} {suffix}")).unwrap()}
  let (result,received)=run("search",root,32).await;
  evidence["checks"][format!("{variant}-real-search-read-next-request")]=json!(if result["answer"]==format!("needle {variant} a|needle {variant} b")&&received.as_array().unwrap().len()==3{"passed"}else{"failed"});
  evidence["cases"][variant]=json!({"result":result,"received":received});
 }
 let root=base.join("AZURE");
 for mode in ["failures","error","empty","normal","limit"]{let (result,received)=run(mode,root.clone(),32).await;evidence["cases"][mode]=json!({"result":result,"received":received});}
 for file in ["same-a.txt","same-b.txt"]{std::fs::write(root.join(file),"identical").unwrap();let(result,received)=run(file,root.clone(),32).await;evidence["cases"][file]=json!({"result":result,"received":received});}
 evidence["checks"]["events-retain-call-inputs"]=json!(if evidence["cases"]["same-a.txt"]["result"]["events"]==evidence["cases"]["same-b.txt"]["result"]["events"]{"failed"}else{"passed"});
 println!("{}",serde_json::to_string_pretty(&evidence).unwrap());
}
