# UV環境でのセットアップ

## 方法1: uv run を使用（推奨）

```powershell
cd C:\Users\a2189\uv-envs\web_clipping

# 依存パッケージをインストール
uv pip install playwright beautifulsoup4

# Playwrightブラウザドライバをインストール
uv run python -m playwright install chromium
```

## 方法2: Python -m を使用

```powershell
cd C:\Users\a2189\uv-envs\web_clipping

# 依存パッケージをインストール
uv pip install playwright beautifulsoup4

# Pythonモジュールとして実行
python -m playwright install chromium
```

## 方法3: pyproject.toml を使用（推奨）

`pyproject.toml` を作成：

```toml
[project]
name = "article-extractor"
version = "0.1.0"
description = "論文本文＋参考文献自動抽出ツール"
requires-python = ">=3.8"
dependencies = [
    "playwright>=1.40.0",
    "beautifulsoup4>=4.12.0",
]
```

その後以下を実行：

```powershell
cd C:\Users\a2189\uv-envs\web_clipping

# 依存パッケージをインストール
uv sync

# Playwrightブラウザドライバをインストール
uv run python -m playwright install chromium
```

## スクリプト実行方法

### 方法A: uv run で実行（推奨）

```powershell
uv run python extract_full_article.py \
  -u "https://journals.lww.com/jbjsjournal/fulltext/..." \
  -o "C:\path\to\article.md"
```

### 方法B: 直接実行

```powershell
python extract_full_article.py \
  -u "https://journals.lww.com/jbjsjournal/fulltext/..." \
  -o "C:\path\to\article.md"
```

## トラブルシューティング

### エラー: "playwright: The term 'playwright' is not recognized"

**原因**: Playwrightが PATH に登録されていない

**解決**: `uv run python -m playwright install chromium` を使用

### エラー: "No such file or directory: chromium"

**原因**: ブラウザドライバがまだインストールされていない

**解決**:
```powershell
uv run python -m playwright install chromium
```

### エラー: "ModuleNotFoundError: No module named 'playwright'"

**原因**: パッケージがインストールされていない

**解決**:
```powershell
uv pip install playwright beautifulsoup4
```

## 推奨セットアップ手順（UV環境）

```powershell
# 1. ディレクトリに移動
cd C:\Users\a2189\uv-envs\web_clipping

# 2. パッケージをインストール
uv pip install playwright beautifulsoup4

# 3. Playwrightブラウザをインストール
uv run python -m playwright install chromium

# 4. スクリプトを実行
uv run python extract_full_article.py \
  -u "https://journals.lww.com/jbjsjournal/fulltext/..." \
  -o "C:\path\to\article.md"
```

## 確認方法

インストール後、以下で確認できます：

```powershell
# Playwrightが正しくインストールされているか確認
uv run python -c "from playwright.sync_api import sync_playwright; print('✅ Playwright OK')"

# BeautifulSoupが正しくインストールされているか確認
uv run python -c "from bs4 import BeautifulSoup; print('✅ BeautifulSoup OK')"
```

## UV コマンド一覧

| コマンド | 説明 |
|--------|------|
| `uv pip install <package>` | パッケージをインストール |
| `uv pip list` | インストール済みパッケージを表示 |
| `uv pip uninstall <package>` | パッケージをアンインストール |
| `uv run <command>` | コマンドを実行（仮想環境を使用） |
| `uv sync` | pyproject.toml から依存関係をインストール |

## 注意事項

- `uv run` を使用することで、常に正しい環境でスクリプトが実行されます
- PowerShellで複数行コマンドを実行する場合は、バックスラッシュ `\` の代わりにバックティック `` ` `` を使用してください

### PowerShell での複数行実行例

```powershell
uv run python extract_full_article.py `
  -u "https://journals.lww.com/jbjsjournal/fulltext/..." `
  -o "C:\path\to\article.md"
```

または1行で：

```powershell
uv run python extract_full_article.py -u "URL" -o "PATH"
```
