"""Chaos module — wraps native C++ chaoshash extension."""

from src.chaos.engine import (
    ChaosEngine,
    derive_chaos_parameters,
    python_reference_transform,
    quantize_vector,
)

try:
    import chaoshash
except ImportError:
    try:
        from . import chaoshash  # type: ignore
    except ImportError:
        chaoshash = None

__all__ = [
    "chaoshash",
    "ChaosEngine",
    "derive_chaos_parameters",
    "quantize_vector",
    "python_reference_transform",
]

