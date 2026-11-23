"""Hand-computed values, boundaries and error paths for the ethanol design modules.

Every expected number below is derived on paper from the formula in the
module docstring (shown in the comment beside it), not read back from the
code under test. CoolProp is only used at 1 atm (the shipped default).
"""
import math

import pytest

from ethanol_design import ddgs as DD
from ethanol_design import dehydration as DH
from ethanol_design import distillation as D
from ethanol_design import feedstock as F
from ethanol_design import fermentation as FM
from ethanol_design import properties as P
from ethanol_design import starch_hydrolysis as SH
from ethanol_design import stillage as ST

# ---------------------------------------------------------------- feedstock


def test_cane_juice_defaults_and_bounds():
    f = F.cane_juice_feedstock(100.0)
    assert f.name == "cane juice"
    assert f.fermentable_sugar_kg_s() == pytest.approx(14.0)  # 100 * 0.14
    with pytest.raises(ValueError):
        F.cane_juice_feedstock(100.0, tfs_mass_frac=0.0)
    with pytest.raises(ValueError):
        F.cane_juice_feedstock(100.0, tfs_mass_frac=0.30)
    assert F.cane_juice_feedstock(100.0, tfs_mass_frac=0.299).tfs_mass_frac == 0.299


def test_molasses_routes_use_their_own_yield_and_tfs():
    b = F.b_heavy_molasses_feedstock(100.0)
    c = F.c_heavy_molasses_feedstock(100.0)
    assert b.mass_flow_kg_s == pytest.approx(7.25)
    assert b.fermentable_sugar_kg_s() == pytest.approx(3.625)  # 7.25 * 0.50
    assert c.mass_flow_kg_s == pytest.approx(4.5)
    assert c.fermentable_sugar_kg_s() == pytest.approx(1.8)  # 4.5 * 0.40
    assert b.name == "B-heavy molasses" and c.name == "C-heavy molasses"
    assert F.b_heavy_molasses_feedstock(10.0, 0.1, 0.3).fermentable_sugar_kg_s() == pytest.approx(0.3)


def test_grain_feedstock_applies_the_hydrolysis_mass_gain():
    g = F.grain_feedstock(10.0, 0.5)
    assert g.tfs_mass_frac == pytest.approx(0.5 * 180.156 / 162.14)
    assert g.tfs_mass_frac > 0.5  # water is added, so sugar mass > starch mass
    with pytest.raises(ValueError):
        F.grain_feedstock(10.0, 0.95)  # 0.95 * 1.1111 > 1


# ------------------------------------------------------------ fermentation


def test_theoretical_yields_conserve_mass():
    assert FM.THEORETICAL_ETHANOL_YIELD_KG_PER_KG_SUGAR == pytest.approx(0.51144, abs=1e-4)
    assert FM.THEORETICAL_CO2_YIELD_KG_PER_KG_SUGAR == pytest.approx(0.48856, abs=1e-4)
    total = FM.THEORETICAL_ETHANOL_YIELD_KG_PER_KG_SUGAR + FM.THEORETICAL_CO2_YIELD_KG_PER_KG_SUGAR
    assert total == pytest.approx(1.0, abs=1e-3)


def test_ferment_hand_computed_balance_at_full_efficiency():
    feed = F.FeedstockAnalysis("syrup", 20.0, 0.5)  # 10 kg/s sugar
    r = FM.ferment(feed, wash_water_kg_s=80.0, fermentation_efficiency=1.0)
    eth, co2 = 10 * 2 * 46.068 / 180.156, 10 * 2 * 44.01 / 180.156
    assert r.fermentable_sugar_kg_s == pytest.approx(10.0)
    assert r.ethanol_mass_flow_kg_s == pytest.approx(eth)
    assert r.co2_mass_flow_kg_s == pytest.approx(co2)
    assert r.ethanol_volume_flow_l_s == pytest.approx(eth / 0.789)
    wash = 20.0 + 80.0 - co2  # only CO2 leaves
    assert r.wash_ethanol_mass_frac == pytest.approx(eth / wash)
    assert r.wash_ethanol_vol_pct == pytest.approx(100.0 * (eth / 0.789) / wash)
    assert r.feedstock_name == "syrup"


