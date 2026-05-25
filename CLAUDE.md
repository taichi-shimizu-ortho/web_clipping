# Web Clipping Workflow - Obsidian論文自動取得システム

## 目的
出版社サイトの論文ページ（paywallで保護されているページ含む）から本文コンテンツを自動的に抽出し、Obsidianのノートに統合する。

## システムの構成

### 1. 環境セットアップ
- **ツール**: Claude in Chrome（ブラウザ自動化）
- **対応サイト**: JBJS（Journal of Bone and Joint Surgery）など、HTMLセクション構造を持つ出版社サイト
- **出力形式**: Markdown with embedded images

### 2. 抽出プロセス

#### ステップ1: ターゲットセクションの取得
```
対象: <section id="ArticleBody">
含まれる内容: Introduction → Materials & Methods → Results → Discussion → Conclusion
含まれない内容: Abstract（別セクション）
```

#### ステップ2: 画像URLの抽出
- **方法**: ブラウザJavaScript実行で、HTML `data-src` 属性から画像URLを取得
- **形式**: `data-src="https://images.journals.lww.com/jbjsjournal/..."` から抽出
- **出力形式**: `![figN](URL)` Markdown形式

**例:**
```markdown
![fig1](https://images.journals.lww.com/jbjsjournal/ArticleViewerPreview.00004623-202506040-00004.fig1.jpeg)
Study design summary.
```

#### ステップ3: テキスト本体の整形
- セクションヘッダーを Markdown `##` または `###` に変換
- 図表のキャプションを画像URLの直後に配置
- 参考文献番号（上付き数字）は保持

### 3. Obsidian ノート統合

#### ファイル構造
```
Kamenaga2021.md
├── YAML frontmatter
├── #1 AI要約
├── #2 Citation
├── #3 PDF
├── #4 Main Text （最終的にこれに置き換わる予定）
└── #5 Full Article Text ← ここに本文を追記
```

#### 置き換え方法
1. 既存の `#5 Full Article Text` セクションを置き換え（コンテンツのみ）
2. 既存メタデータ（インポート日時等）は保持
3. Markdown形式で図を含める

## 実装例：Kamenaga2021.md

**記事**: Experimentally Induced Femoroacetabular Impingement Results in Hip Osteoarthritis
**出版社**: JBJS (Journal of Bone and Joint Surgery)
**著者**: Kamenaga, Tomoyuki et al.
**出版年**: 2025/06/04

### 処理内容
1. JBJS論文ページにアクセス
2. `#ArticleBody` セクションのみを抽出
3. 8つの図を Markdown 形式で埋め込み
4. Obsidian ノートの #5 セクションに統合

### ファイル出力
- **記事本体**: `article_body_only.md`
- **ターゲット**: `C:\Users\a2189\Dropbox\obsidian\10_article\RXFP1\Kamenaga2021.md`

## トラブルシューティング

### 画像が表示されない
- **原因**: lazy-loading画像で `src` 属性が空
- **解決**: JavaScriptで `data-src` 属性を抽出して Markdown に変換

### ページがJavaScriptで動的レンダリング
- **原因**: `get_page_text` では HTML 構造が取得できない
- **解決**: Claude in Chrome で実際のブラウザコンテキストで実行

### Abstractが含まれてしまう
- **原因**: セクションIDの誤認識
- **解決**: `<section id="ArticleBody">` を厳密に指定して、Abstract（別セクション）を除外

## 将来の展開

1. **複数記事への対応**
   - `Kamenaga2021.md` と同じ構造の他の論文にも適用可能
   
2. **自動化スクリプト**
   - 記事URL → Obsidian ノート統合を自動化
   
3. **セクション置き換え**
   - 最終的に `#5 Full Article Text` を削除
   - `#4 Main Text` に本文を統合
   
4. **複数出版社対応**
   - 他の学術出版社（Nature、Lancet等）への展開
   - セクション構造の違いに対応

## 注意事項

- 論文内容の抽出のみ（Abstract は除外）
- 著作権保護コンテンツには対応していない
- 出版社サイトの利用規約を遵守
