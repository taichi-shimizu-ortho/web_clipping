#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""引用番号フォーマット修正スクリプト

対象パターン: word.12,31 Next  →  word. (12,31) Next
条件:
  - ピリオドの直前が英字
  - ピリオドの直後が数字（カンマ区切り可）
  - 数字の直後がスペース＋大文字英字（文頭）、または改行
  - Fig. や Figure. は対象外（大文字1文字のみの次の字は除外）

処理範囲: # 4 Main Text セクションのみ
"""

import re
import sys
from pathlib import Path


def fix_citations(filepath):
    path = Path(filepath)
    if not path.exists():
        print(f"ERROR: File not found: {filepath}")
        return False

    print(f"Processing: {path.name}")
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # # 4 Main Text セクションを抽出
    section_header = '# 4 Main Text'
    start = content.find(section_header)
    if start == -1:
        print("ERROR: '# 4 Main Text' section not found")
        return False

    body_start = start + len(section_header)

    # 次の # 見出し（レベル1）またはファイル末尾
    next_h1 = re.search(r'\n# ', content[body_start:])
    if next_h1:
        body_end = body_start + next_h1.start()
    else:
        body_end = len(content)

    section = content[body_start:body_end]
    print(f"Section length: {len(section)} chars")

    count = [0]

    def replace_mid(m):
        """letter . digits<space>UPPERCASE → letter. (digits) UPPERCASE"""
        count[0] += 1
        return m.group(1) + '. (' + m.group(2) + ') ' + m.group(3)

    def replace_eol(m):
        """letter . digits<newline> → letter. (digits)<newline>"""
        count[0] += 1
        return m.group(1) + '. (' + m.group(2) + ')\n'

    # パターン1: word.12 Next  （大文字+小文字で始まる次の単語）
    # (?=[a-z]) で Fig.1 A–D のような単独大文字を除外
    section_new = re.sub(
        r'([a-zA-Z])\.(\d+(?:,\d+)*) ([A-Z])(?=[a-z])',
        replace_mid,
        section
    )

    # パターン2: word.12<改行>
    section_new = re.sub(
        r'([a-zA-Z])\.(\d+(?:,\d+)*)\n',
        replace_eol,
        section_new
    )

    print(f"Replacements: {count[0]}")

    new_content = content[:body_start] + section_new + content[body_end:]

    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print("Done.")
    return True


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python fix_citations.py <file_path>")
        sys.exit(1)

    fix_citations(sys.argv[1])
