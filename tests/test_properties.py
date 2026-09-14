import math

import pytest

from ethanol_design import properties as P


def test_molecular_weights_match_known_reference_values():
    assert P.MW_ETHANOL == pytest.approx(46.068, abs=0.01)
    assert P.MW_WATER == pytest.approx(18.015, abs=0.01)


def test_mass_mole_fraction_round_trip():
    w = 0.80
    x = P.mass_frac_to_mole_frac_ethanol(w)
    w_back = P.mole_frac_to_mass_frac_ethanol(x)
    assert w_back == pytest.approx(w, abs=1e-9)


def test_azeotrope_matches_published_reference_within_a_few_tenths():
    # External cross-check: CoolProp's HEOS ethanol-water mixture model, found by
    # bisection, should land close to the commonly cited textbook figure (95.6
    # wt% ethanol, 78.1 C at 1 atm -- e.g. Perry's Chemical Engineers' Handbook).
    az = P.find_azeotrope()
    w_az = P.mole_frac_to_mass_frac_ethanol(az.x_ethanol_mole)
    assert w_az == pytest.approx(P.PUBLISHED_AZEOTROPE_WT_FRAC_ETHANOL, abs=0.01)
    assert az.T_K == pytest.approx(P.PUBLISHED_AZEOTROPE_T_K, abs=1.0)


def test_relative_volatility_falls_toward_one_approaching_the_azeotrope():
    # A real, defining physical property of an azeotrope: no separation is possible
    # there, i.e. relative volatility -> 1.
    az = P.find_azeotrope()
    dilute = P.bubble_point(0.10)
    assert az.relative_volatility < dilute.relative_volatility
    assert az.relative_volatility == pytest.approx(1.0, abs=0.05)


def test_bubble_point_rejects_out_of_range_composition():
    with pytest.raises(ValueError):
        P.bubble_point(0.0)
    with pytest.raises(ValueError):
        P.bubble_point(1.0)
