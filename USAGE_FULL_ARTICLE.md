# 論文本文＋参考文献 統合取得ツール

## 概要

URL指定 → **本文 + 参考文献を自動抽出** → **# 4 Main Text に統合追記**

このスクリプトは、学術論文のURLから以下を一括で取得し、Obsidian ノートに統合します：

- ✅ 本文（ArticleBody セクション）
- ✅ 画像（data-src属性から自動抽出）
- ✅ 参考文献（30項目以上）
- ✅ Markdown形式で整形

## インストール（初回のみ）

### 依存パッケージ

```bash
cd C:\Users\a2189\uv-envs\web_clipping

pip install playwright beautifulsoup4
playwright install chromium
```

## 使用方法

### 基本形

```bash
python extract_full_article.py \
  --url "論文URL" \
  --output "Obsidian ファイルパス"
```

### 実行例

```bash
python extract_full_article.py \
  --url "https://journals.lww.com/jbjsjournal/fulltext/2025/06040/experimentally_induced_femoroacetabular.4.aspx" \
  --output "C:\Users\a2189\Dropbox\obsidian\10_article\RXFP1\Kamenaga2021.md"
```

### オプション

| オプション | 短縮 | 説明 | デフォルト |
|-----------|------|------|-----------|
| `--url` | `-u` | 論文のURL（必須） | - |
| `--output` | `-o` | Obsidian ファイルパス（必須） | - |
| `--publisher` | `-p` | 出版社ID | `lww` |
| `--verbose` | `-v` | 詳細ログを表示 | なし |
| `--config` | `-c` | publishers_config.json パス | `publishers_config.json` |
| `--list-publishers` | - | 対応出版社のリスト表示 | なし |

## 処理フロー

```
1️⃣ ページを開く
   ↓
2️⃣ クッキーダイアログを閉じる
   ↓
3️⃣ 本文（ArticleBody）を抽出
   ↓
4️⃣ 画像URLを取得（data-src属性）
   ↓
5️⃣ 参考文献リストを展開
   ↓
6️⃣ 参考文献を抽出
   ↓
7️⃣ 両方をMarkdown形式に整形
   ↓
8️⃣ # 4 Main Text に追記
   ↓
✅ 完了
```

## 出力形式

Obsidian ファイルの **# 4 Main Text** セクションに以下の形式で追記されます：

```markdown
# 4 Main Text

## Introduction
Femoroacetabular impingement (FAI) is the leading cause of hip pain...

![fig1](https://images.journals.lww.com/jbjsjournal/...)
Study design summary.

## Materials and Methods

### Animal Model
Thirty 6-week-old immature New Zealand White rabbits...

...（本文全体）...

## References

1. Beck M, Kalhor M, Leunig M, Ganz R. Hip morphology influences the pattern of damage to the acetabular cartilage: femoroacetabular impingement as a cause of early osteoarthritis of the hip. *J Bone Joint Surg Br.* 2005 Jul;87(7):1012-8.

2. Ganz R, Parvizi J, Beck M, Leunig M, Nötzli H, Siebenrock KA. Femoroacetabular impingement: a cause for osteoarthritis of the hip. *Clin Orthop Relat Res.* 2003 Dec;(417):112-20.

... （全参考文献）...
```

## 実行例

### LWW論文の処理

```bash
python extract_full_article.py \
  -u "https://journals.lww.com/jbjsjournal/fulltext/2025/06040/experimentally_induced_femoroacetabular.4.aspx" \
  -o "C:\Users\a2189\Dropbox\obsidian\10_article\RXFP1\NewArticle.md"
```

**出力:**
```
========================================================================
論文自動抽出ツール（本文＋参考文献）
========================================================================
出版社: Lippincott Williams & Wilkins (LWW)
URL: https://journals.lww.com/jbjsjournal/fulltext/...
出力ファイル: C:\Users\a2189\Dropbox\obsidian\10_article\RXFP1\NewArticle.md

▶ ステップ1: 本文と画像を抽出
✓ 本文を抽出完了（12,543文字）

▶ ステップ2: 参考文献を抽出
✓ 参考文献を抽出完了（30件）

▶ ステップ3: Obsidian ファイルを更新
✓ 「# 4 Main Text」セクションを更新しました

========================================================================
✅ 処理完了
   本文: 12,543 文字
   画像: 8 件
   参考文献: 30 件
   更新ファイル: C:\Users\a2189\Dropbox\obsidian\10_article\RXFP1\NewArticle.md
========================================================================
```

