#!/usr/bin/env python3
"""Bounded Mode B stranger-boot verification script for ING-001/ING-002.
Interacts with the real UI at http://127.0.0.1:3000 (booted without VITE_API_URL),
uploads a .eml file, pastes a raw RFC 5322 email, and saves screenshot evidence.
"""

import sys
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

REPO_ROOT = Path(__file__).resolve().parents[3]
SHOT_DIR = REPO_ROOT / "screenshots" / "verify"
SHOT_DIR.mkdir(parents=True, exist_ok=True)

async def run_mode_b_verification():
    print("[Mode B] Starting bounded browser verification on http://127.0.0.1:3000 ...")
    
    upload_fixture = REPO_ROOT / "sample_emails" / "bec_executive_wire_fraud.eml"
    paste_fixture = REPO_ROOT / "sample_emails" / "sbi_phishing_tor_relay.eml"
    raw_payload = paste_fixture.read_text(encoding="utf-8")
    
    upload_subject = "Immediate Out-of-Band Wire Transfer Request"
    paste_subject = "Mandatory KYC Verification Required Within 24 Hours"

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1600, "height": 900})
        
        console_errors = []
        network_errors = []
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.on("response", lambda r: network_errors.append(f"{r.status} {r.url}") if r.status >= 400 else None)

        # 1. Open Dashboard
        await page.goto("http://127.0.0.1:3000", wait_until="domcontentloaded", timeout=15_000)
        await asyncio.sleep(2.0)

        # 2. Test File Upload
        print("[Mode B] Testing .eml file upload...")
        file_mode_btn = page.locator("button:has-text('File Upload')").first
        if await file_mode_btn.count() > 0:
            await file_mode_btn.click(timeout=3_000)
        
        file_input = page.locator("input[type='file']").first
        await file_input.set_input_files(str(upload_fixture))

        # Wait for detail modal to mount
        modal = page.locator("div[role='dialog']").first
        await modal.wait_for(state="attached", timeout=15_000)
        upload_shot = SHOT_DIR / "mode_b_upload.png"
        await page.screenshot(path=str(upload_shot), full_page=True)
        print(f"[Mode B] Upload modal mounted successfully. Screenshot saved to {upload_shot}")

        # Dismiss modal via Escape
        await page.keyboard.press("Escape")
        await modal.wait_for(state="detached", timeout=5_000)
        await asyncio.sleep(0.5)

        # Confirm subject visible in feed
        await page.locator(f"text={upload_subject}").first.wait_for(state="visible", timeout=5_000)
        print(f"[Mode B] Upload subject '{upload_subject}' confirmed in feed.")

        # 3. Test Raw Paste
        print("[Mode B] Testing raw RFC 5322 paste...")
        raw_mode_btn = page.locator("button:has-text('Raw RFC 5322')").first
        await raw_mode_btn.click(timeout=3_000)
        await asyncio.sleep(0.5)

        textarea = page.locator("textarea").first
        await textarea.fill(raw_payload)

        submit_btn = page.locator("button:has-text('Execute Forensic Triage')").first
        await submit_btn.click(timeout=5_000)

        # Wait for detail modal to mount
        await modal.wait_for(state="attached", timeout=15_000)
        paste_shot = SHOT_DIR / "mode_b_paste.png"
        await page.screenshot(path=str(paste_shot), full_page=True)
        print(f"[Mode B] Paste modal mounted successfully. Screenshot saved to {paste_shot}")

        # Dismiss modal via Escape
        await page.keyboard.press("Escape")
        await modal.wait_for(state="detached", timeout=5_000)
        await asyncio.sleep(0.5)

        # Confirm subject visible in feed
        await page.locator(f"text={paste_subject}").first.wait_for(state="visible", timeout=5_000)
        print(f"[Mode B] Paste subject '{paste_subject}' confirmed in feed.")

        # Check console / network health
        real_console_errors = [e for e in console_errors if not any(k in e.lower() for k in ["favicon", "sourcemap", "devtools"])]
        if real_console_errors:
            print(f"[Mode B WARNING] Console errors encountered: {real_console_errors}")
        if network_errors:
            print(f"[Mode B WARNING] Network HTTP >= 400 errors: {network_errors}")

        await browser.close()
        print("[Mode B] Verification completed successfully with zero fatal errors.")

if __name__ == "__main__":
    asyncio.run(run_mode_b_verification())
