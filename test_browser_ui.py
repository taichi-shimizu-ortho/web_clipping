from playwright.sync_api import sync_playwright

print("Opening browser with UI...")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # headless=False でUIを表示
    page = browser.new_page()
    
    print("Loading page... (ブラウザを見ながら待機)")
    try:
        page.goto(
            "https://journals.lww.com/jbjsjournal/fulltext/2025/06040/experimentally_induced_femoroacetabular.4.aspx",
            wait_until="networkidle",
            timeout=120000  # 120秒
        )
        print("✅ Page loaded successfully!")
        print("Press Enter to close browser...")
        input()
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        browser.close()
