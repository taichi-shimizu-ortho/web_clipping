#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract MHTML with images and references to Markdown"""

from pathlib import Path
import re
from bs4 import BeautifulSoup
from email import message_from_binary_file


def extract_mhtml_html_content(mhtml_path: str) -> str:
    """Extract HTML content from MHTML file"""
    path = Path(mhtml_path)
    with open(path, 'rb') as f:
        msg = message_from_binary_file(f)

    for part in msg.walk():
        if part.get_content_type() == 'text/html':
            payload = part.get_payload(decode=True)
            if payload:
                return payload.decode('utf-8', errors='ignore')

    raise ValueError("HTML part not found in MHTML file")


def extract_from_mhtml_with_images(mhtml_path: str) -> dict:
    """Extract article content from MHTML"""
    path = Path(mhtml_path)
    if not path.exists():
        print(f"FILE NOT FOUND: {mhtml_path}")
        return {}

    print(f"Loading MHTML: {path.name}")

    try:
        html_content = extract_mhtml_html_content(str(path))
        soup = BeautifulSoup(html_content, 'html.parser')

        print("\n" + "=" * 80)
        print("1. EXTRACTING ARTICLE SECTION")
        print("=" * 80)

        article_section = soup.find('section', class_='article-section__full')
        if not article_section:
            article_section = soup.find('section', class_='article-section')

        if not article_section:
            print("Article section not found")
            return {}

        print("Article section found")

        body_content = extract_body_content(article_section)
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


def extract_body_content(section) -> dict:
    """Extract body text and images in order"""
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
            src = element.get('src', '')
            if src:
                alt = element.get('alt', 'figure')
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
        for i, ref in enumerate(references, 1):
            md_parts.append(f"{i}. {ref}\n")

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


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 3:
        print("Usage: python extract_with_images.py <mhtml_file> <obsidian_file>")
        sys.exit(1)

    mhtml_path = sys.argv[1]
    obsidian_path = sys.argv[2]

    result = extract_from_mhtml_with_images(mhtml_path)

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
