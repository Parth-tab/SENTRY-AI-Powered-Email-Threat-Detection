import time
from pathlib import Path
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = Path("E:/SENTRY/screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

def drive_app():
    print("[*] Launching Chromium to interact with SENTRY SOC...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        # 1. Open Dashboard
        print("[1] Navigating to http://localhost:3005...")
        page.goto("http://localhost:3005", wait_until="networkidle")
        time.sleep(2)

        # 1. Dashboard Screenshot
        dash_shot = SCREENSHOT_DIR / "1_soc_dashboard_live.png"
        page.screenshot(path=str(dash_shot), full_page=True)
        print(f"[+] Captured Dashboard: {dash_shot}")

        # 2. Click "Investigate" on the SBI Phishing Threat row
        investigate_btns = page.locator('button:has-text("Investigate")')
        if investigate_btns.count() > 0:
            print("[2] Opening Deep Forensic Analyzer Modal...")
            # Click the critical phishing row (last row or specific button)
            investigate_btns.last.click()
            time.sleep(2)

            modal_shot = SCREENSHOT_DIR / "2_email_forensic_analyzer_modal.png"
            page.screenshot(path=str(modal_shot))
            print(f"[+] Captured Analyzer Modal: {modal_shot}")

            # Switch to "RFC Headers" tab inside the modal
            headers_tab = page.locator('button:has-text("RFC Headers")')
            if headers_tab.count() > 0:
                headers_tab.click()
                time.sleep(1)
                headers_shot = SCREENSHOT_DIR / "2b_rfc_headers_inspector.png"
                page.screenshot(path=str(headers_shot))
                print(f"[+] Captured RFC Headers tab: {headers_shot}")

            # Close modal
            close_btn = page.locator('button:has(svg.lucide-x), button:has-text("✕")')
            if close_btn.count() > 0:
                close_btn.first.click()
                time.sleep(1)

        # 3. Navigate to Relay World Map
        map_tab = page.locator('button:has-text("Relay World Map")')
        if map_tab.count() > 0:
            print("[3] Navigating to Relay World Map...")
            map_tab.click()
            time.sleep(2)
            map_shot = SCREENSHOT_DIR / "3_relay_world_map_live.png"
            page.screenshot(path=str(map_shot), full_page=True)
            print(f"[+] Captured Relay Map: {map_shot}")

        # 4. Navigate to Campaign Graph
        graph_tab = page.locator('button:has-text("Campaign Graph")')
        if graph_tab.count() > 0:
            print("[4] Navigating to Campaign Graph...")
            graph_tab.click()
            time.sleep(2)

            # Click on canvas to select central campaign node
            canvas = page.locator('canvas')
            if canvas.count() > 0:
                canvas.click(position={"x": 550, "y": 280})
                time.sleep(1)

            graph_shot = SCREENSHOT_DIR / "4_campaign_network_graph_live.png"
            page.screenshot(path=str(graph_shot), full_page=True)
            print(f"[+] Captured Campaign Graph: {graph_shot}")

        # 5. Navigate to Forensic Vault & Run Hash Chain Verification
        vault_tab = page.locator('button:has-text("Forensic Vault")')
        if vault_tab.count() > 0:
            print("[5] Navigating to Forensic Vault & Executing Cryptographic Verification...")
            vault_tab.click()
            time.sleep(1.5)

            # Click "Verify Hash Chain Integrity"
            verify_btn = page.locator('button:has-text("Verify Hash Chain Integrity")')
            if verify_btn.count() > 0:
                verify_btn.click()
                time.sleep(2)

            vault_shot = SCREENSHOT_DIR / "5_forensic_vault_verified_live.png"
            page.screenshot(path=str(vault_shot), full_page=True)
            print(f"[+] Captured Forensic Vault Verification: {vault_shot}")

        browser.close()
        print("[*] Full autonomous browser interaction finished successfully.")

if __name__ == "__main__":
    drive_app()
