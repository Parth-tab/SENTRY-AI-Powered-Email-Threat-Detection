# GAUNTLET — The 22-Judge Tribunal & Convergence Loop for SENTRY

## 1. System Architecture & Disk Layout

The loop state lives entirely on disk. Any Antigravity session can die and be replaced; nothing is lost.

```
E:\SENTRY\evaluation\
  MASTER_SPEC.md           save THIS document here (git-versioned)
  state.json               {phase, iteration, composite_history[], status}
  battery\
    checks\              one script per dimension (python, self-contained)
    run_battery.py       runs all checks -> writes evidence JSONs
  corpus\                  adversarial EMLs, payload sets, edge fixtures
  runs\iter_N\
    evidence\            metric JSONs, logs, screenshots, diff reports
    scorecard.json       22 judge verdicts + composite
    decisions.md         analysis log for this iteration
  defects.json             global registry (id, severity, status, fix_commit)
  score_history.jsonl      one line per iteration: {iter, composite, floors_met}
  final_report.md          compiled handoff (what I verify at the end)
```

**Loop state machine** (one phase per agent invocation):

```
[ITER-0: BUILD] -> TEST -> SCORE -> ANALYSE -> FIX -> VERIFY -+
                     ^                                          |
                     |  if composite < 95 or floors unmet       |
                     +------------------------------------------+
                                                                |
                          convergence / budget exhausted -> FINAL-REPORT -> TERMINAL
```

**Gate 0 (non-negotiable):** every scored iteration *begins* by running `tools/verify_sentry.py --start`. If any of the 15 golden checks fail, the iteration is aborted and filed as a regression before any scoring happens. The golden path is never traded away for points elsewhere.

---

## Part A — The Tribunal: 22 Judges, Mandates, Weights

Each judge owns a domain. Weights sum to 100. Judges audit mechanical evidence and apply adjustments in **[-10, +5]** — docking is easy, credit requires proof. They are instructed to assume the system is broken until evidence proves otherwise.

| # | Judge | Weight | Mandate (what "excellent" means to them) |
|---|---|---|---|
| 1 | Security Architect | 9 | OWASP API Top 10 closed, authz on every endpoint, zero secrets, injection-proof |
| 2 | Red Team Operator | 7 | Actually attacks the app: XSS via email bodies, SSRF, authz bypass, upload abuse |
| 3 | Digital Forensics Investigator | 8 | Chain of custody provable, hash chain verifiable, evidence immutable, RFC 3227 |
| 4 | SOC Analyst (the user) | 7 | "Does this make my shift faster?" triage->investigate->report in one flow |
| 5 | ML Engineer | 6 | Per-class metrics, no leakage, calibration honest, adversarial robustness |
| 6 | Threat Intel Analyst | 4 | IOC accuracy, no overclaimed attribution, feed failures degrade gracefully |
| 7 | Principal Backend Engineer | 5 | Async correctness, error handling, API consistency, no architectural rot |
| 8 | Frontend Lead | 4 | Component discipline, state management, no console debt, real UI polish |
| 9 | Code Quality Guardian | 4 | Lint/type/complexity/dead-code hygiene; code a stranger could inherit |
| 10 | Platform/SRE Lead | 6 | Cold-start reproducibility, healthchecks, structured logs, deployability |
| 11 | Chaos SRE (on-call) | 4 | Kills Redis/intel APIs mid-run; demands graceful degradation |
| 12 | Performance Engineer | 3 | p95 latencies, throughput, no memory leak, no N+1 queries |
| 13 | Data Engineer | 3 | Schema sanity, migrations, dedupe semantics, data contracts |
| 14 | Chief Product Officer | 5 | PS 26106 traceability — every requirement demonstrably delivered |
| 15 | Security Product PM | 3 | Analyst workflow realism, alert quality, false-positive cost |
| 16 | UX Researcher | 3 | Accessibility, keyboard nav, loading/error/empty states everywhere |
| 17 | Legal/Compliance Officer | 4 | DPDP-aware PII handling, masking, retention, processing notice |
| 18 | Law Enforcement Liaison | 2 | Report is actionable by a non-technical investigating officer |
| 19 | SIH Grand Judge (adversarial) | 6 | Scores against *real* hackathon criteria; compares to 20 unseen rival teams |
| 20 | Solutions Engineer | 2 | Demo story lands in 5 minutes without a single dev tool opened |
| 21 | Maintenance Realist | 3 | Fresh clone -> running in 5 commands; docs match reality |
| 22 | CEO | 2 | One-sentence differentiation vs. existing tools |