def test_ferment_default_efficiency_scales_products():
    feed = F.FeedstockAnalysis("syrup", 20.0, 0.5)
    full = FM.ferment(feed, 80.0, 1.0)
    dflt = FM.ferment(feed, 80.0)
    assert dflt.fermentation_efficiency == pytest.approx(0.9257)
    assert dflt.ethanol_mass_flow_kg_s == pytest.approx(0.9257 * full.ethanol_mass_flow_kg_s)
    assert dflt.co2_mass_flow_kg_s == pytest.approx(0.9257 * full.co2_mass_flow_kg_s)


def test_ferment_efficiency_boundaries():
    feed = F.FeedstockAnalysis("syrup", 20.0, 0.5)
    for bad in (0.0, -0.1, 1.0001):
        with pytest.raises(ValueError):
            FM.ferment(feed, 80.0, bad)
    assert FM.ferment(feed, 80.0, 1.0).fermentation_efficiency == 1.0


def test_ferment_with_no_liquid_returns_zero_wash_composition():
    r = FM.ferment(F.FeedstockAnalysis("nothing", 0.0, 0.5), wash_water_kg_s=0.0)
    assert r.wash_ethanol_vol_pct == 0.0
    assert r.wash_ethanol_mass_frac == 0.0
    assert r.ethanol_mass_flow_kg_s == 0.0


def test_fermenter_sizing_hand_computed():
    feed = F.FeedstockAnalysis("syrup", 10.0, 0.5)
    out = FM.fermenter_sizing(feed, wash_water_kg_s=90.0, batch_cycle_time_h=24.0)
    # 100 kg/s * 24 h * 3600 s/h = 8.64e6 kg -> 8640 m3 at 1000 kg/m3 -> /0.85 working fraction
    assert out["single_fermenter_working_volume_m3"] == pytest.approx(8640.0 / 0.85)
    assert out["batch_cycle_time_h"] == 24.0
    smaller = FM.fermenter_sizing(feed, 90.0, 24.0, working_volume_frac=1.0)
    assert smaller["single_fermenter_working_volume_m3"] == pytest.approx(8640.0)


# ------------------------------------------------------ starch hydrolysis


def test_hydrolyze_starch_hand_computed():
    f = SH.hydrolyze_starch(10.0, 0.8, hydrolysis_efficiency=0.9)
    assert f.tfs_mass_frac == pytest.approx(0.8 * 180.156 / 162.14 * 0.9)
    assert f.mass_flow_kg_s == 10.0
    d = SH.hydrolyze_starch(10.0, 0.8)
    assert d.tfs_mass_frac == pytest.approx(0.8 * 180.156 / 162.14 * 0.95)
    assert d.name == "grain (liquefied + saccharified)"


def test_hydrolyze_starch_input_bounds():
    for bad in (0.0, 1.0, -0.1, 1.5):
        with pytest.raises(ValueError):
            SH.hydrolyze_starch(10.0, bad)
    for bad in (0.0, -0.5, 1.0001):
        with pytest.raises(ValueError):
            SH.hydrolyze_starch(10.0, 0.8, bad)
    assert SH.hydrolyze_starch(10.0, 0.8, 1.0).tfs_mass_frac < 1.0


def test_hydrolyze_starch_rejects_glucose_fraction_above_one():
    # 0.95 starch * 1.1111 * 1.0 efficiency = 1.0556 > 1
    with pytest.raises(ValueError, match="exceeds 1.0"):
        SH.hydrolyze_starch(10.0, 0.95, 1.0)


