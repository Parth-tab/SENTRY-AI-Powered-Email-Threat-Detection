# Contributing to SENTRY

## Setup
Follow the README quickstart, then install dev tooling:
`pip install -r backend/requirements-dev.txt` (pytest, ruff, mypy, coverage)
and `npm install` inside `frontend/`.

## The rules that matter
1. **Nothing merges red.** CI runs: ruff + pytest (branch coverage) +
   `tools/validate_facts.py` + the 21-check E2E golden harness (boots the real stack,
   drives headless Chromium) + the 12-dimension GAUNTLET battery.
2. **Fix the app, never the test.** Weakening a check to make CI pass is the
   one unforgivable move in this repo. If a check is wrong, argue it in a PR
   that makes it stricter.
3. **Every change carries its justification**: defect ID, issue #, or check
   name in the commit message (conventional commits).
4. **Single Source of Truth**: Any quantitative claim added to docs must be
   registered in [`docs/PROJECT_FACTS.md`](docs/PROJECT_FACTS.md) and pass `python tools/validate_facts.py`.
5. **UI & Pixel Fidelity**: Any PR modifying frontend UI views must recapture
   affected tour screenshots using `python tools/capture_tour.py --start`.
6. **Security-relevant changes** (sanitization, auth, headers, upload path)
   require a test in the same PR demonstrating the vulnerability is closed.

## Verification loop for any change
```bash
pytest backend/tests -v                      # unit/integration suite (156 tests)
python tools/verify_sentry.py --start        # end-to-end golden harness (21/21)
python tools/validate_facts.py               # machine-verified fact & link validator
python evaluation/battery/run_battery.py     # full 12-dimension battery
```

## Pull requests
Use the PR template. Include: what changed, what it closes, evidence
(harness output, validator output, or screenshot), and confirmation of the loop above.

## Architecture orientation
Read [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) first. The invariants that are easiest to break:
- Evidence vault is write-once; the hash chain binds to stored vault bytes,
  never re-read source files
- The live runtime must stay daemon-free (air-gapped appliance contract)
- Email content is untrusted input at every layer
