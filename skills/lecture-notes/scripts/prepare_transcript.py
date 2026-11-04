#!/usr/bin/env python3
"""Prepare or check a private, local transcript coverage manifest (stdlib only)."""
import argparse
import hashlib
import json
import re
from pathlib import Path

TIMESTAMP = re.compile(r'(?<!\d)(\d{1,2}:\d{2}:\d{2})(?!\d)')
DISPOSITIONS = {'u6b63u6587', 'u5408u5e76', 'u91cdu590du7701u7565', 'u975eu8bfeu7a0bu4ea4u6d41', 'u5f85u6838u5b9e'}


def prepare(source, out):
    source = Path(source)
    if source.suffix.lower() not in {'.md', '.txt'}:
        raise ValueError('u53eau63a5u53d7UTF-8 Markdownu6216TXTuff1bPDFu548cWordu8bf7u5148u53efu9760u63d0u53d6u3002')
    data = source.read_bytes()
    content = data.decode('utf-8-sig')
    if not content.strip():
        raise ValueError('u6765u6e90u4e3au7a7au3002')
    lines = content.splitlines()
    starts = [i for i, line in enumerate(lines, 1) if TIMESTAMP.search(line)]
    # Include every source line, including the preamble.
    boundaries = sorted(set([1] + starts + [len(lines) + 1]))
    segments = []
    for i, (a, b) in enumerate(zip(boundaries, boundaries[1:]), 1):
        excerpt = '\n'.join(lines[a-1:b-1])
        ts = TIMESTAMP.search(excerpt)
        segments.append({'id': f'segment-{i:04d}', 'start_line': a,
                         'end_line': b-1, 'timestamp': ts.group(1) if ts else None,
                         'speaker': '', 'disposition': '', 'destination': '',
                         'reason': ''})
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    target = out / 'coverage.json'
    if target.exists():
        raise ValueError('coverage.jsonu5df2u5b58u5728uff1bu8bf7u4fddu7559u539fu8bb0u5f55u6216u9009u62e9u65b0u7684u5de5u4f5cu76eeu5f55u3002')
    manifest = {'source_name': source.name, 'sha256': hashlib.sha256(data).hexdigest(),
                'line_count': len(lines), 'segments': segments}
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'u5df2u751fu6210 {target}uff0cu5171{len(segments)}u4e2au533au95f4uff1bu672au4e0au4f20u6765u6e90u3002')


def check(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    cursor = 1
    problems = []
    for segment in data['segments']:
        if segment['start_line'] != cursor or segment['end_line'] < cursor:
            raise ValueError('u533au95f4u4e0du8fdeu7eedu3001u91cdu53e0u6216u987au5e8fu9519u8befu3002')
        cursor = segment['end_line'] + 1
        if segment['disposition'] not in DISPOSITIONS:
            problems.append(segment['id'] + 'uff1au5c1au672au586bu5199u6709u6548u5904u7406u65b9u5f0f')
        elif segment['disposition'] in {'u6b63u6587', 'u5408u5e76'} and not segment['destination'].strip():
            problems.append(segment['id'] + 'uff1au7f3au5c11u6b63u6587u5bf9u5e94u4f4du7f6e')
        elif segment['disposition'] in {'u91cdu590du7701u7565', 'u975eu8bfeu7a0bu4ea4u6d41', 'u5f85u6838u5b9e'} and not segment['reason'].strip():
            problems.append(segment['id'] + 'uff1au7f3au5c11u5904u7406u8bf4u660e')
    if cursor != data['line_count'] + 1:
        raise ValueError('u533au95f4u6ca1u6709u8986u76d6u539fu6587u5168u90e8u884cu3002')
    if problems:
        raise ValueError('\n'.join(problems))
    print('u539fu6587u884cu53f7u8fdeu7eedu8986u76d6uff0cu5904u7406u8bb0u5f55u5b8cu6574uff1bu5185u5bb9u51c6u786eu6027u4ecdu9700u5bf9u7167u539fu6587u5ba1u9605u3002')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', nargs='?', type=Path)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--check', type=Path)
    args = parser.parse_args()
    try:
        if args.check:
            if args.source or args.out:
                parser.error('--checku4e0du80fdu4e0eu6765u6e90u6216--outu540cu65f6u4f7fu7528u3002')
            check(args.check)
        else:
            if args.source is None or args.out is None:
                parser.error('u9700u63d0u4f9bu6765u6e90u4e0e--outuff0cu6216u5355u72ecu4f7fu7528--checku3002')
            prepare(args.source, args.out)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, str(exc) + '\n')
