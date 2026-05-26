#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MHTML ファイルから本文と参考文献を抽出する
LangChain の MHTMLLoader を使用
"""

from pathlib import Path
from bs4 import BeautifulSoup
import bs4
from langchain_community.document_loaders import MHTMLLoader


def extract_from_mhtml(mhtml_path: str) -> dict:
    """MHTML ファイルから本文と参考文献を抽出"""

    path = Path(mhtml_path)
    if not path.exists():
        print(f"❌ ファイルが見つかりません: {mhtml_path}")
        return {}

    print(f"📄 MHTML ファイル読み込み: {path.name}")

    # LangChain の MHTMLLoader を使用
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
        print(f"✅ 抽出完了: {len(docs)} 個のドキュメント\n")

        # 抽出されたテキストを表示
        for i, doc in enumerate(docs, 1):
            content = doc.page_content[:200]
            print(f"[ドキュメント {i}] {len(doc.page_content)} 文字")
            print(f"  {content}...\n")

        return {
            'success': True,
            'documents': docs,
            'count': len(docs)
        }

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        mhtml_path = "Killian2019.mhtml"
    else:
        mhtml_path = sys.argv[1]

    result = extract_from_mhtml(mhtml_path)

    if result.get('success'):
        print("=" * 80)
        print(f"✅ 抽出成功: {result['count']} 個のドキュメント")
        print("=" * 80)
    else:
        print("=" * 80)
        print(f"❌ 抽出失敗: {result.get('error')}")
        print("=" * 80)