@pytest.mark.parametrize("fn,starch,name", [
    (SH.milled_rice, 0.80, "milled rice (hydrolysed)"),
    (SH.broken_rice, 0.80, "broken rice (hydrolysed)"),
    (SH.maize, 0.725, "maize (hydrolysed)"),
])
def test_named_grains_use_their_cited_starch_content(fn, starch, name):
    f = fn(10.0)
    assert f.name == name
    assert f.tfs_mass_frac == pytest.approx(starch * 180.156 / 162.14 * 0.95)
    assert fn(10.0, hydrolysis_efficiency=0.5).tfs_mass_frac == pytest.approx(starch * 180.156 / 162.14 * 0.5)


# -------------------------------------------------------------------- DDGS


def test_ddgs_hand_computed_balance():
    r = DD.characterize_ddgs(10.0, 0.6, 0.9, fermentable_sugar_consumed_kg_s=5.4)
    assert r.non_starch_solids_kg_s == pytest.approx(4.0)       # 10 * 0.4
    assert r.unconverted_starch_kg_s == pytest.approx(0.6)      # 10 * 0.6 * 0.1
    assert r.yeast_biomass_kg_s == pytest.approx(0.432)         # 5.4 * 0.08
    assert r.total_ddgs_solids_kg_s == pytest.approx(5.032)
    assert r.ddgs_flow_kg_s == pytest.approx(5.032 / 0.9)       # 10 % moisture
    assert r.ddgs_flow_tonne_day == pytest.approx(5.032 / 0.9 * 86.4)


def test_ddgs_moisture_boundaries_and_overrides():
    zero = DD.characterize_ddgs(10.0, 0.6, 0.9, 5.4, ddgs_moisture_frac=0.0)
    assert zero.ddgs_flow_kg_s == pytest.approx(zero.total_ddgs_solids_kg_s)
    for bad in (1.0, 1.5, -0.01):
        with pytest.raises(ValueError):
            DD.characterize_ddgs(10.0, 0.6, 0.9, 5.4, ddgs_moisture_frac=bad)
    y = DD.characterize_ddgs(10.0, 0.6, 0.9, 5.4, yeast_biomass_yield_kg_per_kg_sugar=0.1)
    assert y.yeast_biomass_kg_s == pytest.approx(0.54)


def test_full_conversion_leaves_no_unconverted_starch():
    r = DD.characterize_ddgs(10.0, 0.6, 1.0, 0.0)
    assert r.unconverted_starch_kg_s == 0.0
    assert r.yeast_biomass_kg_s == 0.0


# ----------------------------------------------------------------- stillage


def test_stillage_hand_computed_loads():
    r = ST.characterize_stillage(alcohol_flow_l_s=10.0, fresh_water_flow_l_s=100.0)
    assert r.spent_wash_flow_l_s == pytest.approx(120.0)             # 10 * 12
    assert r.spent_wash_flow_m3_day == pytest.approx(10368.0)        # 120 * 86.4
    assert r.cod_load_kg_day == pytest.approx(150000 * 10368 * 1e-3)
    assert r.bod_load_kg_day == pytest.approx(45000 * 10368 * 1e-3)
    assert r.bod_load_kg_day / r.cod_load_kg_day == pytest.approx(0.30)
    assert r.alcohol_flow_l_s == 10.0 and r.fresh_water_flow_l_s == 100.0


def test_stillage_cpcb_water_cap_is_inclusive():
    assert ST.characterize_stillage(10.0, 150.0).meets_cpcb_fresh_water_cap is True   # exactly 15 L/L
    assert ST.characterize_stillage(10.0, 150.1).meets_cpcb_fresh_water_cap is False
    assert ST.characterize_stillage(0.0, 5.0).meets_cpcb_fresh_water_cap is False     # infinite ratio


def test_stillage_overrides():
    r = ST.characterize_stillage(1.0, 1.0, spent_wash_ratio_l_per_l=8.0, cod_ppm=1000.0, bod_ppm=300.0)
    assert r.spent_wash_flow_l_s == 8.0
    assert r.cod_load_kg_day == pytest.approx(1000 * 8 * 86.4 * 1e-3)
    assert r.bod_load_kg_day == pytest.approx(300 * 8 * 86.4 * 1e-3)


