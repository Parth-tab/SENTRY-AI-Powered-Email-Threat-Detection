import os
import time
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

SCREENSHOT_DIR = Path("E:/SENTRY/screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

async def run_browser_automation():
    print("[*] Launching headless browser to interact with SENTRY...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        # 1. Navigate to SOC Dashboard
        print("[1] Opening http://localhost:3000...")
        await page.goto("http://localhost:3000", wait_until="networkidle")
        await page.wait_for_timeout(2000)

        # Trigger Demo Scenario Seeding if not already populated
        seed_btn = page.locator('button:has-text("Load Demo Scenarios")')
        if await seed_btn.count() > 0:
            print("[2] Triggering Load Demo Scenarios...")
            await seed_btn.click()
            await page.wait_for_timeout(2500)

        # Capture Dashboard Screenshot
        dash_shot = SCREENSHOT_DIR / "1_soc_dashboard.png"
        await page.screenshot(path=str(dash_shot), full_page=True)
        print(f"[+] Saved: {dash_shot}")

        # 2. Open Email Forensic Analyzer (Click on the first threat in table)
        investigate_btn = page.locator('button:has-text("Investigate")').first
        if await investigate_btn.count() > 0:
            print("[3] Opening deep forensic investigation modal...")
            await investigate_btn.click()
            await page.wait_for_timeout(2000)
            
            modal_shot = SCREENSHOT_DIR / "2_email_forensic_analyzer.png"
            await page.screenshot(path=str(modal_shot))
            print(f"[+] Saved: {modal_shot}")

            # Close Modal
            close_btn = page.locator('button:has-text("✕"), button:has(svg.lucide-x)')
            if await close_btn.count() > 0:
                await close_btn.first.click()
                await page.wait_for_timeout(1000)

        # 3. Navigate to Relay World Map Tab
        map_tab = page.locator('button:has-text("Relay World Map")')
        if await map_tab.count() > 0:
            print("[4] Navigating to Relay World Map tab...")
            await map_tab.click()
            await page.wait_for_timeout(2000)
            map_shot = SCREENSHOT_DIR / "3_relay_world_map.png"
            await page.screenshot(path=str(map_shot), full_page=True)
            print(f"[+] Saved: {map_shot}")

        # 4. Navigate to Campaign Graph Tab
        graph_tab = page.locator('button:has-text("Campaign Graph")')
        if await graph_tab.count() > 0:
            print("[5] Navigating to Campaign Network Graph tab...")
            await graph_tab.click()
            await page.wait_for_timeout(2000)
            graph_shot = SCREENSHOT_DIR / "4_campaign_network_graph.png"
            await page.screenshot(path=str(graph_shot), full_page=True)
            print(f"[+] Saved: {graph_shot}")

        # 5. Navigate to Forensic Vault Tab & Run Hash Verification
        vault_tab = page.locator('button:has-text("Forensic Vault")')
        if await vault_tab.count() > 0:
            print("[6] Navigating to Forensic Vault tab...")
            await vault_tab.click()
            await page.wait_for_timeout(2000)

            # Click Verify Hash Chain button
            verify_btn = page.locator('button:has-text("Verify Hash Chain Integrity")')
            if await verify_btn.count() > 0:
                print("[7] Executing cryptographic hash-chain verification...")
                await verify_btn.click()
                await page.wait_for_timeout(2000)

            vault_shot = SCREENSHOT_DIR / "5_forensic_vault_verified.png"
            await page.screenshot(path=str(vault_shot), full_page=True)
            print(f"[+] Saved: {vault_shot}")

        await browser.close()
        print("[*] Browser automation walkthrough complete.")

if __name__ == "__main__":
    asyncio.run(run_browser_automation())
