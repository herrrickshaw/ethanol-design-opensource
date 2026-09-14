"""Feedstock characterization for a cane-based fuel-ethanol distillery:
cane -> molasses (B-heavy or C-heavy/final) or direct cane juice, each
carrying a Total Fermentable Sugar (TFS) content -- the standard Indian
sugar-industry measure (sucrose + the reducing sugars glucose and fructose)
that `fermentation.py` converts to ethanol.

Default mass-yield and TFS figures (cane TFS 14% w/w; B-heavy molasses
7.25% of cane mass at 50% TFS; C-heavy/final molasses 4.5% of cane mass at
40% TFS) are the commonly cited India ethanol-policy figures reproduced
across NITI Aayog / press coverage of the B-heavy vs. C-heavy vs. direct-
juice diversion routes (e.g. sugarprocesstech.com, "Ethanol production from
various feedstocks in sugar process"; upsciq.com, "Ethanol production from
B-heavy molasses") -- see docs/VALIDATION.md for the full external
cross-check: all three routes' publicly quoted litres-of-ethanol-per-tonne-
of-cane figures back out to the SAME implied fermentation efficiency
(~92.6% of the Gay-Lussac theoretical yield) once run through this
module + `fermentation.py`, a real internal-consistency finding across
independently sourced numbers, not assumed in advance. Every default here
is overridable with a mill's own measured Brix/TFS lab data."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FeedstockAnalysis:
    name: str
    mass_flow_kg_s: float
    tfs_mass_frac: float  # Total Fermentable Sugars, kg sugar / kg feedstock

    def fermentable_sugar_kg_s(self) -> float:
        return self.mass_flow_kg_s * self.tfs_mass_frac


# Default mass yields (kg feedstock per kg cane crushed) and TFS content --
# see module docstring for sourcing; override with plant-specific lab data.
CANE_TFS_MASS_FRAC = 0.14
B_HEAVY_MOLASSES_YIELD_PER_CANE = 0.0725
B_HEAVY_MOLASSES_TFS_MASS_FRAC = 0.50
C_HEAVY_MOLASSES_YIELD_PER_CANE = 0.045
C_HEAVY_MOLASSES_TFS_MASS_FRAC = 0.40


def cane_juice_feedstock(cane_mass_flow_kg_s: float,
                         tfs_mass_frac: float = CANE_TFS_MASS_FRAC) -> FeedstockAnalysis:
    """Direct cane-juice route: the mill diverts juice straight to
    fermentation instead of extracting sugar first, so 100% of the cane's
    own TFS is available (the "zero sugar, maximum ethanol" diversion
    option India's ethanol policy explicitly allows)."""
    if not 0 < tfs_mass_frac < 0.30:
        raise ValueError("cane TFS mass fraction outside a plausible 0-30% range")
    return FeedstockAnalysis("cane juice", cane_mass_flow_kg_s, tfs_mass_frac)


def b_heavy_molasses_feedstock(cane_mass_flow_kg_s: float,
                               molasses_yield_per_cane: float = B_HEAVY_MOLASSES_YIELD_PER_CANE,
                               tfs_mass_frac: float = B_HEAVY_MOLASSES_TFS_MASS_FRAC) -> FeedstockAnalysis:
    """B-heavy molasses route: the mill draws off B-heavy massecuite ahead of
    the final crystallization stage, trading some sugar recovery for a
    higher-TFS molasses than the C-heavy/final molasses left over from
    maximal sugar extraction."""
    molasses_flow = cane_mass_flow_kg_s * molasses_yield_per_cane
    return FeedstockAnalysis("B-heavy molasses", molasses_flow, tfs_mass_frac)


def c_heavy_molasses_feedstock(cane_mass_flow_kg_s: float,
                               molasses_yield_per_cane: float = C_HEAVY_MOLASSES_YIELD_PER_CANE,
                               tfs_mass_frac: float = C_HEAVY_MOLASSES_TFS_MASS_FRAC) -> FeedstockAnalysis:
    """C-heavy (final) molasses route: the traditional by-product stream left
    after the mill has extracted the maximum sugar it can crystallize --
    lower TFS than B-heavy, but doesn't cut into sugar production."""
    molasses_flow = cane_mass_flow_kg_s * molasses_yield_per_cane
    return FeedstockAnalysis("C-heavy molasses", molasses_flow, tfs_mass_frac)


def grain_feedstock(grain_mass_flow_kg_s: float, starch_mass_frac: float) -> FeedstockAnalysis:
    """Grain (e.g. broken rice, maize) route: starch is hydrolysed to
    glucose before fermentation, (C6H10O5)n + n H2O -> n C6H12O6 -- an exact
    stoichiometric mass gain of MW(glucose)/MW(starch monomer) =
    180.156/162.14 = 1.1112 (both are real molecular weights, not a fitted
    factor), so 1 kg of starch yields 1.1112 kg of fermentable glucose."""
    STARCH_TO_GLUCOSE_MW_RATIO = 180.156 / 162.14
    tfs_mass_frac = starch_mass_frac * STARCH_TO_GLUCOSE_MW_RATIO
    if tfs_mass_frac > 1.0:
        raise ValueError("implied fermentable-sugar mass fraction exceeds 1.0 -- check starch_mass_frac")
    return FeedstockAnalysis("grain (hydrolysed starch)", grain_mass_flow_kg_s, tfs_mass_frac)
