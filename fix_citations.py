#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""引用番号フォーマット修正スクリプト"""

import re
import sys
from pathlib import Path

def fix_citations(filepath):
    """
    引用番号のフォーマットを修正
    パターン: word1number → word. (number)
    改行がある場合はスペース不要
    """
    path = Path(filepath)
    if not path.exists():
        print(f"ERROR: File not found: {filepath}")
        return False

    print(f"Processing: {path.name}")
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # パターン: 文字の直後に数字（カンマ可）、その後改行または文字
    def replace_citation(m):
        before = m.group(1)
        num = m.group(2)
        after = m.group(3)
        if after == '\n':
            return before + '. (' + num + ')\n'
        else:
            return before + '. (' + num + ') ' + after

    content_new = re.sub(
        r'([a-zA-Z])(\d+(?:,\d+)*)(\n|[a-zA-Z])',
        replace_citation,
        content
    )

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content_new)

    print("Done: Citation format fixed")
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python fix_citations.py <file_path>")
        sys.exit(1)

    filepath = sys.argv[1]
    fix_citations(filepath)