**Judge isolation protocol** (the anti-anchoring rule): each judge is evaluated in a fresh reasoning block — list evidence artifacts first, read them, *then* verdict. A judge may not see another judge's score. A claim without an artifact citation is invalid and must be discarded before scoring.

---

## Part B — The Test Battery (12 Dimensions, 61 Checks)

Base scores come from these checks — computed by scripts, not opinions. Judges adjust on top. Scoring notation: **B** = binary (100/0), **G** = graded (metric between floor and target -> linear 0–100).

### D1 — Code Quality (Judge 9)
| ID | Check | Method | Rule |
|---|---|---|---|
| CQ-1 | Lint clean | `ruff check backend frontend` (config in battery) | **B** |
| CQ-2 | Type coverage | `mypy app/ --strict` error count | **G** floor 20 err, target 0 |
| CQ-3 | Docstring coverage >=90% public functions | `interrogate` | **G** 60->90% |
| CQ-4 | Complexity | `radon cc -n D` (no function >10) | **G** count 10->0 |
| CQ-5 | Duplication | `jscpd --min-tokens 70` | **G** 5%->0.5% |
| CQ-6 | Dead code | `vulture` findings resolved or justified | **G** |
| CQ-7 | Zero TODO/FIXME in shipped paths | grep scan + allowlist | **B** |
| CQ-8 | No module >400 LOC unjustified | script | **B** |

### D2 — Test Quality (Judges 9, 7)
| ID | Check | Method | Rule |
|---|---|---|---|
| TQ-1 | Backend branch coverage | `pytest --cov` | **G** 50->85% |
| TQ-2 | Frontend critical-path specs >=10 Playwright scenarios | count | **G** 0->10 |
| TQ-3 | Mutation score on 3 critical modules (header parser, hash chain, scorer) | `mutmut` / AST mutation test | **G** 20->60% |
| TQ-4 | Test order independence | run suite with `pytest-randomly` twice | **B** |
| TQ-5 | Every closed defect has a regression test | registry audit | **B** |

### D3 — Architecture (Judges 7, 13)
| ID | Check | Method | Rule |
|---|---|---|---|
| AR-1 | Layer contracts (api->services->repo, no skips) | `import-linter` contracts | **B** |
| AR-2 | No circular imports | script scan | **B** |
| AR-3 | No raw SQL/Cypher in route handlers | grep + review | **B** |
| AR-4 | Config via env only; no hardcoded secrets/URLs | scan with allowlist | **B** |
| AR-5 | OpenAPI diff — no breaking change without version bump | spec snapshot diff | **B** |
| AR-6 | Service boundaries documented & honored | judge audit w/ evidence | **G** |

### D4 — Security (Judges 1, 2) — **floor 90**
| ID | Check | Method | Rule |
|---|---|---|---|
| SE-1 | Dependency CVEs | `pip-audit` + `npm audit` | **B** (0 high/crit) |
| SE-2 | Secret scan | `gitleaks detect` | **B** |
| SE-3 | Authz sweep — every endpoint: 401 unauth, 403 wrong role | auto-generated from OpenAPI spec | **G** 80->100% endpoints |
| SE-4 | Injection fuzz — 40 SQL/Cypher/header payloads via ingest | corpus\injection.jsonl | **B** no 5xx, no injection effects |
| SE-5 | **XSS via email body** — EML with `<script>`, `onerror=`, `javascript:` rendered in UI | corpus\xss.eml + Playwright assert | **B** — this is the flagship check |
| SE-6 | SSRF — link-analysis fetching blocked for internal ranges/protocols | mock + assert | **B** |
| SE-7 | Rate limiting | burst 200 req -> 429 observed | **B** |
| SE-8 | Upload hardening — 50MB file, zip-bomb-ish, broken encodings | corpus | **B** graceful rejection |
| SE-9 | Security headers (CSP, X-Content-Type-Options, etc.) | header scan on frontend+API | **G** |
| SE-10 | JWT hygiene — expiry <=60min, algorithm pinned, refresh rotation | config + token tests | **B** |

