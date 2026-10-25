"""Batch fermentation: fermentable sugar -> ethanol + CO2, via the Gay-Lussac
stoichiometric reaction C6H12O6 -> 2 C2H5OH + 2 CO2 (any biochemistry/
fermentation-technology text, e.g. Bailey & Ollis, "Biochemical Engineering
Fundamentals", 2nd ed., McGraw-Hill, 1986). The theoretical mass yield is
DERIVED here from molecular weights (2 x 46.068 / 180.156 = 0.5114 kg
ethanol per kg glucose), not typed in from memory, to avoid the exact
transcription risk this project's sibling repos flag for every closed-form
constant.

Real fermentation never reaches the theoretical yield -- yeast also
consumes sugar for cell growth/maintenance and produces trace by-products
(glycerol, higher alcohols). `fermentation_efficiency` (default 0.926)
is the figure this module's own test suite backs out from THREE
independently sourced India ethanol-policy numbers (B-heavy, C-heavy and
direct-juice litres-of-ethanol-per-tonne-of-cane, see `feedstock.py`'s
docstring and docs/VALIDATION.md) -- all three imply the same ~92.6%
efficiency once divided through by this module's own theoretical yield, a
real cross-check, not a number chosen to make a demo work. It sits inside
the independently reported 88-98% range from Indian molasses-fermentation
studies (see docs/VALIDATION.md for those citations), so it is used as the
default rather than an arbitrarily rounder figure."""
from __future__ import annotations

from dataclasses import dataclass

from .feedstock import FeedstockAnalysis

MW_GLUCOSE = 180.156   # g/mol, C6H12O6
MW_ETHANOL = 46.068    # g/mol, C2H5OH
MW_CO2 = 44.01         # g/mol, CO2
ETHANOL_DENSITY_KG_L = 0.789  # anhydrous ethanol at ~20 C, standard reference value

# C6H12O6 -> 2 C2H5OH + 2 CO2
THEORETICAL_ETHANOL_YIELD_KG_PER_KG_SUGAR = 2 * MW_ETHANOL / MW_GLUCOSE
THEORETICAL_CO2_YIELD_KG_PER_KG_SUGAR = 2 * MW_CO2 / MW_GLUCOSE

DEFAULT_FERMENTATION_EFFICIENCY = 0.9257


@dataclass
class FermentationResult:
    feedstock_name: str
    fermentable_sugar_kg_s: float
    ethanol_mass_flow_kg_s: float
    ethanol_volume_flow_l_s: float
    co2_mass_flow_kg_s: float
    fermentation_efficiency: float
    wash_ethanol_vol_pct: float  # %v/v ethanol in the fermented "wash" fed to distillation
    wash_ethanol_mass_frac: float  # exact mass (w/w) fraction -- what distillation.py's column spec needs


def ferment(feedstock: FeedstockAnalysis, wash_water_kg_s: float,
           fermentation_efficiency: float = DEFAULT_FERMENTATION_EFFICIENCY) -> FermentationResult:
    """`wash_water_kg_s` is the dilution water mixed with the feedstock ahead
    of fermentation (molasses is typically diluted to 15-22 degrees Brix
    before pitching yeast; cane juice needs little or none) -- it sets the
    fermented wash's ethanol %v/v, which in turn sets `distillation.py`'s
    feed composition."""
    if not 0 < fermentation_efficiency <= 1.0:
        raise ValueError("fermentation_efficiency must be in (0, 1]")
    sugar = feedstock.fermentable_sugar_kg_s()
    ethanol_kg_s = sugar * THEORETICAL_ETHANOL_YIELD_KG_PER_KG_SUGAR * fermentation_efficiency
    co2_kg_s = sugar * THEORETICAL_CO2_YIELD_KG_PER_KG_SUGAR * fermentation_efficiency
    ethanol_l_s = ethanol_kg_s / ETHANOL_DENSITY_KG_L

    # Consumed sugar becomes ethanol + CO2 (mass-conserving); only the CO2 leaves the
    # fermenter, the ethanol stays in the wash.
    total_wash_kg_s = feedstock.mass_flow_kg_s + wash_water_kg_s - co2_kg_s
    # Approximate wash volume as mass/density of a dilute (mostly water) mixture --
    # adequate for a conceptual %v/v estimate, not a precision hydrometer reading.
    wash_water_like_density_kg_l = 1.0
    wash_vol_l_s = total_wash_kg_s / wash_water_like_density_kg_l
    wash_vol_pct = 100.0 * ethanol_l_s / wash_vol_l_s if wash_vol_l_s > 0 else 0.0
    wash_mass_frac = ethanol_kg_s / total_wash_kg_s if total_wash_kg_s > 0 else 0.0

    return FermentationResult(
        feedstock_name=feedstock.name,
        fermentable_sugar_kg_s=sugar,
        ethanol_mass_flow_kg_s=ethanol_kg_s,
        ethanol_volume_flow_l_s=ethanol_l_s,
        co2_mass_flow_kg_s=co2_kg_s,
        fermentation_efficiency=fermentation_efficiency,
        wash_ethanol_vol_pct=wash_vol_pct,
        wash_ethanol_mass_frac=wash_mass_frac,
    )


def fermenter_sizing(feedstock: FeedstockAnalysis, wash_water_kg_s: float,
                     batch_cycle_time_h: float, working_volume_frac: float = 0.85) -> dict:
    """Number and volume of batch fermenters needed for continuous feedstock
    throughput at a given batch cycle time (fermentation itself, typically
    24-48 h for molasses per the operating conditions this module's
    docs/VALIDATION.md cites, plus fill/empty/clean turnaround).
    `working_volume_frac` leaves headspace for CO2 disengagement and foam,
    a standard fermenter-design allowance (e.g. Bailey & Ollis ch. 9)."""
    total_feed_kg_s = feedstock.mass_flow_kg_s + wash_water_kg_s
    batch_feed_kg = total_feed_kg_s * batch_cycle_time_h * 3600.0
    # Approximate the batch mixture as water-like density for a conceptual volume estimate.
    batch_volume_m3 = batch_feed_kg / 1000.0 / working_volume_frac
    return {"batch_cycle_time_h": batch_cycle_time_h, "single_fermenter_working_volume_m3": batch_volume_m3,
            "note": "one fermenter of this size, filled and emptied every cycle, sustains the given "
                    "continuous feed rate; add a second (or more) in staggered rotation for turnaround/cleaning margin"}
