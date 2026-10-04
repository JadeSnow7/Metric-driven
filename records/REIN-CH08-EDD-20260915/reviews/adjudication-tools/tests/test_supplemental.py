import json,subprocess,tempfile,unittest,importlib.util
from pathlib import Path
ROOT=Path(__file__).parent.parent; TOOL=ROOT/'supplemental_check.py'
spec=importlib.util.spec_from_file_location('supplemental_check',TOOL)
checker=importlib.util.module_from_spec(spec); spec.loader.exec_module(checker)
class T(unittest.TestCase):
 def row(self,estimate=None,claim_value='值',tool=True):
  source={'role':'user','content':'[来源:doc]\n字段：值'}
  if tool:
   source.update({'role':'tool','tool_call_id':'x','tool_calls':[{'id':'c','name':'read','arguments':{'x':'y'}}]})
  m=[{'role':'system','content':'r'},{'role':'user','content':'q'},source]
  r={'taskId':str(id(self)),'strategy':'on-demand','budget':2400,'messages':m,'estimatedUnits':estimate if estimate is not None else checker.est(m),'answer':{'claims':[{'field':'字段','value':claim_value,'source':'doc'}]}}
  return r
 def invoke(self,row):
  d=tempfile.TemporaryDirectory();p=Path(d.name);run=p/'run.json'; rows=[]
  for i in range(16):
   x=dict(row); x['taskId']=f't{i//4}'; x['strategy']=['on-demand','window','summary','retrieval'][i%4]; rows.append(x)
  run.write_text(json.dumps({'exit_code':0,'stdout':json.dumps({'results':rows})}));data=p/'data';data.mkdir();o=subprocess.run(['python3',str(TOOL),'--run',str(run),'--data',str(data)],capture_output=True,text=True);return o
 def test_ordinary_message_claim_passes(self):
  self.assertEqual(self.invoke(self.row(tool=False)).returncode,0)

 def test_tool_result_claim_and_rust_estimate_pass(self):
  self.assertEqual(self.invoke(self.row()).returncode,0)

 def test_wrong_estimate_is_rejected(self):
  self.assertNotEqual(self.invoke(self.row(1)).returncode,0)

 def test_unsupported_claim_is_rejected(self):
  self.assertNotEqual(self.invoke(self.row(claim_value='不存在的值')).returncode,0)

 def test_changed_fact_rejects_old_oracle_claim(self):
  changed=self.row()
  changed['messages'][-1]['content']='[来源:doc]\n字段：新值'
  self.assertNotEqual(self.invoke(changed).returncode,0)
if __name__=='__main__':unittest.main()