# --------------------------------------------------------------- properties


def test_mass_mole_fraction_conversions():
    assert P.mole_frac_to_mass_frac_ethanol(0.0) == 0.0
    assert P.mole_frac_to_mass_frac_ethanol(1.0) == pytest.approx(1.0)
    # x = 0.5 -> 46.068 / (46.068 + 18.015)
    assert P.mole_frac_to_mass_frac_ethanol(0.5) == pytest.approx(46.068 / (46.068 + 18.015), abs=1e-4)
    assert P.mass_frac_to_mole_frac_ethanol(0.0) == 0.0
    for w in (0.01, 0.2, 0.5, 0.956):
        assert P.mole_frac_to_mass_frac_ethanol(P.mass_frac_to_mole_frac_ethanol(w)) == pytest.approx(w)
    # ethanol is heavier per mole, so mass fraction exceeds mole fraction
    assert P.mole_frac_to_mass_frac_ethanol(0.3) > 0.3


@pytest.mark.parametrize("x", [0.0, 1.0, -0.1, 1.1])
def test_bubble_point_rejects_x_outside_open_unit_interval(x):
    with pytest.raises(ValueError):
        P.bubble_point(x)


def test_bubble_point_physical_invariants_at_one_atm():
    pt = P.bubble_point(0.10)
    assert pt.x_ethanol_mole == 0.10
    assert 351.0 < pt.T_K < 373.15           # between ethanol and water normal boiling points
    assert pt.y_ethanol_mole > 0.10          # dilute ethanol enriches in the vapour
    assert pt.relative_volatility > 1.0
    x, y = pt.x_ethanol_mole, pt.y_ethanol_mole
    assert pt.relative_volatility == pytest.approx((y / (1 - y)) / (x / (1 - x)))
    assert P.bubble_point(0.5).T_K < pt.T_K  # more ethanol -> lower boiling point


def test_find_azeotrope_reports_a_point_where_y_equals_x():
    az = P.find_azeotrope()
    assert az.y_ethanol_mole == pytest.approx(az.x_ethanol_mole, abs=2e-3)
    assert 0.85 < az.x_ethanol_mole < 0.93
    assert 350.0 < az.T_K < 352.0


def test_find_azeotrope_raises_when_not_bracketed():
    with pytest.raises(ValueError, match="not bracketed"):
        P.find_azeotrope(lo=0.10, hi=0.50)


def test_find_azeotrope_respects_max_iter():
    coarse = P.find_azeotrope(max_iter=1)
    fine = P.find_azeotrope()
    # one bisection step leaves a much wider bracket than the converged answer
    assert abs(coarse.x_ethanol_mole - fine.x_ethanol_mole) > 1e-3


# ------------------------------------------------------------- distillation


def test_fenske_hand_computed():
    # ln[(0.9/0.1) * (0.9/0.1)] / ln 3 = ln 81 / ln 3 = 4
    assert D.fenske_min_stages(0.9, 0.1, 3.0) == pytest.approx(4.0)
    assert D.fenske_min_stages(0.99, 0.1, 3.0) > D.fenske_min_stages(0.9, 0.1, 3.0)
    assert D.fenske_min_stages(0.9, 0.1, 6.0) < D.fenske_min_stages(0.9, 0.1, 3.0)


def test_saturated_liquid_feed_rmin_hand_computed():
    # alpha=2, xF=0.2 -> y_eq = 0.4/1.2 = 1/3 ; Rmin = (0.8 - 1/3) / (1/3 - 0.2) = 3.5
    assert D.minimum_reflux_saturated_liquid_feed(0.2, 0.8, 2.0) == pytest.approx(3.5)


