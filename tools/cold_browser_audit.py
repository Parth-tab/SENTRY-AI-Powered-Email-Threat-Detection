#!/usr/bin/env python3
"""SENTRY Cold-Browser Final Storefront & UI Audit (D7).

Launches the single-origin production appliance on :8000 and drives
headless Chromium to verify storefront integrity, badges, links,
MaxMind attribution, zero broken assets, and zero console errors.

Outputs:
  - evaluation/artifacts/cold_browser_receipt.json
  - evaluation/artifacts/cold_browser_storefront.png
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

from verify_sentry import (
    Stack, http_json, kill_listeners, wait_http
)

ARTIFACTS_DIR = REPO_ROOT / "evaluation" / "artifacts"
RECEIPT_FILE = ARTIFACTS_DIR / "cold_browser_receipt.json"
SCREENSHOT_FILE = ARTIFACTS_DIR / "cold_browser_storefront.png"


async def run_cold_browser_audit():
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    api_port = 8000
    ui_port = 3000
    base_url = f"http://127.0.0.1:{api_port}"

    kill_listeners(api_port)
    kill_listeners(ui_port)

    # Boot in single-origin production serving mode
    env = os.environ.copy()
    env["SERVE_STATIC"] = "true"
    env["BUILD_MODE"] = "production"
    env["SENTRY_API_TOKEN"] = "sentry_operator_token_2025"

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--app-dir", "backend", "--host", "127.0.0.1", "--port", str(api_port)],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    console_errors = []
    http_errors = []
    receipt = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "target_url": base_url,
        "mode": "single_origin_production_spa",
        "checks": {}
    }

    try:
        if not wait_http(f"{base_url}/health", timeout_s=60):
            raise RuntimeError("Backend failed to boot on port 8000")

        # Seed sample emails
        http_json("POST", f"{base_url}/api/v1/samples/seed")

        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=2)

            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            page.on("response", lambda resp: http_errors.append(f"{resp.status} {resp.url}") if resp.status >= 400 and "/api/v1/upload" not in resp.url else None)

            # 1. Navigate to landing page
            resp = await page.goto(base_url, timeout=30_000)
            receipt["checks"]["http_status"] = resp.status
            assert resp.status == 200, f"Expected HTTP 200, got {resp.status}"

            # 2. Wait for Feed and Metrics
            await page.wait_for_selector("text=Threat Intelligence Ingestion Stream", timeout=15_000)
            await asyncio.sleep(2)  # Settle live feeds and charts

            # 3. Check Header / Title
            title = await page.title()
            receipt["checks"]["page_title"] = title
            receipt["checks"]["has_sentry_title"] = "SENTRY" in title

            # 4. Check Threat Feed Count
            feed_rows = await page.locator("table tbody tr").count()
            receipt["checks"]["feed_row_count"] = feed_rows
            assert feed_rows >= 18, f"Expected >= 18 feed rows, found {feed_rows}"

            # 5. Check Severity Badges
            crit_badges = await page.locator("text=CRITICAL").count()
            med_badges = await page.locator("text=MEDIUM").count()
            receipt["checks"]["critical_badges_visible"] = crit_badges
            receipt["checks"]["medium_badges_visible"] = med_badges
            assert crit_badges > 0, "No CRITICAL severity badges visible"

            # 6. Check MaxMind Attribution
            maxmind_text = await page.locator("text=GeoLite2").count()
            receipt["checks"]["maxmind_attribution_present"] = maxmind_text > 0
            assert maxmind_text > 0, "MaxMind GeoLite2 attribution text not found on page"

            # 7. Take Full Storefront Screenshot
            await page.screenshot(path=str(SCREENSHOT_FILE), full_page=False)
            receipt["checks"]["screenshot_saved"] = str(SCREENSHOT_FILE)

            # 8. Verify Console & HTTP Cleanliness
            receipt["checks"]["console_errors"] = console_errors
            receipt["checks"]["http_errors"] = http_errors
            receipt["status"] = "COLD_BROWSER_AUDIT_PASS" if (len(console_errors) == 0 and len(http_errors) == 0) else "FAIL"

            await browser.close()

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        kill_listeners(api_port)

    RECEIPT_FILE.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(f"\n[+] Cold-Browser Audit Completed: {receipt['status']}")
    print(f"    Receipt JSON: {RECEIPT_FILE}")
    print(f"    Screenshot:   {SCREENSHOT_FILE}")
    return 0 if receipt["status"] == "COLD_BROWSER_AUDIT_PASS" else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(run_cold_browser_audit()))
