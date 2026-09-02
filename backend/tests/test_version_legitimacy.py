import sys
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools import validate_facts


def test_version_legitimacy_backed_by_highest_git_tag():
    """
    MV-1: Asserts that SENTRY's unified version (1.2.2) is mathematically
    backed by the highest release tag in git history (v1.2.2).
    Prevents unauthorized version bumps without corresponding release sequences.
    """
    version_data = validate_facts.compute_app_version()
    assert version_data["unified"] is True, f"Backend ({version_data['backend']}) and frontend ({version_data['frontend']}) versions not unified!"
    assert version_data["version"] == "1.2.2"
    assert version_data["highest_tag"] == "v1.2.2"
    assert version_data["highest_tag_version"] == "1.2.2"
    assert version_data["legitimate"] is True, "Version 1.2.2 must be backed by git tag v1.2.2"

    valid, msg = validate_facts.verify_version_legitimacy(version_data)
    assert valid is True
    assert "backed by git tag v1.2.2" in msg


def test_mutation_kill_unbacked_version_bump_fails_validator():
    """
    MV-1 Mutation Kill:
    If a version is bumped in code (e.g. to 9.9.9) without a corresponding git tag,
    the legitimacy gate in validate_facts Stage 5 must fail, explicitly naming
    the unbacked version ('9.9.9') and the highest existing tag ('v1.2.2').
    """
    unbacked_version = "9.9.9"
    version_data = validate_facts.compute_app_version(
        override_backend=unbacked_version,
        override_frontend=unbacked_version
    )
    assert version_data["version"] == unbacked_version
    assert version_data["highest_tag"] == "v1.2.2"
    assert version_data["legitimate"] is False, (
        f"Mutation Kill Failure: Unbacked version '{unbacked_version}' was falsely marked legitimate!"
    )

    # Verify Stage 5 error message generation
    valid, err_msg = validate_facts.verify_version_legitimacy(version_data)
    assert valid is False
    assert unbacked_version in err_msg, f"Expected unbacked version '{unbacked_version}' in error: {err_msg}"
    assert "v1.2.2" in err_msg, f"Expected highest tag 'v1.2.2' in error: {err_msg}"
    assert "VERSION LEGITIMACY DRIFT" in err_msg


def test_mutation_kill_stale_tags_fails_validator(monkeypatch):
    """
    MV-1 Mutation Kill:
    If the git repository only contains older tags (e.g. v1.2.1) while the codebase
    declares 1.2.2, the legitimacy check must fail.
    """
    monkeypatch.setattr(validate_facts, "get_highest_git_release_tag", lambda: "v1.2.1")
    monkeypatch.delenv("SENTRY_PRE_TAG_STAGING", raising=False)

    version_data = validate_facts.compute_app_version()
    assert version_data["version"] == "1.2.2"
    assert version_data["highest_tag"] == "v1.2.1"
    assert version_data["legitimate"] is False

    valid, err_msg = validate_facts.verify_version_legitimacy(version_data)
    assert valid is False
    assert "1.2.2" in err_msg
    assert "v1.2.1" in err_msg
