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
