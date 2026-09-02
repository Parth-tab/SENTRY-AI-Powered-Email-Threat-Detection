# ⚡ 07 — QUICK CARD: The Presenter's Emergency One-Pager

> *"Keep this page open on your phone or print it double-sided the night before judging. Every line on this card is a direct compression of Stations 05 and 06. Nothing here is new; everything here is verified."*

---

## 🧠 10 Essential Terms (Memory Hooks Only)

1. **Server:** *Servers serve; they do the heavy lifting in the back.* (Port 8000).
2. **Client:** *Clients ask; servers answer.* (Port 3000).
3. **API:** *The messenger and order-taker between programs.*
4. **Endpoint:** *One specific doorway for one specific job.* (29 registered routes).
5. **Gate / Harness:** *The unbribable electronic inspector.* (21 automated gates).
6. **SHA-256:** *The unbreakable gold standard of digital wax seals.* (64-char fingerprint).
7. **SPF / DKIM / DMARC:** *The digital passport and visa stamps of email.*
8. **Indicator of Compromise (IOC):** *The digital clues left behind at the crime scene.*
9. **Forensic Chain of Custody:** *The legal diary proving evidence was never tampered with.*
10. **Air-Gapped:** *Complete security through physical and digital isolation.* (100% offline).

---

## 🖥️ The 5 Screens in 5 Sentences

* **Screen 1 (SOC Threat Dashboard):** Summarizes organizational posture across 📌 18 demo incident cases where 15 are tagged CRITICAL by technical evidence.
* **Screen 2 (Forensic Workbench):** Displays a sanitized raw email payload on the left alongside deep forensic dissection across headers, language, and authentication on the right.
* **Screen 3 (Authentication Forensics):** Interrogates cryptographic SPF/DKIM/DMARC status, isolating the real origin IP (203.0.113.9) using the Reserved-IP Bouncer.
* **Screen 4 (Global Hop Relay Map):** Plots the chronological `Received:` header transit route across an offline global map from foreign origin to corporate perimeter.
* **Screen 5 (Campaign Knowledge Graph):** Clusters interconnected phishing emails around shared infrastructure supernodes while enforcing the Self-Spoof Refusal and Gate 21 spacing.

---

## 🛡️ The 3 Signature Defenses in 3 Sentences

1. **The Reserved-IP Bouncer (Station 2):** Recognizes 22 private and documentation IP subnets, automatically skipping fake loopback hops (`127.0.0.1`, `203.0.113.0/24`) to isolate the genuine external gateway.
2. **The Honest 0.85 Score Floor (Station 4):** Mandates a minimum CRITICAL score of 0.85 when cryptographic authentication fails, while transparently preserving both the raw model score and the policy elevation reason.
3. **The Self-Spoof Refusal (Station 5):** Blocks the attacker's real external IP address while strictly refusing to blacklist internal corporate domains, preventing self-inflicted email shutdowns.

---

## 📌 The 7 Verified Numbers (Anchored to PROJECT_FACTS.md)

| Metric | 📌 Exact Verified Value | Derivation Authority / Caveat |
|---|:---:|---|
| **Test Suite Count** | **164 tests** | `python -m pytest` across 26 modules (100% passing) |
| **Golden Harness Gates** | **21 gates** | `python tools/verify_sentry.py --start` (end-to-end green) |
| **Master Defect Ledger** | **78 total (68 resolved)** | `evaluation/defects.json` (1 interim, 3 cons, 1 def, 5 open) |
| **Registered API Routes** | **29 endpoints** | 24 business forensic endpoints + 5 system routes |
| **Legitimate Ham Benchmark** | **6,777 unique emails** | `0 false positive elevations` (0.00% FP rate) across 6,951 files |
| **Live Demo Seed Corpus** | **18 emails** | 15 Critical, 1 Medium, 2 Low (Active incident response corpus) |
| **ML Benchmark Accuracy** | **0.961 (Macro-F1: 0.952)** | *⚠️ Partially in-sample on Enron/CEAS 2008 training distribution* |

---

## 🏆 The 5 Golden Answers for Judge Cross-Examination

1. **"Why are 15 of 18 demo emails marked CRITICAL?"**
   * *Answer:* *"This is an active incident response corpus targeting Apex National Bank, not a general spam folder. All 15 red emails represent real, verified attacks. When tested against 6,777 legitimate corporate emails, SENTRY produced zero false positive elevations."*
2. **"Does SENTRY send confidential emails to external cloud AI services?"**
   * *Answer:* *"No. SENTRY operates 100% offline as an air-gapped appliance. It uses lightweight decision tree ensembles and calibrated linguistic heuristic scoring that execute in under 15 milliseconds locally without third-party cloud leaks."*
3. **"How do you handle spoofed internal emails from the CEO?"**
   * *Answer:* *"SENTRY is the system that refuses to tell you to block your own domain. It raises a CRITICAL alert on the email, blocks the attacker's real external IP, but strictly refuses to blacklist the internal corporate domain."*
4. **"How does your evidence hold up in a court of law?"**
   * *Answer:* *"Every message is sealed with a Genesis SHA-256 hash ($H_0$) upon intake. Every analysis phase creates an append-only RFC 3227 mathematical hash chain. Any tampering invalidates the chain visibly. Reports export in PDF with fixed-width Courier hashes."*
5. **"What does SENTRY NOT do yet?"**
   * *Answer:* *"Live Microsoft 365 cloud mailbox sync and nation-state geopolitical attribution are documented on our v2.0 roadmap (ROADMAP-01 and ROADMAP-02). We made the deliberate architectural decision to certify our offline, air-gapped forensic appliance first."*

---

## 🌙 The Night-Before Checklist

Before taking the stage or joining the evaluation panel, verify these 6 items in order:

* [ ] **Fact & Link Health:** Run `python tools/validate_facts.py --strict-links` (must output `ALL 5 FACT STAGES VERIFIED AND TRUTHFUL`).
* [ ] **Port Clearance:** Run `powershell -File tools/cleanup.ps1` to ensure ports 8000 and 3000 are completely free.
* [ ] **Automated Boot:** Run `powershell -File tools/demo_day.ps1` and verify Google Chrome opens directly to the login screen in under 15 seconds.
* [ ] **Login Verification:** Log in with `analyst@sentry.internal` / `SentryDemo2026!`.
* [ ] **Walk the 5 Screens:** Click through Dashboard &rarr; Email 1 Detail &rarr; Authentication Tab &rarr; Relay Map &rarr; Campaign Graph &rarr; PDF Export.
* [ ] **Review the Never-Say List:** Confirm that no presenter uses the terms *"AI-powered"*, *"attention vectors"*, or un-caveated accuracy figures.

---

*Return to Compass: [00-START-HERE.md](00-START-HERE.md)*
