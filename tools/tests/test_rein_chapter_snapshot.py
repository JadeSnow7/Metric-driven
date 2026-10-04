import json, stat, tempfile, unittest
from pathlib import Path
from tools import rein_chapter_snapshot as snap

class SnapshotTests(unittest.TestCase):
  def test_filtered_portable_snapshot_and_recovery(self):
    with tempfile.TemporaryDirectory() as d:
      t=Path(d); src=t/'src'; src.mkdir(); (src/'README.md').write_text('chapter'); (src/'package-lock.json').write_text('{}'); (src/'empty').write_bytes(b''); (src/'blob').write_bytes(bytes([0,255])); (src/'tool').write_text('#!/bin/sh\n'); (src/'tool').chmod(0o755); (src/'link').symlink_to('README.md')
      for name in ('node_modules','target','evidence','experiments','task-inputs','chapter-snapshots'): (src/name).mkdir(); (src/name/'ignored').write_text('x')
      (src/'fixtures/evidence').mkdir(parents=True); (src/'fixtures/evidence/kept').write_text('fixture evidence')
      (src/'.env').write_text('SECRET'); (src/'.env.example').write_text('SAFE=')
      out=t/'snap'; portable=t/'portable.tar.gz'; snap.snapshot(src,'05',out,portable_output=portable); data=json.loads((out/'manifest.json').read_text()); paths={x['path'] for x in data['files']}
      self.assertEqual(paths,{'README.md','blob','empty','link','package-lock.json','tool','.env.example','fixtures/evidence/kept'}); self.assertFalse(next(row for row in data['files'] if row['path']=='fixtures/evidence/kept')['git_exec']); self.assertTrue(next(row for row in data['files'] if row['path']=='tool')['git_exec']); self.assertTrue((out/'rein-ch05.tar.gz').exists()); self.assertTrue(portable.exists()); self.assertTrue((out/'files/link').is_symlink()); self.assertTrue((out/'files/tool').stat().st_mode & stat.S_IXUSR)
      import tarfile
      with tarfile.open(out/'rein-ch05.tar.gz') as archive: self.assertTrue(all(member.name == 'rein-ch05' or member.name.startswith('rein-ch05/') for member in archive.getmembers()))
  def test_binary_empty_mode_and_unchanged_baseline_patch(self):
    with tempfile.TemporaryDirectory() as d:
      t=Path(d); base=t/'base'; base.mkdir(); (base/'blob').write_bytes(bytes([0,255])+b'base'); (base/'tool').write_text('x'); (base/'tool').chmod(0o644)
      src=t/'src'; snap.copy_filtered(base,src); (src/'blob').write_bytes(bytes([0,255])+b'changed'); (src/'empty').write_bytes(b''); (src/'tool').chmod(0o755); out=t/'snap'; snap.snapshot(src,'05',out,base); self.assertIn(b'GIT binary patch',(out/'baseline.patch').read_bytes()); self.assertTrue((out/'files/empty').exists()); self.assertTrue((out/'files/tool').stat().st_mode & stat.S_IXUSR)
      same=t/'same'; snap.copy_filtered(base,same); out2=t/'same-snap'; snap.snapshot(same,'05',out2,base); self.assertEqual((out2/'baseline.patch').read_bytes(),b'')
  def test_rejects_existing_output_and_outside_symlink(self):
    with tempfile.TemporaryDirectory() as d:
      t=Path(d); src=t/'src'; src.mkdir(); (src/'out').symlink_to('/tmp');
      with self.assertRaises(RuntimeError): snap.snapshot(src,'05',t/'out')
      with self.assertRaises(RuntimeError): snap.snapshot(src,'05',src/'chapter-snapshots'/'nested')
      (src/'out').unlink(); (src/'ok').write_text('x'); dest=t/'existing'; dest.mkdir()
      with self.assertRaises(RuntimeError): snap.snapshot(src,'05',dest)
if __name__=='__main__': unittest.main()
