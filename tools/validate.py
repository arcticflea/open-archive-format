#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Read-only, offline OAF 0.1.0 structural and referential validation."""
import argparse
from datetime import datetime
import json
import re
from pathlib import Path
import sys

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
MAX_LINE = 8 * 1024 * 1024
MAX_TOTAL = 128 * 1024 * 1024
FORMATS = FormatChecker()


@FORMATS.checks('date-time', raises=ValueError)
def utc_datetime(value):
    if not isinstance(value, str):
        return True
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:[0-5]\d(?:\.\d{1,6})?Z', value):
        return False
    datetime.fromisoformat(value[:-1] + '+00:00')
    return True


class Invalid(ValueError):
    pass


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Invalid('duplicate JSON member')
        result[key] = value
    return result


def bad_constant(value):
    raise Invalid('non-JSON numeric constant')


def parse(text):
    value = json.loads(text, object_pairs_hook=unique_object, parse_constant=bad_constant)
    def check(v):
        if isinstance(v, str) and any(0xD800 <= ord(c) <= 0xDFFF for c in v):
            raise Invalid('unpaired Unicode surrogate')
        if isinstance(v, float) and (v != v or abs(v) == float('inf')):
            raise Invalid('non-finite number')
        if isinstance(v, dict):
            for k, x in v.items():
                check(k); check(x)
        elif isinstance(v, list):
            for x in v:
                check(x)
    check(value)
    return value


def schema_validator(name):
    schema = json.loads((ROOT / 'schemas' / (name + '.schema.json')).read_text())
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FORMATS)


def structural(validator, value, where):
    error = next(validator.iter_errors(value), None)
    if error:
        # Avoid echoing potentially sensitive archive values in diagnostics.
        raise Invalid(where + ': schema mismatch')


def validate_data(manifest, records):
    structural(schema_validator('manifest'), manifest, 'manifest')
    if manifest['required_extensions']:
        raise Invalid('unsupported required extension (reference validator supports core only)')
    validator = schema_validator('record')
    index = {}
    for n, record in enumerate(records, 1):
        structural(validator, record, 'record ' + str(n))
        if record['id'] == manifest['archive_id'] or record['id'] in index:
            raise Invalid('duplicate identity')
        index[record['id']] = record

    def ref(identifier, types):
        target = index.get(identifier)
        if target is None or target['type'] not in types:
            raise Invalid('dangling or incorrectly typed reference')
        return target

    def instant(text):
        # Schema format checker has already checked RFC3339 and UTC Z.
        return datetime.fromisoformat(text[:-1] + '+00:00')

    hashes = {}
    for record in records:
        t = record['type']
        activities = [ref(a, {'activity'}) for a in record.get('activity_ids', [])]
        if t == 'activity':
            for source in record['source_ids']:
                ref(source, {'source'})
            if 'ended_at' in record and instant(record['ended_at']) < instant(record['started_at']):
                raise Invalid('activity ends before it starts')
        elif t == 'asset':
            if 'sha256' in record:
                if not any(a['action'] == 'hash' and a['outcome'] == 'completed' for a in activities):
                    raise Invalid('digest requires completed hash provenance')
                digest = record['sha256']
                size = record.get('size_bytes')
                if size is not None:
                    if digest in hashes and hashes[digest] != size:
                        raise Invalid('same digest with conflicting sizes')
                    hashes[digest] = size
        elif t == 'occurrence':
            ref(record['source_id'], {'source'})
            if not any(record['source_id'] in a['source_ids'] for a in activities):
                raise Invalid('occurrence provenance must name its source')
            if 'size_bytes' in record and (record['kind'] != 'file' or record['state'] != 'present'):
                raise Invalid('size only permitted for present regular files')
            if 'asset_id' in record:
                asset = ref(record['asset_id'], {'asset'})
                if record['kind'] != 'file':
                    raise Invalid('only regular files may refer to byte assets')
                if 'size_bytes' in record and 'size_bytes' in asset and record['size_bytes'] != asset['size_bytes']:
                    raise Invalid('occurrence and asset sizes disagree')
        elif t == 'annotation':
            ref(record['target_id'], {'source', 'activity', 'asset', 'occurrence'})
    return {'version': manifest['version'], 'records': len(index), 'valid': True}


def validate_archive(directory):
    directory = Path(directory)
    paths = [directory / 'manifest.json', directory / 'records.jsonl']
    for path in paths:
        if path.is_symlink() or not path.is_file():
            raise Invalid('required member must be a regular file, not a symlink')
    if paths[0].stat().st_size > MAX_LINE or sum(p.stat().st_size for p in paths) > MAX_TOTAL:
        raise Invalid('reference tool resource limit exceeded')
    manifest = parse(paths[0].read_text(encoding='utf-8'))
    records = []
    total = paths[0].stat().st_size
    with paths[1].open('rb') as stream:
        while True:
            line = stream.readline(MAX_LINE + 1)
            if not line:
                break
            total += len(line)
            if len(line) > MAX_LINE or total > MAX_TOTAL:
                raise Invalid('reference tool resource limit exceeded')
            if not line.endswith(b'\n'):
                raise Invalid('each JSONL record must end with LF')
            if not line.strip():
                raise Invalid('blank JSONL line')
            records.append(parse(line.decode('utf-8')))
    return validate_data(manifest, records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(validate_archive(args.archive), sort_keys=True))
    except (OSError, ValueError, RecursionError, OverflowError) as exc:
        message = str(exc) if isinstance(exc, Invalid) else 'unreadable or malformed archive'
        print('INVALID: ' + message, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
