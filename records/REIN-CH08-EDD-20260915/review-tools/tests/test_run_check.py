import json,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).parent.parent; RUN=ROOT/'run_check.py'
class T(unittest.TestCase):
 def call(self,root,name,cmd,timeout=2): return subprocess.run(['python3',str(RUN),'--cwd',str(root),'--output',str(root/name),'--timeout',str(timeout),'--',*cmd],capture_output=True,text=True)
 def test_five_outcomes(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d); (r/'src.py').write_text('x'); (r/'docs/.vitepress/theme').mkdir(parents=True); (r/'docs/.vitepress/config.mts').write_text('old'); (r/'docs/.vitepress/theme/source.ts').write_text('x'); (r/'docs/.vitepress/dist/assets').mkdir(parents=True); (r/'docs/.vitepress/dist/assets'/'ignored').write_text('x'); (r/'node_modules').mkdir(); (r/'node_modules'/'ignored').write_text('x'); (r/'target').mkdir(); (r/'target'/'ignored').write_text('x')
   self.assertEqual(self.call(r,'ok',["python3","-c","print('ok')"]).returncode,0); ok=json.loads((r/'ok'/'run.json').read_text()); self.assertEqual(ok['exit_code'],0); self.assertIn('docs/.vitepress/config.mts',ok['source_hashes_before']); self.assertIn('docs/.vitepress/theme/source.ts',ok['source_hashes_before']); self.assertNotIn('docs/.vitepress/dist/assets/ignored',ok['source_hashes_before']); self.assertNotIn('node_modules/ignored',ok['source_hashes_before'])
   self.assertEqual(self.call(r,'bad',["python3","-c","import sys;sys.exit(7)"]).returncode,7); self.assertEqual(json.loads((r/'bad'/'run.json').read_text())['wrapper_exit_code'],7)
   changed=self.call(r,'changed',["python3","-c","open('docs/.vitepress/config.mts','w').write('new')"]); self.assertEqual(changed.returncode,0); rec=json.loads((r/'changed'/'run.json').read_text()); self.assertNotEqual(rec['source_hashes_before']['docs/.vitepress/config.mts'],rec['source_hashes_after']['docs/.vitepress/config.mts'])
   self.assertEqual(self.call(r,'timeout',["python3","-c","import time;time.sleep(3)"],.05).returncode,124)
   self.assertEqual(self.call(r,'missing',['no-such-executor']).returncode,127); self.assertIsNone(json.loads((r/'missing'/'run.json').read_text())['exit_code'])
   again=self.call(r,'ok',["python3","-c","pass"]); self.assertNotEqual(again.returncode,0); self.assertEqual(json.loads((r/'ok'/'run.json').read_text())['exit_code'],0)
if __name__=='__main__': unittest.main()
