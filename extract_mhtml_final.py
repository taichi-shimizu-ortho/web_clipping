#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MHTML ファイルから HTML を抽出して Obsidian に統合
本文、画像、参考文献を HTML 形式で保存
"""

from pathlib import Path
import re
import bs4
from bs4 import BeautifulSoup
from langchain_community.document_loaders import MHTMLLoader


def extract_from_mhtml_html(mhtml_path: str) -> dict:
    """MHTML ファイルから本文と参考文献を HTML 形式で抽出"""

    path = Path(mhtml_path)
    if not path.exists():
        print(f"❌ ファイルが見つかりません: {mhtml_path}")
        return {}

    print(f"📄 MHTML ファイル読み込み: {path.name}\n")

    try:
        # MHTML 全体を読み込む
        loader = MHTMLLoader(
            file_path=str(path),
            open_encoding='utf-8',
            bs_kwargs=dict(features='html.parser'),
        )

        docs = loader.load()
        if not docs:
            print("❌ ドキュメントが見つかりません")
            return {}

        # HTML を解析
        soup = BeautifulSoup(docs[0].page_content, 'html.parser')

        # デバッグ：HTML の先頭を確認
        html_preview = docs[0].page_content[:500]
        print(f"HTML 先頭: {html_preview}\n")

        # 1. 本文セクションを抽出
        print("=" * 80)
        print("1. 本文セクション抽出")
        print("=" * 80)

        article_section = soup.select_one('section.article-section.article-section__full')

        # フォールバック：別のセレクタを試す
        if not article_section:
            print("⚠️  article-section__full が見つかりません。別のセレクタを試します...")
            article_section = soup.find('section', class_='article-section')

        if not article_section:
            print("⚠️  article-section も見つかりません。main/article を試します...")
            article_section = soup.find('main') or soup.find('article')

        if not article_section:
            print("❌ 本文セクションが見つかりません")
            print(f"利用可能なセクション: {[sec.get('class') for sec in soup.find_all('section')[:5]]}")
            return {}

        print(f"✅ 本文セクション見つかった\n")

        # 2. 参考文献を抽出（ul.rlist から）
        print("=" * 80)
        print("2. 参考文献抽出")
        print("=" * 80)

        references = []
        ref_list = soup.find('ul', class_='rlist')

        if ref_list:
            li_items = ref_list.find_all('li')
            print(f"✅ ul.rlist 見つかった: {len(li_items)} 個\n")

            for i, li in enumerate(li_items, 1):
                ref_text = li.get_text().strip()

                # 不要なキーワードを削除
                unwanted = ['View', 'Google Scholar', 'PubMed', 'Web of Science', 'Find Full Text', 'CAS', 'Scopus']
                for kw in unwanted:
                    ref_text = re.sub(kw, '', ref_text)

                # 連続するスペースを削除
                ref_text = ' '.join(ref_text.split())

                if ref_text and len(ref_text) > 20:
                    references.append(ref_text)

            print(f"✅ 参考文献抽出完了: {len(references)} 個\n")
        else:
            print("❌ ul.rlist が見つかりません\n")

        # 3. HTML を生成
        print("=" * 80)
        print("3. HTML 生成")
        print("=" * 80)

        html_content = generate_html(article_section, references)
        print(f"✅ HTML 生成完了: {len(html_content)} 文字\n")

        return {
            'success': True,
            'html_content': html_content,
            'ref_count': len(references),
            'html_length': len(html_content)
        }

    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


def generate_html(article_section, references: list) -> str:
    """本文と参考文献から HTML を生成"""

    html_parts = []

    # 本文をセクションごとに処理
    current_section = None

    for element in article_section.find_all(['h2', 'h3', 'p', 'img']):
        if element.name == 'h2':
            text = element.get_text(strip=True)
            if text and text.lower() not in ['references', 'supplemental digital content']:
                html_parts.append(f"<h2>{text}</h2>\n")

        elif element.name == 'h3':
            text = element.get_text(strip=True)
            if text and text.lower() not in ['limitations']:
                html_parts.append(f"<h3>{text}</h3>\n")

        elif element.name == 'p':
            text = element.get_text(strip=True)
            if text and len(text) > 5:
                html_parts.append(f"<p>{text}</p>\n")

        elif element.name == 'img':
            src = element.get('src', '')
            if src:
                alt = element.get('alt', 'figure')
                html_parts.append(f'<figure>\n  <img src="{src}" alt="{alt}">\n  <figcaption>{alt}</figcaption>\n</figure>\n')

    # 参考文献を追加
    if references:
        html_parts.append("<h2>References</h2>\n")
        html_parts.append("<ol>\n")
        for ref in references:
            html_parts.append(f"  <li>{ref}</li>\n")
        html_parts.append("</ol>\n")

    return ''.join(html_parts)


def update_obsidian_file(obsidian_path: str, html_content: str) -> bool:
    """Obsidian ファイルの # 4 Main Text セクションを更新"""

    path = Path(obsidian_path)
    if not path.exists():
        print(f"❌ ファイルが見つかりません: {obsidian_path}")
        return False

    print(f"📝 Obsidian ファイルを更新: {path.name}")

    # ファイルを読み込む
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # # 4 Main Text セクションを見つけて置き換え
    pattern = r'(# 4 Main Text\n)(.*?)(?=\n# 5 |\Z)'
    match = re.search(pattern, content, re.DOTALL)

    if match:
        # セクション内容を置き換え
        new_content = content[:match.start(2)] + html_content + content[match.end(2):]

        # ファイルに書き込む
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
        print("使用方法: python extract_mhtml_final.py <mhtml_file> <obsidian_file>")
        print("例: python extract_mhtml_final.py Killian2019.mhtml ../../Killian2019.md")
        sys.exit(1)

    mhtml_path = sys.argv[1]
    obsidian_path = sys.argv[2]

    # MHTML から抽出
    result = extract_from_mhtml_html(mhtml_path)

    if result.get('success'):
        print("=" * 80)
        print("✅ 抽出成功")
        print("=" * 80)
        print(f"HTML コンテンツ: {result['html_length']} 文字")
        print(f"参考文献: {result['ref_count']} 個\n")

        # Obsidian ファイルを更新
        if update_obsidian_file(obsidian_path, result['html_content']):
            print("=" * 80)
            print("✅ 処理完了")
            print("=" * 80)
        else:
            print("=" * 80)
            print("❌ 処理に問題がありました")
            print("=" * 80)
    else:
        print(f"❌ 抽出失敗: {result.get('error')}")
