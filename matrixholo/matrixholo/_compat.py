"""Python version compatibility checks and shims for matrixholo.

Strictly targets Python >= 3.10.0, < 3.11.
"""

from __future__ import annotations

import sys

if sys.version_info < (3, 10, 0):
    raise RuntimeError("matrixholo requires Python >= 3.10.0")

__all__ = ["check_python_version"]


def check_python_version() -> None:
    """Verify that current runtime meets minimum version requirements."""
    if sys.version_info < (3, 10, 0):
        raise RuntimeError("matrixholo requires Python >= 3.10.0")
