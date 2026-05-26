#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MHTML からテキストを抽出 → HTML に整形 → Obsidian に保存
シンプルで確実なアプローチ
"""

from pathlib import Path
import re
import bs4
from bs4 import BeautifulSoup
from langchain_community.document_loaders import MHTMLLoader


def extract_text_from_mhtml(mhtml_path: str) -> str:
    """MHTML からテキストを抽出"""

    path = Path(mhtml_path)
    if not path.exists():
        print(f"❌ ファイルが見つかりません: {mhtml_path}")
        return ""

    print(f"📄 MHTML ファイル読み込み: {path.name}")

    try:
        loader = MHTMLLoader(
            file_path=str(path),
            open_encoding='utf-8',
            bs_kwargs=dict(features='html.parser'),
        )

        docs = loader.load()
        if not docs:
            print("❌ ドキュメントが見つかりません")
            return ""

        text = docs[0].page_content
        print(f"✅ テキスト抽出: {len(text)} 文字\n")
        return text

    except Exception as e:
        print(f"❌ エラー: {e}")
        return ""


def process_and_clean_text(text: str) -> dict:
    """テキストを処理して整理"""

    print("=" * 80)
    print("テキスト処理")
    print("=" * 80 + "\n")

    # メタデータを削除（本文の開始を見つける）
    body_start_patterns = [
        "The rising rate of osteoarthritis",
        "Acetabular dysplasia is a common",
    ]

    body_start_idx = -1
    for pattern in body_start_patterns:
        idx = text.find(pattern)
        if idx != -1:
            body_start_idx = idx
            print(f"✅ 本文開始検出: \"{pattern[:40]}...\"")
            break

    if body_start_idx != -1:
        text = text[body_start_idx:]
        print(f"✅ メタデータ削除\n")

    # References セクションを分離
    ref_pattern = r'(REFERENCES|References)\s*\n(.*?)(?=\Z)'
    ref_match = re.search(ref_pattern, text, re.IGNORECASE | re.DOTALL)

    references_text = ""
    if ref_match:
        references_text = ref_match.group(2).strip()
        body_text = text[:ref_match.start()]
    else:
        body_text = text

    print(f"本文: {len(body_text)} 文字")
    print(f"参考文献セクション: {len(references_text)} 文字\n")

    # 本文をセクションに分割
    sections = split_sections(body_text)
    print(f"セクション数: {len(sections)}\n")

    # 参考文献をクリーンアップ
    references = clean_references(references_text)
    print(f"参考文献数: {len(references)}\n")

    return {
        'sections': sections,
        'references': references
    }


def split_sections(text: str) -> list:
    """テキストをセクションに分割"""

    sections = []
    current_section = {"title": "Introduction", "content": ""}

    lines = text.split('\n')
    for line in lines:
        # 見出しを検出（大文字で始まり、短い）
        if re.match(r'^[A-Z][A-Z\s]*$', line.strip()) and 3 < len(line.strip()) < 50:
            # 新しいセクション
            if current_section["content"].strip():
                sections.append(current_section)
            current_section = {"title": line.strip(), "content": ""}
        else:
            current_section["content"] += line + "\n"

    # 最後のセクション
    if current_section["content"].strip():
        sections.append(current_section)

    return sections


def clean_references(ref_text: str) -> list:
    """参考文献をクリーンアップ"""

    unwanted_keywords = [
        'View', 'Google Scholar', 'PubMed', 'Web of Science',
        'Find Full Text', 'CAS', 'Scopus', 'CrossRef'
    ]

    lines = [line.strip() for line in ref_text.split('\n') if line.strip()]

    refs = []
    current_ref = []

    for line in lines:
        # 数字で始まる行が参考文献番号
        if re.match(r'^(\d+)[\.\s]', line):
            if current_ref:
                ref_content = ' '.join(current_ref)
                for kw in unwanted_keywords:
                    ref_content = re.sub(kw, '', ref_content)
                ref_content = re.sub(r'\s+', ' ', ref_content).strip()
                ref_content = re.sub(r'^\d+[\.\s]+', '', ref_content).strip()
                if ref_content and len(ref_content) > 20:
                    refs.append(ref_content)

            current_ref = [line]
        else:
            if line and not all(kw in line for kw in ['View', 'Scholar']):
                current_ref.append(line)

    # 最後の参考文献
    if current_ref:
        ref_content = ' '.join(current_ref)
        for kw in unwanted_keywords:
            ref_content = re.sub(kw, '', ref_content)
        ref_content = re.sub(r'\s+', ' ', ref_content).strip()
        ref_content = re.sub(r'^\d+[\.\s]+', '', ref_content).strip()
        if ref_content and len(ref_content) > 20:
            refs.append(ref_content)

    return refs


def generate_html(processed: dict) -> str:
    """処理済みテキストを HTML に変換"""

    html_parts = []

    # セクションを HTML に
    for section in processed['sections']:
        title = section['title'].strip()
        content = section['content'].strip()

        if not title or not content:
            continue

        # 見出しレベルを決定
        if title in ['METHODS', 'RESULTS', 'DISCUSSION', 'INTRODUCTION', 'CONCLUSION']:
            html_parts.append(f"<h2>{title}</h2>\n")
        else:
            html_parts.append(f"<h3>{title}</h3>\n")

        # 段落に分割
        for paragraph in content.split('\n\n'):
            if paragraph.strip():
                html_parts.append(f"<p>{paragraph.strip()}</p>\n")

    # 参考文献を追加
    if processed['references']:
        html_parts.append("<h2>References</h2>\n")
        html_parts.append("<ol>\n")
        for ref in processed['references']:
            html_parts.append(f"  <li>{ref}</li>\n")
        html_parts.append("</ol>\n")

    return ''.join(html_parts)


def update_obsidian_file(obsidian_path: str, html_content: str) -> bool:
    """Obsidian ファイルを更新"""

    path = Path(obsidian_path)
    if not path.exists():
        print(f"❌ ファイルが見つかりません: {obsidian_path}")
        return False

    print(f"📝 Obsidian ファイル更新: {path.name}")

    # ファイルを読み込む
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # # 4 Main Text セクションを置き換え
    pattern = r'(# 4 Main Text\n)(.*?)(?=\n# 5 |\Z)'
    match = re.search(pattern, content, re.DOTALL)

    if match:
        new_content = content[:match.start(2)] + html_content + content[match.end(2):]

        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"✅ ファイル更新完了\n")
        return True
    else:
        print("❌ '# 4 Main Text' セクションが見つかりません\n")
        return False


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 3:
        print("使用方法: python extract_and_save.py <mhtml_file> <obsidian_file>")
        sys.exit(1)

    mhtml_path = sys.argv[1]
    obsidian_path = sys.argv[2]

    # MHTML からテキストを抽出
    text = extract_text_from_mhtml(mhtml_path)
    if not text:
        exit(1)

    # テキストを処理
    processed = process_and_clean_text(text)

    # HTML を生成
    print("=" * 80)
    print("HTML 生成")
    print("=" * 80 + "\n")
    html_content = generate_html(processed)
    print(f"✅ HTML 生成: {len(html_content)} 文字\n")

    # Obsidian ファイルを更新
    print("=" * 80)
    print("Obsidian ファイル更新")
    print("=" * 80 + "\n")

    if update_obsidian_file(obsidian_path, html_content):
        print("=" * 80)
        print("✅ 処理完了！")
        print("=" * 80)
    else:
        print("=" * 80)
        print("❌ 処理に問題がありました")
        print("=" * 80)
