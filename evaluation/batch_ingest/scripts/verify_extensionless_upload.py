#!/usr/bin/env python3
"""Bounded Browser Proof for Extensionless File Upload (B-3).
Uploads a real extensionless SpamAssassin email through the frontend dropzone,
proves ingestion, and validates presence on the live threat feed.
"""

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
ARTIFACTS_DIR = REPO_ROOT / "evaluation" / "artifacts"
SCREENSHOTS_DIR = ARTIFACTS_DIR / "screenshots"


def wait_http(url: str, timeout: int = 30) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.5) as r:
                if 200 <= r.status < 400:
                    return True
        except Exception:
            pass
        time.sleep(0.3)
    return False


def main():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    scratch_db = REPO_ROOT / "evaluation" / "harness_scratch.db"
    if scratch_db.exists():
        try:
            scratch_db.unlink()
        except Exception:
            pass

    fixture_path = REPO_ROOT / "evaluation" / "batch_ingest" / "fixtures" / "00001.7c53336b37003a9286aba55d2945844c"
    if not fixture_path.exists():
        print(f"[ERROR] Extensionless fixture not found: {fixture_path}")
        sys.exit(1)

    print("======================================================================")
    print("  SENTRY EXTENSIONLESS BROWSER UPLOAD VERIFICATION (B-3)")
    print("======================================================================")
    print(f"Target Fixture: {fixture_path.name}")

    cleanup_ps1 = REPO_ROOT / "tools" / "cleanup.ps1"
    if cleanup_ps1.exists() and sys.platform == "win32":
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(cleanup_ps1)], check=False)

    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite+aiosqlite:///{scratch_db.as_posix()}"
    env["SYNC_DATABASE_URL"] = f"sqlite:///{scratch_db.as_posix()}"
    env["ENVIRONMENT"] = "demo"
    backend_cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000", "--host", "127.0.0.1"]
    backend_proc = subprocess.Popen(backend_cmd, cwd=str(REPO_ROOT / "backend"), env=env)

    frontend_cmd = ["npm.cmd" if sys.platform == "win32" else "npm", "run", "dev"]
    frontend_proc = subprocess.Popen(frontend_cmd, cwd=str(REPO_ROOT / "frontend"))

    try:
        if not wait_http("http://127.0.0.1:8000/health", timeout=30):
            raise RuntimeError("Backend failed to boot within 30s")
        if not wait_http("http://127.0.0.1:3000", timeout=30):
            raise RuntimeError("Frontend failed to boot within 30s")

        # Seed initial 18 emails
        req = urllib.request.Request("http://127.0.0.1:8000/api/v1/samples/seed", data=b"", method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            assert resp.status == 200, "Seed failed"

        print(">> Stack booted and seeded. Connecting Playwright...")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1440, "height": 900})
            page = context.new_page()

            page.goto("http://127.0.0.1:3000", wait_until="networkidle", timeout=20000)
            page.wait_for_selector("table tbody tr", timeout=10000)
            init_rows = len(page.locator("table tbody tr").all())
            print(f"  [ INFO ] Initial feed rows: {init_rows}")
            assert init_rows == 18, f"Expected 18 seed rows, got {init_rows}"

            # Upload the extensionless file
            file_input = page.locator("input[type='file']").first
            file_input.set_input_files(str(fixture_path))
            print(f"  [ INFO ] Uploaded extensionless file '{fixture_path.name}' to dropzone")

            # Wait for Subject to appear on live feed
            target_subject = "Re: New Sequences Window"
            item_locator = page.locator(f"text={target_subject}").first
            item_locator.wait_for(state="visible", timeout=10000)
            print(f"  [ PASS ] Target subject '{target_subject}' visible on threat feed")

            page.wait_for_timeout(500)
            updated_rows = len(page.locator("table tbody tr").all())
            print(f"  [ PASS ] Feed rows updated: {init_rows} -> {updated_rows} (delta: +{updated_rows - init_rows})")
            assert updated_rows == 19, f"Expected 19 rows after upload, got {updated_rows}"

            shot_file = SCREENSHOTS_DIR / "extensionless_upload_success.png"
            page.screenshot(path=str(shot_file), full_page=False)
            print(f"  [ SHOT ] Captured: {shot_file.name}")

            browser.close()

        receipt = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "fixture": fixture_path.name,
            "has_extension": False,
            "extracted_subject": target_subject,
            "feed_row_count_before": init_rows,
            "feed_row_count_after": updated_rows,
            "delta": updated_rows - init_rows,
            "screenshot": "evaluation/artifacts/screenshots/extensionless_upload_success.png",
            "verdict": "PASS"
        }

        receipt_path = ARTIFACTS_DIR / "extensionless_proof_receipt.json"
        receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        print(f"\n[SUCCESS] Extensionless upload proof receipt written to: {receipt_path}")

    finally:
        if backend_proc is not None:
            backend_proc.terminate()
            backend_proc.wait()
        if frontend_proc is not None:
            frontend_proc.terminate()
            frontend_proc.wait()
        if cleanup_ps1.exists() and sys.platform == "win32":
            subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(cleanup_ps1)], check=False)


if __name__ == "__main__":
    main()
