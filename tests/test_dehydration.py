import pytest

from ethanol_design import dehydration as DH


def test_bis_spec_constant():
    assert DH.BIS_IS_15464_MAX_WATER_VOL_FRAC == pytest.approx(0.008)


def test_typical_scale_meets_bis_spec_and_returns_positive_sizing():
    r = DH.size_dehydration_bed(ethanol_vapor_mass_flow_kg_s=1.9, inlet_water_mass_frac=0.045)
    assert r.meets_bis_spec is True
    assert r.bed_mass_kg > 0
    assert r.n_beds in (2, 3)
    assert r.regen_heater_duty_kW > 0


def test_regen_duty_is_the_sum_of_sensible_and_latent_components():
    r = DH.size_dehydration_bed(ethanol_vapor_mass_flow_kg_s=1.9, inlet_water_mass_frac=0.045)
    assert r.regen_heater_duty_kW == pytest.approx(r.regen_sensible_duty_kW + r.regen_latent_duty_kW, rel=1e-9)


def test_latent_duty_matches_the_cited_heat_of_adsorption():
    r = DH.size_dehydration_bed(ethanol_vapor_mass_flow_kg_s=1.9, inlet_water_mass_frac=0.045, regen_time_h=4.0)
    expected_latent_kW = r.water_removed_per_cycle_kg * DH.HEAT_OF_ADSORPTION_MJ_PER_KG_WATER * 1000.0 / (4.0 * 3600.0)
    assert r.regen_latent_duty_kW == pytest.approx(expected_latent_kW, rel=1e-9)


def test_latent_duty_dominates_regeneration_energy():
    # A real finding from adding this term: the latent heat of desorption is the
    # majority of regeneration duty at this module's own default parameters, not
    # a small correction -- the original sensible-heat-only model understated
    # regeneration duty roughly tenfold.
    r = DH.size_dehydration_bed(ethanol_vapor_mass_flow_kg_s=1.9, inlet_water_mass_frac=0.045)
    assert r.regen_latent_duty_kW > r.regen_sensible_duty_kW


def test_three_beds_needed_when_regen_plus_cooldown_exceeds_adsorption_time():
    r = DH.size_dehydration_bed(ethanol_vapor_mass_flow_kg_s=1.9, inlet_water_mass_frac=0.045,
                                adsorption_time_h=4.0, regen_time_h=4.0, cooldown_time_h=1.5)
    assert r.n_beds == 3


def test_tall_slender_bed_is_flagged_for_parallel_vessels():
    r = DH.size_dehydration_bed(ethanol_vapor_mass_flow_kg_s=1.9, inlet_water_mass_frac=0.045,
                                design_velocity_m_s=0.30)
    assert r.height_to_diameter_ratio > 0
    if r.height_to_diameter_ratio > 8.0:
        assert r.recommend_parallel_vessels is True


def test_undersized_bed_raises_pancake_guard():
    with pytest.raises(ValueError):
        DH.size_dehydration_bed(ethanol_vapor_mass_flow_kg_s=1.9, inlet_water_mass_frac=0.045,
                                design_velocity_m_s=0.01, min_bed_height_m=50.0)


def test_rejects_implausible_inlet_water_content():
    with pytest.raises(ValueError):
        DH.size_dehydration_bed(ethanol_vapor_mass_flow_kg_s=1.9, inlet_water_mass_frac=0.5)
