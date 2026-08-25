"""Skyfield/DE441 wrapper.

Provides geocentric *apparent* ecliptic quantities: the Sun-Earth-Moon
elongation theta, the Moon's illuminated fraction, and the Moon's ecliptic
latitude.  The loaded kernel and timescale are cached process-wide, because
opening a 1.6 GB SPK is the expensive part.

Why a real ephemeris and not mean elements: over the scan horizon
(2026 .. 7026 CE) a mean-element lunar theory drifts by degrees within a
thousand years and by tens of degrees within five thousand, which is far
larger than the sub-degree effects this project measures.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import numpy as np

from .constants import DEFAULT_KERNEL, KERNEL_URL


class KernelNotFound(RuntimeError):
    """Raised when no SPK kernel can be located."""


def _candidate_paths(kernel: str | None) -> list[Path]:
    name = kernel or os.environ.get("OEYC_KERNEL") or DEFAULT_KERNEL
    if os.path.isabs(name):
        return [Path(name)]
    roots: list[Path] = []
    env_dir = os.environ.get("OEYC_KERNEL_DIR")
    if env_dir:
        roots.append(Path(env_dir))
    roots.append(Path.cwd() / "kernels")
    roots.append(Path.cwd())
    repo_root = Path(__file__).resolve().parents[2]
    roots.append(repo_root / "kernels")
    seen: set[Path] = set()
    out: list[Path] = []
    for r in roots:
        p = (r / name).resolve()
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def resolve_kernel(kernel: str | None = None) -> Path:
    """Find the SPK file on disk, or explain how to get it."""
    tried = _candidate_paths(kernel)
    for p in tried:
        if p.is_file():
            return p
    listing = "\n  ".join(str(p) for p in tried)
    raise KernelNotFound(
        f"Could not find the ephemeris kernel.  Looked in:\n  {listing}\n\n"
        f"Download it once (1.6 GB) with:\n"
        f"  curl -L -C - -o kernels/{DEFAULT_KERNEL} {KERNEL_URL}\n\n"
        f"or point OEYC_KERNEL_DIR at a directory that already holds it."
    )


class Ephemeris:
    """Lazily-opened DE kernel plus the derived Sun/Earth/Moon geometry."""

    def __init__(self, kernel: str | None = None) -> None:
        from skyfield.api import load, load_file

        self.path = resolve_kernel(kernel)
        self.name = self.path.name
        self._eph = load_file(str(self.path))
        self._earth = self._eph["earth"]
        self._sun = self._eph["sun"]
        self._moon = self._eph["moon"]
        # builtin=True uses Skyfield's bundled Delta-T table and long-term
        # polynomial, so no network access and byte-identical results.
        self.ts = load.timescale(builtin=True)

    # -- span -------------------------------------------------------------
    def span_jd(self) -> tuple[float, float]:
        """Julian date range over which every segment we use is valid.

        Skyfield wraps each raw SPK segment, so the JD bounds live on the
        underlying ``spk_segment``.  Only the Sun, the Earth-Moon
        barycentre, the Moon and the Earth are consulted here.
        """
        needed = {(0, 10), (0, 3), (3, 301), (3, 399)}
        lo, hi = -np.inf, np.inf
        for seg in self._eph.segments:
            if (seg.center, seg.target) not in needed:
                continue
            raw = getattr(seg, "spk_segment", seg)
            lo = max(lo, float(raw.start_jd))
            hi = min(hi, float(raw.end_jd))
        if not (np.isfinite(lo) and np.isfinite(hi)):
            raise KernelNotFound(
                f"{self.name} lacks the Sun/Earth/Moon segments this needs"
            )
        return float(lo), float(hi)

    def span_iso(self) -> tuple[str, str]:
        """Validity span as ISO dates.

        Formatted from the calendar tuple rather than ``utc_strftime``,
        because this kernel runs to year 17191 and ``strftime`` refuses
        any year past 9999.
        """

        def fmt(jd: float) -> str:
            c = self.ts.tdb_jd(jd).utc
            return f"{int(c[0]):04d}-{int(c[1]):02d}-{int(c[2]):02d}"

        lo, hi = self.span_jd()
        return fmt(lo), fmt(hi)

    # -- time construction -------------------------------------------------
    def times(self, years, months, days, hours) -> "object":
        """Build a Skyfield Time array from broadcastable UT components."""
        return self.ts.utc(years, months, days, hours)

    # -- geometry ----------------------------------------------------------
    def _latlon(self, t):
        from skyfield.framelib import ecliptic_frame

        e = self._earth.at(t)
        slat, slon, _ = e.observe(self._sun).apparent().frame_latlon(ecliptic_frame)
        mlat, mlon, _ = e.observe(self._moon).apparent().frame_latlon(ecliptic_frame)
        return slat, slon, mlat, mlon

    def theta(self, t) -> np.ndarray:
        """theta = (lambda_moon - lambda_sun) mod 360, degrees.

        Geocentric apparent longitudes in the true ecliptic and equinox of
        date.  0 deg = new moon, 180 deg = full moon.
        """
        _, slon, _, mlon = self._latlon(t)
        return np.asarray((mlon.degrees - slon.degrees) % 360.0)

    def moon_ecliptic_latitude(self, t) -> np.ndarray:
        """Apparent geocentric ecliptic latitude of the Moon, degrees.

        Near a full moon this is what decides eclipse versus no eclipse.
        """
        _, _, mlat, _ = self._latlon(t)
        return np.asarray(mlat.degrees)

    def moon_illumination(self, t) -> np.ndarray:
        """Illuminated fraction of the lunar disc, 0..1.

        Uses the true Sun-Moon-Earth phase angle, not the elongation
        proxy (1 - cos theta) / 2, which differs by up to ~0.5% of disc.
        """
        from skyfield.almanac import fraction_illuminated

        return np.asarray(fraction_illuminated(self._eph, "moon", t))

    def delta_t_seconds(self, t) -> np.ndarray:
        """TT - UT1 in seconds, the dominant systematic in the far future."""
        return np.asarray(t.delta_t)


@lru_cache(maxsize=4)
def get_ephemeris(kernel: str | None = None) -> Ephemeris:
    """Process-wide cached kernel handle."""
    return Ephemeris(kernel)