### D5 — Reliability & Chaos (Judges 11, 10)
| ID | Check | Method | Rule |
|---|---|---|---|
| RL-1 | Redis killed mid-pipeline -> retries complete, no loss | chaos script | **B** |
| RL-2 | All external intel APIs blackholed -> analysis completes degraded | DNS/hosts mock | **B** |
| RL-3 | 100 mutated EMLs -> zero 500s | fuzz-lite corpus gen | **B** |
| RL-4 | Every external call has explicit timeout | code audit + hung-mock test | **B** |
| RL-5 | Re-ingest same email -> dedupe by SHA-256 (documented policy) | ingest twice, assert | **B** |
| RL-6 | **Cold start**: `docker compose down -v` -> `up` -> seed -> harness PASS | full run, timed | **B** |
| RL-7 | Battery flakiness: same HEAD, two runs, zero check flips | run battery twice | **B** |

### D6 — Performance (Judge 12) — on 1,000 seeded emails
| ID | Check | Method | Rule |
|---|---|---|---|
| PF-1 | p95 latency: list/stats/detail endpoints | load script | **G** 1000ms->300ms |
| PF-2 | Bulk pipeline: 100 emails fully analyzed | timed run | **G** 300s->60s |
| PF-3 | Memory bounded over 500-email run (no upward RSS trend) | sampler | **B** |
| PF-4 | Hot queries indexed (EXPLAIN, no seq scans) | audit script | **G** |
| PF-5 | Lighthouse perf >=80 headless | lighthouse CLI | **G** 50->80 |

### D7 — Forensic Integrity (Judge 3) — **floor 90**
| ID | Check | Method | Rule |
|---|---|---|---|
| FI-1 | Hash chain: tamper any evidence row -> verification FAILS | test | **B** |
| FI-2 | Chain-of-custody: every transition logged (actor, action, ts) | audit sample of 20 ops | **G** |
| FI-3 | Re-download ingested EML -> byte-identical | hash compare | **B** |
| FI-4 | Report determinism: same email twice -> identical findings (mod timestamps) | diff | **B** |
| FI-5 | IOC export machine-readable (CSV/STIX-lite) | generate + parse back | **B** |

### D8 — ML Rigor (Judges 5, 6)
| ID | Check | Method | Rule |
|---|---|---|---|
| ML-1 | Per-class P/R/F1 + confusion matrix report exists | artifact | **B** |
| ML-2 | No train/test leakage (hash-dedupe across split) | script | **B** |
| ML-3 | Calibration: predicted confidence vs. empirical accuracy (10 bins) | eval script | **G** |
| ML-4 | Single-email inference <2s | timed | **G** 10s->2s |
| ML-5 | 10 handcrafted evasions (homoglyph, zero-width, image-only, thread-injection) — detect >=7 | corpus\adversarial\ | **G** 4->8 |
| ML-6 | Model version + thresholds documented | docs audit | **B** |

### D9 — API Quality (Judge 7)
| ID | Check | Method | Rule |
|---|---|---|---|
| AQ-1 | OpenAPI validates; every endpoint has description + example | schema lint | **G** |
| AQ-2 | Uniform error envelope `{error:{code,message}}` on all 4xx/5xx | sweep from OpenAPI | **B** |
| AQ-3 | Pagination on all list endpoints | test | **B** |
| AQ-4 | Ingest idempotency semantics documented + tested | test | **B** |

### D10 — UX & Frontend (Judges 8, 16)
| ID | Check | Method | Rule |
|---|---|---|---|
| UX-1 | Lighthouse a11y >=85 | lighthouse | **G** 60->85 |
| UX-2 | Keyboard: tab through dashboard -> open detail -> close, no trap | Playwright keyboard | **B** |
| UX-3 | Loading/error/empty states on every async view (network throttled/offline) | per-route audit | **G** |
| UX-4 | No console errors, no unhandled rejections | harness (already) + extended | **B** |
| UX-5 | Responsive 1280/1440/1920 — no horizontal scroll | screenshots | **B** |

