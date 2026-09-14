"""Interactive fuel-ethanol distillery conceptual sizing tool.

Run with: streamlit run streamlit_app.py

All methods are cited public-domain correlations - see README.md and
docs/METHODOLOGY.md for sources.
"""
from __future__ import annotations

import streamlit as st

from ethanol_design import dehydration as DH
from ethanol_design import distillation as D
from ethanol_design import feedstock as F
from ethanol_design import fermentation as FM
from ethanol_design import properties as P
from ethanol_design import stillage as S

st.set_page_config(page_title="Ethanol Distillery Conceptual Sizing", layout="wide")
st.title("Molasses / Cane-Juice Fuel-Ethanol Distillery (open-source)")
st.caption(
    "Independent open-source conceptual sizing using public-domain correlations "
    "(Gay-Lussac stoichiometry, Fenske-Underwood-Gilliland, GPSA-style adsorber sizing) "
    "and CoolProp thermodynamics. Not derived from any proprietary vendor/client data. "
    "See README.md and docs/METHODOLOGY.md for citations, and the disclaimer at the bottom."
)

tab_feed, tab_ferm, tab_dist, tab_dehy, tab_still, tab_chain = st.tabs([
    "Feedstock", "Fermentation", "Distillation", "Dehydration", "Stillage", "Full Chain",
])

# ---------------------------------------------------------------------
with tab_feed:
    st.header("Feedstock")
    st.caption("India cane/molasses diversion routes -- see docs/METHODOLOGY.md.")
    cane_flow_tpd = st.number_input("Cane crushed (tonnes/day)", min_value=10.0, value=1000.0)
    cane_kg_s = cane_flow_tpd * 1000.0 / 86400.0
    route = st.radio("Route", ["B-heavy molasses", "C-heavy (final) molasses", "Direct cane juice"])
    if route == "B-heavy molasses":
        fs = F.b_heavy_molasses_feedstock(cane_kg_s)
    elif route == "C-heavy (final) molasses":
        fs = F.c_heavy_molasses_feedstock(cane_kg_s)
    else:
        fs = F.cane_juice_feedstock(cane_kg_s)
    st.session_state["feedstock"] = fs
    colA, colB, colC = st.columns(3)
    colA.metric("Feedstock flow", f"{fs.mass_flow_kg_s * 86400 / 1000:,.1f} t/day")
    colB.metric("TFS content", f"{fs.tfs_mass_frac:.0%}")
    colC.metric("Fermentable sugar", f"{fs.fermentable_sugar_kg_s() * 86400 / 1000:,.2f} t/day")

# ---------------------------------------------------------------------
with tab_ferm:
    st.header("Fermentation")
    if "feedstock" not in st.session_state:
        st.info("Set up the Feedstock tab first.")
    else:
        fs = st.session_state["feedstock"]
        wash_ratio = st.slider("Dilution water : feedstock mass ratio", 1.0, 6.0, 3.0)
        efficiency = st.slider("Fermentation efficiency", 0.70, 1.00, FM.DEFAULT_FERMENTATION_EFFICIENCY)
        if st.button("Run fermentation", type="primary"):
            r = FM.ferment(fs, fs.mass_flow_kg_s * wash_ratio, efficiency)
            st.session_state["ferment_result"] = r
            colA, colB, colC = st.columns(3)
            colA.metric("Ethanol produced", f"{r.ethanol_volume_flow_l_s * 86400:,.0f} L/day")
            colB.metric("Wash strength", f"{r.wash_ethanol_vol_pct:.1f}% v/v")
            colC.metric("CO2 evolved", f"{r.co2_mass_flow_kg_s * 86400 / 1000:,.1f} t/day")

