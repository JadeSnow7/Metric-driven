import hashlib
import json
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = Path('/private/tmp/rein-ch08-common-20260915/book/fixtures/ch08-context')
REPO = Path('/private/tmp/rein-ch08-common-20260915/book')
MUTANTS = {
    'missing-row': 'CHECK_EXACT_4X4',
    'duplicate-replacement': 'CHECK_EXACT_4X4',
    'wrong-estimate': 'CHECK_ESTIMATE',
    'larger-budget': 'CHECK_REQUEST_BUDGET',
    'unsupported-claim': 'CHECK_CLAIM_GROUNDED',
    'frozen-original-value': 'CHECK_CLAIM_GROUNDED',
    'frozen-messages-and-answer-on-mutated': 'CHECK_CLAIM_CURRENT_SOURCE',
    'wrong-quality-only-on-mutated': 'CHECK_QUALITY_EXACT',
    'false-exhaustion-default': 'CHECK_EXHAUSTION_ONLY_ZERO_BUDGET',
    'budget0-dispatch': 'CHECK_BUDGET_ZERO_EMPTY',
    'accept-duplicate-metadata': 'CHECK_DUPLICATE_METADATA_REJECTED',
}

def file_hashes(root):
    result = {}
    for path in sorted(root.rglob('*')):
        if not path.is_file():
            continue
        if any(part in {'.git', 'node_modules', 'target', 'dist', 'cache'} for part in path.relative_to(root).parts):
            continue
        result[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result

class EvalTests(unittest.TestCase):
    def run_eval(self, mutant=None, output=None):
        if output is None:
            output = Path(tempfile.mkdtemp(prefix='eval-v4-')) / 'run'
        argv = ['python3', str(ROOT / 'evaluator.py'), '--repo', str(REPO), '--data', str(DATA), '--output', str(output), '--command-json', str(ROOT / 'toy-command.json')]
        env = dict(os.environ)
        env['EDD_MUTANT'] = mutant or ''
        started = time.time()
        process = subprocess.run(argv, capture_output=True, text=True, timeout=180, env=env)
        ended = time.time()
        return output, process, {'argv': argv, 'started_at': started, 'ended_at': ended, 'exit_code': process.returncode, 'stdout': process.stdout, 'stderr': process.stderr}

    def test_dynamic_known_good_suite_and_raw_records(self):
        out, process, _ = self.run_eval()
        self.assertEqual(process.returncode, 0, process.stderr)
        summary = json.loads(process.stdout)
        self.assertEqual([x['rows'] for x in summary['scenarios'][:3]], [16, 16, 16])
        self.assertEqual(summary['scenarios'][3]['exit_code'], 1)
        self.assertTrue((out / 'default/default.json').is_file())
        self.assertTrue((out / 'duplicate/duplicate.json').is_file())

    def test_positive_semantics(self):
        out, process, _ = self.run_eval()
        self.assertEqual(process.returncode, 0, process.stderr)
        mutated = json.loads((out / 'mutated/mutated.json').read_text())
        task01 = [r for r in json.loads(mutated['stdout'])['results'] if r['taskId'] == 'task-01']
        cbor_rows = [r for r in task01 if any('CBOR' in m.get('content', '') for m in r['messages'])]
        self.assertTrue(cbor_rows)
        self.assertTrue(all(r['quality'] == 0.5 for r in cbor_rows))
        default = json.loads((out / 'default/default.json').read_text())
        rows = json.loads(default['stdout'])['results']
        unknown = [r for r in rows if r['taskId'] == 'task-04']
        self.assertTrue(all(not r['answer']['claims'] and r['quality'] == 1 for r in unknown))
        window = next(r for r in rows if r['taskId'] == 'task-01' and r['strategy'] == 'window')
        self.assertEqual(window['quality'], 0.0)
        multi_source = next(r for r in rows if r['taskId'] == 'task-03' and r['strategy'] == 'on-demand')
        self.assertGreaterEqual(len(multi_source['selectedSources']), 2)

    def test_existing_output_sentinel_is_not_overwritten(self):
        parent = Path(tempfile.mkdtemp(prefix='eval-v4-sentinel-'))
        out = parent / 'existing'
        out.mkdir()
        sentinel = b'sentinel summary bytes\n'
        (out / 'summary.json').write_bytes(sentinel)
        _, process, _ = self.run_eval(output=out)
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual((out / 'summary.json').read_bytes(), sentinel)

    def test_no_self_caught_duplicate_failure(self):
        out, _, _ = self.run_eval()
        duplicate = json.loads((out / 'duplicate/duplicate.json').read_text())
        self.assertNotEqual(duplicate['exit_code'], 0)
        self.assertIn('invalid metadata', duplicate['stderr'])

    def test_mutants_hit_distinct_checks_and_write_calibration(self):
        stamp = time.strftime('%Y%m%d-%H%M%S') + f'-{time.time_ns() % 1000000:06d}'
        calibration_root = ROOT / 'calibration' / f'test-{stamp}'
        calibration_root.mkdir(parents=True)
        positive_out = calibration_root / 'positive'
        _, positive_process, positive_call = self.run_eval(output=positive_out)
        self.assertEqual(positive_process.returncode, 0, positive_process.stderr)
        records = [{'name': 'positive', 'status': 'passed', 'run_path': str(positive_out), 'call': positive_call}]
        for mutant, expected in MUTANTS.items():
            out = calibration_root / mutant
            _, process, call = self.run_eval(mutant, output=out)
            self.assertNotEqual(process.returncode, 0, mutant)
            summary = json.loads((out / 'summary.json').read_text())
            checks = [x['check_id'] for x in summary['failed_checks']]
            self.assertIn(expected, checks, mutant)
            records.append({'name': mutant, 'status': 'rejected', 'checkID': expected, 'run_path': str(out), 'call': call})
        archive = {'suite': 'evaluator-v4 toy CLI', 'evaluator_sha256': hashlib.sha256((ROOT / 'evaluator.py').read_bytes()).hexdigest(), 'tool_hashes': file_hashes(ROOT), 'source_hashes': file_hashes(REPO), 'positive': records[0], 'mutants': records[1:], 'scope': 'Toy protocol calibration only; not evidence of Rust/TypeScript product algorithms.'}
        (ROOT / 'calibration-summary.json').write_text(json.dumps(archive, ensure_ascii=False, indent=2) + '\n')

if __name__ == '__main__':
    unittest.main()
