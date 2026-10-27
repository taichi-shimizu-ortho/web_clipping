"""Offline parser correctness and real-MHTML integration checks."""
import base64
import contextlib
import io
import re
import subprocess
import tempfile
import unittest
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import unquote

from extract_sciencedirect import article_markdown, compact, extract_sciencedirect, load_source
from extract_with_images import extract_from_mhtml_with_images, update_obsidian_file

ROOT = Path(__file__).resolve().parents[1]


def fixture(body=None):
    if body is None:
        body = '<h2>1. Introduction</h2><div>' + ('Generated cartilage text. ' * 60) + '</div>'
        body += '<h2>2. Results</h2><div>Signal <em>Ednrb</em> [<a data-xocs-content-type="reference">1</a>], CO<sub>2</sub> and 2<sup>\u2212\u0394\u0394ct</sup>.</div>'
        body += '<figure id="fig1"><span><img src="https://example.org/figure.png" alt="Fig. 1"></span><span class="captions"><span><p>Fig. 1. Histology.</p><div>Caption \u03b1 and \u03bc.</div></span></span></figure>'
    return ('<html><head><meta name="citation_pii" content="S123"><meta name="citation_title" content="Generated article"></head>'
            '<body><h1>Generated article</h1><div id="body">' + body + '</div>'
            '<div class="abstracts"><div class="abstract author"><h2>Abstract</h2><div>Generated abstract.</div></div></div>'
            '<ol class="references"><li><span class="label">[1]</span><span class="reference">'
            '<div>Author. CAS signaling and PubMed indexing in a review.</div>'
            '<div class="ReferenceLinks">Crossref Google Scholar View PDF</div></span></li></ol></body></html>')


class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'tmp')
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)

    def save_html(self, html):
        path = self.work / 'article.html'
        path.write_text(html, encoding='utf-8')
        return path

    def test_inline_unicode_captions_reference_ui(self):
        result = extract_sciencedirect(self.save_html(fixture()))
        text = result['body_markdown']
        self.assertIn('Signal *Ednrb* [1], CO<sub>2</sub>', text)
        self.assertIn('2<sup>\u2212\u0394\u0394ct</sup>', text)
        self.assertIn('Fig. 1. Histology.\n\nCaption \u03b1 and \u03bc.', text)
        self.assertEqual(result['references'], ['Author. CAS signaling and PubMed indexing in a review.'])
        self.assertIn('Generated abstract.', article_markdown(result))
        self.assertEqual(text.count('Fig. 1. Histology.'), 1)
        self.assertNotIn('\ufffd', text)

    def test_rejects_partial_or_challenge_pages(self):
        for html in ['<h1>Are you a robot?</h1>', fixture('<h2>Abstract</h2><p>Short.</p>'),
                     fixture().replace('2. Results', 'Section snippets')]:
            with self.subTest(html=html[:50]), self.assertRaises(ValueError):
                extract_sciencedirect(self.save_html(html))

    def test_mhtml_without_charset_selects_article_and_embedded_asset(self):
        message = EmailMessage()
        message.make_mixed()
        for html in ['<html>Advertisement</html>', fixture()]:
            part = EmailMessage()
            part.set_content(html.encode('utf-8'), maintype='text', subtype='html', cte='base64')
            message.attach(part)
        image = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aGZkAAAAASUVORK5CYII=')
        part = EmailMessage()
        part.set_content(image, maintype='image', subtype='png')
        part['Content-Location'] = 'https://example.org/figure.png'
        message.attach(part)
        source = self.work / 'saved.mhtml'
        source.write_bytes(message.as_bytes())
        result = extract_sciencedirect(source, self.work / 'assets', self.work)
        self.assertTrue(result['images'][0]['local'])
        self.assertEqual((self.work / result['images'][0]['target']).read_bytes(), image)
        self.assertIn('\u03b1', result['body_markdown'])
        self.assertEqual(result['warnings'], [])
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(extract_from_mhtml_with_images(str(source))['success'])

    def test_unembedded_images_are_reported(self):
        result = extract_sciencedirect(self.save_html(fixture()), self.work / 'assets', self.work)
        self.assertFalse(result['images'][0]['local'])
        self.assertEqual(len(result['warnings']), 1)

    def test_existing_note_sections_preserved(self):
        path = self.work / 'note.md'
        prefix, suffix = '# 1 Title\nKeep this\n\n# 4 Main Text\n', '\n# 5 Notes\nKeep these notes\n'
        path.write_text(prefix + 'old text' + suffix, encoding='utf-8')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(update_obsidian_file(str(path), 'new body\n'))
        self.assertEqual(path.read_text(encoding='utf-8'), prefix + 'new body\n' + suffix)

    @unittest.skipUnless((ROOT / 'Li 2026.mhtml').exists(), 'Local ScienceDirect article not present')
    def test_real_article_coverage_and_images(self):
        source = ROOT / 'Li 2026.mhtml'
        result = extract_sciencedirect(source, self.work / 'assets', self.work)
        soup, _, _ = load_source(source)
        self.assertEqual(len(result['images']), 6)
        self.assertEqual(len(result['references']), 46)
        self.assertEqual(result['warnings'], [])
        text = result['body_markdown']
        for heading in soup.select('#body h2, #body h3'):
            self.assertIn(compact(heading.get_text()), text.replace('*', ''))
        # Every main paragraph and caption must survive, including inline scientific symbols.
        plain = re.sub(r'</?(?:sup|sub)>', '', text).replace('*', '')
        plain = re.sub(r'(?<!!)\[([^\]]*)\]\([^)]+\)', r'\1', plain)
        for paragraph in soup.select('#body [id]'):
            if re.fullmatch(r'(?:p|fspara)\d+', paragraph['id']):
                value = compact(paragraph.get_text()).replace('*', '')
                self.assertTrue(re.sub(r'\s+', '', value) in re.sub(r'\s+', '', plain),
                                msg='Missing paragraph: ' + paragraph['id'])
        for image in result['images']:
            self.assertTrue((self.work / unquote(image['target'])).is_file())
        self.assertNotIn('Recommended articles', text)
        self.assertNotIn('\ufffd', article_markdown(result))
        self.assertEqual(len(result['metadata']['authors']), 8)
        with contextlib.redirect_stdout(io.StringIO()):
            auto = extract_from_mhtml_with_images(str(source))
        self.assertEqual(auto['body_markdown'].replace('https://ars.els-cdn.com/content/image/', 'URL/').count('!['), 6)
        self.assertEqual(auto['references'], result['references'])

    @unittest.skipUnless((ROOT / 'Killian2019.mhtml').exists(), 'Local Wiley article not present')
    def test_wiley_matches_repository_original(self):
        old_source = subprocess.check_output(['git', 'show', 'HEAD:extract_with_images.py'], cwd=ROOT).decode('utf-8')
        original = {'__name__': 'original_extractor'}
        exec(compile(old_source, 'original_extractor', 'exec'), original)
        with contextlib.redirect_stdout(io.StringIO()):
            before = original['extract_from_mhtml_with_images'](str(ROOT / 'Killian2019.mhtml'))
            after = extract_from_mhtml_with_images(str(ROOT / 'Killian2019.mhtml'))
        self.assertTrue(after['success'])
        self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()
