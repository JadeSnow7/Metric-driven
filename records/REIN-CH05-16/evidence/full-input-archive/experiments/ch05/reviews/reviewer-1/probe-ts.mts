import {mkdtemp,writeFile,mkdir} from 'node:fs/promises'
import {join} from 'node:path'
import assert from 'node:assert/strict'
const [pkg,label]=process.argv.slice(2)
const {runAgentLoop}=await import(`${pkg}/ts/src/rein/loop.ts`)
const run=(adapter:any,root:string,opts:any={})=>label==='p17'?runAgentLoop(adapter,[{role:'user',content:'inspect current workspace'}],{root},opts):runAgentLoop(adapter,{root},'inspect current workspace',opts)
const final=(text:string,calls:any[]=[])=>({message:{role:'assistant',content:text,toolCalls:calls},toolCalls:calls})
const call=(id:string,name:string,args:any)=>({id,name,arguments:args})
const evidence:any={package:label,checks:{}}
const expect=(key:string,fn:()=>any)=>{try{fn();evidence.checks[key]='passed'}catch(e){evidence.checks[key]='failed';evidence[key+'Error']=String(e)}}
const roots=[]
for(const variant of ['AZURE','OCHRE']){
 const root=await mkdtemp('/private/tmp/rein-ch05-review-evidence-1/ts-ws-');roots.push(root)
 await writeFile(join(root,variant+'-a.txt'),`needle ${variant} apples`);await writeFile(join(root,variant+'-b.txt'),`needle ${variant} books`)
 let count=0; const received:any[]=[]
 const adapter={async complete(messages:any,tools:any){count++;received.push(structuredClone({messages,tools}));if(count===1)return final('',[call('search','search_files',{needle:'needle'})]);if(count===2){const names=messages.at(-1).content.split('\n');return final('',names.map((path:string,i:number)=>call('read-'+i,'read_file',{path})))} return final(messages.filter((m:any)=>m.role==='tool'&&m.toolCallId.startsWith('read-')).map((m:any)=>m.content).join('|'))}}
 const result=await run(adapter,root);evidence[variant]={root,received,result}
 expect(variant+'-real-search-read-next-request',()=>{assert.equal(count,3);assert.equal(result.answer,`needle ${variant} apples|needle ${variant} books`);assert.deepEqual(received[2].messages.filter((m:any)=>m.role==='tool').map((m:any)=>m.toolCallId),['search','read-0','read-1']);assert.equal(result.events.filter((e:any)=>e.type==='tool'||e.type==='tool_result').length,3)})
}
const root=roots[0]
const calls=[call('unknown','no_such_tool',{}),call('invalid','read_file',{path:9}),call('missing','read_file',{path:'missing.md'})]
let failureRequests:any[]=[]
const failure=await run({async complete(m:any){failureRequests.push(structuredClone(m));return failureRequests.length===1?final('',calls):final('feedback received')}},root)
evidence.failures={requests:failureRequests,result:failure}
expect('structured-tool-failure-feedback',()=>{assert.deepEqual(failureRequests[1].filter((m:any)=>m.role==='tool').map((m:any)=>JSON.parse(m.content).error.code),['unknown_tool','arguments_invalid','path_invalid']);assert.equal(failure.answer,'feedback received')})
let errRounds=0;const modelError=await run({async complete(){if(++errRounds===1)return final('',[call('before-error','read_file',{path:'AZURE-a.txt'})]);throw new Error('probe network down')}},root)
evidence.modelError=modelError;expect('model-error-keeps-events-no-answer',()=>{assert.equal(modelError.reason,'model_error');assert.equal(modelError.answer,undefined);assert.ok(modelError.events.some((e:any)=>e.toolCallId==='before-error'))})
const empty=await run({async complete(){return final(' \n ')}},root);evidence.empty=empty;expect('empty-final',()=>{assert.equal(empty.reason,'empty_final');assert.equal(empty.answer,undefined)})
const normal=await run({async complete(){return final('normal')}},root);evidence.normal=normal;expect('normal-final',()=>assert.equal(normal.answer,'normal'))
let limitCount=0;const limit=await run({async complete(){limitCount++;return final('',[call('repeat-'+limitCount,'no_such_tool',{})])}},root);evidence.limit={count:limitCount,result:limit};expect('default-32-model-rounds',()=>{assert.equal(limitCount,32);assert.equal(limit.answer,undefined);assert.match(limit.reason,/^max_(rounds|turns)$/)})
await writeFile(join(root,'same-a.txt'),'identical');await writeFile(join(root,'same-b.txt'),'identical')
const collision=[]
for(const path of ['same-a.txt','same-b.txt']){let n=0;collision.push(await run({async complete(){return ++n===1?final('',[call('read','read_file',{path})]):final('done')}},root))}
evidence.eventReplay={sameEvents:JSON.stringify(collision[0].events)===JSON.stringify(collision[1].events),a:collision[0],b:collision[1]}
expect('events-retain-call-inputs',()=>assert.notDeepEqual(collision[0].events,collision[1].events))
console.log(JSON.stringify(evidence,null,2))
