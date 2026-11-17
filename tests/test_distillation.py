import math

import pytest

from ethanol_design import distillation as D


def test_gilliland_reproduces_its_own_two_limiting_cases():
    n_min, r_min = 8.0, 10.0
    # R -> Rmin: infinite stages (the classic pinch-point limit)
    n_near_rmin = D.gilliland_stages(n_min, r_min, r_min * 1.0001)
    assert n_near_rmin > 100
    # R -> infinity: total reflux, N -> Nmin
    n_huge_r = D.gilliland_stages(n_min, r_min, r_min * 1000)
    assert n_huge_r == pytest.approx(n_min, rel=0.01)


def test_gilliland_rejects_reflux_at_or_below_minimum():
    with pytest.raises(ValueError):
        D.gilliland_stages(8.0, 10.0, 9.5)


def test_relative_volatility_exceeds_one_below_the_azeotrope():
    alpha = D.relative_volatility_avg(x_bottoms_mole=0.001, x_distillate_mole=0.70)
    assert alpha > 1.0


def test_design_column_gives_a_plausible_stage_count_for_a_typical_wash():
    # A typical fermented wash (~8 wt% ethanol) distilled up toward the azeotrope --
    # real industrial beer/rectifier columns commonly run in the 15-30 actual-stage
    # range for this duty (a plausibility check, not a precision-matched benchmark).
    r = D.design_column(x_feed_mass_frac=0.08, x_distillate_mass_frac=0.93, x_bottoms_mass_frac=0.0005)
    assert 5 < r.n_actual_stages < 40
    assert r.r_actual > r.r_min > 0
    assert r.n_actual_stages > r.n_min_stages


def test_design_column_rejects_out_of_order_compositions():
    with pytest.raises(ValueError):
        D.design_column(x_feed_mass_frac=0.50, x_distillate_mass_frac=0.30, x_bottoms_mass_frac=0.001)


def test_richer_distillate_target_needs_more_stages():
    lean = D.design_column(x_feed_mass_frac=0.08, x_distillate_mass_frac=0.85, x_bottoms_mass_frac=0.0005)
    rich = D.design_column(x_feed_mass_frac=0.08, x_distillate_mass_frac=0.94, x_bottoms_mass_frac=0.0005)
    assert rich.n_actual_stages > lean.n_actual_stages


def test_fenske_hand_value():
    # ln((0.8/0.2) x (0.99/0.01)) / ln 2 = ln(396)/ln(2) = 8.62936
    assert D.fenske_min_stages(0.8, 0.01, 2.0) == pytest.approx(8.62936, rel=1e-5)


def test_underwood_feed_pinch_constant_alpha_hand_value():
    # alpha 2, xF 0.1: y* = 0.2/1.1 = 0.181818; Rmin = (0.8 - 0.181818)/(0.181818 - 0.1) = 7.5556
    assert D.minimum_reflux_saturated_liquid_feed(0.1, 0.8, 2.0) == pytest.approx(7.55556, rel=1e-5)


def test_molokanov_gilliland_hand_value():
    # Nmin 8.62936, Rmin 7.55556, R = 1.3 Rmin = 9.82222 -> X = 0.209446,
    # Y = 1 - exp[(1+54.4X)/(11+117.2X) x (X-1)/sqrt(X)] = 0.452439 -> N = 16.5859
    assert D.gilliland_stages(8.62936, 7.55556, 9.82222) == pytest.approx(16.5859, rel=1e-4)


# Ethanol-water VLE at 1 atm, textbook data (Perry's / McCabe-Smith-Harriott table)
_PERRY_X = [0.0190, 0.0721, 0.0966, 0.1238, 0.1661, 0.2337, 0.3273, 0.3965, 0.5079, 0.5732, 0.6763, 0.7472]
_PERRY_Y = [0.1700, 0.3891, 0.4375, 0.4704, 0.5089, 0.5445, 0.5826, 0.6122, 0.6564, 0.6841, 0.7385, 0.7815]


def _rmin_upper_bound_from_perry(x_feed, x_dist):
    """McCabe-Thiele Rmin from the tabulated curve: the steepest line from (xD, xD)
    to any equilibrium point with x >= xF. Linear interpolation lies BELOW the
    (concave) true curve, so this over-estimates Rmin -- an upper bound."""
    import numpy as np
    xs = [x_feed] + [x for x in _PERRY_X if x_feed < x < x_dist]
    slope = max((x_dist - np.interp(x, _PERRY_X, _PERRY_Y)) / (x_dist - x) for x in xs)
    return slope / (1 - slope)


def test_minimum_reflux_not_overstated_versus_textbook_vle():
    """8 wt% wash to 94 wt% distillate: textbook McCabe-Thiele gives Rmin <= ~3.25.

    A single geometric-mean alpha (~3.6) badly under-predicts the dilute-end
    equilibrium (real alpha ~10 at x=0.033), so a feed-pinch Rmin built from it
    comes out ~3x too high.
    """
    c = D.design_column(x_feed_mass_frac=0.08, x_distillate_mass_frac=0.94, x_bottoms_mass_frac=0.0005)
    bound = _rmin_upper_bound_from_perry(c.x_feed_mole, c.x_distillate_mole)
    assert bound == pytest.approx(3.25, abs=0.05)
    assert 1.5 < c.r_min <= bound