### D11 — Production Readiness (Judges 10, 21)
| ID | Check | Method | Rule |
|---|---|---|---|
| PR-1 | Dockerfile: multi-stage, non-root, slim | audit | **B** |
| PR-2 | Compose healthchecks + `depends_on: condition` | audit | **B** |
| PR-3 | Fresh clone -> running <=5 commands, verified by clean-workspace run | agent simulates naive user | **B** |
| PR-4 | Structured logging with request IDs | log sample audit | **G** |
| PR-5 | `.env.example` complete; missing config fails fast with clear message | run without env | **B** |
| PR-6 | README architecture claims spot-checked (5 random claims) | judge audit | **G** |

### D12 — Product & Domain Fit (Judges 14, 4, 15, 17, 18, 19, 20, 22)
| ID | Check | Method | Rule |
|---|---|---|---|
| FIT-1 | **PS 26106 traceability matrix**: every requirement -> working feature -> evidence link | matrix artifact | **G** 70->100% |
| FIT-2 | Analyst workflow end-to-end in UI, no dev tools (ingest->triage->investigate->report->export) | Playwright user-journey | **B** |
| FIT-3 | PII masking toggle works; retention config; processing notice in docs | test + audit | **B** |
| FIT-4 | 5-minute demo script with per-step timings, every step verified | script + dry run | **B** |
| FIT-5 | Differentiation dossier: 3 named tools (e.g., Proofpoint, Abnormal, MHA header analyzer) + explicit delta | doc | **B** |
| FIT-6 | Grand Judge scorecard vs. SIH rubric (innovation/completeness/technical merit/usability) | persona memo w/ evidence | **G** |

---

## Part C — Scoring Protocol

**Per check:** binary -> 0/100. Graded -> `clip((metric - floor)/(target - floor) * 100, 0, 100)`.
**Per dimension:** base = weighted mean of its checks.
**Per judge:** `judge_score = clip(base(dimension) + adjustment, 0, 100)` where adjustment in [-10, +5] and **requires >=1 evidence citation**.
**Composite:** `Σ(weight_j * score_j) / 100`.

**Convergence Criteria (all must hold):**
1. Composite >= 95
2. Floors: Security >= 90, Forensics >= 90, every other dimension >= 85
3. **Stability clause:** criteria 1–2 hold on 2 consecutive iterations with zero regressions.

---

## Part D — Loop Protocol

| Phase | What happens | Budget |
|---|---|---|
| **ITER-0 BUILD** | Materialize battery scripts, corpora, judge charters, defect registry; smoke-run battery once | 1 session |
| **TEST** | Gate 0 (golden harness) -> `run_battery.py` -> evidence artifacts written | — |
| **SCORE** | 22 judges in isolation -> scorecard.json | — |
| **ANALYSE** | Rank defects: `priority = judge_weight * severity_mult / effort`. Write `decisions.md` | — |
| **FIX** | <=8 fixes, <=18 effort-points, <=3 files per fix, one commit per fix (`fix(<DEFECT-ID>): `) | 1–2 sessions |
| **VERIFY** | Full battery re-run; regression diff vs. previous scorecard | — |
| **FINAL-REPORT** | Compile per Part G | 1 session |

---

---

## Part F — Time-Budget Calibration & Demo Runway Amendment (3–7 Days)

### eval-change: time-budget calibration for 3-7 day runway

1. **ANALYSE priority formula amended:**
   $$\text{priority} = \text{weight} \times \text{severity} \times \text{multiplier} / \text{effort}$$
   where $\text{multiplier} = 2.0$ for defects blocking FIT-1 (traceability) or FIT-4 (demo script) on the COMPRESSED path, and $1.5$ on the FULL path from iteration 4 onward (after floors).
2. **Iteration budget:** 6 (FULL path: 5–7 days) / 4 (COMPRESSED path: 3–4 days) scored iterations.
3. **Early-stop is a SUCCESS outcome:** Marginal gain $<1.0$ across 2 iterations $\to$ freeze early, spend surplus on demo readiness and narration rehearsal.
4. **New Phase `DEMO-PREP` (post-freeze, replaces further FIX phases):**
   a. **Build demo corpus:** 15–25 curated EMLs across 2–3 realistic cybercrime campaigns so the map and graph render rich live data (`demo: curated corpus`).
   b. **Extend `tools/verify_sentry.py` with `--demo-run` flag:** walks the exact FIT-4 script with per-step timings; target total $5:00 \pm 0:30$.
   c. **Record full clean run as backup proof.**

