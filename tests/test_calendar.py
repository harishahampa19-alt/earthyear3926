"""Exact calendar arithmetic.  No ephemeris required."""

from __future__ import annotations

import datetime

import pytest

from oeyc.calendar_math import (
    D,
    Z,
    civil_from_days,
    days_from_civil,
    digital_root,
    is_leap_year,
    leap_days,
    satisfies_c1,
    terminal_date_iso,
    weekday,
)
from oeyc.constants import BASE_YEAR, G400, G400_WEEKS, W


# ---------------------------------------------------------------------------
# the reference instance
# ---------------------------------------------------------------------------


def test_reference_instance_y39_forward():
    """Y = 39 gives D = 14245 and an exactly integer Z = 2035."""
    assert leap_days(39) == 10
    assert D(39) == 39 * 365 + 10 == 14245
    assert Z(39) == 2035
    assert Z(39).denominator == 1
    assert satisfies_c1(39)


def test_reference_instance_y39_backward():
    """The founding pair runs backwards from the base epoch to 1987."""
    assert leap_days(-39) == -10
    assert D(-39) == -14245
    assert abs(D(-39)) // W == 2035
    assert satisfies_c1(-39)
    assert terminal_date_iso(-39) == "1987-06-30"


def test_both_ends_are_tuesdays():
    assert weekday(2026, 6, 30) == "Tuesday"
    assert weekday(1987, 6, 30) == "Tuesday"
    assert weekday(2065, 6, 30) == "Tuesday"


def test_metonic_decomposition():
    """39 = 19 + 19 + 1; the double Metonic is what preserves the phase."""
    assert D(19) == 19 * 365 + leap_days(19)
    assert D(39) - D(38) in (365, 366)
    # 38 years is within a tenth of a day of 470 whole lunations
    from oeyc.constants import M_SYN

    assert abs(D(38) / M_SYN - 470) < 0.05
    # the extra single year adds a bit over 12 lunations, not a whole number
    extra = (D(39) - D(38)) / M_SYN
    assert 12.3 < extra < 12.4


# ---------------------------------------------------------------------------
# the 400-year cycle
# ---------------------------------------------------------------------------


def test_gregorian_cycle_is_146097_days_and_20871_weeks():
    assert D(400) == G400 == 146097
    assert G400 % W == 0
    assert G400 // W == G400_WEEKS == 20871
    assert Z(400) == 20871


def test_c1_membership_is_400_periodic():
    """D(Y+400) - D(Y) = 146097, which is divisible by 7, so C1 repeats."""
    for Y in range(-500, 1500):
        assert D(Y + 400) - D(Y) == G400
        assert satisfies_c1(Y) == satisfies_c1(Y + 400)


def test_c1_density_over_one_cycle():
    """146097 days is 20871 whole weeks, so C1 membership repeats with
    period 400 in Y.  There are 58 residues, not the 400/7 = 57.1 a uniform
    spread would give, because leap days bunch the day counts."""
    hits = [Y for Y in range(400) if satisfies_c1(Y)]
    assert len(hits) == 58
    assert 0 in hits  # the trivial Y = 0 span


# ---------------------------------------------------------------------------
# leap rule and day-number conversions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "year,expected",
    [
        (2024, True),
        (2025, False),
        (2100, False),
        (2200, False),
        (2000, True),
        (2400, True),
        (1900, False),
    ],
)
def test_gregorian_leap_rule(year, expected):
    assert is_leap_year(year) is expected


def test_leap_days_match_datetime_over_full_range():
    base = datetime.date(BASE_YEAR, 6, 30)
    for Y in range(-500, 1000):
        expected = (datetime.date(BASE_YEAR + Y, 6, 30) - base).days
        assert D(Y) == expected, f"D({Y}) disagrees with datetime"


def test_day_number_round_trip():
    for z in range(-800000, 800000, 997):
        y, m, d = civil_from_days(z)
        assert days_from_civil(y, m, d) == z


def test_day_number_matches_datetime():
    d0 = datetime.date(1970, 1, 1)
    for offset in range(-40000, 40000, 313):
        expected = d0 + datetime.timedelta(days=offset)
        assert civil_from_days(offset) == (
            expected.year,
            expected.month,
            expected.day,
        )


def test_weekday_matches_datetime():
    from oeyc.constants import WEEKDAY_NAMES

    d0 = datetime.date(1970, 1, 1)
    for offset in range(-20000, 20000, 97):
        d = d0 + datetime.timedelta(days=offset)
        assert weekday(d.year, d.month, d.day) == WEEKDAY_NAMES[d.weekday()]


def test_day_numbers_work_past_year_9999():
    """datetime.date stops at 9999; the scan does not."""
    z = days_from_civil(17000, 6, 30)
    assert civil_from_days(z) == (17000, 6, 30)
    with pytest.raises(ValueError):
        datetime.date(17000, 6, 30)


# ---------------------------------------------------------------------------
# digital roots
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "n,expected", [(0, 0), (9, 9), (18, 9), (14245, 7), (2035, 1), (146097, 9)]
)
def test_digital_root(n, expected):
    assert digital_root(n) == expected


def test_digital_root_is_mod_nine():
    for n in range(1, 5000):
        assert digital_root(n) == 1 + (n - 1) % 9
