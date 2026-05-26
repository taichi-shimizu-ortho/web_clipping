#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wileyページのテスト
ユーザーが手動でクッキーをクリックできるようにブラウザを開いたまま待機
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time

url = "https://onlinelibrary.wiley.com/doi/10.1002/jor.24146"

print("=" * 80)
print("Wileyページをブラウザで開きます")
print("=" * 80)
print("\n手動でクッキー許可をクリックしてください")
print("その後、ページが読み込まれるまで待機します...\n")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(url, wait_until="domcontentloaded", timeout=90000)

    print("✓ ページが開きました")
    print("✓ 自動で30秒待機します（その間にクッキーをクリックしてください）\n")

    for i in range(30, 0, -1):
        print(f"待機中... {i}秒", end="\r")
        time.sleep(1)

    print("\n✓ クッキー処理完了\n")

    # ページの現在の状態を確認
    html = page.content()
    soup = BeautifulSoup(html, 'html.parser')

    print("=" * 80)
    print("現在のページ状態を確認中...")
    print("=" * 80)

    # 本文セクションを確認
    article_section = soup.select('section.article-section.article-section__full')
    if article_section:
        print(f"✓ 本文セクション: 見つかりました ({len(article_section)}個)")
    else:
        print("✗ 本文セクション: 見つかりません")

    # 参考文献リストを確認
    ref_list = soup.find('ul', class_='rlist')
    if ref_list:
        li_items = ref_list.find_all('li')
        print(f"✓ 参考文献リスト: 見つかりました ({len(li_items)}個の参考文献)")
    else:
        print("✗ 参考文献リスト: 見つかりません")

    # アコーディオンコントロールを確認
    accordion_controls = soup.find_all('div', class_='accordion__control')
    print(f"✓ アコーディオンコントロール: {len(accordion_controls)}個")

    print("\n" + "=" * 80)
    print("次に、アコーディオンを自動で展開します...\n")

    # アコーディオンを展開
    try:
        controls = page.query_selector_all('.accordion__control')
        print(f"✓ JavaScriptで {len(controls)} 個のアコーディオンを見つけました")

        for i, control in enumerate(controls):
            is_expanded = control.evaluate('el => el.getAttribute("aria-expanded")')
            print(f"  [{i+1}] aria-expanded = {is_expanded}")

            if is_expanded == "false":
                print(f"       → クリック中...")
                control.click()
                page.wait_for_timeout(1500)
    except Exception as e:
        print(f"✗ エラー: {e}")

    print("\n✓ アコーディオン展開完了\n")

    # 再度参考文献リストを確認
    print("=" * 80)
    print("展開後のページを確認中...")
    print("=" * 80)

    html_after = page.content()
    soup_after = BeautifulSoup(html_after, 'html.parser')

    ref_list_after = soup_after.find('ul', class_='rlist')
    if ref_list_after:
        li_items_after = ref_list_after.find_all('li')
        print(f"✓ 参考文献リスト: {len(li_items_after)}個の参考文献が取得可能です")

        print("\n最初の3つの参考文献:")
        for i, li in enumerate(li_items_after[:3]):
            ref_text = li.get_text().strip()[:100]
            print(f"  {i+1}. {ref_text}...")
    else:
        print("✗ 参考文献リスト: まだ見つかりません")

    print("\n" + "=" * 80)
    print("テスト完了")
    print("ブラウザは開いたままです（確認後に閉じてください）")
    print("=" * 80)

    # ブラウザを開いたままにする
    input("\nEnterキーを押してブラウザを閉じます...")
    browser.close()
