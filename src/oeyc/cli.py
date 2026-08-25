"""Command line entry point.

    python -m oeyc.cli scan --ymax 5000 --eps 0.1 --out data/
    python -m oeyc.cli verify
    python -m oeyc.cli theorem
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from . import conjectures as conj
from . import series
from .constants import (
    BASE_DAY,
    BASE_MONTH,
    BASE_WEEKDAY,
    BASE_YEAR,
    G400,
    M_SYN,
    T_TROP,
    W,
)
from .scan import (
    HOURS,
    minimal_exact_solution,
    reference_instance,
    stage1,
    stage2,
)

COLUMNS = [
    "Y",
    "date",
    "weekday",
    "D",
    "L",
    "Z",
    "K",
    "slip",
    "resid_trop",
    "E",
    "theta",
    "hour",
    "illum",
    "beta",
    "delta_t_h",
    "dr_Y",
    "dr_D",
    "dr_Z",
    "dr_K",
]

_ROUND = {
    "slip": 6,
    "resid_trop": 4,
    "E": 6,
    "theta": 6,
    "illum": 5,
    "beta": 4,
    "delta_t_h": 3,
    "theta_h0": 4,
}


def _round_row(r: dict) -> dict:
    out = {}
    for k, v in r.items():
        out[k] = round(v, _ROUND[k]) if k in _ROUND and v is not None else v
    return out


def _progress(done: int, total: int) -> None:
    pct = 100.0 * done / total if total else 100.0
    sys.stderr.write(f"\r  ephemeris {done}/{total} ({pct:5.1f}%)")
    sys.stderr.flush()
    if done >= total:
        sys.stderr.write("\n")


def cmd_scan(args: argparse.Namespace) -> int:
    from .ephemeris import get_ephemeris

    t_start = time.time()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Stage 1: integer filter over Y = {args.ymin} .. {args.ymax}")
    rows = stage1(args.ymin, args.ymax, BASE_YEAR)
    scanned = args.ymax - args.ymin + 1
    print(
        f"  {len(rows)} of {scanned} satisfy C1 "
        f"({100.0 * len(rows) / scanned:.2f}%), ephemeris skipped for the rest"
    )

    print("Stage 2: ephemeris")
    eph = get_ephemeris(args.kernel)
    print(f"  kernel {eph.name}")
    span = eph.span_iso()
    print(f"  valid {span[0]} .. {span[1]}")
    stage2(rows, eph, HOURS, chunk_rows=args.chunk, progress=_progress)

    ref = reference_instance(eph)
    summary = series.summarize(rows, args.eps, args.ymax)
    members = series.select(rows, args.eps)
    gap_seq = series.gaps(members)
    period = series.c1_period_check(rows, args.ymax)
    conjectures = conj.run_all(rows, members, args.ymax, gap_seq, BASE_YEAR)
    exact = minimal_exact_solution()

    import skyfield

    payload = {
        "meta": {
            "oeyc_version": __version__,
            "generated_utc": datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "base_epoch": f"{BASE_YEAR:04d}-{BASE_MONTH:02d}-{BASE_DAY:02d}T00:00:00 UT",
            "base_weekday": BASE_WEEKDAY,
            "ymin": args.ymin,
            "ymax": args.ymax,
            "years_scanned": scanned,
            "eps_default": args.eps,
            "hours_sampled": len(HOURS),
            "hour_grid_deg": round(360.0 / M_SYN / 24.0 / 2.0, 4),
            "kernel": eph.name,
            "kernel_valid_from": span[0],
            "kernel_valid_to": span[1],
            "timescale": "UTC, Skyfield builtin Delta-T table and long-term polynomial",
            "constants": {
                "T_trop": T_TROP,
                "M_syn": M_SYN,
                "W": W,
                "G400": G400,
                "gregorian_mean_year": G400 / 400,
            },
            "counts": {
                "scanned": scanned,
                "c1_survivors": len(rows),
                "members_at_default_eps": len(members),
                "exact_solutions": summary["exact_solutions"],
            },
            "runtime_s": None,
            "software": {
                "python": platform.python_version(),
                "skyfield": skyfield.__version__,
            },
        },
        "theorem": {
            "statement": (
                "No span satisfies C1 and C3 exactly for any Y below "
                "5.66 million years."
            ),
            "argument": (
                "C1 gives D = 7Z.  C3 taken exactly gives D = K*M_syn.  "
                "Writing M_syn as the rational 295305889/10^7 turns "
                "7*Z*10^7 = K*295305889 into an integer equation.  "
                "295305889 is odd, is not a multiple of 5, and leaves "
                "remainder 4 modulo 7, so it is coprime to both 7 and 10^7.  "
                "Therefore 7*10^7 divides K."
            ),
            "minimal_exact": exact,
            "infimum": (
                "The error floor is nevertheless zero.  D(Y+400) = D(Y) + "
                "146097 and 146097/M_syn is not an integer, so successive "
                "400-year blocks advance the lunar phase by an irrational-"
                "looking increment and near-solutions become arbitrarily "
                "good.  Strictly the orbit is periodic, with period "
                "295305889 blocks of 400 years, again only because M_syn "
                "was truncated to seven decimals."
            ),
        },
        "c1_periodicity": period,
        "summary": summary,
        "reference_instance": ref,
        "conjectures": conjectures,
        "columns": COLUMNS,
        "rows": [_round_row(r) for r in rows],
    }
    payload["meta"]["runtime_s"] = round(time.time() - t_start, 1)

    json_path = out_dir / "results.json"
    json_path.write_text(json.dumps(payload, indent=1), encoding="utf-8")

    import pandas as pd

    df = pd.DataFrame([_round_row(r) for r in rows])[COLUMNS]
    csv_path = out_dir / "results.csv"
    df.to_csv(csv_path, index=False)

    print(f"\nWrote {json_path} ({json_path.stat().st_size / 1024:.0f} KB)")
    print(f"Wrote {csv_path} ({csv_path.stat().st_size / 1024:.0f} KB)")
    print(
        f"\nC1 survivors: {len(rows)}   |S({args.eps})| = {len(members)}   "
        f"exact solutions: {summary['exact_solutions']}"
    )
    if summary["best_Y"] is not None:
        print(
            f"Best alignment: Y = {summary['best_Y']} "
            f"({summary['best_date']}), E = {summary['best_E']:.6f} deg"
        )
    print(f"Runtime {payload['meta']['runtime_s']} s")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    from .ephemeris import get_ephemeris

    eph = get_ephemeris(args.kernel)
    ref = reference_instance(eph)
    print("Reference instance: the founding hypothesis")
    print(f"  Y = {ref['Y']}, D = {ref['D']}, Z = {ref['Z']}  ({ref['note']})")
    for e in ref["ends"]:
        print(
            f"  {e['date']}  {e['weekday']:<9}  theta(00 UT) = "
            f"{e['theta_00ut']:8.4f} deg   illuminated {e['illum_00ut'] * 100:5.2f}%"
        )
    print(f"  slip = {ref['slip']:+.4f} d over K = {ref['K']} lunations")
    m = ref["metonic"]
    print(
        f"  Metonic check: 38 y = {m['D_38']} d = "
        f"{m['lunations_38']:.4f} lunations; the extra year adds "
        f"{m['extra_year_lunations']:.4f}"
    )
    return 0


def cmd_theorem(args: argparse.Namespace) -> int:
    ex = minimal_exact_solution()
    print("C1 and C3 cannot both hold exactly below:")
    print(f"  K = {ex['K']:,} lunations")
    print(f"  D = {ex['D']:,} days")
    print(f"  Z = {ex['Z']:,} weeks")
    print(f"  ~ {ex['years_tropical']:,.0f} tropical years")
    print(f"  {ex['note']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="oeyc", description="One Earth Year Completion recurrences"
    )
    p.add_argument("--version", action="version", version=f"oeyc {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan", help="run the two-stage scan and write data")
    s.add_argument("--ymin", type=int, default=1)
    s.add_argument("--ymax", type=int, default=5000)
    s.add_argument("--eps", type=float, default=0.1, help="degrees")
    s.add_argument("--out", default="data/")
    s.add_argument("--kernel", default=None)
    s.add_argument("--chunk", type=int, default=200, help="rows per ephemeris block")
    s.set_defaults(func=cmd_scan)

    v = sub.add_parser("verify", help="reproduce the 1987/2026 reference instance")
    v.add_argument("--kernel", default=None)
    v.set_defaults(func=cmd_verify)

    t = sub.add_parser("theorem", help="print the minimal exact solution")
    t.set_defaults(func=cmd_theorem)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
