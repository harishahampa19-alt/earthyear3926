"""Three testable conjectures about S(epsilon), each reported with its
current computational status rather than a verdict.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Sequence

from .calendar_math import D, satisfies_c1
from .constants import BASE_YEAR, M_SYN, M_SYN_EXACT, T_TROP, W

# --------------------------------------------------------------------------
# (a) additivity
# --------------------------------------------------------------------------


def d_additivity(ymax: int, base_year: int = BASE_YEAR) -> dict:
    """Is D itself additive, that is, does D(a) + D(b) == D(a+b)?

    Not in general: L counts leap years in a window anchored at the base
    year, and two windows laid end to end fail to tile a longer window
    whenever a skipped century (100 yes, 400 no) falls differently.  This
    measures how often it survives anyway.
    """
    total = 0
    holds = 0
    failures: list[dict] = []
    for a in range(1, ymax + 1):
        da = D(a, base_year)
        for b in range(a, ymax + 1 - a):
            total += 1
            if da + D(b, base_year) == D(a + b, base_year):
                holds += 1
            elif len(failures) < 5:
                failures.append(
                    {
                        "a": a,
                        "b": b,
                        "D_a": da,
                        "D_b": D(b, base_year),
                        "sum": da + D(b, base_year),
                        "D_ab": D(a + b, base_year),
                    }
                )
    return {
        "pairs_tested": total,
        "holds": holds,
        "fails": total - holds,
        "fraction": holds / total if total else None,
        "sample_failures": failures,
    }


def additivity(
    members: Sequence[dict], ymax: int, base_year: int = BASE_YEAR
) -> dict:
    """For every pair in S(epsilon), is Y_a + Y_b also in S(epsilon)?

    Only pairs whose sum stays inside the scanned range are counted, so the
    result is not biased by sums that were never tested.
    """
    ys = sorted(r["Y"] for r in members)
    member_set = set(ys)
    c1_closed = 0
    in_s = 0
    tested = 0
    examples: list[dict] = []
    for i, a in enumerate(ys):
        for b in ys[i:]:
            s = a + b
            if s > ymax:
                continue
            tested += 1
            c1 = satisfies_c1(s, base_year)
            c1_closed += c1
            hit = s in member_set
            in_s += hit
            if hit and len(examples) < 10:
                examples.append({"a": a, "b": b, "sum": s})
    return {
        "members": len(ys),
        "pairs_tested": tested,
        "sum_satisfies_c1": c1_closed,
        "sum_in_S": in_s,
        "fraction_c1": c1_closed / tested if tested else None,
        "fraction_in_S": in_s / tested if tested else None,
        "closed_under_addition": tested > 0 and in_s == tested,
        "examples": examples,
    }


def spec_triple(base_year: int = BASE_YEAR) -> dict:
    """The 179 + 437 = 616 case, checked against both leap rules.

    The founding write-up quotes 9340 + 22802 = 32142 weeks and
    2214 + 5405 = 7619 lunations.  Those week counts require a Julian leap
    rule (every fourth year, no century exceptions).  Under the Gregorian
    rule that condition C2 actually specifies the day counts differ, and
    none of the three years satisfies C1 at all.
    """
    out: dict = {
        "terms": [],
        "claimed_weeks": [9340, 22802, 32142],
        "claimed_lunations": [2214, 5405, 7619],
    }
    for Y in (179, 437, 616):
        greg = D(Y, base_year)
        jul = 365 * Y + ((base_year + Y) // 4 - base_year // 4)
        out["terms"].append(
            {
                "Y": Y,
                "D_gregorian": greg,
                "weeks_gregorian": greg / W,
                "c1_gregorian": satisfies_c1(Y, base_year),
                "D_julian": jul,
                "weeks_julian": jul / W,
                "c1_julian": jul % W == 0,
                "K": round(greg / M_SYN),
            }
        )
    g = [t["D_gregorian"] for t in out["terms"]]
    j = [t["D_julian"] for t in out["terms"]]
    k = [t["K"] for t in out["terms"]]
    out["D_additive_gregorian"] = g[0] + g[1] == g[2]
    out["D_additive_julian"] = j[0] + j[1] == j[2]
    out["K_additive"] = k[0] + k[1] == k[2]
    out["weeks_match_claim_gregorian"] = [
        t["weeks_gregorian"] == c
        for t, c in zip(out["terms"], out["claimed_weeks"])
    ]
    out["weeks_match_claim_julian"] = [
        t["weeks_julian"] == c for t, c in zip(out["terms"], out["claimed_weeks"])
    ]
    return out


# --------------------------------------------------------------------------
# (b) continued fractions
# --------------------------------------------------------------------------


def continued_fraction(x: Fraction, n_terms: int = 20) -> list[int]:
    terms: list[int] = []
    for _ in range(n_terms):
        a = x.numerator // x.denominator  # floor
        terms.append(a)
        frac = x - a
        if frac == 0:
            break
        x = 1 / frac
    return terms


def convergents(terms: Sequence[int]) -> list[Fraction]:
    out: list[Fraction] = []
    h_prev, h = 1, terms[0]
    k_prev, k = 0, 1
    out.append(Fraction(h, k))
    for a in terms[1:]:
        h, h_prev = a * h + h_prev, h
        k, k_prev = a * k + k_prev, k
        out.append(Fraction(h, k))
    return out


def cf_predictions(members: Sequence[dict], ymax: int, n_terms: int = 24) -> dict:
    """Convergents of M_syn / 7 as candidate (Z, K) pairs.

    C1 and C3 together demand Z / K = M_syn / 7.  The best rational
    approximations to that ratio are its continued-fraction convergents, so
    each convergent p/q proposes Z = p and K = q, hence D = 7p and a
    predicted year offset Y ~ D / T_trop.  This records how close the
    members of S(epsilon) come to those predictions.
    """
    ratio = M_SYN_EXACT / 7
    terms = continued_fraction(ratio, n_terms)
    cvs = convergents(terms)
    ys = sorted(r["Y"] for r in members)
    preds: list[dict] = []
    for c in cvs:
        d = 7 * c.numerator
        y_pred = d / T_TROP
        rec: dict = {
            "p": c.numerator,
            "q": c.denominator,
            "value": float(c),
            "abs_error": float(abs(c - ratio)),
            "D_pred": d,
            "Y_pred": y_pred,
            "in_range": 0 < y_pred <= ymax,
        }
        if rec["in_range"] and ys:
            nearest = min(ys, key=lambda y: abs(y - y_pred))
            rec["nearest_member_Y"] = nearest
            rec["distance_years"] = abs(nearest - y_pred)
        preds.append(rec)
    return {
        "ratio": float(ratio),
        "ratio_exact": str(ratio.numerator) + "/" + str(ratio.denominator),
        "cf_terms": terms,
        "convergents": preds,
        "note": (
            "M_syn / 7 is rational only because M_syn was written as a "
            "terminating decimal, so its continued fraction terminates. "
            "The final convergent is not an approximation but an identity, "
            "and it is the minimal exact solution of C1 and C3."
        ),
    }


# --------------------------------------------------------------------------
# (c) gap periodicity
# --------------------------------------------------------------------------


def gap_periodicity(gap_seq: Sequence[int], max_period: int | None = None) -> dict:
    """Is the gap sequence eventually periodic?

    Reports every p for which the whole sequence repeats with period p, and
    the best partial match when no exact period exists.
    """
    n = len(gap_seq)
    if n < 4:
        return {"length": n, "conclusive": False, "reason": "sequence too short"}
    cap = max_period or max(1, n // 2)
    exact: list[int] = []
    best = {"period": None, "match_fraction": 0.0}
    for p in range(1, cap + 1):
        total = n - p
        if total <= 0:
            continue
        agree = sum(1 for i in range(p, n) if gap_seq[i] == gap_seq[i - p])
        frac = agree / total
        if frac == 1.0:
            exact.append(p)
        if frac > best["match_fraction"]:
            best = {"period": p, "match_fraction": frac}
    return {
        "length": n,
        "distinct_values": sorted(set(gap_seq)),
        "exact_periods": exact,
        "is_periodic": bool(exact),
        "best_partial": best,
        "conclusive": True,
    }


def run_all(
    rows: Sequence[dict],
    members: Sequence[dict],
    ymax: int,
    gap_seq: Sequence[int],
    base_year: int = BASE_YEAR,
) -> dict:
    return {
        "additivity": additivity(members, ymax, base_year),
        "d_additivity": d_additivity(min(ymax, 1200), base_year),
        "spec_triple": spec_triple(base_year),
        "continued_fractions": cf_predictions(members, ymax),
        "gap_periodicity": gap_periodicity(gap_seq),
    }
