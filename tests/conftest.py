"""Shared fixtures.

Tests that need the 1.6 GB DE441 kernel are skipped when it is absent, so a
clean checkout still runs the whole integer-arithmetic suite.
"""

from __future__ import annotations

import pytest


@pytest.fixture(scope="session")
def eph():
    from oeyc.ephemeris import KernelNotFound, get_ephemeris

    try:
        return get_ephemeris()
    except KernelNotFound as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"ephemeris kernel not available: {exc}")
