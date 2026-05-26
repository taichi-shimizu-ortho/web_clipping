#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
論文の本文と参考文献を自動抽出してObsidian に統合するスクリプト

使用方法:
    python extract_full_article.py \
        --url "https://journals.lww.com/..." \
        --output "/path/to/article.md" \
        --publisher "lww"

処理内容:
    1. 本文（ArticleBody）を抽出
    2. 画像URLを取得（data-src属性）
    3. 参考文献を抽出
    4. Markdown形式に整形
    5. Obsidian の「# 4 Main Text」に追記
"""

import json
import argparse
import logging
import sys
import re
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
except ImportError:
    print("Error: playwright が必要です。以下でインストールしてください:")
    print("  pip install playwright")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: beautifulsoup4 が必要です。以下でインストールしてください:")
    print("  pip install beautifulsoup4")
    sys.exit(1)


# ============================================================================
# ロギング設定
# ============================================================================

def setup_logging(verbose: bool = False) -> logging.Logger:
    """ロギング設定"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)


logger = setup_logging()


# ============================================================================
# Publishers Config 管理
# ============================================================================

class PublisherConfig:
    """出版社設定を管理するクラス"""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """publishers_config.json を読み込む"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"設定ファイルが見つかりません: {self.config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"設定ファイルのJSONが無効です: {e}")
            sys.exit(1)

    def get_publisher(self, publisher_id: str) -> Optional[Dict]:
        """出版社設定を取得"""
        publishers = self.config.get('publishers', [])
        for pub in publishers:
            if pub.get('id') == publisher_id:
                return pub
        return None

    def list_publishers(self) -> List[str]:
        """利用可能な出版社のリストを取得"""
        return [pub.get('id') for pub in self.config.get('publishers', [])]


# ============================================================================
# 本文と画像抽出エンジン
# ============================================================================

class ArticleBodyExtractor:
    """論文の本文と画像を抽出するクラス"""

    def __init__(self, publisher_config: Dict, timeout: int = 30):
        self.publisher_config = publisher_config
        self.timeout = timeout
        self.body_html = None
        self.images = {}

    def extract(self, url: str) -> Tuple[str, Dict]:
        """
        URLから本文と画像を抽出

        Returns:
            (本文のHTML, 画像URLの辞書)
        """
        logger.info(f"ページを開く: {url}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            try:
                # ページに移動（domcontentloadedで十分）
                page.goto(url, wait_until="domcontentloaded", timeout=self.timeout * 1000)
                logger.info("ページロード完了")

                # クッキーダイアログを閉じる（存在する場合）
                try:
                    page.click("button:has-text('Accept All Cookies')", timeout=5000)
                    logger.debug("「Accept All Cookies」をクリックしました")
                    page.wait_for_timeout(2000)  # ダイアログが消えるまで待機
                except:
                    try:
                        page.click("button:has-text('Reject All Cookies')", timeout=5000)
                        logger.debug("「Reject All Cookies」をクリックしました")
                        page.wait_for_timeout(2000)
                    except:
                        logger.debug("クッキーダイアログは見つかりませんでした")

                # 本文を抽出
                self.body_html = page.content()

                # 画像URLを抽出
                self._extract_images(page)

                logger.info(f"{len(self.images)} 件の画像を抽出しました")

            except PlaywrightTimeoutError:
                logger.error(f"ページロードがタイムアウトしました（{self.timeout}秒）")
                sys.exit(1)
            finally:
                context.close()
                browser.close()

        return self.body_html, self.images

    def _extract_images(self, page):
        """ページから画像URLを抽出"""
        logger.debug("画像URLを抽出中...")

        try:
            images = page.evaluate("""
                () => {
                    const imgs = [];
                    const imgElements = document.querySelectorAll('img[data-src]');
                    imgElements.forEach((img, idx) => {
                        const src = img.getAttribute('data-src') || img.getAttribute('src');
                        const alt = img.getAttribute('alt') || `fig${idx + 1}`;
                        if (src) {
                            imgs.push({
                                key: `fig${idx + 1}`,
                                url: src,
                                alt: alt
                            });
                        }
                    });
                    return imgs;
                }
            """)

            for img in images:
                self.images[img['key']] = {
                    'url': img['url'],
                    'alt': img['alt']
                }

            logger.info(f"{len(self.images)} 件の画像URLを取得")

        except Exception as e:
            logger.warning(f"画像抽出に失敗: {e}")

    def get_markdown_body(self) -> str:
        """本文をMarkdown形式で取得"""
        if not self.body_html:
            return ""

        soup = BeautifulSoup(self.body_html, 'html.parser')

        # 出版社設定からセレクタを取得
        selector_config = self.publisher_config.get('articleBodySelector', {})
        selector_type = selector_config.get('type', 'section_id')
        selector_value = selector_config.get('value', 'ArticleBody')

        article_body = None

        # セレクタタイプに応じて本文を取得
        if selector_type == 'section_id':
            # LWW: <section id="ArticleBody">
            article_body = soup.find('section', {'id': selector_value})

        elif selector_type == 'class':
            # <div class="..."> または <section class="...">
            article_body = soup.find(class_=selector_value)

        elif selector_type == 'css':
            # CSSセレクタ: "section.article-section.article-section__full"
            results = soup.select(selector_value)
            if results:
                article_body = results[0]

        elif selector_type == 'xpath':
            logger.warning("XPath selector not supported in BeautifulSoup")

        # フォールバック
        if not article_body:
            logger.warning(f"指定されたセレクタで見つかりません: {selector_type}={selector_value}")
            article_body = soup.find('article')

        if not article_body:
            logger.error("本文セクションが見つかりません")
            return ""

        # テキストを抽出して整形
        markdown = self._parse_article_body(article_body)
        return markdown

    def _parse_article_body(self, body_element) -> str:
        """ArticleBody要素をMarkdown形式に変換"""
        markdown_lines = []

        for element in body_element.find_all(['h2', 'h3', 'p', 'img', 'table', 'figure']):
            if element.name == 'h2':
                text = element.get_text(strip=True)
                if text and text.lower() not in ['references', 'supplemental digital content', 'copyright', 'supporting information']:
                    markdown_lines.append(f"\n## {text}\n")

            elif element.name == 'h3':
                text = element.get_text(strip=True)
                if text and text.lower() not in ['limitations']:
                    markdown_lines.append(f"\n### {text}\n")

            elif element.name == 'p':
                text = element.get_text(strip=True)
                if text and len(text) > 5:
                    # 参考文献番号を処理
                    text = self._process_citation_numbers(text)
                    markdown_lines.append(f"{text}\n")

            elif element.name == 'img':
                # 画像を処理
                img_markdown = self._process_image(element)
                if img_markdown:
                    markdown_lines.append(img_markdown + "\n")

            elif element.name == 'figure':
                # figure タグ内の画像とキャプションを処理
                img = element.find('img')
                figcaption = element.find('figcaption')
                if img:
                    img_markdown = self._process_image(img)
                    if img_markdown:
                        markdown_lines.append(img_markdown + "\n")
                    if figcaption:
                        caption = figcaption.get_text(strip=True)
                        if caption:
                            markdown_lines.append(f"{caption}\n")

            elif element.name == 'table':
                # テーブルを処理
                markdown_lines.append(self._process_table(element) + "\n")

        return '\n'.join(markdown_lines)

    def _process_citation_numbers(self, text: str) -> str:
        """上付き参考文献番号を処理"""
        # <sup>1</sup> → ¹ に変換
        text = re.sub(r'<sup[^>]*>(\d+)</sup>', r'^\1', text)
        # 他の sup タグを削除
        text = re.sub(r'<sup[^>]*>.*?</sup>', '', text)
        return text

    def _process_image(self, img_element) -> Optional[str]:
        """画像要素を処理"""
        src = img_element.get('data-src') or img_element.get('src')
        if not src:
            return None

        alt = img_element.get('alt', 'image')
        return f"![{alt}]({src})"

    def _process_table(self, table_element) -> str:
        """テーブルをMarkdown形式に変換"""
        # シンプルな実装: テーブルはそのままテキストで出力
        text = table_element.get_text(separator=' | ', strip=True)
        return f"```\n{text}\n```"


# ============================================================================
# 参考文献抽出エンジン
# ============================================================================

class ReferenceExtractor:
    """LWW サイトから参考文献を抽出するクラス"""

    def __init__(self, publisher_config: Dict, timeout: int = 30):
        self.publisher_config = publisher_config
        self.timeout = timeout
        self.references = []

    def extract(self, url: str) -> List[str]:
        """
        URLから参考文献を抽出

        Returns:
            参考文献のMarkdown リスト
        """
        logger.info(f"参考文献を抽出中...")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            try:
                # ページに移動（domcontentloadedで十分）
                page.goto(url, wait_until="domcontentloaded", timeout=self.timeout * 1000)

                logger.info("ページロード完了。クッキーダイアログ処理開始...")

                # クッキーダイアログを閉じる（存在する場合）
                # プライベートブラウザでは自動消滅する可能性があるため、
                # 見つからなくても例外を出さない
                try:
                    # まず "Accept" を含むボタンを探す
                    accept_found = page.evaluate("""
                        () => {
                            const buttons = Array.from(document.querySelectorAll('button'));
                            const acceptBtn = buttons.find(btn =>
                                btn.textContent.includes('Accept') || btn.textContent.includes('accept')
                            );
                            if (acceptBtn) {
                                acceptBtn.click();
                                console.log('Clicked accept button');
                                return true;
                            }
                            return false;
                        }
                    """)

                    if accept_found:
                        logger.info("クッキーダイアログをクリックしました")
                        page.wait_for_timeout(3000)
                    else:
                        logger.info("クッキーダイアログが見つかりませんでした（自動消滅済みか）")
                        page.wait_for_timeout(2000)

                except Exception as e:
                    logger.warning(f"クッキー処理エラー（続行します）: {e}")
                    page.wait_for_timeout(2000)

                # 参考文献リストを展開
                self._expand_references(page)

                # 参考文献テキストを取得
                page_text = page.content()

                # 参考文献を抽出
                self.references = self._parse_references(page_text)

                logger.info(f"{len(self.references)} 件の参考文献を抽出しました")

            except PlaywrightTimeoutError:
                logger.error(f"ページロードがタイムアウトしました")
                sys.exit(1)
            finally:
                context.close()
                browser.close()

        return self.references

    def _expand_references(self, page):
        """参考文献リストを展開する（出版社別対応）"""
        logger.info("参考文献リストを展開中...")

        publisher_id = self.publisher_config.get('id', 'lww')

        try:
            if publisher_id == 'wiley':
                # Wiley: アコーディオンコントロールを展開
                logger.info("Wiley: アコーディオン展開ロジック実行")

                result = page.evaluate("""
                    () => {
                        // まず、すべてのアコーディオンコントロールを確認
                        const allControls = document.querySelectorAll('.accordion__control');
                        console.log(`Total accordion controls: ${allControls.length}`);

                        // aria-expanded=false のもののみをクリック
                        const collapsedControls = document.querySelectorAll('.accordion__control[aria-expanded="false"]');
                        console.log(`Collapsed controls: ${collapsedControls.length}`);

                        let expanded_count = 0;
                        collapsedControls.forEach((ctrl, idx) => {
                            try {
                                console.log(`Expanding accordion ${idx}...`);
                                ctrl.click();
                                expanded_count++;
                            } catch (e) {
                                console.error(`Error expanding ${idx}: ${e}`);
                            }
                        });

                        console.log(`Successfully expanded ${expanded_count} accordions`);
                        return {
                            total: allControls.length,
                            collapsed: collapsedControls.length,
                            expanded: expanded_count
                        };
                    }
                """)

                logger.info(f"Wiley: 合計 {result['total']} 個、展開前 {result['collapsed']} 個 → {result['expanded']} 個展開")
                page.wait_for_timeout(3000)  # DOM更新待機

                # 参考文献が見つかるか確認
                ref_count = page.evaluate("""
                    () => {
                        const refs = document.querySelectorAll('ul.rlist li');
                        return refs.length;
                    }
                """)
                logger.info(f"Wiley: 参考文献 {ref_count} 個が表示されました")

            else:
                # LWW: "View full references list" リンクをクリック
                logger.info("LWW: 参考文献展開ロジック実行")

                result = page.evaluate("""
                    () => {
                        const allLinks = Array.from(document.querySelectorAll('a, button, span'));
                        for (let el of allLinks) {
                            if (el.textContent.includes('View full references list')) {
                                el.click();
                                return true;
                            }
                        }
                        return false;
                    }
                """)

                if result:
                    logger.info("LWW: 参考文献リストを展開しました")
                    page.wait_for_timeout(3000)
                else:
                    logger.warning("LWW: 'View full references list' リンクが見つかりません")

        except Exception as e:
            logger.error(f"参考文献展開に失敗: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def _parse_references(self, html: str) -> List[str]:
        """HTMLから参考文献を解析する（出版社別対応）"""
        soup = BeautifulSoup(html, 'html.parser')

        references = []
        ref_count = 0

        # 出版社IDから適切なパーサーを選択
        publisher_id = self.publisher_config.get('id', 'lww')

        if publisher_id == 'wiley':
            # Wiley: <ul class="rlist separator"> 内の <li> を抽出
            ref_list = soup.find('ul', class_='rlist')
            logger.info(f"Wiley: rlist 要素見つかった: {ref_list is not None}")

            if ref_list:
                li_items = ref_list.find_all('li')
                logger.info(f"Wiley: <li> 要素数: {len(li_items)}")

                for idx, li in enumerate(li_items):
                    ref_text = li.get_text().strip()
                    if ref_text:
                        # テキスト長をログ
                        if idx < 3:  # 最初の3個のみログ
                            logger.debug(f"  [{idx}] テキスト長: {len(ref_text)}, 最初の100文字: {ref_text[:100]}")

                        # 番号と著者名の部分を整理
                        formatted = self._format_reference(ref_text)
                        if formatted:
                            references.append(formatted)
                            ref_count += 1
                        else:
                            if idx < 3:  # 最初の3個のみログ
                                logger.debug(f"  [{idx}] フォーマット後は空: {ref_text[:50]}")

                logger.info(f"Wiley参考文献パース完了: {ref_count} 件（{len(li_items)} 個の <li> から）")
                return references
            else:
                logger.warning("Wiley: <ul class='rlist'> が見つかりません")
                return []

        else:
            # LWW: テキストベースの抽出
            text = soup.get_text()

            # "References" で始まるセクションを特定
            ref_patterns = ["References\n", "## References\n", "## References"]
            ref_start = -1

            for pattern in ref_patterns:
                pos = text.find(pattern)
                if pos > 0:
                    ref_start = pos + len(pattern)
                    break

            if ref_start < 0:
                logger.warning("References セクションが見つかりません")
                return []

            ref_section = text[ref_start:]

            # セクションの終了を判定
            end_keywords = ['Copyright', 'Your Privacy', 'Terms of Use', '©']
            end_pos = len(ref_section)
            for keyword in end_keywords:
                pos = ref_section.find(keyword)
                if pos > 0:
                    end_pos = min(end_pos, pos)

            ref_section = ref_section[:end_pos]

            # 不要なテキストをフィルタリング
            unwanted_keywords = [
                'Cited Here', 'View Full Text', 'PubMed', 'CrossRef', 'Google Scholar',
                'Hide full references list', 'Supplemental Digital Content', 'SDC',
                'Copyright', 'Your Privacy', 'Terms of Use', '[Other]'
            ]

            # 参考文献は数字で始まる行
            lines = ref_section.split('\n')
            current_ref = ""

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # 不要なキーワードを含む行をスキップ
                skip_line = any(keyword in line for keyword in unwanted_keywords)
                if skip_line:
                    continue

                # 参考文献番号で始まっているか確認
                match_num = re.match(r'^(\d{1,2})\.\s+', line)
                if match_num:
                    if current_ref:
                        formatted = self._format_reference(current_ref)
                        if formatted:
                            references.append(formatted)
                            ref_count += 1
                    current_ref = line
                else:
                    if current_ref and line and not any(kw in line for kw in unwanted_keywords):
                        current_ref += " " + line

            # 最後の参考文献を保存
            if current_ref:
                formatted = self._format_reference(current_ref)
                if formatted:
                    references.append(formatted)
                    ref_count += 1

            logger.info(f"LWW参考文献パース完了: {ref_count} 件")
            return references

    def _format_reference(self, ref_text: str) -> Optional[str]:
        """参考文献テキストをMarkdown形式にフォーマット"""
        if not ref_text or len(ref_text.strip()) < 10:
            return None

        # 番号部分を削除
        ref_text = ref_text.lstrip('0123456789[]., \t')
        ref_text = ref_text.strip()

        if not ref_text:
            return None

        # ジャーナル名をイタリックに（簡易版）
        ref_text = self._italicize_journal_names(ref_text)

        return ref_text

    def _italicize_journal_names(self, text: str) -> str:
        """ジャーナル名をイタリック化する"""
        journal_patterns = [
            (r'J Bone Joint Surg', r'*J Bone Joint Surg*'),
            (r'Am J Sports Med', r'*Am J Sports Med*'),
            (r'Osteoarthritis Cartilage', r'*Osteoarthritis Cartilage*'),
            (r'Clin Orthop Relat Res', r'*Clin Orthop Relat Res*'),
            (r'J Arthroplasty', r'*J Arthroplasty*'),
            (r'J Orthop Res', r'*J Orthop Res*'),
            (r'Acta Orthop', r'*Acta Orthop*'),
            (r'Arthritis Rheumatol', r'*Arthritis Rheumatol*'),
            (r'Ann Rheum Dis', r'*Ann Rheum Dis*'),
            (r'Lab Anim', r'*Lab Anim*'),
            (r'Skeletal Radiol', r'*Skeletal Radiol*'),
            (r'Histopathology', r'*Histopathology*'),
            (r'Methods', r'*Methods*'),
        ]

        import re
        for pattern, replacement in journal_patterns:
            text = re.sub(pattern, replacement, text)

        return text


# ============================================================================
# Obsidian ファイル管理
# ============================================================================

class ObsidianFileUpdater:
    """Obsidian ファイルを更新するクラス"""

    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            logger.error(f"ファイルが見つかりません: {self.file_path}")
            sys.exit(1)

        self.content = self._read_file()

    def _read_file(self) -> str:
        """ファイルを読み込む"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _write_file(self, content: str):
        """ファイルに書き込む"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"ファイルを更新しました: {self.file_path}")

    def update_main_text(self, body_markdown: str, references: List[str]):
        """# 4 Main Text セクションを更新（見出しは既存のものを保持）"""

        # 既存の "# 4 Main Text" セクションを探す
        section_start_pattern = r'# 4 Main Text\n'
        section_start = re.search(section_start_pattern, self.content)

        if section_start:
            logger.info("既存の「# 4 Main Text」セクションを置き換えます")
            # セクション内容の開始位置（見出しの後ろ）
            start_pos = section_start.end()

            # 次のセクション（# 5）を探す
            next_section_pattern = r'\n# 5 '
            next_section = re.search(next_section_pattern, self.content[start_pos:])

            if next_section:
                # 次のセクションの直前までを置き換え
                end_pos = start_pos + next_section.start()
                self.content = self.content[:start_pos] + self._create_main_text_section(body_markdown, references) + self.content[end_pos:]
            else:
                # 次のセクションがない場合は最後まで置き換え
                self.content = self.content[:start_pos] + self._create_main_text_section(body_markdown, references)
        else:
            logger.warning("「# 4 Main Text」セクションが見つかりません。末尾に追加します")
            if not self.content.endswith('\n'):
                self.content += '\n'
            self.content += '# 4 Main Text\n'
            self.content += self._create_main_text_section(body_markdown, references)

        # ファイルに書き込む
        self._write_file(self.content)
        logger.info(f"「# 4 Main Text」セクションを更新しました")

    def _create_main_text_section(self, body_markdown: str, references: List[str]) -> str:
        """Main Text セクションを作成"""
        section = body_markdown.strip() + '\n\n'

        # 参考文献を追加
        if references:
            section += '## References\n\n'
            for i, ref in enumerate(references, 1):
                section += f'{i}. {ref}\n\n'

        return section


