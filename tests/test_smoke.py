"""Smoke test — verifies pytest runs and the chaoshash C++ module loads."""


def test_smoke():
    """Baseline: pytest itself is working."""
    assert True


def test_chaoshash_ping():
    """P0 acceptance: the pybind11 stub module is importable and responds."""
    import chaoshash

    result = chaoshash.ping()
    assert result == "chaoshash module loaded OK"