@pytest.mark.parametrize("alpha", [1.0, 0.8])
def test_saturated_liquid_feed_rmin_needs_alpha_above_one(alpha):
    with pytest.raises(ValueError, match="above the feed"):
        D.minimum_reflux_saturated_liquid_feed(0.2, 0.8, alpha)


def test_gilliland_hand_computed_point():
    # R=1.5, Rmin=1: X = 0.5/2.5 = 0.2; Molokanov Y = 0.46056; N = (4 + Y)/(1 - Y)
    assert D.gilliland_stages(4.0, 1.0, 1.5) == pytest.approx(8.2693, rel=1e-3)


def test_gilliland_more_reflux_means_fewer_stages_and_never_below_nmin():
    stages = [D.gilliland_stages(6.0, 2.0, r) for r in (2.2, 3.0, 5.0, 20.0)]
    assert stages == sorted(stages, reverse=True)
    assert all(n > 6.0 for n in stages)


def test_gilliland_equal_reflux_is_rejected():
    with pytest.raises(ValueError, match="must exceed"):
        D.gilliland_stages(8.0, 10.0, 10.0)


def test_relative_volatility_avg_is_the_geometric_mean_of_end_alphas():
    a_bot = P.bubble_point(0.01).relative_volatility
    a_top = P.bubble_point(0.5).relative_volatility
    assert D.relative_volatility_avg(0.01, 0.5) == pytest.approx(math.sqrt(a_bot * a_top))
    # alpha falls toward 1 as the azeotrope is approached
    assert a_top < a_bot


def test_minimum_reflux_from_vle_is_positive_and_grows_with_distillate_purity():
    r_lo = D.minimum_reflux_from_vle(0.03, 0.60)
    r_hi = D.minimum_reflux_from_vle(0.03, 0.85)
    assert 0 < r_lo < r_hi


def test_minimum_reflux_from_vle_rejects_target_beyond_azeotrope():
    with pytest.raises(ValueError, match="azeotrope"):
        D.minimum_reflux_from_vle(0.5, 0.95)


def test_design_column_rejects_misordered_compositions():
    with pytest.raises(ValueError, match="x_bottoms < x_feed < x_distillate"):
        D.design_column(0.93, 0.08, 0.0005)   # feed richer than distillate
    with pytest.raises(ValueError):
        D.design_column(0.08, 0.93, 0.08)     # bottoms == feed
    with pytest.raises(ValueError):
        D.design_column(0.0001, 0.93, 0.0005)  # feed leaner than bottoms


def test_design_column_reflux_factor_and_consistency():
    base = D.design_column(0.08, 0.90, 0.0005)
    assert base.r_actual == pytest.approx(1.3 * base.r_min)
    tight = D.design_column(0.08, 0.90, 0.0005, reflux_ratio_factor=2.0)
    assert tight.r_actual == pytest.approx(2.0 * tight.r_min)
    assert tight.n_actual_stages < base.n_actual_stages
    assert base.n_actual_stages > base.n_min_stages
    assert base.distillate_mass_frac_ethanol == pytest.approx(0.90)
    assert base.x_distillate_mole == pytest.approx(P.mass_frac_to_mole_frac_ethanol(0.90))
    assert base.x_bottoms_mole < base.x_feed_mole < base.x_distillate_mole


# ------------------------------------------------------------ dehydration

_M, _W = 1.9, 0.045
# paper sizing: water = 1.9*3600*8*0.045 ; mass = water/0.04 ; V = mass/700
_WATER = _M * 3600 * 8 * _W
_AREA = (_M / 1.5) / 0.30
_VOL = _WATER / 0.04 / 700.0
_HEIGHT = _VOL / _AREA
_DIAM = math.sqrt(4 * _AREA / math.pi)


