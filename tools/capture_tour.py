#!/usr/bin/env python3
"""SENTRY guided-tour capture — deterministic screenshots for docs/FEATURE_TOUR.md.

Reuses the golden harness machinery (boot, markers, cleanup) under the same
laws: no foreground servers, ports 8000/3000 only, every wait timed, global
watchdog, cleanup guaranteed. Does NOT modify verify_sentry.py.

Run:   E:/SENTRY/.venv/Scripts/python tools/capture_tour.py --start
Out:   docs/assets/tour/*.png, docs/assets/tour/manifest.json,
       docs/assets/tour/08-forensic-report.pdf (if export fires)
"""

import argparse
import asyncio
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from verify_sentry import (  # noqa: E402
    DASHBOARD_MARKER, DETAIL_MARKER, FEED_ROW_TEXT, GRAPH_NAV, MAP_NAV,
    Stack, http_json, kill_listeners, wait_http,
)

TOUR_DIR = REPO_ROOT / "docs" / "assets" / "tour"
VIEWPORT = {"width": 1920, "height": 1080}
SCALE = 2                     # retina-crisp on GitHub zoom

AUTH_RE    = re.compile(r"RFC Authentication|SPF.*7208|DKIM|DMARC", re.I)
VERIFY_RE  = re.compile(r"Verify Hash Chain|Verify.*Integrity", re.I)
SUCCESS_RE = re.compile(r"INTEGRITY VERIFIED|verified|valid|intact|pass", re.I)
REPORT_RE  = re.compile(r"Download PDF|Export Forensic PDF|Forensic Report", re.I)
VAULT_NAV  = re.compile(r"Forensic Vault|Reports", re.I)
CANVAS     = "canvas, svg"


def now():
    return datetime.now(timezone.utc).isoformat()


class Tour:
    def __init__(self):
        self.manifest = {"started": now(), "shots": [], "console_errors": []}

    def record(self, name, status, hint, detail=""):
        self.manifest["shots"].append(
            {"name": name, "file": f"{name}.png", "status": status,
             "caption_hint": hint, "detail": str(detail)[:300]})
        print(f"  [{status:^7}] {name}" + (f" -- {detail}" if detail else ""))


async def shot(page, tour, name, hint, full_page=False):
    try:
        await page.screenshot(path=str(TOUR_DIR / f"{name}.png"),
                              full_page=full_page)
        tour.record(name, "PASS", hint)
    except Exception as exc:
        try:
            await page.screenshot(path=str(TOUR_DIR / f"{name}_FAIL.png"))
        except Exception:
            pass
        tour.record(name, "FAIL", hint, repr(exc)[:200])


async def nav_click(page, pattern):
    """Click a navigation button or tab matching pattern."""
    for loc in (page.get_by_role("button", name=pattern),
                page.get_by_role("link", name=pattern),
                page.get_by_text(pattern)):
        try:
            await loc.first.click(timeout=5_000)
            return True
        except Exception:
            continue
    return False


async def open_first_alert(page, ui):
    """Navigate to dashboard, settle websocket, open the EmailDetailModal.

    Mirrors the harness exactly: 3s settle after feed rows appear, then click
    the Investigate button (not a raw row click which lands on severity text).
    Gate on the modal overlay (div.fixed.inset-0.z-50) before returning — this
    is the only element that proves the modal is mounted and not just text on
    the dashboard.
    """
    await page.goto(ui, timeout=30_000)
    await page.get_by_text(DASHBOARD_MARKER).first.wait_for(
        state="visible", timeout=20_000)
    await page.get_by_text(FEED_ROW_TEXT).first.wait_for(
        state="visible", timeout=20_000)
    await asyncio.sleep(3)                           # websocket settle, mirrors harness
    # Click the first Investigate button explicitly
    await page.locator('button:has-text("Investigate")').first.click(timeout=10_000)
    # Gate: modal overlay must be attached before we shoot
    await page.locator("div.fixed.inset-0.z-50").first.wait_for(
        state="attached", timeout=15_000)
    await asyncio.sleep(1.5)                         # React render settle


