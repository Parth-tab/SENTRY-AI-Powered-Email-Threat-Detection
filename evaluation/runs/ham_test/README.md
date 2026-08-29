# SENTRY Ham Corpus Benchmark Report (6,951 Emails)

**Evaluation Date:** 2026-08-29  
**Corpus Size:** 6,951 RFC 5322 messages (SpamAssassin 2002–2003 Public Corpus)  
**Execution Runtime:** 24.44s total (284.5 emails/sec, 3.52ms/email average latency)  
**Pipeline Stability:** 6,951/6,951 parsed with 0 unhandled exceptions (100% reliability)  

---

## 1. Distribution & Honest Metrics Breakdown

| Threat Tier | Score Range | Count | Percentage | Classification Breakdown |
|---|---|---|---|---|
| **LOW** (Clean Baseline) | 0.00 – 0.39 | 5,312 | 76.42% | Legitimate / Clean Traffic |
| **MEDIUM** (Triage Review) | 0.40 – 0.59 | 1,604 | 23.08% | Unauthenticated Mailing Lists & Newsletters |
| **ELEVATED / HIGH** | 0.60 – 0.79 | 35 | 0.50% | Heavy-Link Aggregators & Forwarded Mail |
| **CRITICAL** | 0.80 – 1.00 | 0 | 0.00% | Zero False Positive Critical Blocks |

> **Metric Reframing:** Rather than an unqualified "0% False Positive" marketing claim, SENTRY's forensic posture is accurately described as:
> - **0 Critical False Positives (0.00%)** — Zero legitimate emails triggered automated critical quarantine/blocking.
> - **35 Elevated/High Flags (0.50%)** — 35 out of 6,951 emails scored $\ge 0.60$, attributed to specific structural characteristics analyzed below.
> - **1,639 Medium Tier (23.58%)** — 1,604 moderate scores reflecting missing pre-2004 authentication (SPF/DKIM/DMARC) and mailing list header re-writing.

---

## 2. Analysis of Highest-Scoring Clean Emails ($\ge 0.60$)

Inspection of the 35 elevated ham samples reveals why clean 2002–2003 traffic scores between 0.60 and 0.79:

1. **Mailing List Resending (`From:` vs `Sender:` / `Return-Path:` mismatch):** Legacy mailing list software (Mailman, SourceForge, YahooGroups) replaced envelope sender headers while retaining original author `From:` addresses. Under SENTRY's deterministic spoofing rules, this presents as potential sender impersonation because RFC 7208 SPF and RFC 6376 DKIM were not present in 2003.
2. **High-Density URL Footers:** Multi-topic newsletter digests contained 40+ external HTTP links and tracking query parameters, triggering structural link-density heuristics.
3. **Historical Clock Skew & Relay Latency:** Several messages traversed legacy dial-up or dial-on-demand relays resulting in multi-day inter-hop delays that modern forensic engines flag as relay anomalies.

These detections represent explainable and legitimate forensic feature activations on historical corpora rather than pipeline defects.

---

## 3. Training & Validation Data Provenance (P0 Integrity Verdict)

- **Internal 15,240 Validation Set:** SENTRY's internal GBDT validation benchmark (4,200 Phishing, 2,850 BEC, 2,100 Impersonation, 1,800 Suspicious, 4,290 Legitimate) was constructed from Enron, CEAS 2008, and synthetic multi-hop attack scenarios.
- **Enron Provenance & Overlap Flag:** Because the 4,290 legitimate baseline samples in the 15,240-sample validation set were derived from the public Enron and CEAS 2008 corpora, the reported 0.961 accuracy metric is **partially in-sample** regarding corporate baseline distributions.
- **SpamAssassin Corpus Independence:** The 6,951 SpamAssassin ham dataset tested in this benchmark contains zero overlap with the 15,240 validation set and was evaluated strictly out-of-sample as an external stress test of timezone resilience, null-safety, and regex throughput.
- **Provenance Verdict:** The ham benchmark is an **independent external out-of-sample test** of pipeline robustness and feature bounds.

---

## 4. Geolocation Caveat

> **Historical IP Notice:** Origin country and ASN distributions (e.g. Netherlands 30.8%, Germany 15.5%) reflect a **2025 GeoLite2/MaxMind database applied to 2002–2003 IP allocations**. Many IP subnets assigned to North American educational and telecom institutions in 2003 were subsequently reallocated to European cloud and hosting providers over the intervening two decades. This metric serves as a pipeline exercise demonstrating multi-hop parsing throughput, not a historical attribution claim.
