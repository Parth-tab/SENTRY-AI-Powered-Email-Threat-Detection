import time
from pathlib import Path
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = Path("E:/SENTRY/screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})

    # 1. Open and seed
    page.goto("http://localhost:3000", wait_until="networkidle")
    time.sleep(1)

    # Click seed button if needed
    seed_btn = page.locator('button:has-text("Load Demo Scenarios")')
    if seed_btn.count() > 0:
        seed_btn.click()
        time.sleep(3)

    # Reload to ensure React state reflects all seeded data
    page.reload(wait_until="networkidle")
    time.sleep(2)

    # 1. Dashboard with loaded artifacts
    page.screenshot(path=str(SCREENSHOT_DIR / "1_soc_dashboard_live.png"), full_page=True)
    print("[+] Dashboard captured")

    # 2. Click first email to open Modal Analyzer
    row = page.locator('tbody tr').first
    if row.count() > 0:
        row.click()
        time.sleep(2)
        page.screenshot(path=str(SCREENSHOT_DIR / "2_email_forensic_analyzer_modal.png"))
        print("[+] Forensic modal captured")

        # Close Modal
        close_btn = page.locator('button:has(svg.lucide-x), button:has-text("✕")')
        if close_btn.count() > 0:
            close_btn.first.click()
            time.sleep(1)

    # 3. Relay World Map
    map_btn = page.locator('button:has-text("Relay World Map")')
    if map_btn.count() > 0:
        map_btn.click()
        time.sleep(2)
        page.screenshot(path=str(SCREENSHOT_DIR / "3_relay_world_map_live.png"), full_page=True)
        print("[+] Relay Map captured")

    # 4. Campaign Graph
    graph_btn = page.locator('button:has-text("Campaign Graph")')
    if graph_btn.count() > 0:
        graph_btn.click()
        time.sleep(2)
        page.screenshot(path=str(SCREENSHOT_DIR / "4_campaign_network_graph_live.png"), full_page=True)
        print("[+] Campaign Graph captured")

    # 5. Forensic Vault & Hash Verification
    vault_btn = page.locator('button:has-text("Forensic Vault")')
    if vault_btn.count() > 0:
        vault_btn.click()
        time.sleep(1.5)

        verify_btn = page.locator('button:has-text("Verify Hash Chain Integrity")')
        if verify_btn.count() > 0:
            verify_btn.click()
            time.sleep(2)

        page.screenshot(path=str(SCREENSHOT_DIR / "5_forensic_vault_verified_live.png"), full_page=True)
        print("[+] Forensic Vault captured")

    browser.close()
    print("[*] Complete gallery generated!")
