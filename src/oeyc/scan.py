"""Two-stage scan over year offsets Y.

Stage 1 is pure integer arithmetic: keep only the Y for which condition C1
holds (Z = D/7 is an exact integer).  That throws away six sevenths of the
search space for the cost of a modulo.

Stage 2 touches the ephemeris, and only for the survivors.  For each one it
evaluates theta at all 24 UT hours of the terminal date and takes
E(Y) = min_h |theta - 180|.
"""

from __future__ import annotations

import math
from typing import Iterable, Sequence

import numpy as np

from .calendar_math import (
    D,
    digital_root,
    leap_days,
    satisfies_c1,
    terminal_date,
    terminal_date_iso,
    weekday,
)
from .constants import BASE_YEAR, M_SYN, M_SYN_EXACT, T_TROP, W

HOURS = tuple(range(24))


def lunations(d: int) -> int:
    """K(Y) = round(D / M_syn), the nearest whole number of mean lunations."""
    return int(round(d / M_SYN))


def slip_days(d: int, k: int) -> float:
    """D - K*M_syn: how far the span misses a whole number of lunations."""
    return d - k * M_SYN


def is_exact_lunation(d: int) -> bool:
    """True iff D is an exact integer multiple of M_syn *as written*.

    M_syn = 29.5305889 is a terminating decimal, so it is the rational
    295305889 / 10^7 and this test is exact integer arithmetic.
    """
    return (d * 10**7) % M_SYN_EXACT.numerator == 0


def stage1(
    ymin: int = 1, ymax: int = 5000, base_year: int = BASE_YEAR
) -> list[dict]:
    """Integer filter.  Returns one record per C1 survivor, no ephemeris."""
    rows: list[dict] = []
    for Y in range(ymin, ymax + 1):
        d = D(Y, base_year)
        if d % W != 0:
            continue  # C1 fails
        z = d // W
        k = lunations(d)
        y, m, dd = terminal_date(Y, base_year)
        rows.append(
            {
                "Y": Y,
                "date": terminal_date_iso(Y, base_year),
                "weekday": weekday(y, m, dd),
                "D": d,
                "L": leap_days(Y, base_year),
                "Z": z,
                "K": k,
                "slip": slip_days(d, k),
                "resid_trop": d - Y * T_TROP,
                "exact_lunation": is_exact_lunation(d),
                "dr_Y": digital_root(Y),
                "dr_D": digital_root(d),
                "dr_Z": digital_root(z),
                "dr_K": digital_root(k),
            }
        )
    return rows


def _chunks(seq: Sequence, n: int) -> Iterable[Sequence]:
    for i in range(0, len(seq), n):
        yield seq[i : i + n]


def stage2(
    rows: list[dict],
    eph,
    hours: Sequence[int] = HOURS,
    chunk_rows: int = 200,
    progress=None,
) -> list[dict]:
    """Ephemeris pass.  Adds E, theta, hour, illumination, latitude, Delta-T.

    ``E`` is the minimum of |theta - 180| taken over the given UT hours of
    the terminal date.  With the default hourly grid the sampling itself
    contributes up to +/- 0.254 deg, because theta advances about
    0.508 deg per hour; see the methods panel.
    """
    nh = len(hours)
    hour_arr = np.asarray(hours, dtype=float)
    done = 0
    for block in _chunks(rows, chunk_rows):
        years = np.repeat([r["Y"] for r in block], nh)
        # every terminal date is 30 June of its year
        y_civil = years + BASE_YEAR
        months = np.full(y_civil.shape, 6)
        days = np.full(y_civil.shape, 30)
        hh = np.tile(hour_arr, len(block))

        t = eph.times(y_civil, months, days, hh)
        theta = eph.theta(t).reshape(len(block), nh)
        err = np.abs(theta - 180.0)
        best = np.argmin(err, axis=1)

        # second, cheap pass at the winning hour only
        bh = hour_arr[best]
        tb = eph.times(
            np.asarray([r["Y"] + BASE_YEAR for r in block]),
            np.full(len(block), 6),
            np.full(len(block), 30),
            bh,
        )
        illum = eph.moon_illumination(tb)
        beta = eph.moon_ecliptic_latitude(tb)
        dt_s = eph.delta_t_seconds(tb)

        for i, r in enumerate(block):
            j = int(best[i])
            r["E"] = float(err[i, j])
            r["theta"] = float(theta[i, j])
            r["hour"] = int(hours[j])
            r["illum"] = float(np.atleast_1d(illum)[i])
            r["beta"] = float(np.atleast_1d(beta)[i])
            r["delta_t_h"] = float(np.atleast_1d(dt_s)[i]) / 3600.0
            r["theta_h0"] = float(theta[i, 0])
        done += len(block)
        if progress:
            progress(done, len(rows))
    return rows


