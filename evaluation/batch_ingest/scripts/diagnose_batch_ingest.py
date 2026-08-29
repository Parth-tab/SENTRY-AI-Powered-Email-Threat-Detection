#!/usr/bin/env python3
"""Bounded diagnostic script for Phase 0 of BATCH-INGESTION.
Attempts 4 real UI dropzone interactions against http://127.0.0.1:3000:
  (a) drop ONE extensionless ham file
  (b) multi-select 10 extensionless files
  (c) drop small zip containing 3 .eml files
  (d) drop ling.csv-style CSV fixture
Captures console errors, network requests (URL + status), dropzone reaction, and log lines.
"""

import sys
import json
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "evaluation" / "batch_ingest" / "fixtures"
MAIN_HAM_DIR = Path(r"C:\Users\Parth\Downloads\ham_zipped\main_ham")

async def run_diagnostics():
    results = {}
    print("[Batch Diagnosis] Starting bounded Playwright diagnostic on http://127.0.0.1:3000 ...")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1600, "height": 900})

        console_logs = []
        network_calls = []

        page.on("console", lambda m: console_logs.append(f"[{m.type}] {m.text}"))
        page.on("response", lambda r: network_calls.append({
            "url": r.url,
            "status": r.status,
            "status_text": r.status_text
        }))

        await page.goto("http://127.0.0.1:3000", wait_until="domcontentloaded", timeout=15_000)
        await asyncio.sleep(2.0)

        file_input = page.locator("input[type='file']").first

        # (a) Drop ONE extensionless ham file
        print("[Diagnosis (a)] Attempting ONE extensionless ham file...")
        console_logs.clear()
        network_calls.clear()
        extless_file = list(FIXTURES_DIR.glob("00001.*"))[0]
        
        try:
            await file_input.set_input_files(str(extless_file))
            await asyncio.sleep(2.0)
            dropzone_text = await page.locator("body").inner_text()
            error_el = page.locator("div.bg-rose-500\\/10, div.text-rose-400")
            err_text = await error_el.text_content() if await error_el.count() > 0 else ""
            results["(a) single_extensionless"] = {
                "file": extless_file.name,
                "network": list(network_calls),
                "console": list(console_logs),
                "error_displayed": err_text.strip(),
                "verdict": "REJECTED" if any(n["status"] >= 400 for n in network_calls) or err_text else "ACCEPTED"
            }
        except Exception as exc:
            results["(a) single_extensionless"] = {"exception": repr(exc), "verdict": "EXCEPTION"}

        # (b) Multi-select 10 extensionless files
        print("[Diagnosis (b)] Attempting multi-select 10 extensionless files...")
        console_logs.clear()
        network_calls.clear()
        ten_files = [str(f) for f in sorted(list(MAIN_HAM_DIR.iterdir()))[:10]]
        try:
            # Check if input supports multiple
            is_multiple = await file_input.get_attribute("multiple")
            await file_input.set_input_files(ten_files)
            await asyncio.sleep(2.0)
            error_el = page.locator("div.bg-rose-500\\/10, div.text-rose-400")
            err_text = await error_el.text_content() if await error_el.count() > 0 else ""
            results["(b) multi_select_10_files"] = {
                "input_has_multiple_attribute": is_multiple is not None,
                "files_count": len(ten_files),
                "network": list(network_calls),
                "console": list(console_logs),
                "error_displayed": err_text.strip(),
                "verdict": "REJECTED_OR_SINGLE_ONLY"
            }
        except Exception as exc:
            results["(b) multi_select_10_files"] = {"exception": repr(exc), "verdict": "EXCEPTION"}

        # (c) Drop small zip containing 3 .eml files
        print("[Diagnosis (c)] Attempting small zip archive...")
        console_logs.clear()
        network_calls.clear()
        zip_file = FIXTURES_DIR / "small_sample.zip"
        try:
            await file_input.set_input_files(str(zip_file))
            await asyncio.sleep(2.0)
            error_el = page.locator("div.bg-rose-500\\/10, div.text-rose-400")
            err_text = await error_el.text_content() if await error_el.count() > 0 else ""
            results["(c) zip_archive"] = {
                "file": zip_file.name,
                "network": list(network_calls),
                "console": list(console_logs),
                "error_displayed": err_text.strip(),
                "verdict": "REJECTED" if any(n["status"] >= 400 for n in network_calls) or err_text else "ACCEPTED"
            }
        except Exception as exc:
            results["(c) zip_archive"] = {"exception": repr(exc), "verdict": "EXCEPTION"}

        # (d) Drop ling.csv fixture (subject, body, label)
        print("[Diagnosis (d)] Attempting CSV fixture...")
        console_logs.clear()
        network_calls.clear()
        csv_file = FIXTURES_DIR / "ling_sample.csv"
        try:
            await file_input.set_input_files(str(csv_file))
            await asyncio.sleep(2.0)
            error_el = page.locator("div.bg-rose-500\\/10, div.text-rose-400")
            err_text = await error_el.text_content() if await error_el.count() > 0 else ""
            results["(d) csv_file"] = {
                "file": csv_file.name,
                "network": list(network_calls),
                "console": list(console_logs),
                "error_displayed": err_text.strip(),
                "verdict": "REJECTED" if any(n["status"] >= 400 for n in network_calls) or err_text else "ACCEPTED"
            }
        except Exception as exc:
            results["(d) csv_file"] = {"exception": repr(exc), "verdict": "EXCEPTION"}

        await browser.close()

    out_path = REPO_ROOT / "evaluation" / "batch_ingest" / "diagnosis_raw.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"[Batch Diagnosis] Completed. Raw results written to {out_path}")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    asyncio.run(run_diagnostics())
