# SPDX-License-Identifier: MIT
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('oaf_validate', ROOT / 'tools' / 'validate.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.m = json.loads((ROOT / 'examples/provenance/manifest.json').read_text())
        self.r = [json.loads(line) for line in (ROOT / 'examples/provenance/records.jsonl').read_text().splitlines()]

    def record(self, kind):
        return next(r for r in self.r if r['type'] == kind)

    def invalid(self):
        with self.assertRaises(v.Invalid):
            v.validate_data(self.m, self.r)

    def test_shipped_archives(self):
        for name in ('minimal', 'provenance'):
            self.assertTrue(v.validate_archive(ROOT / 'examples' / name)['valid'])

    def test_schemas_well_formed(self):
        for name in ('manifest', 'record'):
            v.schema_validator(name)

    def test_empty_archive(self):
        self.assertEqual(v.validate_data(self.m, [])['records'], 0)

    def test_order_independent(self):
        self.assertEqual(v.validate_data(self.m, self.r), v.validate_data(self.m, self.r[::-1]))

    def test_duplicate_identity(self):
        self.r.append(copy.deepcopy(self.r[0])); self.invalid()

    def test_archive_identity_collision(self):
        self.m['archive_id'] = self.r[0]['id']; self.invalid()

    def test_unknown_version(self):
        for version in ('0.2.0', '1.0.0', '0.1.1', '0.1'):
            self.m['version'] = version; self.invalid()

    def test_content_profile_is_future(self):
        self.m['profile'] = 'content'; self.invalid()

    def test_required_extension_rejected(self):
        self.m['required_extensions'] = ['https://example.org/oaf#essential']; self.invalid()

    def test_optional_extension_and_metadata(self):
        self.r[0]['extensions']['https://example.org/oaf#unknown'] = {'nested': [1, None, 'é']}
        self.r[0]['metadata'] = {'unrecognized': {'a': True}}
        self.assertTrue(v.validate_data(self.m, self.r)['valid'])

    def test_unknown_core_field(self):
        self.r[0]['surprise'] = 1; self.invalid()

    def test_unknown_type(self):
        self.r[0]['type'] = 'content'; self.invalid()

    def test_bad_extension_key(self):
        self.r[0]['extensions'] = {'custom': True}; self.invalid()

    def test_dangling_ref(self):
        self.record('annotation')['target_id'] = self.m['archive_id']; self.invalid()

    def test_wrong_target_type(self):
        self.record('annotation')['target_id'] = self.record('annotation')['id']; self.invalid()

    def test_source_ref_type(self):
        self.record('occurrence')['source_id'] = self.record('asset')['id']; self.invalid()

    def test_missing_provenance(self):
        self.record('asset')['activity_ids'] = []; self.invalid()

    def test_activity_ref_type(self):
        self.record('asset')['activity_ids'] = [self.record('source')['id']]; self.invalid()

    def test_provenance_source_mismatch(self):
        source = self.record('occurrence')['source_id']
        for r in self.r:
            if r['type'] == 'activity':
                r['source_ids'] = [s for s in r['source_ids'] if s != source]
        self.invalid()

    def test_digest_without_completed_hash(self):
        for r in self.r:
            if r['type'] == 'activity' and r['action'] == 'hash':
                r['outcome'] = 'partial'
        self.invalid()

    def test_bad_digest(self):
        self.record('asset')['sha256'] = '0' * 63; self.invalid()

    def test_asset_size_disagrees(self):
        self.record('asset')['size_bytes'] = 1; self.invalid()

    def test_digest_size_conflict(self):
        a = copy.deepcopy(self.record('asset'))
        a['id'] = 'urn:uuid:99999999-9999-4999-8999-999999999999'
        a['size_bytes'] = 99
        self.r.append(a); self.invalid()

    def test_bad_size_types_and_range(self):
        for size in (-1, True, '0', 9007199254740992):
            self.record('asset')['size_bytes'] = size; self.invalid()

    def test_size_for_missing_or_package(self):
        for r in self.r:
            if r['type'] == 'occurrence' and r['state'] == 'missing':
                r['size_bytes'] = 0
        self.invalid()

    def test_package_asset_forbidden(self):
        for r in self.r:
            if r['type'] == 'occurrence' and r['kind'] == 'package':
                r['asset_id'] = self.record('asset')['id']
        self.invalid()

    def test_paths_are_safe_labels(self):
        for segments in (['..'], ['.'], ['/root'], ['a/b'], ['a\\b'], ['a\x00b'], ['']):
            self.record('occurrence')['path_segments'] = segments; self.invalid()

    def test_root_and_withheld_paths(self):
        self.record('occurrence')['path_segments'] = []
        self.assertTrue(v.validate_data(self.m, self.r)['valid'])
        del self.record('occurrence')['path_segments']
        self.assertTrue(v.validate_data(self.m, self.r)['valid'])

    def test_invalid_timestamps(self):
        for timestamp in ('2026-02-30T00:00:00Z', 'yesterday', '2026-01-01T00:00:00+00:00'):
            self.m['created_at'] = timestamp; self.invalid()

    def test_reversed_activity_time(self):
        self.record('activity')['ended_at'] = '2025-01-01T00:00:00Z'; self.invalid()

    def test_duplicate_and_non_json_values(self):
        for text in ('{"a":1,"a":2}', '{"x":{"a":1,"a":2}}', '{"x":NaN}', '{"x":Infinity}', '{"x":1e9999}', '"\\ud800"'):
            with self.subTest(text=text), self.assertRaises((v.Invalid, ValueError)):
                v.parse(text)

    def test_framing_and_cli_privacy(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / 'manifest.json').write_text(json.dumps(self.m))
            for content in ('\n', '{}', 'not-json\n', '\ufeff{}\n'):
                (p / 'records.jsonl').write_text(content)
                with self.assertRaises(ValueError):
                    v.validate_archive(p)
            (p / 'records.jsonl').write_text('{"private_secret":"DO_NOT_ECHO"}\n')
            result = subprocess.run([sys.executable, str(ROOT / 'tools/validate.py'), d], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertNotIn('DO_NOT_ECHO', result.stdout + result.stderr)
            self.assertNotIn(d, result.stdout + result.stderr)

    def test_crlf_and_empty_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / 'manifest.json').write_text(json.dumps(self.m))
            (p / 'records.jsonl').write_bytes(b'')
            self.assertEqual(v.validate_archive(p)['records'], 0)
            (p / 'records.jsonl').write_bytes(b''.join(json.dumps(r).encode() + b'\r\n' for r in self.r))
            self.assertEqual(v.validate_archive(p)['records'], len(self.r))

    def test_symlink_member_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / 'manifest.json').symlink_to(ROOT / 'examples/minimal/manifest.json')
            (p / 'records.jsonl').write_bytes(b'')
            with self.assertRaises(v.Invalid):
                v.validate_archive(p)

    def test_resource_limit(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / 'manifest.json').write_text(json.dumps(self.m))
            (p / 'records.jsonl').write_bytes(b'x' * (v.MAX_LINE + 1))
            with self.assertRaises(v.Invalid):
                v.validate_archive(p)

    def test_validation_does_not_mutate(self):
        m, r = copy.deepcopy(self.m), copy.deepcopy(self.r)
        v.validate_data(self.m, self.r)
        self.assertEqual((self.m, self.r), (m, r))


if __name__ == '__main__':
    unittest.main()
