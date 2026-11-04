#!/usr/bin/env python3
"""Prepare or check a private, local transcript coverage manifest (stdlib only)."""
import argparse
import hashlib
import json
import re
from pathlib import Path

TIMESTAMP = re.compile(r'(?<!\d)(\d{1,2}:\d{2}:\d{2})(?!\d)')
DISPOSITIONS = {'正文', '合并', '重复省略', '非课程交流', '待核实'}


def prepare(source, out):
    source = Path(source)
    if source.suffix.lower() not in {'.md', '.txt'}:
        raise ValueError('只接受UTF-8 Markdown或TXT；PDF和Word请先可靠提取。')
    data = source.read_bytes()
    content = data.decode('utf-8-sig')
    if not content.strip():
        raise ValueError('来源为空。')
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
        raise ValueError('coverage.json已存在；请保留原记录或选择新的工作目录。')
    manifest = {'source_name': source.name, 'sha256': hashlib.sha256(data).hexdigest(),
                'line_count': len(lines), 'segments': segments}
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'已生成 {target}，共{len(segments)}个区间；未上传来源。')


def check(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    cursor = 1
    problems = []
    for segment in data['segments']:
        if segment['start_line'] != cursor or segment['end_line'] < cursor:
            raise ValueError('区间不连续、重叠或顺序错误。')
        cursor = segment['end_line'] + 1
        if segment['disposition'] not in DISPOSITIONS:
            problems.append(segment['id'] + '：尚未填写有效处理方式')
        elif segment['disposition'] in {'正文', '合并'} and not segment['destination'].strip():
            problems.append(segment['id'] + '：缺少正文对应位置')
        elif segment['disposition'] in {'重复省略', '非课程交流', '待核实'} and not segment['reason'].strip():
            problems.append(segment['id'] + '：缺少处理说明')
    if cursor != data['line_count'] + 1:
        raise ValueError('区间没有覆盖原文全部行。')
    if problems:
        raise ValueError('\n'.join(problems))
    print('原文行号连续覆盖，处理记录完整；内容准确性仍需对照原文审阅。')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', nargs='?', type=Path)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--check', type=Path)
    args = parser.parse_args()
    try:
        if args.check:
            if args.source or args.out:
                parser.error('--check不能与来源或--out同时使用。')
            check(args.check)
        else:
            if args.source is None or args.out is None:
                parser.error('需提供来源与--out，或单独使用--check。')
            prepare(args.source, args.out)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, str(exc) + '\n')
