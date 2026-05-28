#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug: Check image elements in Wiley article"""

import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


async def debug_images():
    """Debug image extraction"""
    url = "https://onlinelibrary.wiley.com/doi/10.1002/jor.24146"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print(f"Loading: {url}")
        try:
            await page.goto(url, wait_until="load", timeout=60000)
        except:
            print("⚠️ Timeout, continuing...")
            pass

        await page.wait_for_timeout(3000)

        # Try to close cookie banner
        try:
            await page.click('button[data-testid="cookie-banner-close"]', timeout=5000)
        except:
            pass

        # Wait for article section
        try:
            await page.wait_for_selector('section.article-section__full', timeout=20000)
        except:
            pass

        # Get HTML
        html_content = await page.content()
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find article section
        article_section = soup.find('section', class_='article-section__full')

        if article_section:
            # Find all img tags
            img_tags = article_section.find_all('img')
            print(f"\n✅ Found {len(img_tags)} img tags in article section\n")

            # Show details of first few images
            for i, img in enumerate(img_tags[:5], 1):
                print(f"Image {i}:")
                print(f"  src: {img.get('src', 'NO SRC')[:80]}")
                print(f"  data-src: {img.get('data-src', 'NO DATA-SRC')[:80]}")
                print(f"  alt: {img.get('alt', 'NO ALT')}")
                print(f"  class: {img.get('class', [])}")
                print()

            # Check for picture tags
            picture_tags = article_section.find_all('picture')
            print(f"✅ Found {len(picture_tags)} picture tags\n")

            for i, pic in enumerate(picture_tags[:3], 1):
                print(f"Picture {i}:")
                sources = pic.find_all('source')
                for src in sources:
                    print(f"  source srcset: {src.get('srcset', 'NO SRCSET')[:80]}")
                img = pic.find('img')
                if img:
                    print(f"  img src: {img.get('src', 'NO SRC')[:80]}")
                print()

            # Check for figure tags
            figure_tags = article_section.find_all('figure')
            print(f"✅ Found {len(figure_tags)} figure tags")

        await browser.close()


asyncio.run(debug_images())
