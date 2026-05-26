#!/usr/bin/env python3
# Simple wrapper to run extraction without UTF-8 issues
import sys
import subprocess
import os

os.chdir('/sessions/sharp-nice-gauss/mnt/web_clipping')

# Build command
cmd = [
    'python', 'extract_full_article.py',
    '-u', 'https://journals.lww.com/jbjsjournal/fulltext/2025/06040/experimentally_induced_femoroacetabular.4.aspx',
    '-o', '/sessions/sharp-nice-gauss/mnt/RXFP1/Kamenaga2021_v2.md',
    '--timeout', '90',
    '--verbose'
]

# Run the script
result = subprocess.run(cmd)
sys.exit(result.returncode)