# ============================================================================
# メイン処理
# ============================================================================

def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='論文の本文と参考文献を自動抽出してObsidian の「# 4 Main Text」に統合',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  # URL から抽出
  python extract_full_article.py \\
    --url "https://journals.lww.com/jbjsjournal/fulltext/..." \\
    --output "/path/to/article.md" \\
    --publisher "lww"

  # MHTML ファイルから抽出
  python extract_full_article.py \\
    --mhtml "article.mhtml" \\
    --output "/path/to/article.md" \\
    --publisher "wiley"
        """
    )

    parser.add_argument(
        '--url', '-u',
        required=False,
        help='論文のURL'
    )
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='出力Obsidian ファイルパス'
    )
    parser.add_argument(
        '--publisher', '-p',
        default='lww',
        help='出版社ID（デフォルト: lww）'
    )
    parser.add_argument(
        '--config', '-c',
        default='publishers_config.json',
        help='publishers_config.json のパス'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='詳細ログを出力'
    )
    parser.add_argument(
        '--list-publishers',
        action='store_true',
        help='利用可能な出版社のリストを表示'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=60,
        help='ページロードのタイムアウト時間（秒、デフォルト: 60）'
    )

    args = parser.parse_args()

    # ロギング設定
    setup_logging(args.verbose)

    # 設定ファイルを読み込む
    config_path = Path(args.config)
    publisher_cfg = PublisherConfig(config_path)

    # 利用可能な出版社のリストを表示して終了
    if args.list_publishers:
        publishers = publisher_cfg.list_publishers()
        print("利用可能な出版社:")
        for pub_id in publishers:
            pub = publisher_cfg.get_publisher(pub_id)
            print(f"  - {pub_id}: {pub.get('name', 'N/A')}")
        return

    logger.info("=" * 70)
    logger.info("論文自動抽出ツール（本文＋参考文献）")
    logger.info("=" * 70)

    # 出版社設定を取得
    pub_config = publisher_cfg.get_publisher(args.publisher)
    if not pub_config:
        logger.error(f"出版社が見つかりません: {args.publisher}")
        logger.info(f"利用可能な出版社: {', '.join(publisher_cfg.list_publishers())}")
        sys.exit(1)

    logger.info(f"出版社: {pub_config.get('name', args.publisher)}")
    logger.info(f"URL: {args.url}")
    logger.info(f"出力ファイル: {args.output}")

    # 本文と参考文献を1回のブラウザセッションで抽出
    try:
        logger.info("\n▶ ステップ1: ページを開く")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            try:
                # ページに移動
                page.goto(args.url, wait_until="domcontentloaded", timeout=args.timeout * 1000)
                logger.info("ページロード完了")

                # クッキーダイアログを閉じる（出版社別対応）
                if pub_config.get('id') == 'wiley':
                    logger.debug("Wileyクッキーダイアログを処理中...")
                    try:
                        # Wiley固有のクッキーボタン（ここにセレクタを入れる）
                        page.click("button:has-text('Accept')", timeout=5000)
                        logger.debug("「Accept」をクリックしました")
                        page.wait_for_timeout(3000)
                    except:
                        logger.debug("Wileyクッキーボタンが見つかりません")
                else:
                    # LWW
                    try:
                        page.click("button:has-text('Accept All Cookies')", timeout=5000)
                        logger.debug("「Accept All Cookies」をクリックしました")
                        page.wait_for_timeout(2000)
                    except:
                        try:
                            page.click("button:has-text('Reject All Cookies')", timeout=5000)
                            logger.debug("「Reject All Cookies」をクリックしました")
                            page.wait_for_timeout(2000)
                        except:
                            logger.debug("クッキーダイアログは見つかりませんでした")

                # 本文を抽出
                logger.info("\n▶ ステップ1: 本文と画像を抽出")
                body_extractor = ArticleBodyExtractor(pub_config, timeout=args.timeout)
                body_html = page.content()
                body_extractor.body_html = body_html
                body_extractor._extract_images(page)
                body_markdown = body_extractor.get_markdown_body()

                if not body_markdown:
                    logger.error("本文を抽出できませんでした")
                    sys.exit(1)

                # 画像情報を取得
                images = body_extractor.images if hasattr(body_extractor, 'images') else []
                logger.info(f"0 件の画像URLを取得")
                logger.info(f"✓ 本文を抽出完了（{len(body_markdown)}文字）")

                # 参考文献を抽出
                logger.info("\n▶ ステップ2: 参考文献を抽出")

                # 参考文献を抽出
                if pub_config.get('id') == 'wiley':
                    # Wiley: アコーディオン展開なしで直接 ul.rlist li から抽出
                    logger.info("Wiley: ul.rlist から参考文献を直接抽出中...")
                    references = page.evaluate("""
                        () => {
                            const refs = [];
                            const liItems = document.querySelectorAll('ul.rlist li');
                            console.log(`Found ${liItems.length} li elements`);

                            liItems.forEach((li) => {
                                const text = li.textContent.trim();
                                if (text && text.length > 10) {
                                    refs.push(text);
                                }
                            });

                            return refs;
                        }
                    """)
                    logger.info(f"Wiley: {len(references)} 件の参考文献を抽出")
                else:
                    # LWW の場合はHTML解析
                    ref_extractor = ReferenceExtractor(pub_config, timeout=args.timeout)
                    page_text = page.content()
                    references = ref_extractor._parse_references(page_text)

                if not references:
                    logger.warning("参考文献を抽出できませんでした（継続）")
                    references = []

                logger.info(f"✓ 参考文献を抽出完了（{len(references)}件）")

            except PlaywrightTimeoutError:
                logger.error(f"ページロードがタイムアウトしました（{args.timeout}秒）")
                sys.exit(1)
            finally:
                context.close()
                browser.close()

        # Obsidian ファイルを更新
        logger.info("\n▶ ステップ3: Obsidian ファイルを更新")
        updater = ObsidianFileUpdater(args.output)
        updater.update_main_text(body_markdown, references)

        logger.info("=" * 70)
        logger.info("✅ 処理完了")
        logger.info(f"   本文: {len(body_markdown)} 文字")
        logger.info(f"   画像: {len(images)} 件")
        logger.info(f"   参考文献: {len(references)} 件")
        logger.info(f"   更新ファイル: {args.output}")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
