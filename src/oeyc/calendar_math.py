"""Pure integer calendar arithmetic.  No ephemeris, no floating point.

Everything here is exact.  Dates are handled with a proleptic Gregorian
day-number conversion rather than :mod:`datetime`, because the scan runs
past year 9999 where :class:`datetime.date` refuses to go.  ``tests/
test_calendar.py`` cross-checks the implementation against ``datetime``
over the range where both are defined.
"""

from __future__ import annotations

from fractions import Fraction

from .constants import BASE_DAY, BASE_MONTH, BASE_YEAR, G400, W, WEEKDAY_NAMES

# 1970-01-01 is day 0 and was a Thursday (index 3 with Monday = 0).
_EPOCH_WEEKDAY_INDEX = 3


def days_from_civil(y: int, m: int, d: int) -> int:
    """Days from 1970-01-01 to y-m-d in the proleptic Gregorian calendar.

    Howard Hinnant's civil_from_days inverse; exact for any integer year,
    negative ones included.  Python's floor division removes the sign
    corrections the original C++ needs.
    """
    y -= m <= 2
    era = y // 400
    yoe = y - era * 400  # [0, 399]
    doy = (153 * (m + (-3 if m > 2 else 9)) + 2) // 5 + d - 1  # [0, 365]
    doe = yoe * 365 + yoe // 4 - yoe // 100 + doy  # [0, 146096]
    return era * G400 + doe - 719468


def civil_from_days(z: int) -> tuple[int, int, int]:
    """Inverse of :func:`days_from_civil`."""
    z += 719468
    era = z // G400
    doe = z - era * G400  # [0, 146096]
    yoe = (doe - doe // 1460 + doe // 36524 - doe // 146096) // 365  # [0, 399]
    y = yoe + era * 400
    doy = doe - (365 * yoe + yoe // 4 - yoe // 100)  # [0, 365]
    mp = (5 * doy + 2) // 153  # [0, 11]
    d = doy - (153 * mp + 2) // 5 + 1  # [1, 31]
    m = mp + (3 if mp < 10 else -9)  # [1, 12]
    return y + (m <= 2), m, d


def is_leap_year(y: int) -> bool:
    """Gregorian rule: divisible by 4 yes, by 100 no, by 400 yes."""
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def _leaps_through(y: int) -> int:
    """Count of leap years in [1, y]."""
    return y // 4 - y // 100 + y // 400


def leap_days(Y: int, base_year: int = BASE_YEAR) -> int:
    """L(Y): leap days strictly inside the span of Y years from the base date.

    The base date is 30 June, which falls *after* 29 February, so the
    February 29ths crossed by a forward span of Y years are exactly those of
    the calendar years ``base_year + 1 .. base_year + Y``.  For negative Y
    the same expression counts backwards and returns a negative number.
    """
    return _leaps_through(base_year + Y) - _leaps_through(base_year)


def D(Y: int, base_year: int = BASE_YEAR) -> int:
    """D(Y) = 365Y + L(Y): elapsed days across Y whole calendar years."""
    return 365 * Y + leap_days(Y, base_year)


def Z(Y: int, base_year: int = BASE_YEAR) -> Fraction:
    """Z(Y) = D(Y) / 7, exact.  Integer exactly when condition C1 holds."""
    return Fraction(D(Y, base_year), W)


def satisfies_c1(Y: int, base_year: int = BASE_YEAR) -> bool:
    """C1: Z(Y) is an exact integer, i.e. both ends fall on the same weekday."""
    return D(Y, base_year) % W == 0


def weekday_index(y: int, m: int, d: int) -> int:
    """0 = Monday .. 6 = Sunday."""
    return (days_from_civil(y, m, d) + _EPOCH_WEEKDAY_INDEX) % W


def weekday(y: int, m: int, d: int) -> str:
    return WEEKDAY_NAMES[weekday_index(y, m, d)]


def terminal_date(
    Y: int,
    base_year: int = BASE_YEAR,
    base_month: int = BASE_MONTH,
    base_day: int = BASE_DAY,
) -> tuple[int, int, int]:
    """The date Y whole calendar years after the base date."""
    return (base_year + Y, base_month, base_day)


def terminal_date_iso(Y: int, base_year: int = BASE_YEAR) -> str:
    y, m, d = terminal_date(Y, base_year)
    return f"{y:04d}-{m:02d}-{d:02d}"


def digital_root(n: int) -> int:
    """Repeated digit sum; 0 only for 0.  Defined on |n| for negative input."""
    n = abs(n)
    return 0 if n == 0 else 1 + (n - 1) % 9
