import json, subprocess, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; SEAL=ROOT/"seal.py"; AUDIT=ROOT/"audit.py"

class OrchestrationTests(unittest.TestCase):
 def test_seal_preserves_manifest_and_rejects_second_write(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d); source=r/'source'; work=r/'work'; run=r/'run'; out=r/'seal'; [x.mkdir() for x in (source,work,run)]
   (source/'a').write_text('base'); (work/'a').write_text('changed'); (work/'new').write_text('new'); (work/'.git').mkdir(); (work/'.git'/'ignored').write_text('x'); (run/'stdout.jsonl').write_text('output'); (run/'cargo-target').mkdir(); (run/'cargo-target'/'cache.bin').write_text('ignored')
   cmd=['python3',str(SEAL),'--source',str(source),'--work',str(work),'--run',str(run),'--output',str(out),'--thread-id','t']
   good=subprocess.run(cmd,capture_output=True,text=True); self.assertEqual(good.returncode,0,good.stdout); data=json.loads((out/'source-manifest.json').read_text()); self.assertEqual(data['modified'],['a']); self.assertEqual(data['added'],['new']); self.assertFalse((out/'run'/'.git').exists())
   again=subprocess.run(cmd,capture_output=True,text=True); self.assertNotEqual(again.returncode,0); self.assertTrue((out/'source-manifest.json').exists())
   audit=subprocess.run(['python3',str(AUDIT),str(out)],capture_output=True,text=True); self.assertEqual(audit.returncode,0); self.assertIn('isolation_limit',json.loads(audit.stdout)); self.assertIsNone(json.loads((out/'meta.json').read_text())['session']['token_count']['total'])

if __name__=='__main__': unittest.main()
