"""Fundamental constants.

Every value here is either an exact integer property of the proleptic
Gregorian calendar or a conventional mean astronomical period.  Nothing in
this module touches an ephemeris, so it can be imported without a kernel.
"""

from __future__ import annotations

from fractions import Fraction

# --- mean astronomical periods (days) -------------------------------------
# These are *mean* values quoted to seven decimal places.  They are used for
# the integer bookkeeping (lunation count K, tropical residual); the actual
# Sun-Moon geometry always comes from the ephemeris, never from these.
T_TROP = 365.2421897  # mean tropical year
M_SYN = 29.5305889  # mean synodic month

# --- exact calendar integers ----------------------------------------------
W = 7  # days per week
G400 = 146097  # days in one 400-year Gregorian cycle
G400_WEEKS = G400 // W  # 20871 — G400 is divisible by 7, exactly

# --- exact rational forms --------------------------------------------------
# T_TROP and M_SYN are terminating decimals, hence *rational*.  The theorem
# in README.md turns on this fact, so the exact numerators are kept here.
M_SYN_EXACT = Fraction(295_305_889, 10**7)
T_TROP_EXACT = Fraction(3_652_421_897, 10**7)
GREGORIAN_MEAN_YEAR = Fraction(G400, 400)  # 365.2425 exactly

# --- base epoch ------------------------------------------------------------
BASE_YEAR = 2026
BASE_MONTH = 6
BASE_DAY = 30
BASE_WEEKDAY = "Tuesday"
BASE_THETA_CLAIMED = 180.01  # degrees, per the founding hypothesis

WEEKDAY_NAMES = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)

# --- default kernel --------------------------------------------------------
# de441_part-2 spans 1969-06-27 .. 17191-03-15, which covers the base epoch,
# the 1987 reference instance, and every terminal date out to Y = 15000.
DEFAULT_KERNEL = "de441_part-2.bsp"
KERNEL_URL = (
    "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/"
    + DEFAULT_KERNEL
)
