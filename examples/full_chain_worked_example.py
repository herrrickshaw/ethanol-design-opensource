"""End-to-end worked example: cane -> B-heavy molasses -> fermentation ->
distillation -> molecular-sieve dehydration -> spent wash, sized against a
real, publicly disclosed India ethanol-policy figure (21.75 L of ethanol
per tonne of cane crushed via the B-heavy molasses route, at 7.25% molasses
yield and 50% TFS -- see feedstock.py/fermentation.py docstrings and
docs/VALIDATION.md for the sourcing) at a representative large-distillery
throughput of 1,000 tonnes of cane crushed per day.

Run: python examples/full_chain_worked_example.py
"""
from __future__ import annotations

from ethanol_design import dehydration as DH
from ethanol_design import distillation as D
from ethanol_design import feedstock as F
from ethanol_design import fermentation as FM
from ethanol_design import stillage as S

CANE_TONNES_PER_DAY = 1000.0
CANE_KG_S = CANE_TONNES_PER_DAY * 1000.0 / 86400.0


def main() -> None:
    print(f"=== B-heavy molasses distillery: {CANE_TONNES_PER_DAY:.0f} t/day cane ===\n")

    feedstock = F.b_heavy_molasses_feedstock(CANE_KG_S)
    print(f"Feedstock: {feedstock.name}, {feedstock.mass_flow_kg_s * 86400 / 1000:.1f} t/day, "
          f"TFS {feedstock.tfs_mass_frac:.0%}")

    wash_water_kg_s = feedstock.mass_flow_kg_s * 3.0  # illustrative dilution to fermentable Brix
    ferm = FM.ferment(feedstock, wash_water_kg_s)
    liters_per_tonne_cane = ferm.ethanol_volume_flow_l_s / (CANE_KG_S / 1000.0)
    print(f"Fermentation: {ferm.ethanol_volume_flow_l_s * 86400:,.0f} L/day ethanol "
          f"({liters_per_tonne_cane:.2f} L per tonne cane -- published figure: 21.75 L/t), "
          f"wash strength {ferm.wash_ethanol_vol_pct:.1f}% v/v")

    fermenter = FM.fermenter_sizing(feedstock, wash_water_kg_s, batch_cycle_time_h=36.0)
    print(f"Fermenter: {fermenter['single_fermenter_working_volume_m3']:,.0f} m3 working volume "
          f"({fermenter['batch_cycle_time_h']:.0f} h cycle)")

    column = D.design_column(x_feed_mass_frac=ferm.wash_ethanol_mass_frac,
                             x_distillate_mass_frac=0.94, x_bottoms_mass_frac=0.0005)
    print(f"\nDistillation: {column.n_actual_stages:.0f} actual stages "
          f"(Nmin {column.n_min_stages:.1f}, Rmin {column.r_min:.2f}, R {column.r_actual:.2f}), "
          f"distillate {column.distillate_mass_frac_ethanol:.1%} w/w ethanol")

    ethanol_vapor_kg_s = ferm.ethanol_mass_flow_kg_s / column.distillate_mass_frac_ethanol
    bed = DH.size_dehydration_bed(ethanol_vapor_kg_s, inlet_water_mass_frac=1 - column.distillate_mass_frac_ethanol)
    print(f"Dehydration: {bed.bed_mass_kg:,.0f} kg sieve/bed, {bed.n_beds} beds, "
          f"{bed.bed_diameter_m:.2f} m dia x {bed.bed_height_m:.1f} m, "
          f"regen duty {bed.regen_heater_duty_kW:.0f} kW, meets BIS IS 15464 anhydrous spec: {bed.meets_bis_spec}")
    if bed.recommend_parallel_vessels:
        print(f"  (height:diameter = {bed.height_to_diameter_ratio:.1f} -- recommend splitting across "
              f"parallel vessels rather than one very slender bed)")

    stillage = S.characterize_stillage(alcohol_flow_l_s=ferm.ethanol_volume_flow_l_s,
                                        fresh_water_flow_l_s=wash_water_kg_s / 1.0)
    print(f"\nStillage: {stillage.spent_wash_flow_m3_day:,.0f} m3/day spent wash, "
          f"COD load {stillage.cod_load_kg_day:,.0f} kg/day, "
          f"meets CPCB fresh-water cap: {stillage.meets_cpcb_fresh_water_cap}")

    print(f"\n=== Validation: {liters_per_tonne_cane:.2f} L/tonne cane vs. published 21.75 L/tonne "
          f"({'MATCH' if abs(liters_per_tonne_cane - 21.75) < 0.1 else 'MISMATCH'}) ===")


if __name__ == "__main__":
    main()
