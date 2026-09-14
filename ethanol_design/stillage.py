"""Spent wash (vinasse) mass balance and effluent characterization for a
molasses-based distillery -- the still bottoms left over once ethanol is
stripped out, India's best-known distillery environmental-compliance issue.

Generation ratio (8-15 L spent wash per L of alcohol produced, this
module's default 12 L/L is the midpoint) and the CPCB (Central Pollution
Control Board) fresh-water consumption cap (15 L per L of alcohol) are
both from CPCB's own "Charter for Zero Liquid Discharge (ZLD) in Molasses
Based Distilleries" and are widely reproduced in the distillery-effluent
literature (e.g. teamonebiotech.com, "How to Treat Distillery Effluent";
wealthywaste.com, "Management of Spent Wash in Distilleries"). COD range
(110,000-205,000 ppm, this module's default 150,000 ppm is an
illustrative mid-range value, NOT a derived average) is the commonly
cited range for raw distillery spent wash in the same literature.

This module is a mass-balance/characterization tool, not an effluent-
treatment-plant sizing tool -- CPCB's own recommended ZLD route
(concentration/incineration with energy recovery, or anaerobic digestion
to biogas followed by aerobic polishing) is a real, separate design
problem. Note for a reader of this project's sibling repos: vinasse is
itself a genuine anaerobic-digestion feedstock (its very high COD is
exactly what an AD process consumes) -- sizing that digester is the
`cbg-design-opensource` sibling repo's job (`anaerobic_digestion.py`),
not duplicated here."""
from __future__ import annotations

from dataclasses import dataclass

DEFAULT_SPENT_WASH_RATIO_L_PER_L_ALCOHOL = 12.0
CPCB_MAX_FRESH_WATER_L_PER_L_ALCOHOL = 15.0
DEFAULT_COD_PPM = 150_000.0
DEFAULT_BOD_PPM = 45_000.0  # BOD is commonly cited as roughly 30% of COD for raw spent wash


@dataclass
class StillageResult:
    alcohol_flow_l_s: float
    spent_wash_flow_l_s: float
    spent_wash_flow_m3_day: float
    cod_load_kg_day: float
    bod_load_kg_day: float
    fresh_water_flow_l_s: float
    meets_cpcb_fresh_water_cap: bool


def characterize_stillage(
    alcohol_flow_l_s: float,
    fresh_water_flow_l_s: float,
    spent_wash_ratio_l_per_l: float = DEFAULT_SPENT_WASH_RATIO_L_PER_L_ALCOHOL,
    cod_ppm: float = DEFAULT_COD_PPM,
    bod_ppm: float = DEFAULT_BOD_PPM,
) -> StillageResult:
    spent_wash_l_s = alcohol_flow_l_s * spent_wash_ratio_l_per_l
    spent_wash_m3_day = spent_wash_l_s * 86400.0 / 1000.0
    # ppm (mg/L) x m3/day x 1e-3 = kg/day
    cod_kg_day = cod_ppm * spent_wash_m3_day * 1e-3
    bod_kg_day = bod_ppm * spent_wash_m3_day * 1e-3
    fresh_water_ratio = fresh_water_flow_l_s / alcohol_flow_l_s if alcohol_flow_l_s > 0 else float("inf")

    return StillageResult(
        alcohol_flow_l_s=alcohol_flow_l_s,
        spent_wash_flow_l_s=spent_wash_l_s,
        spent_wash_flow_m3_day=spent_wash_m3_day,
        cod_load_kg_day=cod_kg_day,
        bod_load_kg_day=bod_kg_day,
        fresh_water_flow_l_s=fresh_water_flow_l_s,
        meets_cpcb_fresh_water_cap=fresh_water_ratio <= CPCB_MAX_FRESH_WATER_L_PER_L_ALCOHOL,
    )
