# Web Clipping to Obsidian

学術論文をウェブページから抽出して、Obsidian の Markdown ファイルに統合するシステムです。複数のパブリッシャー（Wiley、LWW など）に対応しています。

## 概要

このシステムは、学術出版社のウェブページまたは MHTML ファイル（保存されたウェブページ）から：
- **論文本文**（見出し、段落、画像を含む）
- **参考文献**（参考文献セクション）
を自動的に抽出し、Obsidian ノートに追加します。

## 対応パブリッシャー

`publishers_config.json` で定義されています：

| パブリッシャー | URL | 対応状況 |
|---|---|---|
| **Wiley** | https://onlinelibrary.wiley.com/ | ✅ 完全対応 |
| **LWW** (Lippincott Williams & Wilkins) | https://journals.lww.com/ | ✅ 対応予定 |

## インストール

```bash
# 依存パッケージのインストール
pip install -r requirements.txt
```

必要なライブラリ：
- `playwright` - ブラウザ自動化
- `beautifulsoup4` - HTML 解析
- `lxml` - XML/HTML パーサー

## 使い方

### 1. URL から直接抽出（Playwright ベース）

ウェブページから直接記事を抽出する場合：

```bash
python extract_from_url.py <URL> <Obsidian ファイルパス>
```

**例：**
```bash
python extract_from_url.py \
  "https://onlinelibrary.wiley.com/doi/10.1002/jor.24146" \
  "/path/to/your/notes/Killian2019.md"
```

**処理内容：**
1. Playwright でウェブページを読み込み
2. クッキーバナーを自動閉じ
3. 論文本文を抽出（見出し、段落、画像）
4. 参考文献を抽出・クリーニング
5. Obsidian ファイルの「# 4 Main Text」セクションを更新

### 2. MHTML ファイルから抽出

ブラウザで保存された MHTML ファイルから抽出する場合：

```bash
python extract_with_images.py <MHTML ファイル> <Obsidian ファイルパス>
```

**例：**
```bash
python extract_with_images.py \
  "Killian2019.mhtml" \
  "/path/to/your/notes/Killian2019.md"
```

**処理内容：**
1. MHTML ファイルをメール形式でデコード
2. 論文セクション（`article-section__full`）を検出
3. HTML コンテンツを Markdown に変換
4. 画像を保持（Wiley CDN のリンク）
5. 参考文献を抽出・整形
6. Obsidian ファイルを更新

## Obsidian ノートの構造

更新対象となる Obsidian ファイルは、以下の構造を想定しています：

```markdown
# 1 Title
論文のタイトル

# 2 Basic Information
- DOI: ...
- Authors: ...
- Published: ...

# 3 Abstract
要約

# 4 Main Text
（このセクションが抽出内容で更新されます）

## Methods
...

## Results
...

# 5 References
（参考文献セクション）
```

**重要：** ファイルに「# 4 Main Text」セクションが必須です。このセクションが検出されなければファイルは更新されません。

## 画像処理

### Wiley からの抽出の場合
- 外部 URL のリンクで保持（Wiley CDN）
- Obsidian で自動的に表示されます
- オフライン利用には対応していません

### 画像の確認・デバッグ
ウェブページの画像要素をデバッグする場合：

```bash
python debug_images.py
```

このスクリプトは：
- `<img>` タグの詳細情報を表示
- `<picture>` タグの srcset を検査
- `<figure>` タグの構造を確認

## 参考文献の処理

抽出後、以下のキーワードが自動的に削除されます：
- View
- Google Scholar
- PubMed
- Web of Science
- Find Full Text
- CAS
- Scopus
- CrossRef

20 文字未満の行は削除されます。

## トラブルシューティング

### 「Article section not found」

**原因：** パブリッシャーの HTML 構造が変わった、または非対応パブリッシャーの URL

**対策：**
1. URL が正しいパブリッシャーかご確認ください
2. `publishers_config.json` にパブリッシャー設定があるか確認してください
3. `debug_images.py` で HTML 構造を確認してください

### 「# 4 Main Text section not found」

**原因：** Obsidian ファイルに「# 4 Main Text」がない

**対策：** ファイルに以下のセクションを追加してください：
```markdown
# 4 Main Text
```

### 画像が Obsidian に表示されない

**原因：** Obsidian がリモート画像の表示に対応していない設定

**対策：** Obsidian の設定を確認：
- Settings → Files & Links → Adjust default new note location
- リモート画像を有効にする設定を確認

## 開発者向け情報

### プロジェクト構成

| ファイル | 用途 |
|---|---|
| `extract_from_url.py` | **メイン：** URL から Playwright で抽出 |
| `extract_with_images.py` | MHTML ファイルから抽出 |
| `debug_images.py` | 画像要素のデバッグ |
| `publishers_config.json` | パブリッシャー設定 |

### 新しいパブリッシャーの追加

1. `publishers_config.json` に設定を追加：

```json
{
  "id": "publisher_id",
  "name": "Publisher Name",
  "url": "https://publisher.com/",
  "articleBodySelector": {
    "type": "css",
    "value": "section.article-content"
  },
  "notes": "説明"
}
```

2. `extract_from_url.py` の `extract_body_content_with_images()` を調整（必要に応じて）

## ライセンス

このシステムは個人用・研究用です。著作権および利用規約はパブリッシャーの指定に従ってください。

## 最終更新

- 2026-05-28
- 作成者: Taichi (a218954@gmail.com)
