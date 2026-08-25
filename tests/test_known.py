"""Ephemeris regression tests.  Require the DE441 kernel.

Two groups of assertions live here.

The first pins values the founding write-up got right, most importantly the
1987/2026 pair.  The second pins values it got *wrong*: Y = 1031 and
Y = 4374 were published as near-perfect alignments and are nothing of the
kind.  Those are kept as tests rather than deleted, so that any future
change to the ephemeris, the frame or the phase definition has to confront
them explicitly.
"""

from __future__ import annotations

import numpy as np
import pytest

from oeyc.calendar_math import D, satisfies_c1
from oeyc.scan import HOURS, reference_instance

pytestmark = pytest.mark.ephemeris


def _best_theta(eph, Y: int) -> tuple[float, float, int]:
    """Return (theta, E, hour) at the best UT hour of the terminal date."""
    year = 2026 + Y
    n = len(HOURS)
    t = eph.times(
        np.full(n, year),
        np.full(n, 6),
        np.full(n, 30),
        np.asarray(HOURS, dtype=float),
    )
    th = np.atleast_1d(eph.theta(t))
    j = int(np.argmin(np.abs(th - 180.0)))
    return float(th[j]), float(abs(th[j] - 180.0)), int(HOURS[j])


# ---------------------------------------------------------------------------
# our phase angle is the same quantity Skyfield computes
# ---------------------------------------------------------------------------


def test_theta_agrees_with_skyfield_almanac(eph):
    """theta must be identical to skyfield.almanac.moon_phase.

    If this drifts, every other number in the project is suspect.
    """
    from skyfield.almanac import moon_phase

    years = [1987, 2026, 2178, 3609, 3829, 6911]
    n = len(years)
    t = eph.times(years, [6] * n, [30] * n, [0.0] * n)
    mine = np.atleast_1d(eph.theta(t))
    theirs = np.atleast_1d(moon_phase(eph._eph, t).degrees)
    assert np.allclose(mine, theirs, atol=1e-9)


# ---------------------------------------------------------------------------
# what the founding write-up got right
# ---------------------------------------------------------------------------


def test_base_epoch_is_a_full_moon(eph):
    """Claimed 180.01 deg; measured 180.0252 deg."""
    th, e, _ = _best_theta(eph, 0)
    assert abs(th - 180.01) < 0.05
    assert e < 0.05


def test_1987_end_of_the_founding_pair(eph):
    """Claimed 41.12 deg and a 12 percent crescent."""
    ref = reference_instance(eph)
    end_1987 = ref["ends"][0]
    assert end_1987["date"] == "1987-06-30"
    assert end_1987["weekday"] == "Tuesday"
    assert abs(end_1987["theta_00ut"] - 41.12) < 0.05
    assert 0.11 < end_1987["illum_00ut"] < 0.14


def test_founding_pair_slip_is_about_a_third_of_a_lunation(eph):
    """39 = 19 + 19 + 1, and the odd year costs roughly 11 days."""
    ref = reference_instance(eph)
    assert ref["K"] == 482
    assert 11.0 < ref["slip"] < 11.5
    assert 0.37 < ref["slip"] / 29.5305889 < 0.39
    assert 12.3 < ref["metonic"]["extra_year_lunations"] < 12.4


# ---------------------------------------------------------------------------
# what the founding write-up got wrong
# ---------------------------------------------------------------------------


def test_y1031_is_not_an_alignment(eph):
    """Published as ~179.98 deg.  It is not: theta is about 74.6 deg.

    Y = 1031 does satisfy C1, so it reaches the ephemeris stage, but the
    Moon is a waxing crescent-to-quarter that day, some 105 degrees from
    full.  The nearest C1 year that is genuinely close is Y = 1059.
    """
    assert satisfies_c1(1031)
    assert D(1031) == 376565
    th, e, _ = _best_theta(eph, 1031)
    assert abs(th - 74.60) < 0.2
    assert e > 100.0
    assert abs(e - 179.98 + 180.0) > 100.0  # nowhere near the published value


def test_y4374_does_not_even_satisfy_c1(eph):
    """Published as ~180.000 deg.  It cannot be in the series at all.

    D(4374) = 1597571, which leaves remainder 3 on division by 7, so the
    two ends fall on different weekdays and C1 fails before the ephemeris
    is ever consulted.  Measured anyway, theta is about 138 degrees.
    """
    assert D(4374) == 1597571
    assert D(4374) % 7 == 3
    assert not satisfies_c1(4374)
    th, e, _ = _best_theta(eph, 4374)
    assert abs(th - 138.05) < 0.2
    assert e > 40.0


@pytest.mark.parametrize("Y,e_max", [(1059, 1.5), (4361, 5.0)])
def test_nearest_real_alignments_to_the_published_years(eph, Y, e_max):
    """The genuine near-hits closest to the two published years."""
    assert satisfies_c1(Y)
    _, e, _ = _best_theta(eph, Y)
    assert e < e_max


# ---------------------------------------------------------------------------
# the actual best members of the series
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "Y,e_max",
    [
        (152, 0.06),
        (277, 0.03),
        (839, 0.03),
        (1583, 0.005),
        (1803, 0.002),
        (3386, 0.01),
        (4885, 0.02),
    ],
)
def test_series_members_reproduce(eph, Y, e_max):
    assert satisfies_c1(Y)
    _, e, _ = _best_theta(eph, Y)
    assert e < e_max


def test_best_alignment_in_five_thousand_years(eph):
    """Y = 1803, terminal date 3829-06-30, E below a thousandth of a degree."""
    th, e, hour = _best_theta(eph, 1803)
    assert D(1803) == 658532
    assert D(1803) // 7 == 94076
    assert e < 0.001
    assert abs(th - 180.0) < 0.001
    assert 0 <= hour <= 23
