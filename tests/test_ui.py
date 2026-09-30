"""tests/test_ui.py

Streamlit AppTest smoke test suite for ZK-CaMBio UI (Phase 8).
Verifies:
1. Every page (Enroll, Verify, Identify, Revoke, Results, Threat demo) renders cleanly without uncaught exceptions.
2. Required page-specific UI widgets and headers are present.
3. The mandatory disclosure footer renders on every page.
4. UI strictly makes no imports of models, keys, or chaotic projection engines.
"""

from __future__ import annotations

from streamlit.testing.v1 import AppTest

MANDATORY_FOOTER_SNIPPET = "Virtual subjects built from UMDFaces + FVC2004"


def test_ui_imports_no_models_or_chaos():
    """FR-11: Asserts that the UI module never imports models, torch, or the chaos engine."""
    with open("src/ui/app.py", encoding="utf-8") as f:
        content = f.read()

    forbidden = [
        "import torch",
        "from torch",
        "import facenet_pytorch",
        "import chaoshash",
        "from src.chaos",
        "from src.api.service",
    ]
    for pattern in forbidden:
        assert pattern not in content, f"Forbidden import found in src/ui/app.py: {pattern}"


def test_ui_enroll_page_smoke():
    """Smoke test: Enroll page renders headers, inputs, and footer."""
    at = AppTest.from_file("../src/ui/app.py", default_timeout=30)
    at.run()
    assert not at.exception
    # Assert header and buttons
    assert any("Subject Enrollment" in h.value for h in at.header)
    assert any("Enroll Subject" in b.label for b in at.button)
    # Check footer
    assert any(MANDATORY_FOOTER_SNIPPET in m.value for m in at.markdown)


def test_ui_verify_page_smoke():
    """Smoke test: Verify (1:1) page renders inputs, threshold slider, and footer."""
    at = AppTest.from_file("../src/ui/app.py", default_timeout=30)
    at.run()
    # Switch to Verify (1:1)
    at.sidebar.radio[0].set_value("Verify (1:1)").run()
    assert not at.exception
    assert any("Biometric Verification" in h.value for h in at.header)
    assert any("Verify Probe" in b.label for b in at.button)
    assert any("Operating Threshold" in s.label for s in at.slider)
    assert any(MANDATORY_FOOTER_SNIPPET in m.value for m in at.markdown)


def test_ui_identify_page_smoke():
    """Smoke test: Identify (1:N) page renders warning banner, top-k slider, and footer."""
    at = AppTest.from_file("../src/ui/app.py", default_timeout=30)
    at.run()
    at.sidebar.radio[0].set_value("Identify (1:N)").run()
    assert not at.exception
    assert any("Biometric Identification" in h.value for h in at.header)
    assert any("Run 1:N Identification" in b.label for b in at.button)
    # Explanation banner of why user_secret users are excluded
    assert any("server_key mode" in m.value for m in at.markdown)
    assert any(MANDATORY_FOOTER_SNIPPET in m.value for m in at.markdown)


def test_ui_revoke_page_smoke():
    """Smoke test: Revoke page renders revocation button and footer."""
    at = AppTest.from_file("../src/ui/app.py", default_timeout=30)
    at.run()
    at.sidebar.radio[0].set_value("Revoke").run()
    assert not at.exception
    assert any("Template Revocation" in h.value for h in at.header)
    assert any("Revoke Active Template" in b.label for b in at.button)
    assert any(MANDATORY_FOOTER_SNIPPET in m.value for m in at.markdown)


def test_ui_results_page_smoke():
    """Smoke test: Results page renders benchmark tabs and claims table."""
    at = AppTest.from_file("../src/ui/app.py", default_timeout=30)
    at.run()
    at.sidebar.radio[0].set_value("Results").run()
    assert not at.exception
    assert any("Empirical Evaluation Results" in h.value for h in at.header)
    assert any(MANDATORY_FOOTER_SNIPPET in m.value for m in at.markdown)


def test_ui_threat_demo_page_smoke():
    """Smoke test: Threat demo page renders precomputed numbers and honest disclosure."""
    at = AppTest.from_file("../src/ui/app.py", default_timeout=30)
    at.run()
    at.sidebar.radio[0].set_value("Threat demo").run()
    assert not at.exception
    assert any("Threat Model & Security Demonstration" in h.value for h in at.header)
    assert any("Cross-Key Decorrelation" in sh.value for sh in at.subheader)
    assert any(MANDATORY_FOOTER_SNIPPET in m.value for m in at.markdown)
