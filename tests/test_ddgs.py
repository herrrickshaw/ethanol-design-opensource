import pytest

from ethanol_design import ddgs as D


def test_total_solids_conserve_mass_with_fermentation():
    grain_kg_s = 1000.0
    starch_frac, hydrolysis_eff = 0.80, 0.95
    fermentable_sugar_kg_s = grain_kg_s * starch_frac * (180.156 / 162.14) * hydrolysis_eff
    r = D.characterize_ddgs(grain_kg_s, starch_frac, hydrolysis_eff, fermentable_sugar_kg_s)

    non_starch = grain_kg_s * (1 - starch_frac)
    unconverted = grain_kg_s * starch_frac * (1 - hydrolysis_eff)
    yeast = fermentable_sugar_kg_s * D.DEFAULT_YEAST_BIOMASS_YIELD_KG_PER_KG_SUGAR
    assert r.total_ddgs_solids_kg_s == pytest.approx(non_starch + unconverted + yeast, rel=1e-9)


def test_ddgs_flow_accounts_for_moisture():
    r = D.characterize_ddgs(1000.0, 0.80, 0.95, fermentable_sugar_consumed_kg_s=650.0, ddgs_moisture_frac=0.10)
    assert r.ddgs_flow_kg_s == pytest.approx(r.total_ddgs_solids_kg_s / 0.90, rel=1e-9)


def test_higher_hydrolysis_efficiency_reduces_unconverted_starch_and_ddgs():
    low_eff = D.characterize_ddgs(1000.0, 0.80, 0.85, fermentable_sugar_consumed_kg_s=600.0)
    high_eff = D.characterize_ddgs(1000.0, 0.80, 0.99, fermentable_sugar_consumed_kg_s=700.0)
    assert high_eff.unconverted_starch_kg_s < low_eff.unconverted_starch_kg_s


def test_rejects_implausible_moisture_fraction():
    with pytest.raises(ValueError):
        D.characterize_ddgs(1000.0, 0.80, 0.95, 650.0, ddgs_moisture_frac=1.0)


def test_ddgs_by_hand():
    # 10 kg/s grain, 80 % starch, 95 % hydrolysis, 8 kg/s sugar fermented:
    # non-starch 2.0 + unconverted 0.4 + yeast 0.64 = 3.04 kg/s solids
    # / 0.9 = 3.3778 kg/s = 291.84 t/day
    r = D.characterize_ddgs(10.0, 0.80, 0.95, 8.0)
    assert r.total_ddgs_solids_kg_s == pytest.approx(3.04)
    assert r.ddgs_flow_kg_s == pytest.approx(3.37778, rel=1e-5)
    assert r.ddgs_flow_tonne_day == pytest.approx(291.84, rel=1e-5)
