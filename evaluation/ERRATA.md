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

