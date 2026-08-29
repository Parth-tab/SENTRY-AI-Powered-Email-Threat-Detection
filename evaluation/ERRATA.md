# Errata — Verification Record

This file annotates post-hoc corrections to the engagement's verification record.
Per the audit culture that governs this repository: **evidence is annotated, not discarded.**

---

## Errata 001 — Golden Check #10 (`ui.email_detail_opens`) — recorded at `e0b6dcd`

**Applies to:** All `15/15` receipts before commit `e0b6dcd`
(cold-boot, fresh-clone, fresh-venv, browserless, archived Gate-0 at `demo-freeze-v2`).

### What happened

`verify_sentry.py` check #10 matched `DETAIL_MARKER`
(`Threat Score|Authentication|Origin|SPF|DKIM|DMARC|Risk Score`) after clicking
the first alert row. The intent was to verify the analyzer modal opened. The flaw:
that text also appears on the dashboard feed rows as authentication verdict chips.
Pre-click count was **2** (dashboard chips); post-click count in normal harness runs
was >2 (modal content arrived). But the check waited only for text, not for the modal
container, so it would pass even if only the dashboard text were present.

The discriminator (`tools/_discriminator.py`) confirmed this by measuring the
`[role=dialog],dialog,.modal,[data-modal]` selector set. That selector returned **0**
in all states — which was correctly interpreted not as a failed click but as a
**true measurement of a semantic gap**: the modal (`div.fixed.inset-0.z-50`) has
none of those semantics. This finding became defect **UX-003**.

Separately, the discriminator's pre/post DETAIL_MARKER counts (2→13) confirm the
modal *did* open in those runs — the click was correct throughout.

### The fix

`e0b6dcd` strengthens check #10 to a two-gate protocol:
1. Wait for `div.fixed.inset-0.z-50` — the modal backdrop element, unique to
   `EmailDetailModal` — to attach to the DOM (this cannot pre-exist on the dashboard).
2. Only then scan for DETAIL_MARKER inside the confirmed-open modal.

Harness 15/15 PASS confirmed under the strengthened check. Pass-time screenshot in
`screenshots/verify/02_email_detail.png` shows the full modal with live forensic data.

### What this means for prior receipts

**All prior 15/15 receipts stand for their remaining 14 checks.**

Check #10 was the only weakened gate. The modal itself was functional throughout:
- Manually captured during the initial build session.
- Machine-verified at HEAD with **zero frontend code changes since `demo-freeze-v2`**
  (all post-seal diffs are `tools/` and `docs/` only).
- The strengthened check at HEAD therefore verifies the same modal that ships at the tag.

The retroactive conclusion: pre-`e0b6dcd` check #10 verified the row-click action;
the modal's correctness is retroactively confirmed by HEAD verification against
unchanged frontend code. The receipts are annotated, not voided.

### Source

