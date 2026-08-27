# tools/scratch/

Development and debugging scripts used during the build phase.
These are preserved in version history for reference but are **not part of the
production codebase** — they were used to probe, diagnose, and exercise the
system during active development.

| Script | Purpose |
|--------|---------|
| `browse_sentry.py` | Async Playwright session for interactive UI debugging |
| `browse_sentry_sync.py` | Sync variant of above (Playwright sync API) |
| `capture_modal.py` | One-shot modal screenshot probe (superseded by `capture_tour.py`) |
| `generate_perfect_gallery.py` | Gallery screenshot generator (port 3000) |
| `generate_perfect_gallery_3001.py` | Gallery screenshot generator (port 3001 variant) |
| `run_full_browser_interaction.py` | Full-stack browser interaction probe |
| `test_api_8001.py` | API smoke test against port 8001 |
| `test_api_8002.py` | API smoke test against port 8002 |
| `upload_samples.py` | Bulk sample upload utility |

For the current canonical tools, see the `tools/` parent directory:
- `tools/verify_sentry.py` — the golden harness (15/15 checks)
- `tools/capture_tour.py` — the guided tour capture script
- `tools/generate_corpus.py` — demo corpus seed generator
