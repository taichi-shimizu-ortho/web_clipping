#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obsidianファイルの ## References セクション内の改行を整理する。
各要素が空行区切りの個別行になっているものを、1文献 = 1行に変換する。

使い方:
    python clean_references.py <obsidian_file>

例:
    python clean_references.py "C:/path/to/Sherwood2004.md"
"""

import re
import sys
from pathlib import Path


def get_tokens(text: str) -> list[str]:
    """空行を除去してトークンリストを作成"""
    return [t.strip() for t in text.split('\n') if t.strip()]


def reconstruct_references(tokens: list[str]) -> list[str]:
    """
    トークンリストを解析して 1文献 = 1文字列 のリストを返す。

    文献の区切り条件:
      - '–' の後の数字（終了ページ）の直後に、
        英字始まりの著者名 or 文献番号（1〜3桁の整数）が来る
    """
    refs = []
    current: list[str] = []
    prev_was_dash = False

    for i, token in enumerate(tokens):

        current.append(token)

        # '–' を記憶
        if token == '–':   # en dash
            prev_was_dash = True
            continue

        # ダッシュの直後の数字 → 終了ページ
        if prev_was_dash and re.match(r'^\d+$', token):
            prev_was_dash = False
            # 次のトークンを先読み
            if i + 1 < len(tokens):
                nxt = tokens[i + 1]
                is_new_ref = (
                    # 英字始まりでイタリック記号なし → 著者苗字
                    (re.match(r'^[A-Z]', nxt) and not nxt.startswith('*'))
                    # 1〜3桁の数字のみ → 文献番号
                    or re.match(r'^\d{1,3}$', nxt)
                )
                if is_new_ref:
                    refs.append(format_reference(current))
                    current = []
            else:
                # ファイル末尾
                refs.append(format_reference(current))
                current = []
            continue

        prev_was_dash = False

    # 残りをフラッシュ
    if current:
        refs.append(format_reference(current))

    return refs


def format_reference(tokens: list[str]) -> str:
    """
    トークンを結合してテキストを整形する。
    先頭の文献番号（数字のみ）があれば取り除く。
    """
    # 先頭が文献番号（1〜3桁の整数）なら除去
    if tokens and re.match(r'^\d{1,3}$', tokens[0]):
        tokens = tokens[1:]

    text = ' '.join(tokens)

    # 区切り記号の前後スペースを整理
    text = re.sub(r'\s+,\s+', ', ', text)
    text = re.sub(r'\s+:\s+', ': ', text)
    text = re.sub(r'\s+;\s+', '; ', text)
    text = re.sub(r'\s+\.\s+', '. ', text)
    text = re.sub(r'\s*–\s*', '–', text)   # – 前後スペース除去

    return text.strip()


def clean_references_in_file(filepath: str) -> bool:
    """
    Obsidianファイルの ## References セクションを整形する。
    元のセクションを 1文献 = 1行 に置き換える。
    """
    path = Path(filepath)
    if not path.exists():
        print(f"ERROR: File not found: {filepath}")
        return False

    print(f"Reading: {path.name}")
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # ## References セクションを探す
    ref_header = '## References'
    ref_start = content.find(ref_header)
    if ref_start == -1:
        print("ERROR: '## References' section not found")
        return False

    ref_body_start = ref_start + len(ref_header)

    # セクションの終わり: 次の ## 見出しまたはファイル末尾
    next_section = re.search(r'\n## ', content[ref_body_start:])
    if next_section:
        ref_body_end = ref_body_start + next_section.start()
    else:
        ref_body_end = len(content)

    ref_body = content[ref_body_start:ref_body_end]

    print(f"References section found ({len(ref_body)} chars)")

    # トークン化 → 文献再構成
    tokens = get_tokens(ref_body)
    print(f"Tokens: {len(tokens)}")

    refs = reconstruct_references(tokens)
    print(f"References reconstructed: {len(refs)}")

    # 整形済みセクションを作成
    new_ref_body = '\n\n' + '\n'.join(refs) + '\n'

    # ファイルを更新
    new_content = (
        content[:ref_body_start]
        + new_ref_body
        + content[ref_body_end:]
    )

    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"File updated: {path.name}")
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python clean_references.py <obsidian_file>")
        sys.exit(1)

    filepath = sys.argv[1]
    success = clean_references_in_file(filepath)
    if success:
        print("Done.")
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
