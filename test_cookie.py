from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    print("Loading page...")
    page.goto("https://journals.lww.com/jbjsjournal/fulltext/2025/06040/experimentally_induced_femoroacetabular.4.aspx", wait_until="domcontentloaded", timeout=120000)
    
    print("Looking for cookie button...")
    
    # クッキーダイアログを探してクリック
    try:
        # 「Accept All Cookies」ボタンを探す
        page.click("button:has-text('Accept All Cookies')", timeout=5000)
        print("✅ Clicked 'Accept All Cookies'")
    except:
        try:
            # 別のセレクタで試す
            page.click("button[data-test*='accept']", timeout=5000)
            print("✅ Clicked cookie button")
        except:
            print("⚠️ Cookie button not found")
    
    print("Waiting for page load...")
    page.wait_for_load_state("networkidle", timeout=120000)
    print("✅ Page fully loaded!")
    print("Press Enter to close...")
    input()
    browser.close()
