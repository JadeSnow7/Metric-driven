import http.server,threading,subprocess,os,json,pathlib,tempfile
base=pathlib.Path('/private/tmp/rein-ch05-production-rereview-1')
root=pathlib.Path(tempfile.mkdtemp(dir=base,prefix='live-ws-'));(root/'README.md').write_text('marker: LOCAL-LIVE-EVIDENCE')
state={}
class Handler(http.server.BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_POST(self):
  data=json.loads(self.rfile.read(int(self.headers['Content-Length'])));state['requests'].append({'path':self.path,'body':data});n=len(state['requests'])
  if state['mode']=='error':self.send_response(503);self.end_headers();self.wfile.write(b'{"error":{"message":"local only"}}');return
  if state['mode']=='limit' or n==1:
   name='read_file' if state['mode']=='success' else 'no_such_tool';args={'path':'README.md'} if name=='read_file' else {}
   msg={'role':'assistant','content':None,'tool_calls':[{'id':'local-'+str(n),'type':'function','function':{'name':name,'arguments':json.dumps(args)}}]}
  else:msg={'role':'assistant','content':next(m['content'] for m in data['messages'] if m['role']=='tool')}
  body=json.dumps({'choices':[{'message':msg}]}).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
server=http.server.HTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
results=[]
try:
 for lang in ['ts','rust']:
  for mode in ['success','limit','error']:
   state.clear();state.update(mode=mode,requests=[])
   env={k:v for k,v in os.environ.items() if not k.startswith('REIN_')};env.update(REIN_BASE_URL='http://127.0.0.1:'+str(server.server_port),REIN_API_KEY='local-test-only',REIN_MODEL='local-model')
   argv=['npm','run','ch05:live','--','--live',str(root),'read README'] if lang=='ts' else ['/private/tmp/rein-production-rereview-build/debug/examples/ch05_loop','--live']
   cwd='/private/tmp/rein-production-20260914/ts' if lang=='ts' else '/private/tmp/rein-production-20260914'
   p=subprocess.run(argv,cwd=cwd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=25)
   item={'language':lang,'mode':mode,'argv':argv,'cwd':cwd,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'requests':state['requests'].copy()}
   try:
    result=json.loads(p.stdout[p.stdout.index('{'):]);count=len(item['requests']);reason=result['reason'];item['checks']={'request_count':count,'reason':reason,'no_retry_and_bound':count=={'success':2,'limit':4,'error':1}[mode]}
    if mode=='success':item['checks']['actual_tool_result_in_next_request']=result['answer']==next(m['content'] for m in item['requests'][1]['body']['messages'] if m['role']=='tool') and 'marker:' in result['answer']
   except Exception as e:item['parse_error']=str(e)
   results.append(item)
finally:server.shutdown();server.server_close()
(base/'live-loopback-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print(json.dumps([{k:v for k,v in r.items() if k not in ['requests','stdout','stderr']} for r in results],ensure_ascii=False,indent=2))
