#!/usr/bin/env python3
"""Extract a legitimately saved ScienceDirect MHTML/HTML page, without networking."""
import argparse
import hashlib
import json
import re
from email import policy
from email.parser import BytesParser
from pathlib import Path
from urllib.parse import quote, urljoin, urlparse
from bs4 import BeautifulSoup, NavigableString, Tag

BODY_SELECTOR = '#body, .article-body, .Body'
BLOCKS = {'div', 'section', 'p', 'h2', 'h3', 'h4', 'h5', 'figure', 'ul', 'ol', 'table'}


def compact(text):
    return re.sub(r'\s+', ' ', text).strip()


def load_source(path):
    """Select the article HTML part, not a first-position advertising iframe."""
    path = Path(path)
    resources, candidates = {}, []
    if path.suffix.lower() in {'.mhtml', '.mht'}:
        message = BytesParser(policy=policy.default).parsebytes(path.read_bytes())
        for part in message.walk():
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            location = part.get('Content-Location', '')
            cid = part.get('Content-ID', '').strip('<>')
            if part.get_content_type() == 'text/html':
                # Chrome can omit MIME charset while retaining UTF-8 HTML.
                candidates.append((payload.decode(part.get_content_charset() or 'utf-8'), location))
            elif part.get_content_type().startswith('image/'):
                entry = (payload, part.get_content_type())
                if location:
                    resources[location] = entry
                if cid:
                    resources['cid:' + cid] = entry
    else:
        candidates = [(path.read_text(encoding='utf-8-sig'), '')]
    for html, location in candidates:
        soup = BeautifulSoup(html, 'html.parser')
        if soup.select_one('meta[name="citation_pii"]') and soup.select_one('h1'):
            return soup, location, resources
    raise ValueError('No ScienceDirect article HTML found. Save the full article page as MHTML.')


def inline(node, base_url=''):
    """Keep original inline spacing, citation punctuation and scientific exponents."""
    if isinstance(node, NavigableString):
        return str(node)
    if not isinstance(node, Tag) or node.name in {'script', 'style', 'button', 'svg'}:
        return ''
    if set(node.get('class', [])) & {'sr-only', 'list-label'}:
        return ''
    text = ''.join(inline(child, base_url) for child in node.children)
    if node.name in {'sub', 'sup'}:
        return f'<{node.name}>{text}</{node.name}>'
    if node.name in {'em', 'i'}:
        return f'*{text}*' if text.strip() else text
    if node.name in {'strong', 'b'}:
        return f'**{text}**' if text.strip() else text
    if node.name == 'br':
        return ' '
    if node.name == 'a':
        href = urljoin(base_url, node.get('href', ''))
        if node.get('data-xocs-content-type') == 'reference' or '#' in href:
            return text
        if urlparse(href).scheme in {'http', 'https'} and text.strip():
            return f'[{text}]({href})'
    return text


class Renderer:
    def __init__(self, resources, base_url, assets_dir=None, link_root=None):
        self.resources, self.base_url = resources, base_url
        self.assets_dir = Path(assets_dir) if assets_dir else None
        self.link_root = Path(link_root) if link_root else None
        self.images, self.warnings = [], []

    def figure(self, figure):
        lines = []
        for image in figure.find_all('img'):
            raw_src = image.get('data-src') or image.get('src', '')
            if not raw_src:
                continue
            src = urljoin(self.base_url, raw_src)
            target, local = src, False
            resource = self.resources.get(src)
            if resource and self.assets_dir:
                extensions = {'image/jpeg': '.jpg', 'image/png': '.png', 'image/gif': '.gif',
                              'image/webp': '.webp', 'image/svg+xml': '.svg'}
                extension = extensions.get(resource[1])
                if extension:
                    name = re.sub(r'[^A-Za-z0-9_-]', '_', figure.get('id', 'figure'))
                    name += '-' + hashlib.sha256(resource[0]).hexdigest()[:10] + extension
                    path = self.assets_dir / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(resource[0])
                    target = path.relative_to(self.link_root or path.parent.parent).as_posix()
                    local = True
            if self.assets_dir and not local:
                self.warnings.append(f'Image not embedded in MHTML; remote URL retained: {src}')
            alt = compact(image.get('alt', 'Figure')).replace('[', '(').replace(']', ')')
            lines.append(f'![{alt}]({quote(target, safe="/:?=&%#")})')
            self.images.append({'src': src, 'alt': alt, 'target': target, 'local': local})
        captions = figure.select_one('.captions, figcaption')
        if captions:
            lines.extend(self.blocks(captions))
        return lines

    def blocks(self, node):
        if not isinstance(node, Tag) or node.name in {'script', 'style', 'button', 'svg'}:
            return []
        if node.name in {'h2', 'h3', 'h4', 'h5'}:
            return ['#' * int(node.name[1]) + ' ' + compact(inline(node, self.base_url))]
        if node.name == 'figure':
            return self.figure(node)
        if node.name == 'table':
            rows = [[compact(inline(c, self.base_url)).replace('|', '\\|')
                     for c in row.find_all(['th', 'td'], recursive=False)]
                    for row in node.find_all('tr')]
            rows = [row for row in rows if row]
            if not rows:
                return []
            width = max(map(len, rows))
            rows = [row + [''] * (width - len(row)) for row in rows]
            rows.insert(1, ['---'] * width)
            return ['\n'.join('| ' + ' | '.join(row) + ' |' for row in rows)]
        if node.name in {'ul', 'ol'}:
            return ['\n'.join(('- ' if node.name == 'ul' else f'{i}. ') +
                              compact(inline(li, self.base_url))
                              for i, li in enumerate(node.find_all('li', recursive=False), 1))]
        block_children = [child for child in node.children
                          if isinstance(child, Tag) and (child.name in BLOCKS or child.find(list(BLOCKS)))]
        if node.name == 'p' or not block_children:
            value = compact(inline(node, self.base_url))
            return [value] if value else []
        result, pending = [], []
        for child in node.children:
            if isinstance(child, Tag) and (child.name in BLOCKS or child.find(list(BLOCKS))):
                value = compact(''.join(pending))
                if value:
                    result.append(value)
                pending = []
                result.extend(self.blocks(child))
            else:
                pending.append(inline(child, self.base_url))
        value = compact(''.join(pending))
        if value:
            result.append(value)
        return result


