# ScienceDirect → Obsidian（MHTML）

## 取得手順

1. 普段のブラウザーでScienceDirectの論文ページを開きます。
2. 必要なら大学の機関認証を行い、Materials and methods、Results、Discussionの本文全体が読めることを確認します。抄録と「Section snippets」だけのページは使えません。
3. ページ末尾までスクロールして図を読み込み、参考文献も表示します。
4. `Ctrl+S`で「ウェブページ、単一ファイル（*.mhtml）」を選んで保存します。PDFや「HTMLのみ」は選びません。
5. 保存ファイルを以下のスクリプトに渡します。抽出時のネットワーク接続やAPIキーは不要です。

ScienceDirectへのHTTP直接取得は403や人間確認で止まる場合があります。機関認証・人間確認はブラウザーで行い、閲覧できたページの保存ファイルを入力とします。本処理は認証や購読制限を回避しません。

## 新規ノートの作成（推奨）

```powershell
uv run python extract_sciencedirect.py "Li 2026.mhtml" --output "output/Li2026/Li2026.md"
```

依存パッケージがなければ `uv pip install beautifulsoup4` を実行します。

- タイトル、著者、雑誌、日付、DOI、Abstract、Highlightsを取得します。
- 本文の見出し・段落・図・キャプション・参考文献を保持します。
- MHTML内の図を隣接する `Li2026_assets/` に保存し、相対パスで埋め込みます。
- 保存ファイルに画像データがなければ元URLを残し、警告します。高解像度リンクから追加ダウンロードはしません。
- 上付き・下付きの科学表記は `<sup>`・`<sub>` として保持します。
- 参考文献の操作リンクはHTMLのコンテナー単位で除去し、タイトル中の語句を削除しません。
- `.extraction.json` に書誌情報、画像一覧、参考文献、警告、入力のSHA-256を出力します。
- 出力が存在すると停止します。意図的に再作成する場合のみ `--force` を指定してください。

ノートと `_assets` フォルダーを一緒にObsidianの保管庫へコピーしてください。

## 既存ノートのMain Textだけを更新

```powershell
uv run python extract_with_images.py "Li 2026.mhtml" "path/to/existing-note.md"
```

ScienceDirectを自動判定し、既存方式に合わせて `# 4 Main Text` 内に本文と `## References` を挿入します。`# 5` 以降とそれ以前のセクションは維持します。Abstractや書誌情報、既存の `# 5 References` は更新しません。図はノートの横の `<ノート名>_assets/` に保存します。新規ノートでは上の専用コマンドを使用してください。

## 検証状況と限界

- 実論文: Li et al., BBRC 811 (2026), 153410。DOI: `10.1016/j.bbrc.2026.153410`。
- この論文の保存MHTMLで本文、図6点とキャプション、参考文献46件の抽出を検証しました。
- ScienceDirectのすべての雑誌・古いHTML形式への対応は未検証です。
- 結合セルを含む複雑な表、数式、補足ファイルの本体取得には追加対応が必要です。補足資料は本文中のリンクを保持します。
- PDFからの変換は行いません。

検証コマンド: `uv run python -m unittest discover -s tests -v`
