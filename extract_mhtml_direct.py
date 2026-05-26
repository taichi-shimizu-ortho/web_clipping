#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MHTML ファイルから BeautifulSoup で直接抽出
ul.rlist から参考文献を1行ずつ取得
"""

from pathlib import Path
import bs4
from bs4 import BeautifulSoup
from langchain_community.document_loaders import MHTMLLoader


def extract_from_mhtml_direct(mhtml_path: str) -> dict:
    """MHTML ファイルから本文と参考文献を直接抽出"""

    path = Path(mhtml_path)
    if not path.exists():
        print(f"❌ ファイルが見つかりません: {mhtml_path}")
        return {}

    print(f"📄 MHTML ファイル読み込み: {path.name}\n")

    try:
        # MHTML 全体を読み込む（HTML タグの構造を保持）
        loader = MHTMLLoader(
            file_path=str(path),
            open_encoding='utf-8',
        )

        docs = loader.load()
        if not docs:
            print("❌ ドキュメントが見つかりません")
            return {}

        # HTML 全体を BeautifulSoup で解析
        soup = BeautifulSoup(docs[0].page_content, 'html.parser')

        # 1. 本文を抽出
        print("=" * 80)
        print("1. 本文の抽出")
        print("=" * 80)

        article_section = soup.select_one('section.article-section.article-section__full')
        if article_section:
            body_text = article_section.get_text()
            print(f"✅ 本文セクション見つかった: {len(body_text)} 文字\n")
        else:
            print("❌ 本文セクションが見つかりません\n")
            body_text = ""

        # 2. 参考文献を抽出
        print("=" * 80)
        print("2. 参考文献の抽出 (ul.rlist li)")
        print("=" * 80)

        references = []
        ref_list = soup.find('ul', class_='rlist')

        if ref_list:
            li_items = ref_list.find_all('li')
            print(f"✅ ul.rlist 見つかった: {len(li_items)} 個の li 要素\n")

            for i, li in enumerate(li_items, 1):
                # li の内容をテキストで取得
                ref_text = li.get_text().strip()

                # 不要なキーワードを削除
                unwanted = ['View', 'Google Scholar', 'PubMed', 'Web of Science', 'Find Full Text', 'CAS']
                for kw in unwanted:
                    ref_text = ref_text.replace(kw, '')

                # 連続するスペースと改行を削除
                ref_text = ' '.join(ref_text.split())

                if ref_text:
                    references.append(ref_text)

                # 最初の3個をサンプル表示
                if i <= 3:
                    print(f"[{i}] {ref_text[:100]}...")

            print(f"\n✅ 参考文献抽出完了: {len(references)} 個")
        else:
            print("❌ ul.rlist が見つかりません\n")

        return {
            'success': True,
            'body_text': body_text,
            'references': references,
            'body_length': len(body_text),
            'ref_count': len(references)
        }

    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        mhtml_path = "Killian2019.mhtml"
    else:
        mhtml_path = sys.argv[1]

    result = extract_from_mhtml_direct(mhtml_path)

    if result.get('success'):
        print("\n" + "=" * 80)
        print("✅ 抽出成功")
        print("=" * 80)
        print(f"本文: {result['body_length']} 文字")
        print(f"参考文献: {result['ref_count']} 個")

        # 結果をファイルに保存（テスト用）
        with open('test_output.txt', 'w', encoding='utf-8') as f:
            f.write("# 本文\n\n")
            f.write(result['body_text'][:1000])
            f.write("\n\n# 参考文献\n\n")
            for i, ref in enumerate(result['references'][:5], 1):
                f.write(f"{i}. {ref}\n")

        print("\n✅ テスト出力: test_output.txt")
    else:
        print(f"❌ 失敗: {result.get('error')}")
