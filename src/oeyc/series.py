"""Build S(epsilon) and the quantities derived from it."""

from __future__ import annotations

import statistics
from typing import Sequence

from .calendar_math import digital_root
from .constants import G400


def select(rows: Sequence[dict], eps: float) -> list[dict]:
    """S(epsilon) = the C1 survivors whose terminal alignment beats epsilon."""
    return [r for r in rows if r.get("E") is not None and r["E"] < eps]


def gaps(members: Sequence[dict]) -> list[int]:
    """Differences between consecutive Y values of S(epsilon)."""
    ys = [r["Y"] for r in members]
    return [b - a for a, b in zip(ys, ys[1:])]


def c1_period_check(rows: Sequence[dict], ymax: int) -> dict:
    """C1 membership is exactly 400-periodic in Y.

    D(Y+400) - D(Y) = 146097 = 7 * 20871, so adding 400 years never changes
    D mod 7.  This verifies that structural claim against the scan itself.
    """
    hits = {r["Y"] for r in rows}
    checked = 0
    violations = 0
    for Y in sorted(hits):
        if Y + 400 <= ymax:
            checked += 1
            if (Y + 400) not in hits:
                violations += 1
    residues = sorted({Y % 400 for Y in hits})
    return {
        "period": 400,
        "days_per_cycle": G400,
        "weeks_per_cycle": G400 // 7,
        "pairs_checked": checked,
        "violations": violations,
        "holds": violations == 0,
        "residues_mod_400": residues,
        "residue_count": len(residues),
    }


def digital_root_histogram(members: Sequence[dict], key: str = "Y") -> dict[int, int]:
    h: dict[int, int] = {}
    for r in members:
        v = r.get("dr_" + key)
        if v is None:
            v = digital_root(r[key])
        h[v] = h.get(v, 0) + 1
    return dict(sorted(h.items()))


def running_minimum(rows: Sequence[dict]) -> list[dict]:
    """The descending error floor: best E seen at or before each Y."""
    out: list[dict] = []
    best = float("inf")
    for r in sorted(rows, key=lambda r: r["Y"]):
        if r.get("E") is None:
            continue
        if r["E"] < best:
            best = r["E"]
            out.append({"Y": r["Y"], "E": r["E"], "date": r["date"]})
    return out


def summarize(rows: Sequence[dict], eps: float, ymax: int) -> dict:
    members = select(rows, eps)
    g = gaps(members)
    es = [r["E"] for r in rows if r.get("E") is not None]
    slips = [abs(r["slip"]) for r in rows]
    best = min(rows, key=lambda r: r.get("E", float("inf"))) if rows else None
    return {
        "eps": eps,
        "ymax": ymax,
        "c1_survivors": len(rows),
        "members": len(members),
        "first": members[0]["Y"] if members else None,
        "last": members[-1]["Y"] if members else None,
        "gap_min": min(g) if g else None,
        "gap_max": max(g) if g else None,
        "gap_mean": (sum(g) / len(g)) if g else None,
        "gap_median": statistics.median(g) if g else None,
        "distinct_gaps": sorted(set(g)) if g else [],
        "E_min": min(es) if es else None,
        "E_max": max(es) if es else None,
        "E_median": statistics.median(es) if es else None,
        "abs_slip_min": min(slips) if slips else None,
        "best_Y": best["Y"] if best else None,
        "best_E": best.get("E") if best else None,
        "best_date": best["date"] if best else None,
        "exact_solutions": sum(
            1 for r in rows if r.get("exact_lunation") and r["D"] % 7 == 0
        ),
        "digital_roots_Y": digital_root_histogram(members, "Y"),
        "running_minimum": running_minimum(rows),
    }
