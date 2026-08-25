"""The impossibility result.

C1 forces D = 7Z.  C3 taken exactly forces D = K * M_syn.  Both together
force 7 * 10^7 to divide K, which puts the first exact solution some 5.66
million years out -- and even that one is an artifact of writing M_syn as a
seven-decimal terminating value.  No ephemeris required.
"""

from __future__ import annotations

import math
from fractions import Fraction

import pytest

from oeyc.calendar_math import D, satisfies_c1
from oeyc.conjectures import continued_fraction, convergents
from oeyc.constants import M_SYN, M_SYN_EXACT, T_TROP, W
from oeyc.scan import is_exact_lunation, lunations, minimal_exact_solution, stage1

N = M_SYN_EXACT.numerator  # 295305889
DEN = M_SYN_EXACT.denominator  # 10**7


# ---------------------------------------------------------------------------
# the arithmetic the theorem rests on
# ---------------------------------------------------------------------------


def test_m_syn_is_exactly_the_stated_rational():
    assert N == 295_305_889
    assert DEN == 10**7
    assert float(M_SYN_EXACT) == M_SYN


def test_numerator_is_coprime_to_seven_and_to_ten_million():
    assert N % 7 == 4  # not divisible by 7
    assert N % 2 == 1  # odd
    assert N % 5 == 4  # not a multiple of 5
    assert math.gcd(N, 7) == 1
    assert math.gcd(N, DEN) == 1


def test_minimal_exact_solution_is_where_the_theorem_says():
    ex = minimal_exact_solution()
    assert ex["K"] == 7 * 10**7
    assert ex["D"] == 7 * N == 2_067_141_223
    assert ex["Z"] == N == 295_305_889
    # it really does satisfy both conditions, exactly
    assert ex["D"] % W == 0
    assert Fraction(ex["D"]) == ex["K"] * M_SYN_EXACT
    assert 5.6e6 < ex["years_tropical"] < 5.7e6


def test_only_multiples_of_ten_million_give_whole_days():
    """K * M_syn is a whole number of days exactly when 10^7 divides K."""
    probes = list(range(1, 20_000)) + [DEN - 1, DEN, DEN + 1, 2 * DEN, 7 * DEN]
    for k in probes:
        assert ((k * N) % DEN == 0) == (k % DEN == 0)


def test_whole_day_spans_need_k_divisible_by_seven_times_ten_million():
    """Among the K giving whole days, only every seventh also gives a whole
    number of weeks, so the first exact solution sits at K = 7 * 10^7."""
    for j in range(1, 30):  # K = j * 10^7, hence D = j * N
        d = j * N
        assert (d % W == 0) == (j % 7 == 0)
    assert (7 * N) % W == 0


def test_exactness_predicate_agrees_with_the_divisibility_rule():
    for k in (1, 2, 6, 7, 10**7, 7 * 10**7):
        d = k * N // DEN if (k * N) % DEN == 0 else None
        if d is None:
            continue
        assert is_exact_lunation(d) is True
    assert is_exact_lunation(7 * N) is True
    assert is_exact_lunation(14245) is False


# ---------------------------------------------------------------------------
# the scan finds nothing, as promised
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ymax", [400, 5000, 20000])
def test_scan_contains_no_exact_solution(ymax):
    rows = stage1(1, ymax)
    assert rows, "stage 1 should always find C1 survivors"
    for r in rows:
        assert r["D"] % W == 0  # C1 by construction
        assert not r["exact_lunation"], f"exact solution claimed at Y = {r['Y']}"
        assert abs(r["slip"]) > 1e-9


def test_slip_is_never_zero_within_the_first_million_years():
    """A far wider sweep than the published scan, still nothing."""
    worst = None
    for Y in range(1, 1_000_000, 7):
        if not satisfies_c1(Y):
            continue
        d = D(Y)
        s = abs(d - lunations(d) * M_SYN)
        if worst is None or s < worst[1]:
            worst = (Y, s)
    assert worst is not None
    assert worst[1] > 0.0, f"exact slip found at Y = {worst[0]}"


# ---------------------------------------------------------------------------
# the infimum is nevertheless zero
# ---------------------------------------------------------------------------


def test_error_floor_descends():
    """Sampling further out finds strictly better near-solutions."""
    best = {}
    for limit in (500, 5_000, 50_000):
        b = min(
            (abs(D(Y) - lunations(D(Y)) * M_SYN) for Y in range(1, limit + 1)
             if satisfies_c1(Y)),
        )
        best[limit] = b
    assert best[5_000] < best[500]
    assert best[50_000] < best[5_000]


def test_gregorian_cycle_does_not_close_the_lunar_phase():
    """146097 days is not a whole number of lunations, which is what makes
    successive 400-year blocks keep exploring new phases."""
    from oeyc.constants import G400

    q = Fraction(G400) / M_SYN_EXACT
    assert q.denominator != 1
    assert 4947 < float(q) < 4948


# ---------------------------------------------------------------------------
# continued fractions terminate, because the constant is rational
# ---------------------------------------------------------------------------


def test_continued_fraction_of_m_over_seven_terminates():
    ratio = M_SYN_EXACT / 7
    terms = continued_fraction(ratio, 200)
    cvs = convergents(terms)
    assert cvs[-1] == ratio, "the last convergent must be the value itself"
    assert terms[0] == 4
    assert 4.2186 < float(ratio) < 4.2187


def test_final_convergent_reproduces_the_minimal_exact_solution():
    ratio = M_SYN_EXACT / 7
    last = convergents(continued_fraction(ratio, 200))[-1]
    ex = minimal_exact_solution()
    # M_syn/7 = Z/K in lowest terms, so the denominator is K itself
    assert last.numerator == ex["Z"] == 295_305_889
    assert last.denominator == ex["K"] == 70_000_000
    assert 7 * last.numerator == ex["D"]


def test_tropical_year_constant_is_only_used_for_bookkeeping():
    """The residual against T_trop is reported, never used to filter."""
    rows = stage1(1, 200)
    for r in rows:
        assert abs(r["resid_trop"]) == abs(r["D"] - r["Y"] * T_TROP)