def test_bed_geometry_hand_computed():
    r = DH.size_dehydration_bed(_M, _W)
    assert r.water_removed_per_cycle_kg == pytest.approx(2462.4)
    assert r.bed_mass_kg == pytest.approx(61560.0)
    assert r.bed_volume_m3 == pytest.approx(61560.0 / 700.0)
    assert r.bed_diameter_m == pytest.approx(_DIAM)
    assert r.bed_height_m == pytest.approx(_HEIGHT)
    assert r.height_to_diameter_ratio == pytest.approx(_HEIGHT / _DIAM)
    assert r.regen_ethanol_vapor_flow_kg_s == pytest.approx(0.2 * _M)
    assert r.regen_latent_duty_kW == pytest.approx(2462.4 * 4.19 * 1000 / (4 * 3600))
    assert math.pi * (r.bed_diameter_m / 2) ** 2 * r.bed_height_m == pytest.approx(r.bed_volume_m3)


def test_parallel_vessel_flag_flips_at_aspect_ratio_eight():
    assert _HEIGHT / _DIAM > 8.0
    assert DH.size_dehydration_bed(_M, _W).recommend_parallel_vessels is True
    # a faster design velocity shrinks the area, so the same volume gets taller -> still flagged;
    # a slower one widens the bed and drops below 8:1
    wide = DH.size_dehydration_bed(_M, _W, design_velocity_m_s=0.20)
    assert wide.height_to_diameter_ratio < 8.0
    assert wide.recommend_parallel_vessels is False


def test_min_bed_height_guard_is_a_strict_less_than():
    DH.size_dehydration_bed(_M, _W, min_bed_height_m=_HEIGHT - 1e-6)
    with pytest.raises(ValueError, match="below the practical minimum"):
        DH.size_dehydration_bed(_M, _W, min_bed_height_m=_HEIGHT + 1e-6)


def test_inlet_water_range_is_exclusive_at_both_ends():
    for bad in (0.0, -0.01, 0.20, 0.25):
        with pytest.raises(ValueError, match="plausible"):
            DH.size_dehydration_bed(_M, bad)
    assert DH.size_dehydration_bed(_M, 0.199).water_removed_per_cycle_kg > 0


def test_bed_count_boundary_is_inclusive():
    two = DH.size_dehydration_bed(_M, _W, adsorption_time_h=8.0, regen_time_h=4.0, cooldown_time_h=4.0)
    three = DH.size_dehydration_bed(_M, _W, adsorption_time_h=8.0, regen_time_h=4.0, cooldown_time_h=4.01)
    assert two.n_beds == 2
    assert three.n_beds == 3


def test_bis_spec_flag_is_inclusive_at_the_limit():
    assert DH.size_dehydration_bed(_M, _W, outlet_water_vol_frac=0.008).meets_bis_spec is True
    assert DH.size_dehydration_bed(_M, _W, outlet_water_vol_frac=0.0081).meets_bis_spec is False


def test_sensible_duty_scales_with_purge_and_vanishes_at_zero_temperature_rise():
    base = DH.size_dehydration_bed(_M, _W)
    double = DH.size_dehydration_bed(_M, _W, regen_purge_fraction_of_feed=0.40)
    assert double.regen_sensible_duty_kW == pytest.approx(2 * base.regen_sensible_duty_kW)
    assert double.regen_latent_duty_kW == pytest.approx(base.regen_latent_duty_kW)  # latent is purge-independent
    flat = DH.size_dehydration_bed(_M, _W, feed_temperature_K=498.15, regen_temperature_C=225.0)
    assert flat.regen_sensible_duty_kW == pytest.approx(0.0, abs=1e-9)
    assert base.regen_sensible_duty_kW > 0


def test_working_capacity_and_bulk_density_drive_bed_mass_and_volume():
    r = DH.size_dehydration_bed(_M, _W, working_capacity_wt_pct=8.0, sieve_bulk_density_kg_m3=800.0,
                                min_bed_height_m=0.1)
    assert r.bed_mass_kg == pytest.approx(2462.4 / 0.08)
    assert r.bed_volume_m3 == pytest.approx(2462.4 / 0.08 / 800.0)