Discriminator analysis: `tools/_discriminator.py` (scratch, not committed).
Screenshot evidence: `screenshots/verify/02_email_detail.png`.
Defect registry: `evaluation/defects.json` → UX-003 (modal ARIA semantics gap).
Commit message: `e0b6dcd` (harness section of the message understates this change — this errata serves as the commit's audit supplement).

---

## Errata 002 — "9/9 shots" log line in `capture_tour.py` run

**Applies to:** Tour capture run at `e0b6dcd`, manifest.json shot count.

The capture script logged "9 shots captured" against an 8-stop tour.
Cause: the script called `shot()` twice for stop 08 — once for the pre-export
screenshot and once after the PDF export resolved. Both calls wrote to
`08-forensic-report.png` (second call overwrites first). The manifest JSON
correctly records 8 entries. The tour directory contains exactly 8 PNGs + 1 PDF.
No phantom ninth artifact exists; the count was a log arithmetic artefact.

---

## Errata 003 — Post-Remediation Composite Score Arithmetic — recorded at `ea78aca`

**Applies to:** Post-remediation Blind Panel summary in `evaluation/blind/BLIND_PANEL_REPORT.md` and handoff receipt.

### What happened

Following the remediation of BP-001 (5/5 mutants killed, C4 composite score 96), Panel C recomputed to:
$$\text{Panel C} = \frac{93 + 86 + 91 + 96 + 94}{5} = \mathbf{92.0}$$
Combined with Panel B ($90.6$), the true overall Stranger Readiness Score is:
$$\text{Overall} = \frac{90.6 + 92.0}{2} = \mathbf{91.3}$$
An initial summary line reported `91.2` due to an unrounded floating intermediate before C4 table finalization.

### The fix

Updated `evaluation/blind/BLIND_PANEL_REPORT.md`, `evaluation/blind/state.json`, and `evaluation/HANDOFF.md` to reflect the exact arithmetic composite of **91.3 / 100**.

---

## Errata 004 — Pytest Warnings Accounting (Python 3.12+ / Upstream Deprecations) — recorded at BATCH-004

**Applies to:** Full pytest suite runs without `-W ignore`.

### Accounting of Warnings
A full run of the pytest suite without warning filters emits ~367 non-fatal deprecation warnings categorized into 3 distinct upstream sources:
1. **`datetime.datetime.utcnow()` Deprecation Warnings (~360 instances):** Emitted across SQLite date population and RFC 3227 timestamp generators where `datetime.utcnow()` is flagged for deprecation in future Python versions in favor of `datetime.now(datetime.timezone.utc)`.
2. **Pydantic V2 Config Deprecation (4 instances):** Class-based `Config` in `app/config.py` and response schemas emits `PydanticDeprecatedSince20` notices recommending `ConfigDict`.
3. **Bleach NoCssSanitizerWarning (3 instances):** Emitted in `test_xss_email_body_sanitization` due to `style` attribute presence without a dedicated CSS sanitizer instance.

### Transparency & Integrity Note
None of these warnings represent test assertion failures, memory leaks, or logical defects. All test cases execute with 100% PASS verdicts. In accordance with zero-silent-suppression rules, this ledger explicitly documents upstream technical debt without altering core evaluation metrics.

---

## Errata 005 — Defect Registry Historical Consolidation & Arithmetic Reconciliation (V-1) — recorded at FINAL-INCH

**Applies to:** `evaluation/defects.json` and previous session summary reports.

### What happened
1. **Prior Report Count Arithmetic Discrepancy:** The BATCH-004 session handoff report stated "Open (2) / Resolved (17) / Total (19)" while listing 18 resolved defect IDs by name (`SEC-001`, `SEC-002`, `SEC-003`, `ML-001`, `OBS-001`, `OBS-002`, `CICD-001`, `WS-001`, `AUD-001`, `D-3`, `ING-004`, `CORP-001`, `FEED-001`, `GRAPH-001`, `BATCH-001`, `BATCH-002`, `GRAPH-002`, `BATCH-004`). The arithmetic was discordant ($2 + 18 = 20 \ne 19$) due to an omitted increment when adding `GRAPH-002` and `BATCH-004` to the pre-existing 17-item list.
2. **Historical Registry Truncation:** During earlier compacting sessions (post Gate-0 and post Blind Panel), earlier resolved defect records (`AUD-002`..`AUD-005`, `BP-001`..`BP-004`, `HAM-001`..`HAM-003`, `D-1`..`D-2`, etc.) were compacted from active display rather than maintained in a cumulative append-only register.

### The fix
Reconstructed all historical defects across git history into `evaluation/defects.json`. Explicitly mapped consolidated milestone markers (`BATCH-003` $\rightarrow$ `BATCH-004`, `CORP-002` $\rightarrow$ `CORP-001`, `ING-003` $\rightarrow$ `D-1`), preserving full audit lineage:
- **Total Unique Historical Defects:** 42
- **Resolved:** 36
- **Open:** 2 (`DEF-005`, `MBOX-001`)
- **Deferred:** 1 (`BP-004` - v2.0 roadmap)
- **Consolidated:** 3 (`BATCH-003`, `CORP-002`, `ING-003`)
- **Derivation:** $42 = 36 + 2 + 1 + 3$. Zero phantom or vanished defects.

---

## Errata 006 — Complete Master Defect Ledger (50 IDs) & Dependabot Scope Reconciliation — recorded at FINAL-INCH-2

**Applies to:** `evaluation/defects.json` and Dependabot alert resolution.

### 1. Master Defect Ledger Completion (50 Total IDs)
Following a comprehensive audit across all conventional commit prefixes in git history, eight commit-level feature/fix identifiers (`CORP-003`, `CORP-004`, `CORP-005`, `CORP-006`, `CSV-001`, `CSV-002`, `HAM-004`, `DEF-006`) were identified and permanently entered into the cumulative master register with their evidenced fix commits and regression test references.

**Master Defect Ledger Arithmetic:**
- **Total Tracked Defects:** 50
- **Resolved:** 44
- **Open:** 2 (`DEF-005`, `MBOX-001`)
- **Deferred:** 1 (`BP-004` - v2.0 roadmap)
- **Consolidated:** 3 (`BATCH-003`, `CORP-002`, `ING-003`)
- **Derivation:** $$50 = 44 + 2 + 1 + 3$$

### 2. Dependabot Lockfile & Scope Reconciliation
The repository tracks `frontend/pnpm-lock.yaml` in version control, while the documentation, development quickstart, and CI test pipelines execute commands via `npm`. GitHub Dependabot parses `frontend/pnpm-lock.yaml` and flagged four ecosystem advisories (`GHSA-67mh-4wv8-2f99`, `GHSA-4w7w-66w2-5vf9`, `GHSA-fx2h-pf6j-xcff`, `GHSA-v6wh-96g9-6wx3`). Running `npm audit` directly inside `frontend/` previously reported `ENOLOCK` because `package-lock.json` was omitted from version control. In FINAL-INCH-3, `frontend/pnpm-lock.yaml` was formally upgraded to `vite@6.4.3` and `esbuild@0.25.12`, closing all 4 advisories at the source with `pnpm audit` reporting zero vulnerabilities.

---

## Errata 007 — Lockfile Upgrade, Hero Image False-Positive Explanation & ARCH-001 Ledger Evidencing — recorded at FINAL-INCH-3

**Applies to:** `frontend/pnpm-lock.yaml`, `evaluation/defects.json`, `evaluation/final_inch/cold_browser_simulation.py`.

### 1. Vite & Esbuild Direct Vulnerability Fix
Rather than relying on risk-dismissal rationales, all 4 upstream build-toolchain advisories were directly fixed by upgrading `frontend/pnpm-lock.yaml` to `vite@6.4.3` and `esbuild@0.25.12`. Root cause mechanism: dual lockfiles with divergent versions; the BP-002 bump updated the untracked lockfile while the tracked `pnpm-lock.yaml` remained at Vite 5.4.21 until FINAL-INCH-3:
- `GHSA-67mh-4wv8-2f99` (`esbuild` dev-server request exposure): Fixed in `>=0.24.3` (installed: `0.25.12`).
- `GHSA-4w7w-66w2-5vf9` (`vite` path traversal in `.map` files): Fixed in `>=6.4.2` (installed: `6.4.3`).
- `GHSA-fx2h-pf6j-xcff` (`vite` Windows alternate data stream bypass): Fixed in `>=6.4.1` (installed: `6.4.3`).
- `GHSA-v6wh-96g9-6wx3` (`launch-editor` NTLMv2 UNC path disclosure): Fixed in `>=6.4.3` (installed: `6.4.3`).
- **Audit Verification:** `pnpm audit` now reports: `No known vulnerabilities found` (Exit 0).
- **GitHub Dependabot State:** All 4 alerts transitioned to `Fixed` with 0 open alerts.

### 2. Hero Image State Transition Explanation
A review of git history confirmed that [`docs/assets/dashboard.png`](file:///E:/SENTRY/docs/assets/dashboard.png) (184KB) and its markdown link in [`README.md`](file:///E:/SENTRY/README.md) were never modified or missing. The initial broken report in FINAL-INCH-1 was an artifact of the Playwright script testing `naturalWidth > 0` immediately upon `domcontentloaded` before the 184KB PNG completed loading from GitHub's raw CDN. Updating the harness simulation to wait for `networkidle` and trigger scroll-into-view confirmed that the hero image renders with `naturalWidth=1600x1011` on the unauthenticated public view.

### 3. Removal of Unverifiable ARCH-001 & Final Ledger Arithmetic
A comprehensive search across all git commits, branch heads, and tags revealed no git-level commit hash for `ARCH-001` (an early pre-commit conversational design artifact). In accordance with strict evidential rules requiring 100% git-verifiable provenance, `ARCH-001` was removed from [`evaluation/defects.json`](file:///E:/SENTRY/evaluation/defects.json).

**Final Master Defect Ledger Arithmetic:**
---

## Errata 008 — Defect Registry Arithmetic & Lineage Reconciliation (59-Item Master Registry) — recorded at Phase 6A

**Applies to:** `DILIGENCE.md`, `evaluation/defects.json`, `evaluation/mrws/SHIP_GATE_REVIEW.md`.

### 1. What Happened
Earlier working summaries referenced a "24/24 closed defects" shorthand. That metric was an informal triage aggregate from the early SIH forensic sub-panel rather than the true repository-wide master registry.

### 2. The True Master Registry Derivation
A full-lineage audit of `evaluation/defects.json` reveals exactly **59 tracked defect and gap objects**:
- **Pre-MRWS Historical Defects (FINAL-INCH-3 Ledger):** 49 items
  - Resolved: **43**
  - Consolidated: **3** (`BATCH-003` $\to$ `BATCH-004`, `CORP-002` $\to$ `CORP-001`, `ING-003` $\to$ `D-1`)
  - Deferred: **1** (`BP-004` - v2.0 client-side graph dimension filter)
  - Open (Targeted v1.2 Roadmap): **2** (`DEF-005` forged-header red-team battery, `MBOX-001` multi-message mbox delimiter parser)
- **Enterprise-MRWS Viability Gaps (GAP-001 through GAP-010):** 10 items
  - Resolved: **7** (`GAP-003` single-origin build, `GAP-004` synthetic corpus sanitization, `GAP-006` DFIR operator bearer auth, `GAP-007` MaxMind EULA notices, `GAP-008` ML copy calibration, `GAP-009` Alembic migrations, `GAP-010` hot backup tooling)
  - Interim Mitigated: **1** (`GAP-005` sentry.io trademark disclaimers, targeted v1.2 for formal rebranding)
  - Open (Targeted v1.2 Roadmap): **2** (`GAP-001` scale-out daemons, `GAP-002` automated IMAP/M365 mailbox connector)

### 3. Master Ledger Equation
$$\text{Total Objects (59)} = 50 \text{ Resolved} + 1 \text{ Interim Mitigated} + 3 \text{ Consolidated} + 1 \text{ Deferred} + 4 \text{ Open (v1.2)}$$

Zero (0) blockers or high-severity defects remain open for the v1.1.0 release. All four open items are explicitly scoped and scheduled for v1.2.0. `DILIGENCE.md` and `SHIP_GATE_REVIEW.md` are updated to cite the exact 59-item arithmetic.