# ---------------------------------------------------------------------
with tab_dist:
    st.header("Distillation (Fenske-Underwood-Gilliland)")
    az = P.find_azeotrope()
    st.caption(f"Ethanol-water azeotrope (CoolProp HEOS): "
               f"{P.mole_frac_to_mass_frac_ethanol(az.x_ethanol_mole):.1%} w/w at {az.T_K - 273.15:.1f} C")
    if "ferment_result" not in st.session_state:
        st.info("Run the Fermentation tab first.")
    else:
        r = st.session_state["ferment_result"]
        c1, c2, c3 = st.columns(3)
        with c1:
            x_dist = st.slider("Distillate target (%w/w)", 0.70, 0.955, 0.94)
        with c2:
            x_bot = st.number_input("Bottoms ethanol (%w/w)", min_value=0.0001, max_value=0.01, value=0.0005, format="%.4f")
        with c3:
            reflux_factor = st.slider("Reflux ratio / Rmin", 1.05, 2.0, 1.3)
        if st.button("Design column", type="primary"):
            try:
                col = D.design_column(r.wash_ethanol_mass_frac, x_dist, x_bot, reflux_factor)
                st.session_state["column_result"] = col
                colA, colB, colC = st.columns(3)
                colA.metric("Actual stages", f"{col.n_actual_stages:.0f}")
                colB.metric("Actual reflux ratio", f"{col.r_actual:.2f}")
                colC.metric("Distillate purity", f"{col.distillate_mass_frac_ethanol:.1%} w/w")
                st.caption(f"Nmin {col.n_min_stages:.1f}, Rmin {col.r_min:.2f}, "
                           f"alpha_avg {col.relative_volatility_avg:.2f}")
            except ValueError as e:
                st.error(str(e))

# ---------------------------------------------------------------------
with tab_dehy:
    st.header("Molecular sieve dehydration (3A zeolite VPSA)")
    if "ferment_result" not in st.session_state or "column_result" not in st.session_state:
        st.info("Run the Fermentation and Distillation tabs first.")
    else:
        r, col = st.session_state["ferment_result"], st.session_state["column_result"]
        vapor_kg_s = r.ethanol_mass_flow_kg_s / col.distillate_mass_frac_ethanol
        st.caption(f"Vapor feed to dehydration: {vapor_kg_s:.2f} kg/s "
                   f"({1 - col.distillate_mass_frac_ethanol:.1%} water)")
        adsorption_h = st.slider("Adsorption cycle time (h)", 2.0, 12.0, 8.0)
        if st.button("Size dehydration bed", type="primary"):
            try:
                bed = DH.size_dehydration_bed(vapor_kg_s, 1 - col.distillate_mass_frac_ethanol,
                                              adsorption_time_h=adsorption_h)
                colA, colB, colC = st.columns(3)
                colA.metric("Bed size", f"{bed.bed_diameter_m:.2f} m dia x {bed.bed_height_m:.1f} m")
                colB.metric("Number of beds", bed.n_beds)
                colC.metric("Regen heater duty", f"{bed.regen_heater_duty_kW:.0f} kW")
                st.write(f"Meets BIS IS 15464 anhydrous spec (<=0.8% v/v water): {bed.meets_bis_spec}")
                if bed.recommend_parallel_vessels:
                    st.warning(f"Height:diameter = {bed.height_to_diameter_ratio:.1f} -- "
                               f"recommend splitting across parallel vessels.")
            except ValueError as e:
                st.error(str(e))

# ---------------------------------------------------------------------
with tab_still:
    st.header("Stillage (spent wash / vinasse)")
    if "ferment_result" not in st.session_state:
        st.info("Run the Fermentation tab first.")
    else:
        r = st.session_state["ferment_result"]
        fresh_water = st.number_input("Fresh water use (L per L alcohol)", min_value=1.0, max_value=20.0, value=13.0)
        if st.button("Characterize stillage", type="primary"):
            sw = S.characterize_stillage(r.ethanol_volume_flow_l_s, r.ethanol_volume_flow_l_s * fresh_water)
            colA, colB, colC = st.columns(3)
            colA.metric("Spent wash", f"{sw.spent_wash_flow_m3_day:,.0f} m3/day")
            colB.metric("COD load", f"{sw.cod_load_kg_day:,.0f} kg/day")
            colC.metric("Meets CPCB cap", str(sw.meets_cpcb_fresh_water_cap))

# ---------------------------------------------------------------------
with tab_chain:
    st.header("Full chain: cane -> ethanol")
    st.caption("Runs every module in sequence on one consistent basis - see examples/full_chain_worked_example.py.")
    st.markdown(
        "This mirrors the repo's own worked example, validated against the publicly "
        "quoted **21.75 L ethanol per tonne of cane** figure for the B-heavy molasses "
        "route (see docs/VALIDATION.md). Use the individual tabs above to explore each "
        "unit interactively, or run `python examples/full_chain_worked_example.py` from "
        "a terminal for the full printed trace."
    )

st.divider()
st.caption(
    "**Disclaimer**: this tool implements textbook/public-domain conceptual sizing "
    "methods for early-stage screening only. It is not a substitute for a rigorous "
    "process simulator, fermentation kinetics model, or vendor-certified equipment "
    "data for detailed design."
)
