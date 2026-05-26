# クイックスタート

## 5分で始める

### ステップ1: 依存パッケージのインストール（初回のみ）

```bash
cd C:\Users\a2189\uv-envs\web_clipping

pip install playwright beautifulsoup4
playwright install chromium
```

### ステップ2: スクリプトを実行

```bash
python extract_references.py \
  --url "論文のURL" \
  --output "Obsidianファイルのパス"
```

### ステップ3: 完了

Obsidianファイルの末尾に参考文献が自動追加されます。

---

## 実例

### 例: Kamenaga2021の別バージョンを処理

```bash
python extract_references.py \
  --url "https://journals.lww.com/jbjsjournal/fulltext/2025/06040/experimentally_induced_femoroacetabular.4.aspx" \
  --output "C:\Users\a2189\Dropbox\obsidian\10_article\RXFP1\NewArticle2021.md" \
  --publisher "lww"
```

### 例: 詳細ログを見ながら実行

```bash
python extract_references.py \
  -u "https://journals.lww.com/jbjsjournal/fulltext/..." \
  -o "C:\path\to\article.md" \
  --verbose
```

---

## トラブルシューティング

### Q: "playwright が必要です" というエラーが出た

**A:** 以下を実行してください
```bash
pip install playwright
playwright install chromium
```

### Q: 参考文献が抽出されない

**A:** 詳細ログを確認してください
```bash
python extract_references.py ... --verbose
```

### Q: ファイルパスに空白が含まれている

**A:** ダブルクォーテーションで囲んでください
```bash
python extract_references.py \
  -u "..." \
  -o "C:\Users\a2189\My Documents\article.md"
```

---

## よくある質問

**Q: 複数の論文を一括処理できる？**

A: バッチスクリプトを別途作成することで可能です。詳しくは`README_extract_references.md`を参照してください。

**Q: 出版社を追加できる？**

A: はい。`publishers_config.json`を編集することで、任意の出版社に対応できます。

**Q: 既存の参考文献はどうなる？**

A: スクリプト実行時に、既存の「## References」セクションは置き換えられます。大事な変更がある場合は事前にバックアップしてください。

---

## 次のステップ

- 詳細は`README_extract_references.md`を参照
- より複雑な設定は`publishers_config.json`を編集
- 他の出版社に対応させる場合は、HTMLセレクタの調査が必要です
