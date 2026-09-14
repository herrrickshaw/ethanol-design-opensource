"""End-to-end worked example: grain -> starch hydrolysis -> fermentation
-> distillation -> dehydration -> DDGS, for India's three main grain-
ethanol feedstocks (milled rice, broken rice, maize), cross-checked
against real, publicly reported litres-of-ethanol-per-tonne-of-grain
figures (see docs/VALIDATION.md).

Run: python examples/grain_worked_example.py
"""
from __future__ import annotations

from ethanol_design import dehydration as DH
from ethanol_design import distillation as D
from ethanol_design import ddgs as DG
from ethanol_design import fermentation as FM
from ethanol_design import starch_hydrolysis as SH

GRAIN_TONNES_PER_DAY = 500.0
GRAIN_KG_S = GRAIN_TONNES_PER_DAY * 1000.0 / 86400.0

PUBLISHED_L_PER_TONNE = {"milled rice": 450.0, "broken rice": 440.0, "maize": 380.0}
PRESETS = {"milled rice": (SH.milled_rice, SH.MILLED_RICE_STARCH_MASS_FRAC),
          "broken rice": (SH.broken_rice, SH.BROKEN_RICE_STARCH_MASS_FRAC),
          "maize": (SH.maize, SH.MAIZE_STARCH_MASS_FRAC)}


def run_grain(name: str) -> None:
    preset_fn, starch_frac = PRESETS[name]
    feed = preset_fn(GRAIN_KG_S)

    wash_water_kg_s = feed.mass_flow_kg_s * 3.0
    ferm = FM.ferment(feed, wash_water_kg_s)
    l_per_tonne = ferm.ethanol_volume_flow_l_s / (GRAIN_KG_S / 1000.0)
    published = PUBLISHED_L_PER_TONNE[name]

    column = D.design_column(ferm.wash_ethanol_mass_frac, 0.94, 0.0005)
    ethanol_vapor_kg_s = ferm.ethanol_mass_flow_kg_s / column.distillate_mass_frac_ethanol
    bed = DH.size_dehydration_bed(ethanol_vapor_kg_s, 1 - column.distillate_mass_frac_ethanol)
    dg = DG.characterize_ddgs(feed.mass_flow_kg_s, starch_frac, SH.DEFAULT_HYDROLYSIS_EFFICIENCY,
                              ferm.fermentable_sugar_kg_s)

    print(f"\n=== {name}: {GRAIN_TONNES_PER_DAY:.0f} t/day ===")
    print(f"Fermentation: {l_per_tonne:.1f} L/tonne (published: {published:.1f} L/tonne, "
          f"ratio {l_per_tonne / published:.3f})")
    print(f"Distillation: {column.n_actual_stages:.0f} stages, distillate {column.distillate_mass_frac_ethanol:.1%} w/w")
    print(f"Dehydration: {bed.bed_mass_kg:,.0f} kg sieve, {bed.n_beds} beds, meets BIS spec: {bed.meets_bis_spec}")
    print(f"DDGS co-product: {dg.ddgs_flow_tonne_day:,.1f} t/day "
          f"(non-starch solids {dg.non_starch_solids_kg_s * 86.4:,.1f} t/day, "
          f"unconverted starch {dg.unconverted_starch_kg_s * 86.4:,.1f} t/day, "
          f"yeast {dg.yeast_biomass_kg_s * 86.4:,.1f} t/day)")


def main() -> None:
    print("=" * 78)
    print("GRAIN-BASED FUEL-ETHANOL WORKED EXAMPLE (India: milled rice, broken rice, maize)")
    print("=" * 78)
    for name in PRESETS:
        run_grain(name)

    print("\n=== Honest finding: this model consistently OVERSHOOTS published real-plant "
          "yields (13-21%), since its default hydrolysis efficiency (95%, a lab-optimized "
          "figure) combined with the molasses-calibrated fermentation efficiency (92.6%) "
          "outperforms what real full-scale grain distilleries report. See docs/VALIDATION.md. ===")


if __name__ == "__main__":
    main()
