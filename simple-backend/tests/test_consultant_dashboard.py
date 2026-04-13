"""Tests for optional consultant-dashboard integration."""

from core.consultant_dashboard import _build_identity_query, build_prompt_addition


def test_build_identity_query_from_profile_data():
    profile = {
        "google_sub": "google-sub-123",
        "email": "alex@example.com",
        "name_hash": "namehash",
        "phone_hash": "phonehash",
    }

    query = _build_identity_query(profile)

    assert query["normalized_name_hash"] == "namehash"
    assert query["phone_hash"] == "phonehash"
    assert "google_sub_hash" in query
    assert "email_hash" in query


def test_build_prompt_addition_includes_dashboard_context():
    prompt = build_prompt_addition({
        "notes": "Generalized background notes.",
        "direction": "Focus on routines.",
        "latest_summary": {
            "overview": "Client discussed stress at work.",
            "biomarker_summary": "Stress remained elevated.",
        },
        "baseline": {
            "averages": {
                "hrv": 31.0,
                "stress_index": 52.5,
            }
        },
        "alerts": [
            {"severity": "warning", "title": "Elevated stress"},
        ],
    })

    assert "Background notes" in prompt
    assert "Focus on routines." in prompt
    assert "Client discussed stress at work." in prompt
    assert "stress_index=52.5" in prompt
    assert "warning: Elevated stress" in prompt
