import pytest

from ethanol_design import stillage as S


def test_spent_wash_flow_scales_with_alcohol_flow_and_ratio():
    r = S.characterize_stillage(alcohol_flow_l_s=1.0, fresh_water_flow_l_s=10.0, spent_wash_ratio_l_per_l=12.0)
    assert r.spent_wash_flow_l_s == pytest.approx(12.0)


def test_cod_load_matches_hand_calculation():
    r = S.characterize_stillage(alcohol_flow_l_s=1.0, fresh_water_flow_l_s=10.0,
                                spent_wash_ratio_l_per_l=10.0, cod_ppm=150_000.0)
    spent_wash_m3_day = 10.0 * 86400.0 / 1000.0  # 864 m3/day
    expected_cod_kg_day = 150_000.0 * spent_wash_m3_day * 1e-3
    assert r.cod_load_kg_day == pytest.approx(expected_cod_kg_day, rel=1e-9)


def test_fresh_water_cap_flag():
    within_cap = S.characterize_stillage(alcohol_flow_l_s=1.0, fresh_water_flow_l_s=14.0)
    over_cap = S.characterize_stillage(alcohol_flow_l_s=1.0, fresh_water_flow_l_s=20.0)
    assert within_cap.meets_cpcb_fresh_water_cap is True
    assert over_cap.meets_cpcb_fresh_water_cap is False


def test_default_ratio_within_the_cited_8_to_15_range():
    assert 8.0 <= S.DEFAULT_SPENT_WASH_RATIO_L_PER_L_ALCOHOL <= 15.0


def test_stillage_by_hand():
    # 1 L/s alcohol x 12 = 12 L/s = 1036.8 m3/day; COD 150,000 mg/L -> 155,520 kg/day
    r = S.characterize_stillage(1.0, fresh_water_flow_l_s=15.0)
    assert r.spent_wash_flow_m3_day == pytest.approx(1036.8)
    assert r.cod_load_kg_day == pytest.approx(155520.0)
    assert r.bod_load_kg_day == pytest.approx(46656.0)
    assert r.meets_cpcb_fresh_water_cap  # exactly at the 15 L/L cap
    assert S.characterize_stillage(0.0, 1.0).meets_cpcb_fresh_water_cap is False
