import pytest

from ethanol_design import feedstock as F


def test_cane_juice_uses_full_cane_tfs():
    fs = F.cane_juice_feedstock(1000.0)
    assert fs.tfs_mass_frac == pytest.approx(F.CANE_TFS_MASS_FRAC)
    assert fs.fermentable_sugar_kg_s() == pytest.approx(1000.0 * 0.14)


def test_b_heavy_yields_more_molasses_but_c_heavy_has_lower_tfs():
    b = F.b_heavy_molasses_feedstock(1000.0)
    c = F.c_heavy_molasses_feedstock(1000.0)
    assert b.mass_flow_kg_s > c.mass_flow_kg_s
    assert b.tfs_mass_frac > c.tfs_mass_frac


def test_grain_starch_hydrolysis_factor_is_the_exact_molecular_weight_ratio():
    # (C6H10O5)n + n H2O -> n C6H12O6: the mass-gain factor is exactly
    # MW(glucose)/MW(starch monomer) = 180.156/162.14, not a fitted number.
    fs = F.grain_feedstock(1000.0, starch_mass_frac=0.60)
    expected = 0.60 * (180.156 / 162.14)
    assert fs.tfs_mass_frac == pytest.approx(expected, rel=1e-6)


def test_grain_feedstock_rejects_impossible_starch_fraction():
    with pytest.raises(ValueError):
        F.grain_feedstock(1000.0, starch_mass_frac=0.95)


def test_cane_juice_rejects_implausible_tfs():
    with pytest.raises(ValueError):
        F.cane_juice_feedstock(1000.0, tfs_mass_frac=0.50)
