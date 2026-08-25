"""Generate notebooks/01_explore.ipynb.

Kept in the repo so the notebook is regenerable rather than hand-maintained
JSON.  Run from the repository root:  python scripts/_build_notebook.py
"""

import json
import pathlib


def md(*lines):
    return {"cell_type": "markdown", "metadata": {},
            "source": [line + "\n" for line in lines]}


def code(*lines):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": [line + "\n" for line in lines]}


CELLS = [
    md("# OEYC — a reproducible walkthrough",
       "",
       "Every number on the site and in the README comes from this pipeline.",
       "This notebook rebuilds the important ones from scratch.",
       "",
       "The integer sections need nothing but Python. The ephemeris sections",
       "need the DE441 kernel (1.6 GB) in `kernels/`, and skip themselves if",
       "it is absent."),

    code("import sys, pathlib",
         "sys.path.insert(0, str(pathlib.Path.cwd().parent / 'src'))",
         "",
         "from oeyc.calendar_math import (D, Z, leap_days, satisfies_c1,",
         "                                weekday, terminal_date_iso)",
         "from oeyc.constants import M_SYN, T_TROP, W, G400, M_SYN_EXACT",
         "from oeyc.scan import stage1, lunations, minimal_exact_solution",
         "import oeyc",
         "print('oeyc', oeyc.__version__)"),

    md("## 1. The reference instance",
       "",
       "30 June 1987 and 30 June 2026: both Tuesdays, 39 calendar years apart."),

    code("for Y in (39, -39):",
         "    print(f'Y={Y:+3d}  L={leap_days(Y):+3d}  D={D(Y):+7d}  '",
         "          f'Z={Z(Y)}  C1={satisfies_c1(Y)}  {terminal_date_iso(Y)}')",
         "",
         "print()",
         "print('1987-06-30 is a', weekday(1987, 6, 30))",
         "print('2026-06-30 is a', weekday(2026, 6, 30))"),

    md("## 2. The 400-year cycle",
       "",
       "146097 days is exactly 20871 weeks, so C1 membership is 400-periodic",
       "in Y. This is the one structural regularity the project establishes."),

    code("print('D(400)      =', D(400), '  (G400 =', G400, ')')",
         "print('146097 / 7  =', G400 / W)",
         "print('146097 % 7  =', G400 % W)",
         "",
         "hits = [Y for Y in range(400) if satisfies_c1(Y)]",
         "print()",
         "print(len(hits), 'admissible residues mod 400:')",
         "print(hits)",
         "",
         "assert all(satisfies_c1(Y) == satisfies_c1(Y + 400)",
         "           for Y in range(-500, 1500))",
         "print()",
         "print('periodicity verified over Y in [-500, 1500]')"),

    md("## 3. The impossibility theorem",
       "",
       "C1 gives `D = 7Z`. C3 taken exactly gives `D = K*M_syn`. Because",
       "M_syn is written as a terminating decimal it is the rational",
       "`295305889 / 10**7`, which turns the pair into an integer equation."),

    code("import math",
         "N, DEN = M_SYN_EXACT.numerator, M_SYN_EXACT.denominator",
         "print('M_syn =', N, '/', DEN)",
         "print('N mod 7 =', N % 7, '   N is odd:', N % 2 == 1,",
         "      '   N mod 5 =', N % 5)",
         "print('gcd(N, 7)     =', math.gcd(N, 7))",
         "print('gcd(N, 10**7) =', math.gcd(N, DEN))",
         "print()",
         "print('therefore 7 * 10**7 must divide K')",
         "print()",
         "",
         "ex = minimal_exact_solution()",
         "for key, val in ex.items():",
         "    print(' ', key, ':', val)"),

    md("The smallest exact solution sits 5.66 million years out, and even",
       "that one is an artifact of the seven-decimal truncation. For the",
       "physical synodic month, which is irrational and drifting, the",
       "solution set is empty outright."),

    md("## 4. Stage 1 — the integer filter",
       "",
       "Six sevenths of the search space falls away for the cost of a modulo."),

    code("rows = stage1(1, 5000)",
         "print(len(rows), 'of 5000 satisfy C1  ',",
         "      f'({100 * len(rows) / 5000:.2f}%)')",
         "print()",
         "for r in rows[:6]:",
         "    print(f\"Y={r['Y']:>4}  {r['date']}  D={r['D']:>7}  \"",
         "          f\"Z={r['Z']:>6}  K={r['K']:>5}  slip={r['slip']:+8.4f}\")",
         "",
         "print()",
         "print('exact lunation counts found:',",
         "      sum(r['exact_lunation'] for r in rows))"),

    md("## 5. Stage 2 — the ephemeris",
       "",
       "Needs `kernels/de441_part-2.bsp`. Everything below degrades to a",
       "message if the kernel is missing."),

    code("try:",
         "    from oeyc.ephemeris import get_ephemeris",
         "    eph = get_ephemeris()",
         "    HAVE_KERNEL = True",
         "    print('kernel:', eph.name)",
         "    print('valid :', ' to '.join(eph.span_iso()))",
         "except Exception as exc:",
         "    HAVE_KERNEL = False",
         "    print('no kernel, ephemeris sections skipped:')",
         "    print(exc)"),

    md("### The founding hypothesis, measured"),

    code("if HAVE_KERNEL:",
         "    from oeyc.scan import reference_instance",
         "    ref = reference_instance(eph)",
         "    for e in ref['ends']:",
         "        print(f\"{e['date']}  {e['weekday']:<9} \"",
         "              f\"theta={e['theta_00ut']:8.4f} deg  \"",
         "              f\"lit={e['illum_00ut'] * 100:6.2f}%\")",
         "    print()",
         "    print(f\"slip {ref['slip']:+.4f} d over K={ref['K']} lunations\")",
         "    m = ref['metonic']",
         "    print(f\"19 y = {m['lunations_19']:.4f} lunations\")",
         "    print(f\"38 y = {m['lunations_38']:.4f} lunations\")",
         "    print(f\"the extra year adds {m['extra_year_lunations']:.4f}\")"),

    md("### Cross-check theta against Skyfield's own phase function",
       "",
       "If this disagrees, nothing else in the project can be trusted."),

    code("if HAVE_KERNEL:",
         "    import numpy as np",
         "    from skyfield.almanac import moon_phase",
         "    years = [1987, 2026, 2178, 3609, 3829]",
         "    n = len(years)",
         "    t = eph.times(years, [6] * n, [30] * n, [0.0] * n)",
         "    mine, theirs = eph.theta(t), moon_phase(eph._eph, t).degrees",
         "    for y, a, b in zip(years, mine, theirs):",
         "        print(f'{y}  ours {a:10.6f}   skyfield {b:10.6f}   '",
         "              f'diff {abs(a - b):.2e}')"),

    md("### The two published values that do not reproduce",
       "",
       "Y = 1031 was recorded at about 179.98 deg and Y = 4374 at about",
       "180.000 deg. Neither survives measurement."),

    code("if HAVE_KERNEL:",
         "    import numpy as np",
         "    for Y in (1031, 4374):",
         "        yr = 2026 + Y",
         "        t = eph.times(np.full(24, yr), np.full(24, 6),",
         "                      np.full(24, 30), np.arange(24.0))",
         "        th = eph.theta(t)",
         "        j = int(np.argmin(np.abs(th - 180)))",
         "        print(f'Y={Y}  D={D(Y)}  D mod 7 = {D(Y) % 7}  '",
         "              f'C1={satisfies_c1(Y)}')",
         "        print(f'      best theta = {th[j]:.4f} deg at {j:02d} UT'",
         "              f'  ->  E = {abs(th[j] - 180):.4f} deg')"),

    md("## 6. The full scan",
       "",
       "Reproduces `data/results.json`."),

    code("if HAVE_KERNEL:",
         "    from oeyc.scan import stage2, HOURS",
         "    from oeyc import series",
         "    rows = stage1(1, 5000)",
         "    stage2(rows, eph, HOURS)",
         "    summary = series.summarize(rows, 0.1, 5000)",
         "    members = series.select(rows, 0.1)",
         "    print('C1 survivors', summary['c1_survivors'],",
         "          '  |S(0.1)| =', summary['members'],",
         "          '  exact', summary['exact_solutions'])",
         "    print()",
         "    header = ('Y', 'date', 'Z', 'K', 'slip', 'E deg')",
         "    print(f'{header[0]:>5} {header[1]:>11} {header[2]:>7} '",
         "          f'{header[3]:>6} {header[4]:>9} {header[5]:>10}')",
         "    for r in members:",
         "        print(f\"{r['Y']:>5} {r['date']:>11} {r['Z']:>7} \"",
         "              f\"{r['K']:>6} {r['slip']:>+9.4f} {r['E']:>10.6f}\")",
         "    print()",
         "    print('gaps:', series.gaps(members))"),

    md("### The descending error floor"),

    code("if HAVE_KERNEL:",
         "    for p in summary['running_minimum']:",
         "        print(f\"Y={p['Y']:>5}  {p['date']}  E={p['E']:.6f} deg\")"),

    md("## 7. Verify the committed data",
       "",
       "The same check CI runs on every push."),

    code("import subprocess, sys",
         "out = subprocess.run(",
         "    [sys.executable, '../scripts/check_data.py',",
         "     '../data/results.json'],",
         "    capture_output=True, text=True)",
         "print(out.stdout or out.stderr)"),
]


def main():
    nb = {
        "cells": CELLS,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python",
                           "name": "python3"},
            "language_info": {"name": "python", "version": "3.12"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    root = pathlib.Path(__file__).resolve().parents[1]
    out = root / "notebooks" / "01_explore.ipynb"
    out.write_text(json.dumps(nb, indent=1), encoding="utf-8")
    json.loads(out.read_text(encoding="utf-8"))  # validate
    print(f"wrote {out} ({out.stat().st_size} bytes, {len(CELLS)} cells)")


if __name__ == "__main__":
    main()
