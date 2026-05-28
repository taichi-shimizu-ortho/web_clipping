# MHTML to Obsidian Markdown Extraction System

## Project Overview
Automated system to extract academic journal articles from MHTML files (saved web pages) and format them as Markdown with embedded images and references, integrated into Obsidian notes.

## Current Status: ✅ COMPLETE

System successfully extracts and processes Wiley journal articles from MHTML format.

## System Architecture

### Main Script: extract_with_images.py

**Purpose:** Extract full article body, images, and references from MHTML files and append to Obsidian notes.

**Key Components:**

1. **extract_mhtml_html_content(mhtml_path)** 
   - Decodes MHTML file from email/MIME format
   - Uses email.message_from_binary_file() to parse MHTML structure
   - Extracts text/html part and returns decoded content

2. **extract_body_content(section)**
   - Iterates through h2, h3, p, img elements preserving order
   - Converts headings to Markdown (## and ###)
   - Embeds images as Markdown with working URLs
   - Returns markdown string and image list

3. **extract_references(soup)**
   - Finds article-section__references section
   - Extracts ul.rlist contents
   - Removes unwanted keywords: View, Google Scholar, PubMed, Web of Science, Find Full Text, CAS, Scopus, CrossRef
   - Returns cleaned reference list

4. **update_obsidian_file(obsidian_path, markdown_content)**
   - Finds # 4 Main Text section in Obsidian note
   - Replaces section content only (preserves heading)
   - Updates file with extracted content

## Environment

This project uses **uv** as the Python package manager and runner.

- Always run scripts with `uv run python` instead of `python` or `python3`
- Install dependencies with `uv pip install` instead of `pip install`
- Virtual environment is located at `.venv/`

## Usage

```bash
uv run python extract_with_images.py <mhtml_file> <obsidian_file>

# Example:
uv run python extract_with_images.py Killian2019.mhtml "/path/to/Killian2019.md"
```

## Test Results: Killian2019.md

**Journal:** Journal of Orthopaedic Research (Wiley)
**Article:** Novel model for the induction of postnatal murine hip deformity
**MHTML File Size:** 7.2 MB

### Extraction Results
- Body text: 34,643 characters
- Images: 8 with working Wiley CDN URLs
- References: 58 items
- Total output: 46,018 characters of Markdown
- Status: Successfully updated Obsidian file

## Expected HTML Structure (Wiley)

```html
<section class="article-section__full">
  <h2>Methods</h2>
  <p>Article text...</p>
  <img src="https://..." alt="Figure caption" />
  ...
</section>

<section class="article-section__references">
  <ul class="rlist">
    <li>1. Author, Year. Title. Journal...</li>
    ...
  </ul>
</section>
```

## Implementation Details

### MHTML Parsing
- MHTML files are email/MIME archives containing HTML and embedded resources
- Script extracts HTML part using email module
- Decodes from UTF-8 with error tolerance

### Element Ordering
- Uses find_all(['h2', 'h3', 'p', 'img']) to preserve document flow
- Images maintain position relative to text

### Reference Cleaning
- Removes publisher links and metadata keywords
- Collapses whitespace
- Filters items < 20 characters

### Obsidian Integration
- Regex pattern: `(# 4 Main Text\n)(.*?)(?=\n# 5 |\Z)`
- Replaces content only, preserves heading and surrounding sections

## Files in This Project

- `extract_with_images.py` - Main working script
- `extract_with_images_fixed.py` - Backup copy
- `process_mhtml_text.py` - Text extraction version (reference)
- `extract_and_save.py` - HTML generation version (reference)
- `mhtml_decoded.html` - Temporary decoded HTML for debugging

## Known Limitations

1. **Wiley-Specific**
   - Configured for Wiley article structure
   - Needs adjustment for other publishers (LWW, Nature, etc.)

2. **Reference Extraction**
   - Assumes standard ul.rlist HTML structure
   - May miss context-specific keywords

3. **Image Handling**
   - Requires accessible image URLs (external links)
   - No local image embedding

## Future Enhancements

1. **Multi-Publisher Support**
   - LWW/Wolters Kluwer
   - Nature journals
   - Lancet journals

2. **Advanced Processing**
   - Tables as Markdown
   - Better caption association
   - Footnotes/endnotes
   - Metadata extraction

3. **Quality Improvements**
   - Better reference filtering
   - Image compression/optimization
   - Supplementary material handling

## Version History

### v1.0 - Final (2026-05-26)
- Fixed MHTML decoding using email module
- Fixed reference extraction targeting correct section
- Implemented proper image positioning in Markdown
- Successfully tested on Killian2019.mhtml

### Previous Versions
- Used LangChain MHTMLLoader (issues with decoding)
- Attempted browser automation (slow)
- HTML-only extraction (structure issues)

## Troubleshooting

**"Article section not found"**
- Verify MHTML is from Wiley
- Check for article-section__full class

**"Reference section not found"**
- Verify MHTML contains article-section__references
- Check for ul.rlist elements

**Images not showing in Obsidian**
- Test image URLs in browser first
- Ensure Obsidian supports remote images
- Check for special characters in alt text

---
Created for: Taichi (a218954@gmail.com)
Last updated: 2026-05-26
