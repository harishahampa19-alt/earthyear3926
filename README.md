# OEYC — One Earth Year Completion

[![CI](https://github.com/harishahampa19-alt/earthyear3926/actions/workflows/ci.yml/badge.svg)](https://github.com/harishahampa19-alt/earthyear3926/actions/workflows/ci.yml)
[![Live](https://img.shields.io/badge/live-vercel-7fb8ff)](https://earthyeartimepasssss.vercel.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**[→ Explore the interactive map of near-solutions](https://earthyeartimepasssss.vercel.app/)**

Start from **30 June 2026, 00:00 UT** — a Tuesday, at a full moon
(θ = 180.03°). Go forward a whole number of calendar years. When does the
terminal date land on a Tuesday *and* at a full moon again?

---

## The theorem: never

> **C1** forces `D = 7Z`.  **C3** taken exactly forces `D = K·M`.
>
> Writing `M = 29.5305889` as the rational `295305889 / 10⁷` turns
> `7·Z·10⁷ = K·295305889` into an integer equation. The numerator 295305889
> is odd, is not a multiple of 5, and leaves remainder 4 modulo 7 — so it is
> coprime to both 7 and 10⁷.
>
> **Therefore `7·10⁷` divides `K`.**

The first span that satisfies C1 and C3 exactly needs

| | |
|---|---|
| K | 70,000,000 lunations |
| D | 2,067,141,223 days |
| Z | 295,305,889 weeks |
| ≈ | **5,659,645 tropical years** |

Nothing below that works. And that solution is an artifact of writing M to
seven decimal places: the physical synodic month is neither rational nor
constant, so for the real Moon the solution set is **empty outright**.

Reproduce it with `python -m oeyc.cli theorem`; the divisibility argument is
established both by construction and by brute force in
[`tests/test_theorem.py`](tests/test_theorem.py).

### But the infimum is zero

Each 400-year Gregorian block advances the calendar by exactly 146097 days,
which is **not** a whole number of lunations (146097 / M ≈ 4947.31). So
successive blocks keep landing on new lunar phases and the near-solutions
improve without bound. **This project maps them.**

> A caveat stated plainly: because M was truncated to seven decimals, that
> walk is strictly periodic rather than equidistributed — with a period of
> 295,305,889 blocks of 400 years. At any horizon a human cares about, the
> distinction is invisible.

---

## Results, Y ≤ 15000

Scan of 15000 years from the base epoch — the full range the ephemeris
supports, since DE441 ends in March 17191. **2174** satisfy C1; **31** land
within 0.1° of a true full moon; **0** are exact, as the theorem requires.

The twelve closest, with the ΔT column priced in degrees of lunar phase so it
can be read against E directly:

| Y | terminal date | D | Z | K | slip (d) | E (deg) | ΔT (h) | ΔT as phase |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| **1803** | **3829-06-30** | 658,532 | 94,076 | 22,300 | −0.1325 | **0.000661** | 3.5 | 1.80° |
| 1583 | 3609-06-30 | 578,179 | 82,597 | 19,579 | −0.4001 | 0.002162 | 2.8 | 1.42° |
| 14913 | 16939-06-30 | 5,446,861 | 778,123 | 184,448 | +2.9386 | 0.003091 | 206.1 | 104.71° |
| 11983 | 14009-06-30 | 4,376,701 | 625,243 | 148,209 | +1.9497 | 0.003196 | 133.9 | 68.03° |
| 3386 | 5412-06-30 | 1,236,711 | 176,673 | 41,879 | −0.5325 | 0.005312 | 11.5 | 5.86° |
| 14845 | 16871-06-30 | 5,422,025 | 774,575 | 183,607 | +2.1638 | 0.011484 | 204.3 | 103.77° |
| 4885 | 6911-06-30 | 1,784,209 | 254,887 | 60,419 | +0.3493 | 0.016982 | 23.3 | 11.82° |
| 839 | 2865-06-30 | 306,439 | 43,777 | 10,377 | +0.0790 | 0.019117 | 0.9 | 0.45° |
| 277 | 2303-06-30 | 101,171 | 14,453 | 3,426 | −0.7976 | 0.021569 | 0.1 | 0.06° |
| 9110 | 11136-06-30 | 3,327,359 | 475,337 | 112,675 | −0.1043 | 0.022350 | 78.2 | 39.71° |
| 12067 | 14093-06-30 | 4,407,382 | 629,626 | 149,248 | +0.6679 | 0.024664 | 135.8 | 68.97° |
| 8586 | 10612-06-30 | 3,135,972 | 447,996 | 106,194 | +0.6424 | 0.042125 | 69.6 | 35.36° |

**Wherever ΔT-as-phase exceeds E, the miss is smaller than the uncertainty in
what time it is.** Past roughly Y = 1200 that is every row. The entries beyond
Y = 8000 carry 35° to 105° of phase uncertainty and are arithmetic, not
prediction; the site shades them.

### The error floor descends, then stops

| Y | 11 | 73 | 141 | 152 | 277 | 839 | 1583 | 1803 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **E (deg)** | 27.533 | 20.031 | 17.275 | 0.04890 | 0.02157 | 0.01912 | 0.00216 | **0.00066** |

The last record is set at **Y = 1803**, and the remaining **13,197** years of
the scan never beat it. The best that follows is Y = 14913 at 0.003091°, which
is **4.7× worse**.

This is not a contradiction of `inf |error| = 0`. Records in an equidistributed
sequence improve *logarithmically* — each new one takes exponentially longer to
arrive, so a scan three times longer is expected to add roughly one more, and
may add none. Y = 1803 was an early lucky draw. The infimum is still zero; no
finite scan can display it.

| tolerance ε | members |
|---|---:|
| 0.01° | 5 |
| 0.05° | 16 |
| 0.1° | 31 |
| 0.25° | 75 |
| 1.0° | 86 |

**Established result:** C1 membership is exactly 400-periodic in Y, because
`D(Y+400) − D(Y) = 146097 = 7 × 20871`. There are 58 admissible residues mod
400 — verified over 2116 pairs with zero violations.

---

## Quickstart

```bash
pip install -r requirements.txt
python -m oeyc.cli scan --ymax 15000 --eps 0.1
```

`requirements.txt` ends with `-e .`, so that first command installs the `oeyc`
package too and no second install step is needed.

The scan needs the JPL DE441 kernel, a **1.6 GB** one-time download that is
never committed:

```bash
mkdir -p kernels && curl -L -C - -o kernels/de441_part-2.bsp https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de441_part-2.bsp
```

`de441_part-2` spans 1969-06-27 to 17191-03-14, covering the base epoch, the
1987 reference instance, and every terminal date out to Y = 15000. Point
`OEYC_KERNEL_DIR` at any directory that already holds it.

Other commands:

```bash
python -m oeyc.cli verify    # reproduce the 1987/2026 reference instance
python -m oeyc.cli theorem   # the minimal exact solution; needs no kernel
pytest -q                    # ephemeris tests skip cleanly without the kernel
python scripts/check_data.py # re-derive every integer column of results.json
```

To view the site locally:

```bash
python scripts/serve.py . 8765
```

then open <http://127.0.0.1:8765/site/>. Use `scripts/serve.py` rather than
`python -m http.server`: the latter speaks HTTP/1.0 and closes the socket after
every response, which some browsers mishandle on a payload the size of
`results.json`.

---

## Deployment

**Live at <https://earthyeartimepasssss.vercel.app/>** (Vercel).

The site is static and self-contained. Both targets assemble the same document
root: `site/` at the top with `data/` copied in beside it. `app.js` probes
`../data/results.json` then `data/results.json`, so the identical source works
from a plain checkout and from an assembled build.

**GitHub Pages** — `.github/workflows/pages.yml` is kept as an alternative
but runs only on manual dispatch, so it cannot fail on pushes while Pages is
switched off. To use it, enable *Settings → Pages → Source → GitHub Actions*,
then run the workflow from the Actions tab.

**Vercel** — `vercel.json` carries the build. Import the repository and accept
the defaults; no framework preset, no install step, output directory `_site`.
To preview the assembled build exactly as Vercel serves it:

```bash
mkdir -p _site && cp -r site/. _site/ && mkdir -p _site/data && cp data/results.json data/results.csv _site/data/
python scripts/serve.py _site 8766
```

Neither target needs the ephemeris kernel or any Python at deploy time — the
scan is committed, so the site is pure static assets.

---

## The founding hypothesis, and why it failed

This project began with a pair of dates: **30 June 1987** and **30 June
2026**. Both Tuesdays, exactly 39 calendar years and 2035 whole weeks apart.
The expectation was that the Moon would come back too.

| | 1987-06-30 | 2026-06-30 |
|---|---|---|
| weekday | Tuesday | Tuesday |
| θ | **41.11°** | **180.03°** |
| illuminated | 12.47% | 99.88% |
| verdict | thin waxing crescent | full moon |

**The cause is 39 = 19 + 19 + 1.** The Metonic cycle of 19 years is 235.0106
lunations — very nearly whole, which is why 38 years preserves lunar phase to
0.021 of a lunation. The extra single year adds 12.3601 lunations. That
leftover 0.36 of a cycle is **11.26 days** of slip, and it is the whole story:
the calendar and the week closed, the Moon did not.

The negative result is part of the finding, not an embarrassment. C1 and C2
are cheap — 724 years in this scan satisfy them. Satisfying C3 and C4 as well
is what is impossible.

### Two published values that do not reproduce

The founding write-up also lists Y = 1031 at ≈179.98° and Y = 4374 at
≈180.000°. Neither survives contact with the ephemeris:

- **Y = 1031** passes C1 (D = 376,565), but θ measures **74.60°** — about 105°
  from full, a waxing crescent-to-quarter Moon. The nearest C1 year that is
  genuinely close is Y = 1059, at E = 1.32°.
- **Y = 4374** fails C1 outright. D(4374) = 1,597,571, which is 3 mod 7, so
  the two ends fall on different weekdays and the year never reaches the
  ephemeris stage. Measured anyway, θ = 138.05°.

Before concluding the published values were wrong, θ was cross-checked against
`skyfield.almanac.moon_phase` and agrees to 3 × 10⁻¹⁴ degrees. Both cases are
kept as regression tests in [`tests/test_known.py`](tests/test_known.py)
rather than deleted.

### And the 179 + 437 = 616 additivity case

Recorded as exact in years, weeks (9340 + 22802 = 32142) and lunations
(2214 + 5405 = 7619). The lunations add correctly and the triple really is
D-additive. The week counts, however, match a **Julian** leap rule — every
fourth year, no century exceptions, giving L = 45, 109, 154. The Gregorian
rule that condition C2 specifies gives L = 43, 106, 149, and under it **none
of 179, 437 or 616 satisfies C1**. The arithmetic was right; the leap rule
was not.

---

## The four conditions

For integer Y years after the base epoch:

| | definition | role |
|---|---|---|
| **L(Y)** | leap days in the span, Gregorian rule (÷4 yes, ÷100 no, ÷400 yes) | |
| **D(Y)** | `365Y + L(Y)` — elapsed days | |
| **Z(Y)** | `D(Y) / 7` — weeks | |
| **K(Y)** | `round(D(Y) / 29.5305889)` — lunations | |
| **slip** | `D − K·M` — phase error in days | |
| **E(Y)** | `min over UT hours h of |θ(base + D days + h) − 180|` | |
| **C1** | Z(Y) is an exact integer | same weekday at both ends |
| **C2** | D(Y) = 365Y + L(Y) | whole calendar years; **non-selective**, the residual against Y·365.2421897 is recorded, never used to filter |
| **C3** | \|slip\| small | integer lunations |
| **C4** | E(Y) < ε | alignment at the terminal date |

θ(t) = (λ_moon − λ_sun) mod 360, geocentric apparent ecliptic longitudes.

---

## Method, and what these numbers do not mean

**Two-stage scan.** Stage 1 is pure integer arithmetic and keeps only the C1
survivors, discarding roughly six sevenths of the search space for the cost of
a modulo. Stage 2 touches the ephemeris only for those, evaluating θ across
all 24 UT hours of each terminal date. A 5000-year scan takes about 3 seconds.

**Ephemeris.** JPL DE441 via Skyfield. Apparent geocentric ecliptic longitudes
in the true ecliptic and equinox of date, light-time corrected. Mean-element
lunar theories were rejected: they drift by degrees within a thousand years of
the epoch and by tens of degrees within five thousand, which is larger than
the entire sub-degree signal being measured. `T_trop` and `M_syn` appear only
as bookkeeping — for K, slip and the tropical residual — never as a source of
position.

**The hourly grid.** E is a minimum over the 24 whole UT hours of the terminal
date, as specified. θ moves ≈0.508° per hour, so the grid alone contributes up
to **±0.254°**. An E below roughly a quarter of a degree therefore says the
full moon fell close to a whole hour, not merely that it fell on that day.
`slip` is the sampling-free companion measure; its smallest absolute value in
this scan is 0.0281 days.

**ΔT in the far future.** Converting UT to dynamical time needs ΔT, which is
extrapolated well beyond the observed record. θ moves 0.508° per hour, so ΔT
converts directly into phase uncertainty. At the far end of this scan the model
value reaches **208 hours — about 106° of lunar phase**, and its uncertainty is
plausibly of the same order.

**E values past roughly Y = 1200 are reproducible but not predictive**: exact
statements about a defined time scale, not forecasts of what a future observer
would see. Even the best entry, Y = 1803, carries 3.5 hours of ΔT — 1.80° of
phase, some 2700× its own 0.000661° miss. The results table prints ΔT beside E
for every row so the comparison cannot be missed, and shades any row past 24
hours of ΔT.

**Column accuracy.** Y, D, L, Z, K are exact integers. `slip` is exact to
double precision from the defining constant. E and θ are ephemeris-limited to
well under 0.001°, then grid-limited as above. `lit` uses the true phase
angle, not the (1 − cos θ)/2 proxy. Digital roots are exact integers,
presented as curiosities with no claim attached.

Every number on the site is produced by the committed code from the committed
`data/results.json`; `scripts/check_data.py` re-derives every integer column
in CI and fails on any drift.

---

## Conjectures

| | status | finding |
|---|---|---|
| **(a) Additivity** | falsified | S is not closed under addition: of 297 in-range pairs, 132 sums keep C1 but only 14 land in S. It cannot be closed — D itself is additive for only 53.6% of pairs, because L counts leap years in a window anchored at the base year and two such windows fail to tile a longer one whenever a skipped century falls differently. Smallest failure: D(1) + D(1) = 730 against D(2) = 731. |
| **(b) Continued fractions** | no correspondence | No convergent of M/7 predicts a member of S; the closest comes within 18.5 years against gaps of order 100. The convergents optimise Z/K freely, while a real member must also land on a Gregorian whole-year boundary — two constraints, one respected. M/7 = 295305889/70000000 is rational, so the expansion terminates after 21 terms and its final convergent *is* the theorem. |
| **(c) Gap periodicity** | inconclusive | 30 gaps, 20 distinct values, no exact period, best partial match 12%. Tripling the range tripled the gap count and *lowered* the best partial match, which is what noise does. Still too small to decide either way. |
| **C1 400-periodicity** | **proved and verified** | D(Y+400) − D(Y) = 146097 = 7 × 20871, so C1 membership repeats with period 400. 58 residues mod 400, 2116 pairs checked, 0 violations. |

---

## Repository

```
src/oeyc/
  constants.py      T_trop, M_syn, W, G400, and their exact rational forms
  calendar_math.py  leap_days, D, Z, weekday — pure integer, no ephemeris
  ephemeris.py      Skyfield/DE441 wrapper: theta, illumination, latitude
  scan.py           two-stage scan; C1 filter first, ephemeris on survivors
  series.py         build S(eps); gaps, digital roots, running minimum
  conjectures.py    additivity, continued fractions, gap periodicity
  cli.py            scan / verify / theorem
tests/              calendar, theorem, ephemeris regressions
scripts/            check_data.py — CI re-derivation of results.json
data/               results.json, results.csv (committed, so the site needs no compute)
notebooks/          01_explore.ipynb
site/               single page, vanilla JS + Chart.js from CDN
.github/workflows/  ci.yml, scan.yml, pages.yml
```

### data/results.json

`meta` (scan parameters, kernel, software versions, counts) · `theorem`
(statement, argument, minimal exact solution) · `c1_periodicity` · `summary`
(gaps, extrema, running minimum, digital-root histogram) ·
`reference_instance` (the 1987/2026 pair and the Metonic decomposition) ·
`conjectures` · `columns` · `rows` (one per C1 survivor).

---

## License

MIT — see [LICENSE](LICENSE).

Ephemeris data is JPL DE441, produced by the Jet Propulsion Laboratory,
California Institute of Technology, and is not redistributed here.
