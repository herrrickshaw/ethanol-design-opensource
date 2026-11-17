"""Binary ethanol-water distillation, shortcut (Fenske-Underwood-Gilliland,
"FUG") method -- the standard conceptual-design sizing approach for a binary
or pseudo-binary column (any distillation text, e.g. Seader, Henley &
Roper, "Separation Process Principles", 3rd ed., Wiley, ch. 5; McCabe,
Smith & Harriott, "Unit Operations of Chemical Engineering").

Relative volatility comes from `properties.py`'s CoolProp HEOS bubble-point
flash (the actual ethanol-water equation of state), evaluated at the column's
bottoms and distillate compositions and geometrically averaged -- not a
single textbook alpha value copied from memory, and it correctly falls
toward 1.0 as the column approaches the azeotrope, which a constant-alpha
assumption would miss.

Minimum reflux ratio (`minimum_reflux_saturated_liquid_feed`) is derived
here directly from the McCabe-Thiele pinch-point geometry at the feed stage
(rectifying operating line meets the equilibrium curve exactly at the feed
composition, for a saturated-liquid feed) rather than quoting Underwood's
published formula from memory -- the same "derive, don't recall" choice
this project's sibling repos make for `mche_tube_design.py`'s heat-transfer
coefficients and the financial-analysis-toolkit repo makes for its
geometric Asian option. The number-of-stages step (`gilliland_stages`) uses
the Molokanov et al. (1972) analytical fit to Gilliland's original
empirical correlation -- a real, widely reproduced closed form (e.g.
Seader/Henley eq. 5-48), verified against its own two limiting boundary
cases in this module's test suite (R->Rmin gives infinite stages, R->infinity
gives Nmin stages) rather than only trusted by inspection."""
from __future__ import annotations

import math
from dataclasses import dataclass

from .properties import bubble_point, mass_frac_to_mole_frac_ethanol, mole_frac_to_mass_frac_ethanol


@dataclass
class ColumnDesign:
    x_feed_mole: float
    x_distillate_mole: float
    x_bottoms_mole: float
    relative_volatility_avg: float
    n_min_stages: float
    r_min: float
    r_actual: float
    n_actual_stages: float
    distillate_mass_frac_ethanol: float


def _alpha_at(x_mole: float, P_Pa: float) -> float:
    return bubble_point(x_mole, P_Pa).relative_volatility


def relative_volatility_avg(x_bottoms_mole: float, x_distillate_mole: float, P_Pa: float = 101325.0) -> float:
    """Geometric mean of the relative volatility evaluated at the column's
    bottoms and distillate compositions -- the standard way to collapse a
    composition-varying alpha into one Fenske-equation number (Seader/
    Henley eq. 5-39 uses the same top/bottom geometric-mean convention)."""
    a_top = _alpha_at(x_distillate_mole, P_Pa)
    a_bot = _alpha_at(x_bottoms_mole, P_Pa)
    return math.sqrt(a_top * a_bot)


def fenske_min_stages(x_distillate_mole: float, x_bottoms_mole: float, alpha_avg: float) -> float:
    """Minimum theoretical stages at total reflux (Fenske equation)."""
    num = math.log((x_distillate_mole / (1 - x_distillate_mole)) * ((1 - x_bottoms_mole) / x_bottoms_mole))
    return num / math.log(alpha_avg)


def minimum_reflux_saturated_liquid_feed(x_feed_mole: float, x_distillate_mole: float, alpha_avg: float) -> float:
    """Rmin for a saturated-liquid (bubble-point) feed: at minimum reflux the
    rectifying operating line's pinch point sits exactly at the feed
    composition, where it must touch the equilibrium curve
    y_eq(xF) = alpha*xF / (1 + (alpha-1)*xF). Equating that to the
    rectifying line xD/(R+1) + R/(R+1)*xF and solving for R gives
    Rmin = (xD - y_eq) / (y_eq - xF), derived directly rather than quoted."""
    y_eq_at_feed = alpha_avg * x_feed_mole / (1 + (alpha_avg - 1) * x_feed_mole)
    if y_eq_at_feed <= x_feed_mole:
        raise ValueError("equilibrium curve does not lie above the feed composition -- "
                          "check that x_feed is below the azeotrope/relative volatility > 1")
    return (x_distillate_mole - y_eq_at_feed) / (y_eq_at_feed - x_feed_mole)


