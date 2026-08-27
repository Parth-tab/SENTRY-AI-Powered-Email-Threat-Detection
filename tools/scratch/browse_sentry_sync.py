import time
from pathlib import Path
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = Path("E:/SENTRY/screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

def run():
    print("[*] Launching Chromium to interact with SENTRY...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        # 1. Open SOC Dashboard
        print("[1] Opening http://localhost:3000...")
        page.goto("http://localhost:3000", wait_until="networkidle")
        time.sleep(2)

        # 2. Click "Load Demo Scenarios"
        seed_btn = page.locator('button:has-text("Load Demo Scenarios")')
        if seed_btn.count() > 0:
            print("[2] Triggering Load Demo Scenarios...")
            seed_btn.click()
            time.sleep(2.5)

        # Capture Dashboard Screenshot
        dash_shot = SCREENSHOT_DIR / "1_soc_dashboard.png"
        page.screenshot(path=str(dash_shot), full_page=True)
        print(f"[+] Saved: {dash_shot}")

        # 3. Open Email Forensic Analyzer
        investigate_btn = page.locator('button:has-text("Investigate")').first
        if investigate_btn.count() > 0:
            print("[3] Opening deep forensic investigation modal...")
            investigate_btn.click()
            time.sleep(2)
            
            modal_shot = SCREENSHOT_DIR / "2_email_forensic_analyzer.png"
            page.screenshot(path=str(modal_shot))
            print(f"[+] Saved: {modal_shot}")

            # Close Modal
            close_btn = page.locator('button:has-text("✕"), button:has(svg.lucide-x)')
            if close_btn.count() > 0:
                close_btn.first.click()
                time.sleep(1)

        # 4. Navigate to Relay World Map Tab
        map_tab = page.locator('button:has-text("Relay World Map")')
        if map_tab.count() > 0:
            print("[4] Navigating to Relay World Map tab...")
            map_tab.click()
            time.sleep(2)
            map_shot = SCREENSHOT_DIR / "3_relay_world_map.png"
            page.screenshot(path=str(map_shot), full_page=True)
            print(f"[+] Saved: {map_shot}")

        # 5. Navigate to Campaign Graph Tab
        graph_tab = page.locator('button:has-text("Campaign Graph")')
        if graph_tab.count() > 0:
            print("[5] Navigating to Campaign Network Graph tab...")
            graph_tab.click()
            time.sleep(2)
            graph_shot = SCREENSHOT_DIR / "4_campaign_network_graph.png"
            page.screenshot(path=str(graph_shot), full_page=True)
            print(f"[+] Saved: {graph_shot}")

        # 6. Navigate to Forensic Vault Tab & Run Hash Verification
        vault_tab = page.locator('button:has-text("Forensic Vault")')
        if vault_tab.count() > 0:
            print("[6] Navigating to Forensic Vault tab...")
            vault_tab.click()
            time.sleep(2)

            # Click Verify Hash Chain button
            verify_btn = page.locator('button:has-text("Verify Hash Chain Integrity")')
            if verify_btn.count() > 0:
                print("[7] Executing cryptographic hash-chain verification...")
                verify_btn.click()
                time.sleep(2)

            vault_shot = SCREENSHOT_DIR / "5_forensic_vault_verified.png"
            page.screenshot(path=str(vault_shot), full_page=True)
            print(f"[+] Saved: {vault_shot}")

        browser.close()
        print("[*] Browser automation completed successfully.")

if __name__ == "__main__":
    run()
