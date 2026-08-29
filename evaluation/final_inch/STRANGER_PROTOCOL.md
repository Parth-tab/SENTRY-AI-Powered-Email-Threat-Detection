# SENTRY Stranger Testing Protocol (Phase 5)

This protocol governs the human-administered stranger test for the SENTRY public repository.

---

## 1. Candidate Recruitment
Recruit **3 participants** who have never seen or heard about this project before:
1. **Participant 1 (Technical):** Software engineer, systems administrator, cybersecurity professional, or CS graduate.
2. **Participant 2 (Non-Technical):** Business analyst, domain generalist, legal/compliance officer, or end-user.
3. **Participant 3 (Student / Educator):** University student, researcher, or teacher.

---

## 2. The Verbatim Ask (Zero Prompting)
Present the participant with a browser showing `https://github.com/Parth-tab/SENTRY-AI-Powered-Email-Threat-Detection` (or local landing screen) and state verbatim:

> *"Here's a thing I built — can you look at this page for two minutes and tell me what you think it is?"*

Do **NOT** explain what SENTRY does. Do **NOT** guide their cursor. Do **NOT** apologize for visual layout or defects.

---

## 3. Silent Observation Guide (First 90 Seconds)
Remain completely silent. Observe and record:
- **Eye Path:** Where do their eyes land first? (Hero title, badge strip, architecture diagram, code blocks, or file tree).
- **Scroll Depth:** Do they stay above the fold, scan the TOC, or scroll all the way to benchmarks/evaluation?
- **First Click:** What is the first link, image, or tab they click on?
- **Frown Moments:** Where do they pause, squint, re-read, or look visibly confused?

---

## 4. The Cardinal Metric
- **THE ONE METRIC:** Record their **FIRST SPOKEN SENTENCE** verbatim without rephrasing or sanitization.

---

## 5. Structured Debrief (4 Mandatory Questions)
After 2 minutes of silent observation, ask these four questions and record verbatim responses:
1. **"In your own words, what is this system?"**
2. **"If you were evaluating or using this, what is the very first button or link you would click?"**
3. **"What was the single most confusing or unclear thing on the page?"**
4. **"If you were a security analyst or judge, would you feel confident running this based on what you see?"**

---

## 6. Friction Log Template
For each friction event observed, record:
| Timestamp | Location / Section | Observed Behavior / Hesitation | Participant Quote | Root Cause |
|---|---|---|---|---|
| `0:15` | Hero / Badges | Looked confused at broken image | *"Is this image supposed to load?"* | Relative image path resolution in markdown |

---
