"""Chaos module — wraps native C++ chaoshash extension."""

try:
    import chaoshash
except ImportError:
    try:
        from . import chaoshash  # type: ignore
    except ImportError:
        chaoshash = None

__all__ = ["chaoshash"]
