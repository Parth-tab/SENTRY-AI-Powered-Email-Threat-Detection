#!/usr/bin/env python3
"""Cold Browser Simulation Script (Phase 5).
Audits the public GitHub repository from a fresh, logged-out, unauthenticated perspective.
Verifies time-to-first-content, badge/image rendering health, link resolution,
topics/description/license visibility, and captures above-the-fold screenshots.
"""

import time
import json
import urllib.request
import urllib.error
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO_URL = "https://github.com/Parth-tab/SENTRY-AI-Powered-Email-Threat-Detection"
OUTPUT_DIR = Path("E:/SENTRY/evaluation/final_inch")
SCREENSHOT_PATH = OUTPUT_DIR / "above_the_fold.png"
RECEIPT_PATH = OUTPUT_DIR / "stranger_simulation.json"

def check_url_resolution(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return {"url": url, "status": resp.status, "ok": 200 <= resp.status < 400}
    except urllib.error.HTTPError as e:
        return {"url": url, "status": e.code, "ok": False}
    except Exception as e:
        return {"url": url, "status": str(e), "ok": False}

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("======================================================================")
    print("  SENTRY COLD-BROWSER STRANGER SIMULATION")
    print("======================================================================")
    print(f"Target URL: {REPO_URL}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            storage_state=None
        )
        page = context.new_page()

        # Step 1: Measure Time to First README Content
        t0 = time.time()
        page.goto(REPO_URL, wait_until="networkidle", timeout=30000)
        page.wait_for_selector("article.markdown-body", timeout=20000)
        time_to_readme_seconds = round(time.time() - t0, 3)
        print(f"  [ PASS ] README article attached in {time_to_readme_seconds}s")

        # Step 2: Capture Above-The-Fold Screenshot
        page.screenshot(path=str(SCREENSHOT_PATH), full_page=False)
        print(f"  [ SHOT ] Above-the-fold screenshot captured: {SCREENSHOT_PATH.name}")

        # Step 3: Audit Topics, Description, License, Release in About Section
        about_h2 = page.locator("h2", has_text="About")
        about_cell = about_h2.first.locator("xpath=..") if about_h2.count() > 0 else page.locator("div.BorderGrid-cell").first
        
        desc_elem = about_cell.locator("p").first
        desc_text = desc_elem.inner_text().strip() if desc_elem.count() > 0 else ""
        
        topics = [t.strip() for t in page.locator("a[href*='/topics/']").all_inner_texts() if t.strip()]
        
        license_elem = page.locator("a[href*='LICENSE']").first
        has_license = license_elem.count() > 0
        license_text = license_elem.inner_text().strip() if has_license else ""

        release_elem = page.locator("a[href*='/releases/tag/']").first
        has_release = release_elem.count() > 0
        release_text = release_elem.inner_text().strip() if has_release else ""

        print(f"  [ INFO ] About Description: '{desc_text}'")
        print(f"  [ INFO ] About Topics ({len(topics)}): {topics}")
        print(f"  [ INFO ] License visible: {has_license} ('{license_text}')")
        print(f"  [ INFO ] Release visible: {has_release} ('{release_text}')")

        # Step 4: Audit Every Image/Badge in README
        readme_images = page.locator("article.markdown-body img").all()
        images_audit = []
        for img in readme_images:
            src = img.get_attribute("src") or ""
            alt = img.get_attribute("alt") or ""
            img.scroll_into_view_if_needed()
            page.wait_for_timeout(300)
            is_loaded = img.evaluate("el => el.complete && el.naturalWidth > 0")
            nw = img.evaluate("el => el.naturalWidth")
            nh = img.evaluate("el => el.naturalHeight")
            images_audit.append({
                "src": src,
                "alt": alt,
                "dimensions": f"{nw}x{nh}",
                "rendered": bool(is_loaded)
            })

        print(f"  [ AUDIT] Evaluated {len(images_audit)} images/badges in README:")
        broken_images = [img for img in images_audit if not img["rendered"]]
        for img in images_audit:
            print(f"    - [{img['alt']}] Rendered: {img['rendered']} ({img['dimensions']})")

        # Step 5: Audit First 3 Links in README
        readme_links = page.locator("article.markdown-body a[href^='http']").all()
        links_to_test = []
        for a in readme_links[:10]:
            href = a.get_attribute("href")
            if href and href not in links_to_test:
                links_to_test.append(href)
            if len(links_to_test) >= 3:
                break

        link_results = []
        for l in links_to_test:
            res = check_url_resolution(l)
            print(f"    - Link '{l}': Status {res['status']} (ok={res['ok']})")
            link_results.append(res)

        browser.close()

        # Step 6: Form Receipt
        receipt = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "target_url": REPO_URL,
            "browser_mode": "Chromium (fresh context, logged-out, unauthenticated)",
            "time_to_readme_seconds": time_to_readme_seconds,
            "description": desc_text,
            "topics": topics,
            "license_visible": has_license,
            "license_text": license_text,
            "release_visible": has_release,
            "release_text": release_text,
            "total_images_in_readme": len(images_audit),
            "rendered_images_count": len(images_audit) - len(broken_images),
            "broken_images_count": len(broken_images),
            "images_audit": images_audit,
            "first_links_audit": link_results,
            "above_the_fold_screenshot": "evaluation/final_inch/above_the_fold.png",
            "verdict": "PASS" if len(broken_images) == 0 and all(r["ok"] for r in link_results) else "FINDINGS_RECORDED"
        }

        RECEIPT_PATH.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        print(f"\n[SUCCESS] Stranger simulation receipt written to: {RECEIPT_PATH}")

if __name__ == "__main__":
    main()
