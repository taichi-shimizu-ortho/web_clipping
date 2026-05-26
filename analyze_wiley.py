#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wileyページの構造を分析するスクリプト
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

url = "https://onlinelibrary.wiley.com/doi/10.1002/jor.24146"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(url, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(3000)

    html = page.content()
    soup = BeautifulSoup(html, 'html.parser')

    print("=" * 80)
    print("1. article-section__content の内容確認")
    print("=" * 80)

    article_section = soup.find('div', class_='article-section__content')
    if article_section:
        # サブセクションを見つける
        sections = article_section.find_all('section')
        print(f"Found {len(sections)} sections:")
        for i, section in enumerate(sections[:5]):  # 最初の5個のセクション
            heading = section.find(['h2', 'h3', 'h4'])
            heading_text = heading.get_text() if heading else "No heading"
            print(f"  Section {i}: {heading_text}")
    else:
        print("article-section__content not found!")

    print("\n" + "=" * 80)
    print("2. References セクションの確認")
    print("=" * 80)

    # References セクションを探す
    all_text = soup.get_text()
    if "REFERENCES" in all_text:
        print("REFERENCES heading found in page text")
        ref_section = soup.find('section', string=lambda s: s and 'REFERENCES' in s)
        if ref_section:
            print(f"Reference section found: {ref_section.name}")

    # H2 タグでReferencesを探す
    ref_heading = None
    for heading in soup.find_all(['h2', 'h3', 'h4']):
        if 'References' in heading.get_text():
            ref_heading = heading
            print(f"Found References heading: {heading.get_text()}")
            break

    print("\n" + "=" * 80)
    print("3. 画像の確認")
    print("=" * 80)

    images = soup.find_all('img')
    print(f"Total images found: {len(images)}")
    for i, img in enumerate(images[:5]):
        src = img.get('src', 'no src')
        data_src = img.get('data-src', 'no data-src')
        alt = img.get('alt', 'no alt')
        print(f"  Image {i}: src={src[:50] if src else 'none'}...")
        if data_src:
            print(f"           data-src={data_src[:50]}")

    print("\n" + "=" * 80)
    print("4. ページ構造（トップレベル）")
    print("=" * 80)

    # main 要素を確認
    main = soup.find('main')
    if main:
        print("Found <main> element")

    # article 要素を確認
    article = soup.find('article')
    if article:
        print("Found <article> element")

    browser.close()