def extract_sciencedirect(path, assets_dir=None, link_root=None):
    soup, location, resources = load_source(path)
    metadata = {tag['name'][9:]: tag.get('content', '')
                for tag in soup.select('meta[name^="citation_"]')}
    pii = metadata.get('pii', '')
    base_url = f'https://www.sciencedirect.com/science/article/pii/{pii}' if pii else location
    body = soup.select_one(BODY_SELECTOR)
    if body is None or len(body.get_text(strip=True)) < 1000 or not body.select('h2, h3'):
        raise ValueError('Full article body missing or too short; abstract-only/challenge pages are not accepted.')
    if body.select_one('.section-snippets, .article-preview') or soup.find(
            ['h2', 'h3'], string=re.compile(r'^Section snippets$', re.I)):
        raise ValueError('ScienceDirect preview detected. Save the authenticated full-text page instead.')
    renderer = Renderer(resources, base_url, assets_dir, link_root)
    body_blocks = renderer.blocks(body)
    # Data availability is a sibling of #body in the current DOM.
    for section in soup.select('section[id^="da"]'):
        if body not in section.parents and section.find(['h2', 'h3'], string=re.compile('Data availability', re.I)):
            body_blocks.extend(renderer.blocks(section))
    references = []
    for li in soup.select('ol.references > li'):
        reference = BeautifulSoup(str(li.select_one('.reference') or li), 'html.parser')
        for control in reference.select('.ReferenceLinks, .reference-links, button, svg'):
            control.decompose()
        text = compact(reference.get_text(' ', strip=True))
        text = re.sub(r'^\[\d+\]\s*', '', text)
        if text:
            references.append(text)
    if not references:
        renderer.warnings.append('No references found. Check that the saved page includes the reference list.')
    abstracts, highlights = [], []
    for abstract in soup.select('#abstracts > .abstract, .abstracts > .abstract'):
        destination = highlights if 'author-highlights' in abstract.get('class', []) else abstracts
        for child in abstract.find_all(recursive=False):
            if child.name != 'h2':
                destination.extend(renderer.blocks(child))
    authors = [compact(node.get_text(' ', strip=True)) for node in soup.select(
        '#author-group .react-xocs-alternative-link')]
    metadata['authors'] = list(dict.fromkeys(authors))
    return {'success': True, 'publisher': 'sciencedirect', 'metadata': metadata,
            'source_url': base_url, 'body_markdown': '\n\n'.join(body_blocks) + '\n',
            'abstract_markdown': '\n\n'.join(abstracts), 'highlights_markdown': '\n\n'.join(highlights),
            'references': references, 'images': renderer.images, 'warnings': renderer.warnings}


def article_markdown(result):
    meta = result['metadata']
    lines = ['# 1 Title', meta.get('title', ''), '# 2 Basic Information',
             '- Authors: ' + '; '.join(meta.get('authors', [])),
             '- Journal: ' + meta.get('journal_title', ''),
             '- Published: ' + meta.get('publication_date', ''),
             '- Online: ' + meta.get('online_date', ''), '- Volume: ' + meta.get('volume', ''),
             '- Article: ' + meta.get('firstpage', ''), '- DOI: https://doi.org/' + meta.get('doi', ''),
             '- Source: ' + result['source_url'], '# 3 Abstract', result['abstract_markdown']]
    if result['highlights_markdown']:
        lines += ['## Highlights', result['highlights_markdown']]
    lines += ['# 4 Main Text', result['body_markdown'], '# 5 References',
              '\n\n'.join(f'{i}. {reference}' for i, reference in enumerate(result['references'], 1))]
    return '\n\n'.join(lines).rstrip() + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='Saved .mhtml, .mht or .html full-text page')
    parser.add_argument('--output', '-o', required=True, type=Path, help='New Obsidian Markdown note')
    parser.add_argument('--force', action='store_true', help='Replace an existing output note')
    args = parser.parse_args()
    if args.output.exists() and not args.force:
        parser.error('Output exists; choose another filename or explicitly use --force.')
    try:
        result = extract_sciencedirect(args.source, args.output.parent / (args.output.stem + '_assets'),
                                       args.output.parent)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(article_markdown(result), encoding='utf-8')
        manifest = {key: value for key, value in result.items() if not key.endswith('markdown')}
        manifest['source_sha256'] = hashlib.sha256(args.source.read_bytes()).hexdigest()
        args.output.with_suffix('.extraction.json').write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    except (OSError, ValueError, LookupError) as error:
        parser.exit(1, f'Extraction failed: {error}\n')
    print(f'Output: {args.output}\nBody: {len(result["body_markdown"])} characters\n'
          f'Figures: {len(result["images"])}\nReferences: {len(result["references"])}')
    for warning in result['warnings']:
        print('WARNING: ' + warning)


if __name__ == '__main__':
    main()
