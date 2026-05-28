#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract article from Wiley URL using Playwright"""

from pathlib import Path
import re
import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


async def extract_from_wiley_url(url: str) -> dict:
    """Extract article content from Wiley URL using Playwright"""

    print(f"Loading Wiley article: {url}")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()

            print("\nLoading page...")
            try:
                await page.goto(url, wait_until="load", timeout=60000)
            except:
                print("WARNING: Page load timeout, continuing anyway...")
                pass

            # Wait a bit for JavaScript to execute
            print("Waiting for content to render...")
            await page.wait_for_timeout(3000)

            # Try to close cookie dialog if present
            try:
                await page.click('button[data-testid="cookie-banner-close"]', timeout=5000)
                print("Closed cookie banner")
            except:
                pass

            # Wait for article content to load
            print("Waiting for article section...")
            try:
                await page.wait_for_selector('section.article-section__full', timeout=20000)
            except:
                print("WARNING: Article section timeout, attempting to extract anyway...")

            # Get page content
            html_content = await page.content()
            await browser.close()

            print("OK: Page loaded successfully")

            soup = BeautifulSoup(html_content, 'html.parser')

            print("\n" + "=" * 80)
            print("1. EXTRACTING ARTICLE SECTION")
            print("=" * 80)

            article_section = soup.find('section', class_='article-section__full')
            if not article_section:
                print("Article section not found")
                return {}

            print("Article section found")

            # Extract base URL (domain + /cms path)
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

            body_content = await extract_body_content_with_images(page, article_section, base_url)
            print(f"Body content: {len(body_content['markdown'])} chars")
            print(f"Images found: {len(body_content['images'])}")

            print("\n" + "=" * 80)
            print("2. EXTRACTING REFERENCES")
            print("=" * 80)

            references = extract_references(soup)
            print(f"References found: {len(references)}\n")

            return {
                'success': True,
                'body_markdown': body_content['markdown'],
                'images': body_content['images'],
                'references': references
            }

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False}


async def extract_body_content_with_images(page, section, base_url: str) -> dict:
    """Extract body text and images using JavaScript for correct URLs"""
    markdown_lines = []
    images = []

    for element in section.find_all(['h2', 'h3', 'p', 'img']):
        if element.name == 'h2':
            text = element.get_text(strip=True)
            if text and text.lower() not in ['references', 'supplemental digital content']:
                markdown_lines.append(f"\n## {text}\n")

        elif element.name == 'h3':
            text = element.get_text(strip=True)
            if text and text.lower() not in ['limitations']:
                markdown_lines.append(f"\n### {text}\n")

        elif element.name == 'p':
            text = element.get_text(strip=True)
            if text and len(text) > 5:
                markdown_lines.append(f"{text}\n")

        elif element.name == 'img':
            # Try to get src from element
            src = element.get('src', '')
            data_src = element.get('data-src', '')
            alt = element.get('alt', 'figure')

            # Use data-src if src is not valid, or if src looks like a placeholder
            if data_src and (not src or 'placeholder' in src.lower() or 'data:' in src):
                src = data_src

            # Convert relative URLs to absolute URLs
            if src:
                if src.startswith('/'):
                    # Relative URL - add base domain
                    src = base_url.rstrip('/') + src

                if 'http' in src:  # Only use if it's a valid URL
                    img_markdown = f"![{alt}]({src})\n"
                    markdown_lines.append(img_markdown)
                    images.append({'src': src, 'alt': alt})

    return {
        'markdown': ''.join(markdown_lines),
        'images': images
    }


def extract_references(soup) -> list:
    """Extract references from article"""
    references = []

    ref_section = soup.find('section', class_='article-section__references')
    if not ref_section:
        print("Reference section not found")
        return references

    ref_list = ref_section.find('ul', class_='rlist')
    if not ref_list:
        print("Reference list not found")
        return references

    li_items = ref_list.find_all('li', recursive=False)
    print(f"Found {len(li_items)} references")

    for li in li_items:
        ref_text = li.get_text().strip()

        unwanted = ['View', 'Google Scholar', 'PubMed', 'Web of Science', 'Find Full Text', 'CAS', 'Scopus', 'CrossRef']
        for kw in unwanted:
            ref_text = re.sub(kw, '', ref_text, flags=re.IGNORECASE)

        ref_text = ' '.join(ref_text.split())

        if ref_text and len(ref_text) > 20:
            references.append(ref_text)

    return references


def generate_markdown(body_markdown: str, references: list) -> str:
    """Generate Markdown output"""
    md_parts = [body_markdown]

    if references:
        md_parts.append("\n## References\n\n")
        for ref in references:
            md_parts.append(f"{ref}\n")

    return ''.join(md_parts)


def update_obsidian_file(obsidian_path: str, markdown_content: str) -> bool:
    """Update Obsidian file with new content"""
    path = Path(obsidian_path)
    if not path.exists():
        print(f"FILE NOT FOUND: {obsidian_path}")
        return False

    print(f"Updating Obsidian file: {path.name}")

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = r'(# 4 Main Text\n)(.*?)(?=\n# 5 |\Z)'
    match = re.search(pattern, content, re.DOTALL)

    if match:
        new_content = content[:match.start(2)] + markdown_content + content[match.end(2):]
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("File updated\n")
        return True
    else:
        print("'# 4 Main Text' section not found\n")
        return False


async def main():
    import sys

    if len(sys.argv) < 3:
        print("Usage: python extract_from_url.py <url> <obsidian_file>")
        sys.exit(1)

    url = sys.argv[1]
    obsidian_path = sys.argv[2]

    result = await extract_from_wiley_url(url)

    if result.get('success'):
        print("=" * 80)
        print("3. GENERATING MARKDOWN")
        print("=" * 80)

        markdown_content = generate_markdown(result['body_markdown'], result['references'])
        print(f"Markdown generated: {len(markdown_content)} chars\n")

        print("=" * 80)
        print("4. UPDATING OBSIDIAN FILE")
        print("=" * 80)

        if update_obsidian_file(obsidian_path, markdown_content):
            print("=" * 80)
            print("COMPLETED")
            print("=" * 80)
            print(f"\nResults:")
            print(f"  Body: {len(result['body_markdown'])} chars")
            print(f"  Images: {len(result['images'])}")
            print(f"  References: {len(result['references'])}")
        else:
            print("=" * 80)
            print("ERROR UPDATING FILE")
            print("=" * 80)
    else:
        print("Extraction failed")


if __name__ == '__main__':
    asyncio.run(main())
