import pytest

from ethanol_design import feedstock as F
from ethanol_design import fermentation as FM


def test_theoretical_yield_matches_gay_lussac_stoichiometry():
    # C6H12O6 -> 2 C2H5OH + 2 CO2: derived from real molecular weights, not typed in.
    expected = 2 * 46.068 / 180.156
    assert FM.THEORETICAL_ETHANOL_YIELD_KG_PER_KG_SUGAR == pytest.approx(expected, rel=1e-6)


@pytest.mark.parametrize("route,liters_per_tonne_cane", [
    ("b_heavy", 21.75),
    ("c_heavy", 10.8),
    ("cane_juice", 84.0),
])
def test_default_efficiency_reproduces_three_independently_published_india_figures(route, liters_per_tonne_cane):
    # External cross-check: three separately sourced India ethanol-policy figures
    # (B-heavy molasses, C-heavy molasses, direct cane-juice routes) all imply the
    # SAME fermentation efficiency once divided through by this module's own
    # theoretical yield -- see feedstock.py and fermentation.py docstrings, and
    # docs/VALIDATION.md, for the full derivation. This test reproduces each
    # published litres-per-tonne-cane figure forward from that shared efficiency.
    cane_kg = 1000.0
    feedstock = {
        "b_heavy": F.b_heavy_molasses_feedstock(cane_kg),
        "c_heavy": F.c_heavy_molasses_feedstock(cane_kg),
        "cane_juice": F.cane_juice_feedstock(cane_kg),
    }[route]
    result = FM.ferment(feedstock, wash_water_kg_s=feedstock.mass_flow_kg_s * 3)
    assert result.ethanol_volume_flow_l_s == pytest.approx(liters_per_tonne_cane, rel=1e-3)


def test_ferment_rejects_efficiency_outside_zero_to_one():
    fs = F.cane_juice_feedstock(1000.0)
    with pytest.raises(ValueError):
        FM.ferment(fs, wash_water_kg_s=2000.0, fermentation_efficiency=1.5)


def test_fermenter_sizing_scales_linearly_with_cycle_time():
    fs = F.b_heavy_molasses_feedstock(1000.0)
    short = FM.fermenter_sizing(fs, wash_water_kg_s=3000.0, batch_cycle_time_h=24.0)
    long = FM.fermenter_sizing(fs, wash_water_kg_s=3000.0, batch_cycle_time_h=48.0)
    assert long["single_fermenter_working_volume_m3"] == pytest.approx(
        2 * short["single_fermenter_working_volume_m3"])


def test_gay_lussac_mass_is_conserved_ethanol_plus_co2_equals_sugar():
    # 2 x 46.068 + 2 x 44.01 = 180.156 exactly
    assert (FM.THEORETICAL_ETHANOL_YIELD_KG_PER_KG_SUGAR
            + FM.THEORETICAL_CO2_YIELD_KG_PER_KG_SUGAR) == pytest.approx(1.0, abs=1e-12)
    assert FM.THEORETICAL_ETHANOL_YIELD_KG_PER_KG_SUGAR == pytest.approx(0.511423, rel=1e-5)


def test_b_heavy_litres_per_tonne_by_hand():
    # 1 t cane -> 72.5 kg B-heavy -> 36.25 kg TFS x 0.511423 x 0.9257 = 17.1617 kg
    # / 0.789 kg/L = 21.751 L.  NOTE: 0.9257 was itself backed out from this same
    # published 21.75 L/t figure, so this is a consistency check, not validation.
    fs = F.b_heavy_molasses_feedstock(1000.0)
    r = FM.ferment(fs, wash_water_kg_s=0.0)
    assert r.ethanol_mass_flow_kg_s == pytest.approx(17.1617, rel=1e-4)
    assert r.ethanol_volume_flow_l_s == pytest.approx(21.751, rel=1e-4)


def test_wash_mass_balance_keeps_the_ethanol_in_the_wash():
    """Sugar consumed -> ethanol + CO2; only the CO2 leaves the fermenter.

    10 kg/s molasses at 50 % TFS + 30 kg/s water, 100 % efficiency:
      ethanol = 5 x 0.511423 = 2.557117 kg/s, CO2 = 2.442883 kg/s
      wash    = 40 - 2.442883 = 37.557117 kg/s  -> ethanol 6.8086 % w/w
    """
    fs = F.FeedstockAnalysis("test molasses", 10.0, 0.50)
    r = FM.ferment(fs, wash_water_kg_s=30.0, fermentation_efficiency=1.0)
    assert r.ethanol_mass_flow_kg_s == pytest.approx(2.557117, rel=1e-6)
    assert r.co2_mass_flow_kg_s == pytest.approx(2.442883, rel=1e-6)
    assert r.wash_ethanol_mass_frac == pytest.approx(0.068086, rel=1e-4)


def test_wash_mass_balance_with_partial_efficiency():
    # unfermented sugar (here 20 %) stays dissolved in the wash
    fs = F.FeedstockAnalysis("test molasses", 10.0, 0.50)
    r = FM.ferment(fs, wash_water_kg_s=30.0, fermentation_efficiency=0.8)
    co2 = 5 * 0.8 * 0.488577
    assert r.wash_ethanol_mass_frac == pytest.approx(5 * 0.8 * 0.511423 / (40 - co2), rel=1e-4)


def test_fermenter_volume_by_hand():
    # (10 + 30) kg/s x 24 h x 3600 = 3,456,000 kg -> 3456 m3 / 0.85 = 4065.88 m3
    fs = F.FeedstockAnalysis("test", 10.0, 0.5)
    v = FM.fermenter_sizing(fs, 30.0, batch_cycle_time_h=24.0)
    assert v["single_fermenter_working_volume_m3"] == pytest.approx(4065.882, rel=1e-6)
