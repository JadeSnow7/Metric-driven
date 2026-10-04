import { mkdtemp, writeFile, mkdir } from 'node:fs/promises';
import { join } from 'node:path';
import assert from 'node:assert/strict';
const pkg = process.argv[2];
const rootPath = `/private/tmp/rein-ch05-review-20260914/reviewer-2/package-${pkg}`;
const {runAgentLoop} = await import(`${rootPath}/ts/src/rein/loop.ts`);
const {createOpenAIAdapter, createReplayAdapter} = await import(`${rootPath}/ts/src/rein/adapters.ts`);
const output:any[]=[];
const run = (adapter:any,root:string, limit?:number) => pkg==='17' ? runAgentLoop(adapter,[{role:'user',content:'查找 marker，读取所有命中文件后总结'}],{root},limit===undefined?{}:{maxRounds:limit}) : runAgentLoop(adapter,{root},'查找 marker，读取所有命中文件后总结',limit===undefined?{}:{maxTurns:limit});
const success=(r:any)=>pkg==='17'?r.ok:r.state==='completed';
const call=(id:string,name:string,args:any)=>({id,type:'function',function:{name,arguments:typeof args==='string'?args:JSON.stringify(args)}});
const response=(text:string|null, tool_calls:any[]=[])=>JSON.stringify({choices:[{message:{role:'assistant',content:text,tool_calls}}]});
function adapterFor(fn:any) { const requests:any[]=[]; const adapter=createOpenAIAdapter({baseUrl:'http://offline.invalid',apiKey:'review-placeholder',model:'offline-review'},{async send(req:any){const body=JSON.parse(req.body); requests.push(structuredClone(body)); return {status:200,statusText:'OK',headers:{},body:await fn(body,requests.length)};}});return {adapter,requests}; }
const base=await mkdtemp('/private/tmp/rein-ch05-review-evidence-2/ts-workspaces-');
for (const [label,contents] of [['A',{'a.txt':'marker: 蓝色 17','nested/b.txt':'marker: 山海 31'}],['B',{'changed.txt':'marker: 金色 29','other.md':'marker: 风声 47'}]] as const) {
 const root=join(base,label); await mkdir(root,{recursive:true});
 for(const [path,value] of Object.entries(contents)){await mkdir(join(root,path,'..'),{recursive:true}); await writeFile(join(root,path),value);}
 const model=adapterFor((body:any,n:number)=>{if(n===1)return response(null,[call('search-1','search_files',{needle:'marker'})]);if(n===2){const tool=body.messages.find((x:any)=>x.role==='tool');assert.equal(tool.tool_call_id,'search-1');const names=tool.content.split('\n');assert.deepEqual(names,Object.keys(contents).sort());return response('先读取搜索命中',names.map((p:string,i:number)=>call(`read-${i+1}`,'read_file',{path:p})));}const reads=body.messages.filter((m:any)=>m.role==='tool' && m.tool_call_id.startsWith('read-'));assert.deepEqual(reads.map((m:any)=>m.content),Object.keys(contents).sort().map(k=>contents[k]));return response(reads.map((m:any)=>m.content).join(' | '));});
 const result=await run(model.adapter,root); assert(success(result)); assert.equal(model.requests.length,3);assert.equal(result.answer,Object.keys(contents).sort().map(k=>contents[k]).join(' | '));output.push({test:'search_then_multi_read_'+label,status:'passed',root,requests:model.requests,result});
}
const root=join(base,'A');
for (const [label,calls,codes] of [['bad_tools',[call('unknown','no_such_tool',{}),call('args','read_file',{path:42}),call('missing','read_file',{path:'missing.md'}),call('directory','read_file',{path:'.'})],['unknown_tool','arguments_invalid','path_invalid','read_failed']]] as const){
 const m=adapterFor((body:any,n:number)=>{if(n===1)return response('pending',calls);const tools=body.messages.filter((x:any)=>x.role==='tool');assert.deepEqual(tools.map((x:any)=>x.tool_call_id),calls.map(c=>c.id));assert.deepEqual(tools.map((x:any)=>JSON.parse(x.content).error.code),codes);return response('已收到结构化失败，可继续');});
 const r=await run(m.adapter,root);assert(success(r));output.push({test:label,status:'passed',requests:m.requests,result:r});
}
const normal=adapterFor(()=>response('完成'));const normalResult=await run(normal.adapter,root);assert(success(normalResult));output.push({test:'normal_final',status:'passed',result:normalResult});
const empty=adapterFor(()=>response(' \n '));const emptyResult=await run(empty.adapter,root);assert.equal(emptyResult.reason,'empty_final');assert.equal(emptyResult.answer,undefined);output.push({test:'empty_final',status:'passed',result:emptyResult});
const failure=adapterFor((body:any,n:number)=>{if(n===1)return response(null,[call('read-before-error','read_file',{path:'a.txt'})]);throw new Error('review-model-failure');});const fr=await run(failure.adapter,root);assert.equal(fr.reason,'model_error');assert.equal(fr.answer,undefined);assert(fr.events.some((x:any)=>x.result));output.push({test:'model_failure_after_tool',status:'passed',requests:failure.requests,result:fr});
const repeat=adapterFor((body:any,n:number)=>response(null,[call(`repeat-${n}`,'read_file',{path:'a.txt'})]));const rr=await run(repeat.adapter,root);assert.equal(repeat.requests.length,32);assert.equal(rr.answer,undefined);output.push({test:'default_32_protection',status:'passed',request_count:repeat.requests.length,result:rr});
const cap=adapterFor((body:any,n:number)=>response(null,[call(`repeat-${n}`,'read_file',{path:'a.txt'})]));const cr=await run(cap.adapter,root,4);assert.equal(cap.requests.length,4);output.push({test:'explicit_4_cap',status:'passed',request_count:cap.requests.length,result:cr});
// An event-only recording must distinguish prompts and tool arguments to reconstruct requests.
async function eventProbe(needle:string){const m=adapterFor((body:any,n:number)=> n===1?response(null,[call('same-id','search_files',{needle})]):response('done'));const r=await run(m.adapter,root);return {events:r.events,requests:m.requests};}
const e1=await eventProbe('absent-query-A');const e2=await eventProbe('absent-query-B');output.push({test:'event_only_reconstruction_counterexample',status:'observed',events_equal:JSON.stringify(e1.events)===JSON.stringify(e2.events),requests_equal:JSON.stringify(e1.requests)===JSON.stringify(e2.requests),first:e1,second:e2});
console.log(JSON.stringify(output,null,2));