# ------------------------------------------------- boundary / survivor tests

_EXACT_UNIT_STARCH = 162.14 / 180.156  # starch fraction whose glucose fraction is exactly 1.0 in IEEE doubles


def _const_alpha_bubble_point(alpha):
    def fake(x, P_Pa=101325.0):
        return P.VLEPoint(x_ethanol_mole=x, y_ethanol_mole=alpha * x / (1 + (alpha - 1) * x), T_K=350.0,
                          relative_volatility=alpha)
    return fake


def test_grain_feedstock_accepts_a_sugar_fraction_of_exactly_one():
    assert _EXACT_UNIT_STARCH * (180.156 / 162.14) == 1.0  # premise of this test
    assert F.grain_feedstock(10.0, _EXACT_UNIT_STARCH).tfs_mass_frac == 1.0


def test_hydrolyze_starch_accepts_a_glucose_fraction_of_exactly_one():
    assert _EXACT_UNIT_STARCH * (180.156 / 162.14) * 1.0 == 1.0
    assert SH.hydrolyze_starch(10.0, _EXACT_UNIT_STARCH, 1.0).tfs_mass_frac == 1.0


def test_hydrolyze_starch_bounds_name_the_offending_argument():
    for bad in (0.0, 1.0):
        with pytest.raises(ValueError, match="starch_mass_frac must be strictly between"):
            SH.hydrolyze_starch(10.0, bad)
    with pytest.raises(ValueError, match="hydrolysis_efficiency must be in"):
        SH.hydrolyze_starch(10.0, 0.8, 1.5)


def test_regen_heater_duty_is_sum_of_the_two_components():
    r = DH.size_dehydration_bed(_M, _W)
    assert r.regen_heater_duty_kW == pytest.approx(r.regen_sensible_duty_kW + r.regen_latent_duty_kW)
    assert r.regen_heater_duty_kW > r.regen_latent_duty_kW


def test_bed_height_exactly_at_the_minimum_is_allowed():
    h = DH.size_dehydration_bed(_M, _W).bed_height_m
    assert DH.size_dehydration_bed(_M, _W, min_bed_height_m=h).bed_height_m == h


def test_minimum_reflux_from_vle_recovers_the_constant_alpha_pinch(monkeypatch):
    monkeypatch.setattr(D, "bubble_point", _const_alpha_bubble_point(2.0))
    # with a constant-alpha curve the pinch is at the feed: Rmin = 3.5 (see saturated-feed test)
    assert D.minimum_reflux_from_vle(0.2, 0.8) == pytest.approx(3.5)
    assert D.minimum_reflux_from_vle(0.2, 0.8) == pytest.approx(
        D.minimum_reflux_saturated_liquid_feed(0.2, 0.8, 2.0))


def test_minimum_reflux_from_vle_rejects_curve_touching_the_diagonal(monkeypatch):
    def on_diagonal(x, P_Pa=101325.0):
        return P.VLEPoint(x, x, 350.0, 1.0)
    monkeypatch.setattr(D, "bubble_point", on_diagonal)
    with pytest.raises(ValueError, match="at or below the diagonal"):
        D.minimum_reflux_from_vle(0.2, 0.8)


def test_design_column_rejects_feed_equal_to_distillate():
    with pytest.raises(ValueError, match="x_bottoms < x_feed < x_distillate"):
        D.design_column(0.5, 0.5, 0.001)


def test_find_azeotrope_accepts_a_zero_at_the_bracket_end(monkeypatch):
    # (y - x) == 0 everywhere: the product f(lo)*f(hi) is exactly 0, which is not "no sign change"
    monkeypatch.setattr(P, "bubble_point", lambda x, P_Pa=101325.0: P.VLEPoint(x, x, 350.0, 1.0))
    az = P.find_azeotrope(lo=0.7, hi=0.99)
    assert 0.7 <= az.x_ethanol_mole <= 0.99
