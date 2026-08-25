#!/usr/bin/env python
"""Verify that data/results.json still matches the committed code.

Every integer column is re-derived from scratch and compared, so a stale
data file or a change in the calendar arithmetic fails CI.  Ephemeris
columns (E, theta, illum, beta) cannot be checked without the 1.6 GB
kernel; their internal consistency is checked instead.

    python scripts/check_data.py [path/to/results.json]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from oeyc.calendar_math import (  # noqa: E402
    D,
    digital_root,
    leap_days,
    satisfies_c1,
    terminal_date_iso,
    weekday,
)
from oeyc.constants import M_SYN, T_TROP, W  # noqa: E402
from oeyc.scan import lunations, stage1  # noqa: E402


def fail(msg: str) -> None:
    print("FAIL: " + msg)
    raise SystemExit(1)


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/results.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    meta = data["meta"]
    rows = data["rows"]

    print(f"checking {path} ({len(rows)} rows, Y <= {meta['ymax']})")

    # 1. the row set is exactly the C1 survivors of the stated range
    expected = stage1(meta["ymin"], meta["ymax"])
    if len(expected) != len(rows):
        fail(f"row count {len(rows)} != recomputed {len(expected)}")
    if [r["Y"] for r in expected] != [r["Y"] for r in rows]:
        fail("the set of C1 survivors does not match")

    # 2. every integer column, re-derived
    for r in rows:
        Y = r["Y"]
        if not satisfies_c1(Y):
            fail(f"Y={Y} is in the data but fails C1")
        checks = {
            "D": D(Y),
            "L": leap_days(Y),
            "Z": D(Y) // W,
            "K": lunations(D(Y)),
            "date": terminal_date_iso(Y),
            "weekday": weekday(2026 + Y, 6, 30),
            "dr_Y": digital_root(Y),
            "dr_D": digital_root(D(Y)),
            "dr_Z": digital_root(D(Y) // W),
            "dr_K": digital_root(lunations(D(Y))),
        }
        for key, want in checks.items():
            if r[key] != want:
                fail(f"Y={Y} column {key}: stored {r[key]!r}, recomputed {want!r}")

        if r["D"] % W != 0:
            fail(f"Y={Y}: D is not divisible by 7")
        if abs(r["slip"] - (r["D"] - r["K"] * M_SYN)) > 5e-6:
            fail(f"Y={Y}: slip does not follow from D and K")
        if abs(r["resid_trop"] - (r["D"] - Y * T_TROP)) > 5e-4:
            fail(f"Y={Y}: tropical residual does not follow from D")

        # ephemeris columns: internal consistency only
        if not (0.0 <= r["theta"] < 360.0):
            fail(f"Y={Y}: theta out of range")
        if abs(r["E"] - abs(r["theta"] - 180.0)) > 5e-6:
            fail(f"Y={Y}: E is not |theta - 180|")
        if not (0 <= r["hour"] <= 23):
            fail(f"Y={Y}: hour out of range")
        if not (0.0 <= r["illum"] <= 1.0):
            fail(f"Y={Y}: illuminated fraction out of range")

    # 3. headline counts quoted on the site
    counts = meta["counts"]
    if counts["c1_survivors"] != len(rows):
        fail("meta.counts.c1_survivors disagrees with the row count")
    if counts["exact_solutions"] != 0:
        fail("an exact solution is claimed; the theorem says there is none")
    for r in rows:
        if r["exact_lunation"]:
            fail(f"Y={r['Y']} claims an exact lunation count")

    # 4. the summary block
    s = data["summary"]
    best = min(rows, key=lambda r: r["E"])
    if s["best_Y"] != best["Y"]:
        fail(f"summary.best_Y {s['best_Y']} != {best['Y']}")
    members = [r for r in rows if r["E"] < s["eps"]]
    if s["members"] != len(members):
        fail("summary.members disagrees with the rows")

    # 5. C1 is 400-periodic, as claimed on the site
    period = data["c1_periodicity"]
    if period["violations"] != 0 or not period["holds"]:
        fail("the 400-year periodicity claim does not hold")
    ys = {r["Y"] for r in rows}
    for Y in sorted(ys):
        if Y + 400 <= meta["ymax"] and (Y + 400) not in ys:
            fail(f"Y={Y} has no counterpart at Y={Y + 400}")

    # 6. the two published values that fail, still fail
    if satisfies_c1(4374):
        fail("Y=4374 now satisfies C1; test_known.py needs revisiting")
    if D(4374) % W != 3:
        fail("D(4374) mod 7 changed")
    if 1031 not in ys:
        fail("Y=1031 should be present as a C1 survivor")

    print(f"OK: {len(rows)} rows re-derived, 0 exact solutions, "
          f"best Y={best['Y']} at E={best['E']:.6f} deg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
