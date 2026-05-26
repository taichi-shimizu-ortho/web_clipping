#!/usr/bin/env python3
"""
論文からreference リストを自動抽出してObsidian ノートに統合するスクリプト

使用方法:
    python extract_references.py \
        --url "https://journals.lww.com/..." \
        --output "/path/to/article.md" \
        --publisher "lww" \
        --section "5 Full Article Text"

要件:
    - selenium または playwright
    - beautifulsoup4
    - requests
"""

import json
import argparse
import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict
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
        logger.info(f"ページを開く: {url}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            try:
                # ページに移動
                page.goto(url, wait_until="networkidle", timeout=self.timeout * 1000)
                logger.info("ページロード完了")

                # クッキーダイアログを閉じる（存在する場合）
                try:
                    page.click("button:has-text('Reject All Cookies')", timeout=5000)
                    logger.debug("クッキーダイアログを閉じました")
                except:
                    logger.debug("クッキーダイアログは見つかりませんでした")

                # 参考文献リストを展開
                self._expand_references(page)

                # 参考文献テキストを取得
                page_text = page.content()

                # 参考文献を抽出
                self.references = self._parse_references(page_text)

                logger.info(f"{len(self.references)} 件の参考文献を抽出しました")

            except PlaywrightTimeoutError:
                logger.error(f"ページロードがタイムアウトしました（{self.timeout}秒）")
                sys.exit(1)
            finally:
                context.close()
                browser.close()

        return self.references

    def _expand_references(self, page):
        """参考文献リストを展開する"""
        logger.debug("参考文献リストを展開中...")

        try:
            # "View full references list" リンクを探してクリック
            page.evaluate("""
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

            # リンククリック後の読み込みを待機
            page.wait_for_timeout(2000)
            logger.debug("参考文献リストが展開されました")

        except Exception as e:
            logger.warning(f"参考文献展開に失敗: {e}")

    def _parse_references(self, html: str) -> List[str]:
        """HTMLから参考文献を解析する"""
        soup = BeautifulSoup(html, 'html.parser')

        references = []
        ref_count = 0

        # テキストから参考文献セクションを取得
        text = soup.get_text()

        # "References" 以降のテキストを抽出
        if "References" in text:
            ref_start = text.index("References") + len("References")
            ref_section = text[ref_start:]

            # 参考文献は通常、数字で始まる行
            lines = ref_section.split('\n')
            current_ref = ""

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # 参考文献番号で始まっているか確認
                if line and (line[0].isdigit() or line.startswith('[')):
                    if current_ref:
                        # 前の参考文献を保存
                        formatted = self._format_reference(current_ref)
                        if formatted:
                            references.append(formatted)
                            ref_count += 1
                    current_ref = line
                else:
                    # 続きを追加
                    if current_ref:
                        current_ref += " " + line

            # 最後の参考文献を保存
            if current_ref:
                formatted = self._format_reference(current_ref)
                if formatted:
                    references.append(formatted)
                    ref_count += 1

        logger.info(f"パース完了: {ref_count} 件の参考文献を処理しました")
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
        # "J Bone Joint Surg" などをイタリックに変換
        ref_text = self._italicize_journal_names(ref_text)

        return ref_text

    def _italicize_journal_names(self, text: str) -> str:
        """ジャーナル名をイタリック化する"""
        # 一般的なジャーナル名パターン
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
            (r'Arthritis', r'*Arthritis*'),
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

    def append_references(self, references: List[str], section_name: str = "5 Full Article Text"):
        """参考文献セクションを追加または更新"""

        # 既存の## References セクションを削除（あれば）
        if "\n## References\n" in self.content:
            logger.info("既存の## References セクションを置き換えます")
            # Conclusion 部分を見つけて、その後のReferences セクションを削除
            parts = self.content.split("\n## References\n")
            self.content = parts[0]

        # 参考文献セクションを作成
        ref_section = self._create_reference_section(references)

        # ファイルの最後に追加
        if not self.content.endswith('\n'):
            self.content += '\n'

        self.content += ref_section

        # ファイルに書き込む
        self._write_file(self.content)

        logger.info(f"{len(references)} 件の参考文献を追加しました")

    def _create_reference_section(self, references: List[str]) -> str:
        """参考文献セクションを作成"""
        section = "\n## References\n\n"

        for i, ref in enumerate(references, 1):
            section += f"{i}. {ref}\n\n"

        return section


# ============================================================================
# メイン処理
# ============================================================================

def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='論文から参考文献を自動抽出してObsidian に統合',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  python extract_references.py \\
    --url "https://journals.lww.com/jbjsjournal/fulltext/..." \\
    --output "/path/to/Kamenaga2021.md" \\
    --publisher "lww"
        """
    )

    parser.add_argument(
        '--url', '-u',
        required=True,
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
        '--section', '-s',
        default='5 Full Article Text',
        help='更新対象のセクション名'
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
    logger.info("論文参考文献自動抽出ツール")
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

    # 参考文献を抽出
    try:
        extractor = ReferenceExtractor(pub_config)
        references = extractor.extract(args.url)

        if not references:
            logger.error("参考文献を抽出できませんでした")
            sys.exit(1)

        # Obsidian ファイルを更新
        updater = ObsidianFileUpdater(args.output)
        updater.append_references(references, args.section)

        logger.info("=" * 70)
        logger.info("✅ 処理完了")
        logger.info(f"   抽出: {len(references)} 件")
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
