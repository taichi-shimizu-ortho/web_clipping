#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MHTML ファイルを解析して、HTML 構造を確認するツール
画像URL、参考文献URL、見出しなどを詳細に分析
"""

import re
from pathlib import Path
from email import message_from_string
from bs4 import BeautifulSoup
import base64
import quopri  # Quoted-Printable デコード

def extract_all_html_parts(mhtml_path: str) -> list:
    """MHTML ファイルからすべての HTML パートを抽出"""
    with open(mhtml_path, 'rb') as f:
        content = f.read()

    html_parts = []

    # すべての <!DOCTYPE と <html を見つける
    for match_bytes in [b'<!DOCTYPE', b'<!doctype', b'<html', b'<HTML']:
        start = 0
        while True:
            pos = content.find(match_bytes, start)
            if pos == -1:
                break

            # このパートの開始位置
            part_start = pos

            # 次のバウンダリを見つける
            boundary_pos = content.find(b'\n--', part_start)
            if boundary_pos == -1:
                boundary_pos = len(content)

            # HTML パートを抽出
            html_bytes = content[part_start:boundary_pos]
            html_text = html_bytes.decode('utf-8', errors='ignore')

            # Quoted-Printable デコード
            if '=3D' in html_text or '=0A' in html_text:
                html_text = quopri.decodestring(html_text.encode('utf-8')).decode('utf-8', errors='ignore')

            if html_text.strip():
                html_parts.append(html_text)

            start = pos + 1

    return html_parts


def extract_html_from_mhtml(mhtml_path: str) -> str:
    """MHTML ファイルから最初の HTML を抽出（互換性のため保持）"""
    parts = extract_all_html_parts(mhtml_path)
    if parts:
        return parts[0]
    return ""

def analyze_mhtml(mhtml_path: str):
    """MHTML ファイルを詳細に分析"""
    path = Path(mhtml_path)
    if not path.exists():
        print(f"❌ ファイルが見つかりません: {mhtml_path}")
        return

    print("=" * 80)
    print(f"MHTML 分析: {path.name}")
    print("=" * 80)

    # すべての HTML パートを抽出
    html_parts = extract_all_html_parts(str(path))
    if not html_parts:
        print("❌ HTML を抽出できませんでした")
        return

    print(f"✅ {len(html_parts)} 個の HTML パートを見つけました\n")

    # 各パートをチェックして、本文を含むものを探す
    article_section = None
    selected_html = None

    for i, html_content in enumerate(html_parts, 1):
        print(f"[パート {i}] HTML サイズ: {len(html_content)} 文字")

        soup = BeautifulSoup(html_content, 'html.parser')

        # section 要素の数を確認
        sections = soup.find_all('section')
        print(f"         section 要素: {len(sections)}")

        # article-section__full を探す
        test_section = soup.select_one('section.article-section.article-section__full')
        if test_section:
            print(f"         ✅ article-section__full を発見！")
            article_section = test_section
            selected_html = html_content
            break

        print()

    if not article_section:
        print("\n❌ article-section__full が見つかりません")
        print("抽出された各パートの先頭を確認して、該当要素を探してください")
        return

    # 最後に選択されたパートを保存
    with open('extracted_html.html', 'w', encoding='utf-8') as f:
        f.write(selected_html)
    print(f"\n✅ 選択されたパートを保存: extracted_html.html\n")

    if not article_section:
        print("⚠️  article-section__full が見つかりません")
        print("\n実際に存在するセクション:")

        # 存在する section を探す
        sections = soup.find_all('section')
        print(f"合計 section 要素: {len(sections)}\n")

        for i, sec in enumerate(sections[:10], 1):
            class_name = sec.get('class', [])
            id_name = sec.get('id', '')
            print(f"[{i}] class: {' '.join(class_name) if class_name else 'N/A':50} id: {id_name}")

        # 別の候補を試す
        article_section = soup.find('section', class_='article-section')
        if not article_section:
            article_section = soup.find('article')

        if not article_section:
            print("\n❌ 本文セクションが見つかりません")
            return

    print("\n✅ 本文セクションを見つけました\n")

    # 1. 見出しの構造
    print("=" * 80)
    print("1. 見出しの構造 (h2, h3, strong)")
    print("=" * 80)

    headings = article_section.find_all(['h2', 'h3', 'strong'])
    for h in headings[:20]:  # 最初の20個
        print(f"{h.name:8} {h.get_text().strip()[:60]}")

    # 2. 画像の詳細
    print("\n" + "=" * 80)
    print("2. 画像 (src, data-src)")
    print("=" * 80)

    images = article_section.find_all('img')
    print(f"合計画像数: {len(images)}\n")

    for i, img in enumerate(images, 1):
        src = img.get('src', 'N/A')
        data_src = img.get('data-src', 'N/A')
        alt = img.get('alt', '')[:40]
        print(f"[{i}] src: {src[:70]}")
        if data_src != 'N/A':
            print(f"    data-src: {data_src[:70]}")
        if alt:
            print(f"    alt: {alt}")
        print()

    # 3. 参考文献セクション
    print("=" * 80)
    print("3. 参考文献セクション (ul.rlist)")
    print("=" * 80)

    ref_list = article_section.find('ul', class_='rlist')
    if ref_list:
        li_items = ref_list.find_all('li')
        print(f"合計参考文献数: {len(li_items)}\n")

        # 最初の3個をサンプル表示
        for i, li in enumerate(li_items[:3], 1):
            text = li.get_text().strip()[:100]
            print(f"[{i}] {text}...")
        print()
    else:
        print("❌ ul.rlist が見つかりません\n")

    # 4. 段落の数
    print("=" * 80)
    print("4. 段落 (<p>)")
    print("=" * 80)

    paragraphs = article_section.find_all('p')
    print(f"合計段落数: {len(paragraphs)}\n")

    # 最初の3段落をサンプル表示
    for i, p in enumerate(paragraphs[:3], 1):
        text = p.get_text().strip()[:80]
        print(f"[{i}] {text}...")

    # 5. テーブル
    print("\n" + "=" * 80)
    print("5. テーブル (<table>)")
    print("=" * 80)

    tables = article_section.find_all('table')
    print(f"合計テーブル数: {len(tables)}\n")

    # 6. リンク (参考文献のURL確認)
    print("=" * 80)
    print("6. 参考文献内のリンク (<a>)")
    print("=" * 80)

    if ref_list:
        links = ref_list.find_all('a')
        print(f"参考文献内のリンク数: {len(links)}\n")

        for i, link in enumerate(links[:5], 1):
            href = link.get('href', 'N/A')
            text = link.get_text().strip()[:40]
            print(f"[{i}] {text}")
            print(f"    href: {href[:70]}")

    print("\n" + "=" * 80)
    print("分析完了")
    print("=" * 80)

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        mhtml_path = "Killian2019.mhtml"
        print(f"使用方法: python analyze_mhtml.py <mhtml_file>")
        print(f"デフォルト: {mhtml_path}\n")
    else:
        mhtml_path = sys.argv[1]

    analyze_mhtml(mhtml_path)