def theta_at(eph, year: int, month: int, day: int, hour: float = 0.0) -> float:
    """Convenience: theta for a single civil date/hour."""
    t = eph.times([year], [month], [day], [float(hour)])
    return float(np.atleast_1d(eph.theta(t))[0])


def minimal_exact_solution() -> dict:
    """The smallest span satisfying C1 and C3 *exactly*, treating M_syn as
    the rational 295305889/10^7.

    C1 gives D = 7Z.  C3 exact gives D = K * M_syn, so
        7 * Z * 10^7 = K * 295305889.
    295305889 is odd, not a multiple of 5, and leaves remainder 4 mod 7, so
    it is coprime to both 7 and 10^7.  Hence 7*10^7 divides K, and the least
    admissible K is 7*10^7.
    """
    n = M_SYN_EXACT.numerator
    assert math.gcd(n, 7) == 1 and math.gcd(n, 10**7) == 1
    k = 7 * 10**7
    d = k * n // 10**7  # = 7 * n, exactly an integer
    return {
        "K": k,
        "D": d,
        "Z": d // 7,
        "years_tropical": d / T_TROP,
        "note": (
            "Artifact of writing M_syn as a 7-decimal terminating value. "
            "The physical synodic month is neither rational nor constant, "
            "so this span is not a real recurrence."
        ),
    }


def reference_instance(eph, hours: Sequence[int] = HOURS) -> dict:
    """The 1987 / 2026 pair: the founding hypothesis and its failure.

    1987-06-30 and 2026-06-30 are both Tuesdays and exactly 39 whole
    calendar years apart, so C1 and C2 hold.  The lunar phase does not
    return: 39 = 19 + 19 + 1, and the extra year past the double Metonic
    adds about 12.37 lunations, leaving roughly a third of a lunation of
    slip.
    """
    out: dict = {"Y": 39, "D": D(39), "Z": D(39) // W, "note": "39 = 19 + 19 + 1"}
    ends = []
    for year in (1987, 2026):
        t0 = eph.times([year], [6], [30], [0.0])
        th0 = float(np.atleast_1d(eph.theta(t0))[0])
        t24 = eph.times(
            np.full(len(hours), year),
            np.full(len(hours), 6),
            np.full(len(hours), 30),
            np.asarray(hours, dtype=float),
        )
        th = np.atleast_1d(eph.theta(t24))
        j = int(np.argmin(np.abs(th - 180.0)))
        ends.append(
            {
                "date": f"{year}-06-30",
                "weekday": weekday(year, 6, 30),
                "theta_00ut": th0,
                "theta_best": float(th[j]),
                "best_hour": int(hours[j]),
                "E": float(abs(th[j] - 180.0)),
                "illum_00ut": float(np.atleast_1d(eph.moon_illumination(t0))[0]),
                "beta_00ut": float(np.atleast_1d(eph.moon_ecliptic_latitude(t0))[0]),
            }
        )
    out["ends"] = ends
    out["theta_difference"] = ends[1]["theta_00ut"] - ends[0]["theta_00ut"]
    k = lunations(D(39))
    out["K"] = k
    out["slip"] = slip_days(D(39), k)
    out["metonic"] = {
        "years": 19,
        "D_19": D(19),
        "lunations_19": D(19) / M_SYN,
        "D_38": D(38),
        "lunations_38": D(38) / M_SYN,
        "extra_year_lunations": (D(39) - D(38)) / M_SYN,
        "extra_year_days": D(39) - D(38),
    }
    return out
