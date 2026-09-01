## What changed & why
<!-- What closes this: defect ID / issue # / check name -->

## Verification loop run
- [ ] `pytest backend/tests -v` — pass (156 tests across 23 modules)
- [ ] `python tools/verify_sentry.py --start` — 21/21 golden gates green
- [ ] `python tools/validate_facts.py` — green (docs/PROJECT_FACTS.md synchronized)
- [ ] UI-touching change -> `python tools/capture_tour.py --start` run to recapture affected tour stops
- [ ] Security/forensics-touching change -> full battery run attached

## Evidence
<!-- harness output, validator output, screenshots, scorecard diff -->

- [ ] No check weakened (if any eval file changed: eval-change: commit linked)
