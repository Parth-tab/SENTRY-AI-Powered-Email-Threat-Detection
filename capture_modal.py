import time
from pathlib import Path
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = Path("E:/SENTRY/screenshots")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto("http://localhost:3000", wait_until="networkidle")
    time.sleep(2)

    # Click on the first row in the table
    row = page.locator('tbody tr').first
    if row.count() > 0:
        row.click()
        time.sleep(2)
        modal_shot = SCREENSHOT_DIR / "2_email_forensic_analyzer.png"
        page.screenshot(path=str(modal_shot))
        print("Captured modal screenshot.")

    browser.close()
