#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wileyページの詳細構造を分析するスクリプト
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
    print("1. article-section__content 内部の詳細構造")
    print("=" * 80)

    article_section = soup.find('div', class_='article-section__content')
    if article_section:
        # 直下の子要素を見る
        print(f"Direct children of article-section__content:")
        for i, child in enumerate(article_section.children):
            if hasattr(child, 'name'):
                print(f"  {i}: {child.name}")
                if child.name == 'section':
                    # セクション内の最初の子要素
                    first_child = list(child.children)[0]
                    if hasattr(first_child, 'name'):
                        print(f"     First child in section: {first_child.name} - {str(first_child)[:100]}")

    print("\n" + "=" * 80)
    print("2. References セクションの詳細")
    print("=" * 80)

    # References セクションを見つける
    ref_section = None
    for section in soup.find_all('section'):
        heading = section.find(['h2', 'h3', 'h4'])
        if heading and 'References' in heading.get_text():
            ref_section = section
            print(f"Found References section with heading: {heading.get_text()}")
            print(f"Section HTML structure: {str(section)[:200]}...")

            # 参考文献リストを探す
            ol = section.find('ol')
            if ol:
                print(f"Found <ol> with {len(ol.find_all('li'))} items")
            else:
                div_class = section.find('div', class_=lambda x: x and 'citation' in x.lower())
                if div_class:
                    print(f"Found div with citation class: {div_class.get('class')}")
                else:
                    # テキスト内容を確認
                    text = section.get_text()[:200]
                    print(f"Section text: {text}...")
            break

    print("\n" + "=" * 80)
    print("3. 本文内の画像を識別")
    print("=" * 80)

    # article-section__content内の画像
    if article_section:
        images_in_content = article_section.find_all('img')
        print(f"Images in article-section__content: {len(images_in_content)}")

        for i, img in enumerate(images_in_content[:3]):
            src = img.get('src', '')
            alt = img.get('alt', '')
            parent = img.parent.name if img.parent else 'no parent'
            print(f"  Image {i}:")
            print(f"    src: {src[:80]}")
            print(f"    alt: {alt}")
            print(f"    parent: {parent}")

    print("\n" + "=" * 80)
    print("4. ABSTRACT/見出しの確認")
    print("=" * 80)

    # ABSTRACTの位置
    abstract_heading = None
    for h in soup.find_all(['h2', 'h3']):
        if 'ABSTRACT' in h.get_text():
            abstract_heading = h
            print(f"Found ABSTRACT heading: {h.name} - {h.get_text()}")

    # INTRODUCTION など他の見出し
    print("\nAll main headings in article-section__content:")
    if article_section:
        for heading in article_section.find_all(['h2', 'h3']):
            print(f"  {heading.name}: {heading.get_text()}")

    browser.close()