### 詳細ログで実行

```bash
python extract_full_article.py \
  -u "https://..." \
  -o "C:\path\to\article.md" \
  --verbose
```

## 対応出版社

現在対応している出版社：

- ✅ **LWW** (Lippincott Williams & Wilkins)
  - JBJS（Journal of Bone and Joint Surgery）
  - American Journal of Sports Medicine
  - その他LWW傘下の学術誌

### 新しい出版社を追加する

`publishers_config.json` を編集して追加：

```json
{
  "id": "nature",
  "name": "Nature Publishing Group",
  "url": "https://www.nature.com/",
  "articleBodySelector": {
    "type": "class",
    "value": "article-body"
  }
}
```

その後、実行時に指定：

```bash
python extract_full_article.py -u "..." -o "..." --publisher nature
```

## トラブルシューティング

### Q: "本文を抽出できませんでした" エラー

**原因**: ArticleBody セクションが見つからない

**解決**:
1. URLが正しいか確認
2. ブラウザで手動確認して、本文セクションが表示されているか確認
3. 別の出版社の場合は、セレクタを調査して `publishers_config.json` に追加

### Q: 画像が取得されない

**原因**: lazy-loading画像で `data-src` が設定されていない

**解決**:
- `--verbose` フラグで詳細ログを確認
- ブラウザで画像のHTML構造を確認
- 必要に応じてセレクタを調整

### Q: 参考文献が多く取得されている

**原因**: ページ内に複数のreferences セクションがある

**解決**:
- `--verbose` で確認して、不要な参考文献をフィルタリング
- 今後のバージョンで改善予定

### Q: Obsidian ファイルに追記されない

**原因**: ファイルパスが間違っている、またはファイルが読み取り専用

**解決**:
1. ファイルパスをダブルクォーテーションで囲む
2. ファイルが読み取り専用でないか確認
3. フォルダが存在するか確認

```bash
# 正しい例（パスに空白がある場合）
python extract_full_article.py \
  -u "..." \
  -o "C:\Users\a2189\My Documents\article.md"
```

## ワークフロー例

### 複数の論文を処理する場合

**batch_process.py** を作成：

```python
#!/usr/bin/env python3
import subprocess

articles = [
    {
        "url": "https://journals.lww.com/jbjsjournal/fulltext/...",
        "output": "C:\Users\a2189\Dropbox\obsidian\10_article\RXFP1\Article1.md"
    },
    {
        "url": "https://journals.lww.com/jbjsjournal/fulltext/...",
        "output": "C:\Users\a2189\Dropbox\obsidian\10_article\RXFP1\Article2.md"
    },
]

for article in articles:
    print(f"\n処理中: {article['url']}")
    result = subprocess.run([
        "python", "extract_full_article.py",
        "-u", article["url"],
        "-o", article["output"]
    ])
    if result.returncode != 0:
        print(f"❌ 失敗: {article['url']}")
    else:
        print(f"✅ 完了: {article['output']}")
```

実行：

```bash
python batch_process.py
```

## 今後の改善予定

- [ ] GUI版の開発
- [ ] 複数出版社の自動判定
- [ ] 参考文献の重複排除
- [ ] DOI自動リンク化
- [ ] Zotero との連携
- [ ] 他の学術サイト対応（Nature, Science, Lancet）
- [ ] テーブルのMarkdown変換改善

## サポート

問題が発生した場合：

1. `--verbose` フラグで詳細ログを確認
2. エラーメッセージと共に以下を報告：
   - 対象論文のURL
   - 使用しているPythonバージョン
   - エラーログの全文

## 技術仕様

### 抽出対象

| 項目 | 対象 | 実装 |
|-----|------|------|
| 本文 | `<section id="ArticleBody">` | ✅ |
| 見出し | `<h2>`, `<h3>` | ✅ |
| 画像 | `img[data-src]` | ✅ |
| 参考文献 | References セクション | ✅ |
| テーブル | `<table>` | ⚠️ (基本的なサポート) |

### ブラウザ自動化

- **エンジン**: Playwright (Chromium)
- **モード**: Headless（UI表示なし）
- **タイムアウト**: 30秒

### Markdown整形

- セクションヘッダー: `##`, `###`
- 画像: `![alt](url)`
- 参考文献: 番号付きリスト
- ジャーナル名: イタリック化（`*Journal Name*`）