def minimum_reflux_from_vle(x_feed_mole: float, x_distillate_mole: float, P_Pa: float = 101325.0,
                            n_points: int = 120) -> float:
    """McCabe-Thiele Rmin for a saturated-liquid feed using the real (CoolProp HEOS)
    equilibrium curve: the steepest rectifying line from (xD, xD) that touches the
    curve anywhere in [xF, xD). Captures both the feed pinch and the tangent pinch
    that ethanol-water's non-ideal curve produces; a single averaged alpha cannot."""
    best = 0.0
    for i in range(n_points):
        x = x_feed_mole + (x_distillate_mole - x_feed_mole) * i / n_points
        y = bubble_point(x, P_Pa).y_ethanol_mole
        if y <= x:
            raise ValueError("equilibrium curve at or below the diagonal between feed and distillate -- "
                             "distillate target is at/beyond the azeotrope")
        best = max(best, (x_distillate_mole - y) / (x_distillate_mole - x))
    return best / (1 - best)


def gilliland_stages(n_min: float, r_min: float, r_actual: float) -> float:
    """Molokanov et al. (1972) analytical fit to the Gilliland correlation:
    X = (R-Rmin)/(R+1), Y = 1 - exp[(1+54.4X)/(11+117.2X) * (X-1)/sqrt(X)],
    Y = (N-Nmin)/(N+1) solved for N."""
    if r_actual <= r_min:
        raise ValueError("actual reflux ratio must exceed the minimum reflux ratio")
    X = (r_actual - r_min) / (r_actual + 1)
    if X <= 0:
        return n_min
    Y = 1 - math.exp(((1 + 54.4 * X) / (11 + 117.2 * X)) * ((X - 1) / math.sqrt(X)))
    return (n_min + Y) / (1 - Y)


def design_column(x_feed_mass_frac: float, x_distillate_mass_frac: float, x_bottoms_mass_frac: float,
                  reflux_ratio_factor: float = 1.3, P_Pa: float = 101325.0) -> ColumnDesign:
    """Full FUG shortcut design from mass-fraction (%w/w) column specs, the
    units a plant's own lab data is reported in. `reflux_ratio_factor` sets
    actual reflux as a multiple of Rmin -- 1.2-1.5x Rmin is the standard
    conceptual-design operating range (McCabe, Smith & Harriott, ch. 18)."""
    x_feed = mass_frac_to_mole_frac_ethanol(x_feed_mass_frac)
    x_dist = mass_frac_to_mole_frac_ethanol(x_distillate_mass_frac)
    x_bot = mass_frac_to_mole_frac_ethanol(x_bottoms_mass_frac)
    if not (x_bot < x_feed < x_dist):
        raise ValueError("require x_bottoms < x_feed < x_distillate (in mole fraction)")

    alpha_avg = relative_volatility_avg(x_bot, x_dist, P_Pa)
    n_min = fenske_min_stages(x_dist, x_bot, alpha_avg)
    r_min = minimum_reflux_from_vle(x_feed, x_dist, P_Pa)
    r_actual = reflux_ratio_factor * r_min
    n_actual = gilliland_stages(n_min, r_min, r_actual)

    return ColumnDesign(
        x_feed_mole=x_feed, x_distillate_mole=x_dist, x_bottoms_mole=x_bot,
        relative_volatility_avg=alpha_avg, n_min_stages=n_min, r_min=r_min,
        r_actual=r_actual, n_actual_stages=n_actual,
        distillate_mass_frac_ethanol=mole_frac_to_mass_frac_ethanol(x_dist),
    )
