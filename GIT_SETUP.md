# Git Setup Instructions

## Problem
The git repository in the web_clipping folder has a corrupted config file that prevents commits.

## Solution: Reset Git Locally

Run these commands in PowerShell on your Windows machine:

```powershell
cd "C:\Users\a2189\uv-envs\web_clipping"

# Remove corrupted .git directory
Remove-Item -Recurse -Force .git

# Initialize new repository
git init

# Configure git
git config user.email "a218954@gmail.com"
git config user.name "Taichi"

# Add files
git add extract_with_images.py CLAUDE.md

# Create initial commit
git commit -m "Initial commit: MHTML to Obsidian extraction system

- Implemented extract_with_images.py for MHTML parsing
- Extracts body text, 8 images, 58 references from journal articles
- Integrates with Obsidian notes (# 4 Main Text section)
- Tested on Killian2019.mhtml (Wiley journal)
- Full documentation in CLAUDE.md"
```

## What These Scripts Do

**extract_with_images.py** - Main extraction script
- Parses MHTML files (email/MIME format)
- Extracts article sections with proper HTML structure
- Embeds images as Markdown with working URLs
- Extracts and cleans reference lists
- Updates Obsidian notes with extracted content

**CLAUDE.md** - Project documentation
- System architecture and components
- Usage instructions
- Test results and performance metrics
- HTML structure expectations
- Troubleshooting guide

## Next Steps

After committing, you can:
1. Test with other Wiley articles
2. Extend to support other publishers (LWW, Nature, etc.)
3. Add table extraction
4. Improve reference keyword filtering

---
Generated: 2026-05-26
