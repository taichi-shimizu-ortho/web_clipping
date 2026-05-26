#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MHTML から抽出したテキストをセクション別に処理
見出しと本文を分離、参考文献を抽出
"""

from pathlib import Path
import re
from bs4 import BeautifulSoup
import bs4
from langchain_community.document_loaders import MHTMLLoader


def extract_text_from_mhtml(mhtml_path: str) -> str:
    """MHTML ファイルからテキストを抽出"""

    path = Path(mhtml_path)
    if not path.exists():
        print(f"❌ ファイルが見つかりません: {mhtml_path}")
        return ""

    print(f"📄 MHTML ファイル読み込み: {path.name}")

    try:
        loader = MHTMLLoader(
            file_path=str(path),
            open_encoding='utf-8',
            bs_kwargs=dict(
                parse_only=bs4.SoupStrainer(
                    class_=("article-section article-section__full", "article-citation")
                ),
            ),
        )

        docs = loader.load()
        if not docs:
            print("❌ ドキュメントが見つかりません")
            return ""

        # 最初のドキュメントのテキストを返す
        text = docs[0].page_content
        print(f"✅ 抽出完了: {len(text)} 文字\n")
        return text

    except Exception as e:
        print(f"❌ エラー: {e}")
        return ""


def process_text(text: str) -> dict:
    """抽出されたテキストを処理"""

    print("=" * 80)
    print("テキスト処理")
    print("=" * 80 + "\n")

    # メタデータを削除（本文の開始を見つける）
    # 一般的なパターン: Introduction の最初の文
    body_start_patterns = [
        "The rising rate of osteoarthritis",  # Killian2019
        "Acetabular dysplasia is a common",    # 別の論文
        "ABSTRACT",                             # Abstract セクション
    ]

    body_start_idx = -1
    for pattern in body_start_patterns:
        idx = text.find(pattern)
        if idx != -1:
            body_start_idx = idx
            print(f"✅ 本文開始パターン検出: \"{pattern[:40]}...\"")
            break

    if body_start_idx != -1:
        # メタデータを削除
        removed_chars = body_start_idx
        text = text[body_start_idx:]
        print(f"✅ メタデータを削除: {removed_chars} 文字\n")
    else:
        print("⚠️  本文開始パターンが見つかりません（そのまま処理します）\n")

    # References セクションを分離
    ref_pattern = r'(REFERENCES|References)\s*\n(.*?)(?=\n[A-Z][A-Z\s]+$|\Z)'
    ref_match = re.search(ref_pattern, text, re.IGNORECASE | re.DOTALL)

    references_text = ""
    if ref_match:
        references_text = ref_match.group(2).strip()
        # References 前のテキストを本文とする
        body_text = text[:ref_match.start()]
    else:
        body_text = text

    print(f"本文: {len(body_text)} 文字")
    print(f"参考文献セクション: {len(references_text)} 文字\n")

    # 本文をセクションに分割（見出しは ## または ###）
    # まず、見出しを検出
    sections_list = []
    current_section = {"title": "Introduction", "content": ""}

    lines = body_text.split('\n')
    for line in lines:
        # 見出しを検出（大文字で始まり、短い）
        if re.match(r'^[A-Z][A-Z\s]*$', line.strip()) and 3 < len(line.strip()) < 50:
            # 新しいセクション
            if current_section["content"].strip():
                sections_list.append(current_section)
            current_section = {"title": line.strip(), "content": ""}
        else:
            current_section["content"] += line + "\n"

    # 最後のセクション
    if current_section["content"].strip():
        sections_list.append(current_section)

    print(f"セクション数: {len(sections_list)}\n")

    # 各セクションの概要を表示
    for sec in sections_list:
        title = sec["title"][:40]
        content_len = len(sec["content"])
        print(f"  - {title:40} ({content_len} 文字)")

    # 参考文献をクリーンアップ
    cleaned_refs = clean_references(references_text)
    print(f"\n参考文献数: {len(cleaned_refs)}")

    return {
        'sections': sections_list,
        'references': cleaned_refs,
        'body_length': len(body_text),
        'ref_length': len(references_text)
    }


def clean_references(ref_text: str) -> list:
    """参考文献テキストをクリーンアップ"""

    # 不要なキーワード
    unwanted_keywords = [
        'View',
        'Google Scholar',
        'PubMed',
        'Web of Science',
        'Find Full Text',
        'CAS',
        'Scopus',
        'CrossRef',
        'Search for more papers',
    ]

    # 参考文献を行ごとに分割
    lines = [line.strip() for line in ref_text.split('\n') if line.strip()]

    print(f"\n参考文献処理詳細:")
    print(f"  入力行数: {len(lines)}")
    print(f"  最初の5行:")
    for i, line in enumerate(lines[:5], 1):
        print(f"    [{i}] {line[:80]}")

    refs = []
    current_ref = []
    ref_num = 0

    for line in lines:
        # 数字で始まる行が新しい参考文献番号（1., 2., など）
        num_match = re.match(r'^(\d+)[\.\s]', line)
        if num_match:
            if current_ref:
                # 前の参考文献を保存
                ref_content = ' '.join(current_ref)
                # 不要なキーワードを削除
                for keyword in unwanted_keywords:
                    ref_content = re.sub(keyword, '', ref_content)
                # 連続するスペースを削除
                ref_content = re.sub(r'\s+', ' ', ref_content).strip()
                # 先頭の番号を削除
                ref_content = re.sub(r'^\d+[\.\s]+', '', ref_content).strip()
                if ref_content:
                    refs.append(ref_content)

            # 新しい参考文献を開始
            ref_num += 1
            current_ref = [line]
        else:
            # 現在の参考文献に追加（ただし不要なキーワードのみの行は除外）
            if line and not all(kw in line for kw in ['View', 'Scholar', 'PubMed']):
                current_ref.append(line)

    # 最後の参考文献
    if current_ref:
        ref_content = ' '.join(current_ref)
        for keyword in unwanted_keywords:
            ref_content = re.sub(keyword, '', ref_content)
        ref_content = re.sub(r'\s+', ' ', ref_content).strip()
        ref_content = re.sub(r'^\d+[\.\s]+', '', ref_content).strip()
        if ref_content:
            refs.append(ref_content)

    print(f"  出力参考文献数: {len(refs)}")
    if refs:
        print(f"  最初の参考文献: {refs[0][:100]}...")

    return refs


def format_as_markdown(processed: dict) -> str:
    """処理済みテキストを Markdown に整形"""

    markdown = ""

    # セクションを Markdown に
    for section in processed['sections']:
        title = section['title'].strip()
        content = section['content'].strip()

        if not title or not content:
            continue

        # 見出しレベルを決定（大文字でキーワードを含むか）
        if title in ['METHODS', 'RESULTS', 'DISCUSSION', 'INTRODUCTION', 'CONCLUSION']:
            markdown += f"\n## {title}\n\n"
        else:
            markdown += f"\n### {title}\n\n"

        markdown += content + "\n"

    # 参考文献を追加
    if processed.get('references'):
        markdown += "\n## References\n\n"
        for i, ref in enumerate(processed['references'], 1):
            markdown += f"{i}. {ref}\n"

    return markdown


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        mhtml_path = "Killian2019.mhtml"
    else:
        mhtml_path = sys.argv[1]

    # MHTML から抽出
    text = extract_text_from_mhtml(mhtml_path)
    if not text:
        exit(1)

    # テキスト処理
    processed = process_text(text)

    # Markdown 整形
    markdown = format_as_markdown(processed)

    # 出力ファイルに保存
    output_path = "processed_output.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown)

    print(f"\n✅ 処理完了")
    print(f"   出力: {output_path}")
    print(f"   サイズ: {len(markdown)} 文字")
