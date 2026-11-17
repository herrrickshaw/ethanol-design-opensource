import pytest

from ethanol_design import starch_hydrolysis as SH


def test_full_efficiency_matches_the_original_stoichiometric_grain_feedstock_factor():
    # At hydrolysis_efficiency=1.0, this should reproduce feedstock.grain_feedstock()'s
    # exact stoichiometric mass-gain factor.
    fs = SH.hydrolyze_starch(1000.0, starch_mass_frac=0.72, hydrolysis_efficiency=1.0)
    expected = 0.72 * SH.STARCH_TO_GLUCOSE_MW_RATIO
    assert fs.tfs_mass_frac == pytest.approx(expected, rel=1e-9)


def test_lower_efficiency_gives_proportionally_less_fermentable_sugar():
    full = SH.hydrolyze_starch(1000.0, 0.72, hydrolysis_efficiency=1.0)
    partial = SH.hydrolyze_starch(1000.0, 0.72, hydrolysis_efficiency=0.5)
    assert partial.tfs_mass_frac == pytest.approx(full.tfs_mass_frac * 0.5, rel=1e-9)


def test_presets_use_their_cited_starch_content():
    assert SH.milled_rice(1000.0).tfs_mass_frac == pytest.approx(
        SH.MILLED_RICE_STARCH_MASS_FRAC * SH.STARCH_TO_GLUCOSE_MW_RATIO * SH.DEFAULT_HYDROLYSIS_EFFICIENCY)
    assert SH.maize(1000.0).tfs_mass_frac == pytest.approx(
        SH.MAIZE_STARCH_MASS_FRAC * SH.STARCH_TO_GLUCOSE_MW_RATIO * SH.DEFAULT_HYDROLYSIS_EFFICIENCY)


def test_rejects_implausible_starch_fraction():
    with pytest.raises(ValueError):
        SH.hydrolyze_starch(1000.0, starch_mass_frac=1.2)


def test_rejects_efficiency_outside_zero_to_one():
    with pytest.raises(ValueError):
        SH.hydrolyze_starch(1000.0, starch_mass_frac=0.72, hydrolysis_efficiency=1.5)
    with pytest.raises(ValueError):
        SH.hydrolyze_starch(1000.0, starch_mass_frac=0.72, hydrolysis_efficiency=0.0)


def test_starch_to_glucose_by_hand():
    # 1 kg starch + water -> 180.156/162.14 = 1.111114 kg glucose; x 0.80 x 0.95 = 0.844447
    from ethanol_design import starch_hydrolysis as SH
    fs = SH.broken_rice(10.0)
    assert fs.tfs_mass_frac == pytest.approx(0.844447, rel=1e-5)
    with pytest.raises(ValueError):
        SH.hydrolyze_starch(1.0, 1.0)
