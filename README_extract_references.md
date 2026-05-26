# 論文参考文献自動抽出ツール

学術論文のウェブサイトから参考文献リストを自動抽出し、Obsidian ノートに統合するPythonスクリプトです。

## 機能

- ✅ LWW（Lippincott Williams & Wilkins）サイト対応
- ✅ ブラウザ自動化で「View full references list」を展開
- ✅ 参考文献を自動抽出・Markdown形式化
- ✅ Obsidian ファイルに自動追記
- ✅ 複数の出版社に対応可能（publishers_config.json で拡張）
- ✅ エラーハンドリング・ログ出力

## 必要な環境

### Python バージョン
- Python 3.8 以上

### 依存パッケージ

```bash
pip install playwright beautifulsoup4
playwright install chromium
```

## セットアップ

### 1. ファイルの配置

```
C:\Users\a2189\uv-envs\web_clipping\
├── extract_references.py          # メインスクリプト
├── publishers_config.json         # 出版社設定（既存）
└── README_extract_references.md   # このファイル
```

### 2. パッケージのインストール

```bash
cd C:\Users\a2189\uv-envs\web_clipping

# 依存パッケージをインストール
pip install playwright beautifulsoup4

# Playwrightブラウザドライバをインストール
playwright install chromium
```

## 使用方法

### 基本的な使い方

```bash
python extract_references.py \
  --url "https://journals.lww.com/jbjsjournal/fulltext/2025/06040/..." \
  --output "C:\Users\a2189\Dropbox\obsidian\10_article\RXFP1\Kamenaga2021.md" \
  --publisher "lww"
```

### オプション一覧

| オプション | 短縮 | 説明 | デフォルト |
|-----------|------|------|-----------|
| `--url` | `-u` | 論文のURL | 必須 |
| `--output` | `-o` | 出力Obsidian ファイルパス | 必須 |
| `--publisher` | `-p` | 出版社ID | `lww` |
| `--config` | `-c` | publishers_config.json パス | `publishers_config.json` |
| `--section` | `-s` | 更新対象セクション名 | `5 Full Article Text` |
| `--verbose` | `-v` | 詳細ログを出力 | なし |
| `--list-publishers` | - | 利用可能な出版社のリスト表示 | なし |

### 実行例

**例1: LWW論文（デフォルト設定）**
```bash
python extract_references.py \
  -u "https://journals.lww.com/jbjsjournal/fulltext/2025/06040/experimentally_induced_femoroacetabular.4.aspx" \
  -o "C:\Users\a2189\Dropbox\obsidian\10_article\RXFP1\Kamenaga2021.md"
```

**例2: 詳細ログを出力**
```bash
python extract_references.py \
  -u "https://journals.lww.com/jbjsjournal/fulltext/..." \
  -o "C:\path\to\article.md" \
  --verbose
```

**例3: 利用可能な出版社を確認**
```bash
python extract_references.py --list-publishers
```

## publishers_config.json の構造

```json
{
  "publishers": [
    {
      "id": "lww",
      "name": "Lippincott Williams & Wilkins (LWW)",
      "url": "https://journals.lww.com/",
      "articleBodySelector": {
        "type": "section_id",
        "value": "ArticleBody"
      },
      "notes": "JBJS (Journal of Bone and Joint Surgery) など"
    }
  ]
}
```

### 新しい出版社を追加する方法

1. `publishers_config.json` を編集
2. 新しい出版社オブジェクトを `publishers` 配列に追加

```json
{
  "id": "nature",
  "name": "Nature Publishing Group",
  "url": "https://www.nature.com/",
  "articleBodySelector": {
    "type": "class",
    "value": "article-body"
  },
  "notes": "Nature journal articles"
}
```

3. スクリプト実行時に `--publisher nature` を指定

## 出力ファイルの形式

スクリプト実行後、Obsidian ファイルの末尾に以下の形式で参考文献が追加されます：

```markdown
## References

1. Beck M, Kalhor M, Leunig M, Ganz R. Hip morphology influences the pattern of damage to the acetabular cartilage: femoroacetabular impingement as a cause of early osteoarthritis of the hip. *J Bone Joint Surg Br.* 2005 Jul;87(7):1012-8.

2. Ganz R, Parvizi J, Beck M, Leunig M, Nötzli H, Siebenrock KA. Femoroacetabular impingement: a cause for osteoarthritis of the hip. *Clin Orthop Relat Res.* 2003 Dec;(417):112-20.

...
```

## トラブルシューティング

### エラー: "playwright が必要です"

```bash
pip install playwright
playwright install chromium
```

### エラー: "beautifulsoup4 が必要です"

```bash
pip install beautifulsoup4
```

### エラー: "ファイルが見つかりません"

- Obsidian ファイルのパスが正しいか確認
- パスに空白やスペースがある場合は、クォーテーションで囲む

```bash
python extract_references.py \
  -u "..." \
  -o "C:\Users\a2189\My Documents\article.md"
```

### 参考文献が抽出されない

- `--verbose` フラグで詳細ログを確認

```bash
python extract_references.py ... --verbose
```

- ブラウザが正しく起動しているか確認（ヘッドレスモード）
- 出版社設定が正しいか確認

```bash
python extract_references.py --list-publishers
```

## スクリプトの動作フロー

```
1. コマンドライン引数を解析
2. publishers_config.json から出版社設定を読み込む
3. Playwrightでブラウザを起動
4. 論文ページにアクセス
5. クッキーダイアログを閉じる（必要に応じて）
6. JavaScriptで「View full references list」をクリック
7. ページのHTML/テキストを解析
8. 参考文献を抽出・Markdown形式化
9. Obsidian ファイルに追記
10. ブラウザを閉じて終了
```

## 今後の拡張予定

- [ ] 複数の出版社自動判定（URLから自動検出）
- [ ] 参考文献の重複排除
- [ ] DOI自動リンク化
- [ ] Zotero との連携
- [ ] GUI版の開発
- [ ] 他の学術サイト対応（Nature, Science, Lancet など）

## ライセンス

MIT License

## サポート

問題が発生した場合は、以下の情報と共に報告してください：

1. エラーメッセージの全文
2. `--verbose` フラグでの実行ログ
3. 対象論文のURL
4. 使用しているPythonバージョン

## 技術仕様

### 使用ライブラリ

- **Playwright**: ブラウザ自動化（JavaScriptサポート）
- **BeautifulSoup**: HTML解析
- **Python標準ライブラリ**: json, logging, argparse, pathlib

### ブラウザ

- Chromium（Playwrightでインストール）
- ヘッドレスモードで実行（UI表示なし）

### 参考文献解析

- ページテキストから "References" セクションを検出
- 数字で始まる行を参考文献として識別
- ジャーナル名を自動的にMarkdown イタリック化
