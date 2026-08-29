#!/usr/bin/env python3
"""
evaluation/ingest_repair/scripts/diagnose_ingest.py
Bounded Playwright script to reproduce and diagnose upload/paste ingest failures.
"""
import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from playwright.async_api import async_playwright

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_PATH = REPO_ROOT / "evaluation" / "ingest_repair" / "fixtures" / "fixture.eml"
SHOT_DIR = REPO_ROOT / "screenshots" / "ingest_repair"
SHOT_DIR.mkdir(parents=True, exist_ok=True)

async def run_diagnostics(ui_url: str, mode_label: str):
    print(f"=== Starting Ingest Diagnostics for {mode_label} ({ui_url}) ===")
    evidence = {
        "mode": mode_label,
        "ui_url": ui_url,
        "timestamp": time.time(),
        "console_logs": [],
        "console_errors": [],
        "network_requests": [],
        "network_responses": [],
        "failed_requests": [],
        "options_preflights": [],
        "steps": {}
    }

    if not FIXTURE_PATH.exists():
        raise FileNotFoundError(f"Fixture not found at {FIXTURE_PATH}")
    fixture_raw = FIXTURE_PATH.read_text(encoding="utf-8")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1600, "height": 1000})
        page = await context.new_page()

        def on_console(msg):
            evidence["console_logs"].append({"type": msg.type, "text": msg.text})
            if msg.type == "error":
                print(f"  [JS ERROR] {msg.text}")
                evidence["console_errors"].append(msg.text)
        page.on("console", on_console)

        def on_request(req):
            entry = {
                "url": req.url,
                "method": req.method,
                "headers": req.headers,
                "post_data": req.post_data[:500] if req.post_data else None
            }
            evidence["network_requests"].append(entry)
            if req.method == "OPTIONS":
                print(f"  [OPTIONS REQ] {req.url}")
        page.on("request", on_request)

        async def on_response(res):
            entry = {
                "url": res.url,
                "status": res.status,
                "headers": res.headers,
                "method": res.request.method
            }
            evidence["network_responses"].append(entry)
            if res.request.method == "OPTIONS":
                print(f"  [OPTIONS RES] {res.status} {res.url}")
                evidence["options_preflights"].append(entry)
            if res.status >= 400:
                print(f"  [HTTP FAIL] {res.status} {res.request.method} {res.url}")
                try:
                    body = await res.text()
                except Exception as e:
                    body = f"<could not read body: {e}>"
                entry["body"] = body
                evidence["failed_requests"].append(entry)
        page.on("response", on_response)

        def on_request_failed(req):
            entry = {
                "url": req.url,
                "method": req.method,
                "failure": req.failure
            }
            print(f"  [NET FAILED] {req.method} {req.url} -- failure: {req.failure}")
            evidence["failed_requests"].append(entry)
        page.on("requestfailed", on_request_failed)

        # Step 0: Dashboard Feed Loading (GET path)
        print("\n--- Step 0: Load Dashboard & Verify Feed ---")
        try:
            await page.goto(ui_url, wait_until="networkidle", timeout=15000)
            await page.wait_for_selector("table tbody tr, [role='row']", timeout=10000)
            evidence["steps"]["step0_dashboard"] = {"status": "PASS"}
            print("  [PASS] Dashboard loaded and feed rendered.")
        except Exception as e:
            evidence["steps"]["step0_dashboard"] = {"status": "FAIL", "error": repr(e)}
            print(f"  [FAIL] Dashboard load failed: {e}")
            await page.screenshot(path=str(SHOT_DIR / f"{mode_label}_step0_FAIL.png"))

        # Step 1: Upload Fixture .eml through Dropzone
        print("\n--- Step 1: Test .eml Upload through Dropzone ---")
        try:
            file_mode_btn = page.locator("button:has-text('File Upload')").first
            if await file_mode_btn.count() > 0:
                await file_mode_btn.click()

            file_input = page.locator("input[type='file']").first
            await file_input.set_input_files(str(FIXTURE_PATH))
            print(f"  Attached fixture {FIXTURE_PATH.name}")

            await asyncio.sleep(3.0)

            # Dropzone specific error banner
            err_locator = page.locator("div.bg-rose-500\\/10.border-rose-500\\/30")
            has_err = await err_locator.count() > 0
            err_text = await err_locator.first.text_content() if has_err else None

            # Check if modal opened or subject appeared in feed
            modal_locator = page.locator("div[role='dialog']")
            modal_opened = await modal_locator.count() > 0

            subject_locator = page.locator("text=/SEC-TEST.*RFC 5322/i")
            appeared = await subject_locator.count() > 0

            await page.screenshot(path=str(SHOT_DIR / f"{mode_label}_upload_result.png"))

            # If modal opened, dismiss it to unblock next interactions
            if modal_opened:
                await page.keyboard.press("Escape")
                await asyncio.sleep(0.5)

            if has_err or (not appeared and not modal_opened):
                evidence["steps"]["step1_upload"] = {
                    "status": "FAIL",
                    "ui_error_message": err_text,
                    "subject_appeared": appeared,
                    "modal_opened": modal_opened
                }
                print(f"  [FAIL] Upload failed! UI Error: {err_text}, Appeared: {appeared}, Modal: {modal_opened}")
            else:
                evidence["steps"]["step1_upload"] = {
                    "status": "PASS",
                    "subject_appeared": appeared,
                    "modal_opened": modal_opened
                }
                print("  [PASS] Upload succeeded and modal/feed updated.")
        except Exception as e:
            evidence["steps"]["step1_upload"] = {"status": "EXCEPTION", "error": repr(e)}
            print(f"  [EXCEPTION] Upload step threw: {e}")
            await page.screenshot(path=str(SHOT_DIR / f"{mode_label}_upload_EXCEPTION.png"))

        # Step 2: Raw RFC 5322 Paste Test
        print("\n--- Step 2: Test Raw RFC 5322 Paste ---")
        try:
            # Ensure any modal is closed
            await page.keyboard.press("Escape")
            await asyncio.sleep(0.5)

            raw_mode_btn = page.locator("button:has-text('Raw RFC 5322')").first
            await raw_mode_btn.click()
            await asyncio.sleep(0.5)

            textarea = page.locator("textarea").first
            await textarea.fill(fixture_raw)

            submit_btn = page.locator("button:has-text('Execute Forensic Triage')").first
            await submit_btn.click()
            print("  Clicked 'Execute Forensic Triage'")

            await asyncio.sleep(3.0)

            err_locator = page.locator("div.bg-rose-500\\/10.border-rose-500\\/30")
            has_err = await err_locator.count() > 0
            err_text = await err_locator.first.text_content() if has_err else None

            modal_locator = page.locator("div[role='dialog']")
            modal_opened = await modal_locator.count() > 0

            await page.screenshot(path=str(SHOT_DIR / f"{mode_label}_paste_result.png"))

            if has_err or not modal_opened:
                evidence["steps"]["step2_paste"] = {
                    "status": "FAIL",
                    "ui_error_message": err_text,
                    "modal_opened": modal_opened
                }
                print(f"  [FAIL] Paste failed! UI Error: {err_text}, Modal: {modal_opened}")
            else:
                evidence["steps"]["step2_paste"] = {
                    "status": "PASS",
                    "modal_opened": True
                }
                print("  [PASS] Paste succeeded.")
        except Exception as e:
            evidence["steps"]["step2_paste"] = {"status": "EXCEPTION", "error": repr(e)}
            print(f"  [EXCEPTION] Paste step threw: {e}")
            await page.screenshot(path=str(SHOT_DIR / f"{mode_label}_paste_EXCEPTION.png"))

        await browser.close()

    out_path = REPO_ROOT / "evaluation" / "ingest_repair" / f"{mode_label}_diagnosis.json"
    out_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(f"\nSaved evidence JSON to {out_path}")
    return evidence

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ui-url", default="http://localhost:3000")
    parser.add_argument("--mode", required=True, choices=["mode_a", "mode_b"])
    args = parser.parse_args()
    asyncio.run(run_diagnostics(args.ui_url, args.mode))
