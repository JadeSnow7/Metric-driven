import {runAgentLoop,estimateMessages} from '/private/tmp/rein-production-candidate-03/ts/src/rein/loop.ts';
import {mkdtempSync,writeFileSync} from 'node:fs';import {tmpdir} from 'node:os';import {join} from 'node:path';
const root=mkdtempSync(join(tmpdir(),'rein07-probe-'));writeFileSync(join(root,'README.md'),'current evidence');
const out:any[]=[];
for (const [id,history] of [
 ['empty-wrong-role-id',[{role:'user',content:'x',toolCallId:''}]],
 ['result-nonarray-calls',[{role:'assistant',content:'',toolCalls:[{id:'a',name:'read_file',arguments:{}}]},{role:'tool',content:'x',toolCallId:'a',toolCalls:{}}]],
 ['wrong-role-id',[{role:'user',content:'x',toolCallId:'orphan'}]],
 ['result-declares-call',[{role:'assistant',content:'',toolCalls:[{id:'a',name:'read_file',arguments:{path:'README.md'}}]},{role:'tool',content:'x',toolCallId:'a',toolCalls:[{id:'evil',name:'read_file',arguments:{}}]}]],
 ['nonfinite-json',[{role:'assistant',content:'',toolCalls:[{id:'a',name:'read_file',arguments:{n:NaN}}]},{role:'tool',content:'x',toolCallId:'a'}]]
] as any) {let calls=0;try {const result=await runAgentLoop({async complete(){calls++;return {message:{role:'assistant',content:'answer'},toolCalls:[]}}},{root},'goal',{context:{rules:['rule'],history,budget:200}});out.push({id,reason:result.reason,calls,events:result.events});} catch(error) {out.push({id,calls,thrown:String(error)})}}
let calls=0;const history:any=[{role:'assistant',content:'',toolCalls:[{id:'a',name:'read_file',arguments:{path:'README.md'}}]},{role:'tool',content:'old',toolCallId:'a'}];
const res=await runAgentLoop({async complete(){calls++;const toolCalls=calls===1?[{id:'a',name:'read_file',arguments:{path:'README.md'}}]:[];return {message:{role:'assistant',content:calls===1?'':'answer',toolCalls},toolCalls};}},{root},'goal',{context:{rules:['rule'],history,budget:400}});out.push({id:'duplicate-next-round',reason:res.reason,calls,events:res.events});
for (const manage of [true,false]) {const result=await runAgentLoop({async complete(){return {message:{role:'assistant',content:'answer'},toolCalls:[]};}},{root},'goal',{context:{rules:['rule'],history:[],budget:100,manage}});const requested:any=result.events.find(e=>e.type==='model_requested');out.push({id:'units-'+manage,actualUnits:estimateMessages(requested.messages),prepared:result.events.find(e=>e.type==='context_prepared')});}
console.log(JSON.stringify(out));