async def run_tour(page, tour, ui):
    # -- Stop 1: dashboard hero ------------------------------------------
    await page.goto(ui, timeout=30_000)
    await page.get_by_text(DASHBOARD_MARKER).first.wait_for(
        state="visible", timeout=20_000)
    await page.get_by_text(FEED_ROW_TEXT).first.wait_for(
        state="visible", timeout=20_000)
    await asyncio.sleep(2)                    # websocket live indicator settles
    await shot(page, tour, "01-dashboard",
               "SOC dashboard: metric cards, live alert feed, severity badges")

    # -- Stop 2: forensic analyzer modal ----------------------------------
    await open_first_alert(page, ui)
    await shot(page, tour, "02-forensic-analyzer",
               "Split-screen analyzer: preserved email vs. dissection")

    # -- Stop 3: authentication forensics (scrolled view in modal) ---------
    try:
        await page.evaluate("""() => {
            const scrollables = document.querySelectorAll('.overflow-y-auto');
            scrollables.forEach(el => el.scrollTop = 220);
        }""")
        await asyncio.sleep(1)
        await shot(page, tour, "03-authentication-forensics",
                   "SPF/DKIM/DMARC verdict matrix and origin geolocation")
    except Exception as e:
        tour.record("03-authentication-forensics", "SKIP",
                    "auth section scroll failed", str(e))

    # -- Stop 4: linguistic & model ensemble triangulation -----------------
    try:
        await page.evaluate("""() => {
            const scrollables = document.querySelectorAll('.overflow-y-auto');
            scrollables.forEach(el => el.scrollTop = 0);
        }""")
        await asyncio.sleep(1)
        await shot(page, tour, "04-attack-language",
                   "3-layer ensemble triangulation and linguistic feature breakdown")
    except Exception as e:
        tour.record("04-attack-language", "SKIP",
                    "linguistic section failed", str(e))

    # Close modal before navigating tabs
    await page.keyboard.press("Escape")
    await asyncio.sleep(0.5)

    # -- Stop 5: relay map --------------------------------------------------
    if await nav_click(page, MAP_NAV):
        await page.locator(CANVAS).first.wait_for(state="visible",
                                                  timeout=15_000)
        await asyncio.sleep(3)                # arcs render/settle
        await shot(page, tour, "05-relay-map",
                   "Multi-hop transmission map, origin highlighted")
    else:
        tour.record("05-relay-map", "SKIP", "map nav not found")

    # -- Stop 6: campaign graph ---------------------------------------------
    if await nav_click(page, GRAPH_NAV):
        await page.locator(CANVAS).first.wait_for(state="visible",
                                                  timeout=15_000)
        await asyncio.sleep(3)                # graph layout settles
        await shot(page, tour, "06-campaign-graph",
                   "Correlation graph: emails, domains, IPs, campaign cluster")
    else:
        tour.record("06-campaign-graph", "SKIP", "graph nav not found")

    # -- Stop 7: chain-of-custody verification -------------------------------
    if await nav_click(page, VAULT_NAV):
        await page.get_by_text("RFC 3227 Hash-Chain Tamper Verification").first.wait_for(
            state="visible", timeout=10_000)
        if await nav_click(page, VERIFY_RE):
            try:
                await page.get_by_text(SUCCESS_RE).first.wait_for(
                    state="visible", timeout=10_000)
            except Exception:
                pass
            await asyncio.sleep(1)
            await shot(page, tour, "07-chain-integrity",
                       "Hash-chain verification result, live in UI")
        else:
            tour.record("07-chain-integrity", "SKIP", "verify control not found")
    else:
        tour.record("07-chain-integrity", "SKIP", "vault nav not found")

    # -- Stop 8: forensic report export (PDF download & UI) ------------------
    try:
        async with page.expect_download(timeout=20_000) as dl_info:
            await nav_click(page, REPORT_RE)
        dl = await dl_info.value
        await dl.save_as(str(TOUR_DIR / "08-forensic-report.pdf"))
        tour.record("08-forensic-report", "PASS",
                    "Exported PDF dossier saved to repo")
        await asyncio.sleep(1)
        await shot(page, tour, "08-forensic-report",
                   "Report/export UI after dossier generation")
    except Exception as e:
        await asyncio.sleep(1)
        await shot(page, tour, "08-forensic-report",
                   f"Report/export UI (download capture state: {e})")


async def main_async(args, tour):
    api = f"http://127.0.0.1:{args.api_port}"
    ui = f"http://127.0.0.1:{args.ui_port}"
    stack = None
    try:
        if args.start:
            kill_listeners(args.api_port)
            kill_listeners(args.ui_port)
            stack = Stack(args.api_port, args.ui_port)
            stack.start_backend()
            if not await asyncio.to_thread(wait_http, api + "/health", 90):
                print("backend failed to boot"); return 3
            stack.start_frontend()
            if not await asyncio.to_thread(wait_http, ui, 90):
                print("frontend failed to boot"); return 3
        http_json("POST", api + "/api/v1/samples/seed")   # idempotent

        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            try:
                browser = await pw.chromium.launch(headless=True)
            except Exception:
                subprocess.run([sys.executable, "-m", "playwright",
                                "install", "chromium"], check=False)
                browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page(viewport=VIEWPORT,
                                          device_scale_factor=SCALE)
            page.on("console", lambda m: tour.manifest["console_errors"]
                    .append(m.text) if m.type == "error" else None)
            await run_tour(page, tour, ui)
            await browser.close()
        return 0
    finally:
        if stack is not None and not args.keep_servers:
            stack.shutdown()


def main():
    p = argparse.ArgumentParser(description="SENTRY tour capture")
    p.add_argument("--start", action="store_true")
    p.add_argument("--api-port", type=int, default=8000)
    p.add_argument("--ui-port", type=int, default=3000)
    p.add_argument("--timeout", type=int, default=360)
    p.add_argument("--keep-servers", action="store_true")
    args = p.parse_args()

    TOUR_DIR.mkdir(parents=True, exist_ok=True)
    tour = Tour()
    print(f"SENTRY tour capture -- ui :{args.ui_port}  watchdog {args.timeout}s\n")
    try:
        code = asyncio.run(asyncio.wait_for(main_async(args, tour),
                                            timeout=args.timeout))
    except asyncio.TimeoutError:
        code = 2
        print(f"\n!! watchdog fired ({args.timeout}s)")
    manifest = TOUR_DIR / "manifest.json"
    manifest.write_text(json.dumps(tour.manifest, indent=2), encoding="utf-8")
    passed = sum(1 for s in tour.manifest["shots"] if s["status"] == "PASS")
    print(f"\nTour: {passed}/{len(tour.manifest['shots'])} shots -> {TOUR_DIR}")
    print(f"Manifest: {manifest}")
    return code


if __name__ == "__main__":
    sys.exit(main())
