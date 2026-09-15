import json, os, selectors, stat, subprocess, tempfile, time, unittest
from pathlib import Path
import sys
from unittest import mock
sys.path.insert(0, str(Path(__file__).parents[1]))
import rein_benchmark_preparation as rb

def product(t, name="product"):
    r=t/name; r.mkdir(); (r/"src").mkdir(); (r/"src/old.rs").write_text("old")
    (r/"01.md").write_text("chapter one"); (r/"fixtures").mkdir(); (r/"fixtures/manifest.json").write_text('{}')
    (r/"package.json").write_text('{"name":"fixture"}'); (r/"package-lock.json").write_text('{}')
    (r/"task-inputs").mkdir(); (r/"task-inputs/old.json").write_text('old history')
    (r/".env").write_text('SECRET'); (r/".env.example").write_text('SAFE=')
    (r/"target").mkdir(); (r/"target/x").write_text('cache'); return r

class BenchmarkTests(unittest.TestCase):
  def test_prepare_replaces_inputs_and_copies_git(self):
    with tempfile.TemporaryDirectory() as d:
      t=Path(d); r=product(t); inp=t/'prompt.md'; inp.write_text('fresh')
      subprocess.run(['git','-C',str(r),'init','-q'],check=True); subprocess.run(['git','-C',str(r),'add','.'],check=True); subprocess.run(['git','-C',str(r),'commit','-qm','first'],check=True)
      out=t/'prep'; result=rb.prepare(r,out,[inp],copy_git=r); arm=out/'control-arm'
      self.assertEqual((arm/'task-inputs/prompt.md').read_text(),'fresh'); self.assertFalse((arm/'task-inputs/old.json').exists())
      self.assertTrue((arm/'.git/HEAD').exists()); self.assertFalse((arm/'.git/config').exists()); self.assertEqual(subprocess.run(['git','-C',str(arm),'rev-parse','HEAD'],capture_output=True,text=True).returncode,0)
      self.assertEqual(rb.manifest(arm),rb.manifest(out/'skill-arm')); self.assertFalse(any(x['path'].startswith('.git/') for x in result['arms']['control']['files']))
      self.assertFalse((arm/'.env').exists()); self.assertTrue((arm/'.env.example').exists()); self.assertTrue((arm/'fixtures/manifest.json').exists())

  def test_multiline_role_fake_cli_protocol(self):
    with tempfile.TemporaryDirectory() as d:
      t=Path(d); r=product(t); coder=t/'coder.toml'; coder.write_text('model="fake"\nmodel_reasoning_effort="low"\ndeveloper_instructions="""line one\nline two\n"""\n'); prompt=t/'p'; prompt.write_text('USER PROMPT')
      fake=t/'fake'; fake.write_text('#!/bin/sh\nprev=; final=\nfor arg in "$@"; do [ "$prev" = "-o" ] && final="$arg"; prev="$arg"; done\ncat > "$CARGO_TARGET_DIR/input"\nprintf \'{"type":"turn.failed","usage":{"input_tokens":2}}\\n\'\nprintf \'final body\' > "$final"\nprintf partial-stderr >&2\nexit 7\n'); fake.chmod(fake.stat().st_mode|stat.S_IXUSR)
      skill=t/'SKILL.md'; skill.write_text('frozen skill'); out=t/'run'; self.assertEqual(rb.run_one(coder,r,prompt,out,skill=skill,executable=str(fake)),7); meta=json.loads((out/'run.json').read_text())
      self.assertEqual(meta['exit_code'],7); self.assertTrue(any('line one' in x and 'line two' in x for x in meta['argv'])); self.assertIn('--skip-git-repo-check',meta['argv']); self.assertIn(str(skill.resolve()),meta['actual_prompt']); self.assertEqual((out/'final.md').read_text(),'final body'); self.assertEqual(meta['usage']['input_tokens'],2); self.assertEqual((out/'cargo-target/input').read_text(),(out/'actual-prompt.md').read_text()); self.assertEqual(meta['actual_prompt'],(out/'actual-prompt.md').read_text()); self.assertEqual(meta['argv'][-1],'-'); self.assertEqual(meta['argv'].count('--add-dir'),2); self.assertIn('partial-stderr',(out/'stderr.txt').read_text())
      control=t/'control-run'; self.assertEqual(rb.run_one(coder,r,prompt,control,executable=str(fake)),7); control_meta=json.loads((control/'run.json').read_text()); self.assertEqual((control/'cargo-target/input').read_text(),(control/'actual-prompt.md').read_text()); self.assertNotIn(str(skill.resolve()),control_meta['actual_prompt']); self.assertNotEqual(meta['actual_prompt'],control_meta['actual_prompt'])

  def test_seal_patch_recovery_and_unfinished(self):
    with tempfile.TemporaryDirectory() as d:
      t=Path(d); base=product(t,'base'); tree=t/'tree'; rb.copy_tree(base,tree); (tree/'src/old.rs').write_text('changed'); execution=t/'run.json'; execution.write_text(json.dumps({'workspace':str(tree),'ended_at':'x','exit_code':0,'terminal_status':'turn.completed'})); (t/'events.jsonl').write_text('{"type":"turn.completed"}\n'); (t/'stderr.txt').write_text(''); (t/'final.md').write_text('final'); out=t/'seal'; rb.seal(tree,out,base,execution); data=json.loads((out/'seal.json').read_text()); self.assertIn('src/old.rs',data['changed']); self.assertNotIn('.env', (out/'baseline.patch').read_text()); self.assertTrue((out/'tree/fixtures/manifest.json').exists()); self.assertTrue((out/'execution.json').exists()); self.assertTrue((out/'events.jsonl').exists()); self.assertTrue((out/'stderr.txt').exists()); self.assertTrue((out/'final.md').exists())
      run=t/'unfinished.json'; run.write_text(json.dumps({'workspace':str(tree)}))
      with self.assertRaises(RuntimeError): rb.seal(tree,t/'bad',execution=run)
      with self.assertRaises(RuntimeError): rb.seal(tree,t/'missing')

  def test_seal_binary_empty_and_executable_git_patch_recovery(self):
    with tempfile.TemporaryDirectory() as d:
      t=Path(d); base=product(t,'base'); (base/'src/blob.bin').write_bytes(bytes([0,255])+b'baseline'); (base/'src/tool.sh').write_text('#!/bin/sh\\nexit 0\\n'); (base/'src/tool.sh').chmod(0o644)
      tree=t/'tree'; rb.copy_tree(base,tree); (tree/'src/blob.bin').write_bytes(bytes([0,255])+b'changed'); (tree/'src/empty').write_bytes(b''); (tree/'src/tool.sh').chmod(0o755)
      execution=t/'run.json'; execution.write_text(json.dumps({'workspace':str(tree),'ended_at':'x','exit_code':0,'terminal_status':'turn.completed'})); out=t/'seal'
      rb.seal(tree,out,base,execution)
      self.assertEqual((out/'tree/src/blob.bin').read_bytes(),bytes([0,255])+b'changed'); self.assertTrue((out/'tree/src/empty').exists()); self.assertEqual((out/'tree/src/empty').stat().st_size,0); self.assertTrue((out/'tree/src/tool.sh').stat().st_mode & stat.S_IXUSR); self.assertIn('src/tool.sh',json.loads((out/'seal.json').read_text())['changed']); self.assertIn(b'GIT binary patch', (out/'baseline.patch').read_bytes())

  def test_seal_unchanged_tree_accepts_empty_git_patch(self):
    with tempfile.TemporaryDirectory() as d:
      t=Path(d); base=product(t,'base'); tree=t/'tree'; rb.copy_tree(base,tree); execution=t/'run.json'; execution.write_text(json.dumps({'workspace':str(tree),'ended_at':'x','exit_code':0,'terminal_status':'turn.completed'})); out=t/'seal'; rb.seal(tree,out,base,execution)
      self.assertEqual((out/'baseline.patch').read_text(),''); self.assertEqual(rb.manifest(out/'tree'),rb.manifest(tree)); self.assertEqual(json.loads((out/'seal.json').read_text())['changed'],[])

  def test_two_sources_two_packages_and_symlink_manifest(self):
    with tempfile.TemporaryDirectory() as d:
      t=Path(d); a=product(t,'a'); b=product(t,'b'); (a/'src/link').symlink_to('old.rs'); (a/'src/dir-link').symlink_to('fixtures', target_is_directory=True); (a/'src/old.rs').write_text('control reviewer-a package-1 legal'); (b/'src/old.rs').write_text('skill reviewer-b package-2 legal'); out=t/'reviews'
      rb.review_pack({'control':a,'skill':b},out,{'reviewer-a':{'control':'package-1','skill':'package-2'},'reviewer-b':{'control':'package-3','skill':'package-4'}},{'task-inputs/old.json'})
      for reviewer in ('reviewer-a','reviewer-b'):
        for package in ('package-1','package-2','package-3','package-4'):
          if (out/reviewer/package).exists(): self.assertTrue((out/reviewer/package/'package-lock.json').exists()); self.assertTrue((out/reviewer/(package+'.cargo-target')).is_dir())
      self.assertTrue((out/'reviewer-a/package-1/src/link').is_symlink())
      self.assertTrue((out/'reviewer-a/package-1/src/dir-link').is_symlink())
      (b/'src/outside').symlink_to('/tmp')
      with self.assertRaises(RuntimeError): rb.copy_tree(b, t/'reject')

  def test_spawn_failure_is_sealed_in_metadata(self):
    with tempfile.TemporaryDirectory() as d:
      t=Path(d); r=product(t); coder=t/'coder.toml'; coder.write_text('model="fake"\n'); prompt=t/'p'; prompt.write_text('x'); out=t/'run'
      self.assertEqual(rb.run_one(coder,r,prompt,out,executable=str(t/'does-not-exist')),127)
      meta=json.loads((out/'run.json').read_text()); self.assertEqual(meta['classification'],'spawn_or_capture_error'); self.assertIn('ended_at',meta); self.assertTrue((out/'events.jsonl').exists()); self.assertTrue((out/'stderr.txt').exists())

  def test_prunes_nested_build_cache_but_keeps_fixture_and_safe_env(self):
    with tempfile.TemporaryDirectory() as d:
      t=Path(d); r=product(t); (r/'docs/.vitepress/cache/nested').mkdir(parents=True); (r/'docs/.vitepress/cache/nested/x').write_text('cache')
      (r/'docs/fixtures').mkdir(); (r/'docs/fixtures/evidence.json').write_text('evidence')
      out=t/'copy'; rb.copy_tree(r,out)
      self.assertFalse((out/'docs/.vitepress/cache').exists())
      self.assertTrue((out/'docs/fixtures/evidence.json').exists())
      self.assertTrue((out/'.env.example').exists())
      paths={x['path'] for x in rb.manifest(r)}
      self.assertNotIn('docs/.vitepress/cache/nested/x',paths); self.assertIn('docs/fixtures/evidence.json',paths)

  def test_missing_codex_version_query_keeps_metadata(self):
    with tempfile.TemporaryDirectory() as d:
      t=Path(d); r=product(t); coder=t/'coder.toml'; coder.write_text('model="fake"\n'); prompt=t/'p'; prompt.write_text('x'); out=t/'run'
      self.assertEqual(rb.run_one(coder,r,prompt,out,executable=str(t/'codex')),127)
      meta=json.loads((out/'run.json').read_text())
      self.assertEqual(meta['classification'],'spawn_or_capture_error'); self.assertIn('ended_at',meta); self.assertIn('exit_code',meta)
      self.assertEqual((out/'events.jsonl').read_text(),''); self.assertEqual((out/'stderr.txt').read_text(),'')

  def test_interrupted_sigterm_ignored_process_is_killed_with_partial_output(self):
    with tempfile.TemporaryDirectory() as d:
      t=Path(d); r=product(t); coder=t/'coder.toml'; coder.write_text('model="fake"\n'); prompt=t/'p'; prompt.write_text('x')
      fake=t/'fake'; fake.write_text('#!/bin/sh\ntrap "" TERM\nprintf \'partial-out\\n\'\nprintf \'partial-err\\n\' >&2\nsleep 30 & child=$!\nprintf \'%s\' "$child" > "$CARGO_TARGET_DIR/child.pid"\nwait\n'); fake.chmod(fake.stat().st_mode|stat.S_IXUSR)
      original=selectors.DefaultSelector.select; calls=0
      def select_then_interrupt(selector, *args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2: raise KeyboardInterrupt
        return original(selector, *args, **kwargs)
      out=t/'run'
      started=time.monotonic()
      try:
        with mock.patch.object(selectors.DefaultSelector,'select',select_then_interrupt):
          self.assertEqual(rb.run_one(coder,r,prompt,out,executable=str(fake)),130)
      finally:
        pid_file=out/'cargo-target/child.pid'
        if pid_file.exists():
          try: os.kill(int(pid_file.read_text()),9)
          except (ProcessLookupError, ValueError): pass
      meta=json.loads((out/'run.json').read_text())
      self.assertLess(time.monotonic()-started,8); self.assertEqual(meta['classification'],'interrupted'); self.assertEqual(meta['exit_code'],130); self.assertIn('ended_at',meta); self.assertFalse(meta['drain_complete'])
      self.assertIn('partial-out',(out/'events.jsonl').read_text()); self.assertIn('partial-err',(out/'stderr.txt').read_text())

if __name__=='__main__': unittest.main()
