"""Distillers Dried Grains with Solubles (DDGS): a grain-based
distillery's real, valuable co-product, in place of the spent wash/
vinasse a molasses distillery produces (see `stillage.py`'s docstring
for that pathway). Everything in the grain that AREN'T fermented to
ethanol -- protein, fiber, oil, ash, plus any starch the
`starch_hydrolysis.py` step didn't convert, plus the yeast cell mass
grown during fermentation -- ends up in the stillage, which is
centrifuged, evaporated and dried to the commercial DDGS product.

This module computes DDGS output from an exact mass balance on those
components (what doesn't leave as ethanol/CO2 must leave as solids or
water), not a recalled "DDGS yield is roughly Nx the original grain"
rule of thumb -- the real yield ratio depends on starch content and
hydrolysis/fermentation efficiency, so deriving it directly is both
more honest and more general than quoting one remembered multiplier.

Yeast biomass yield (`yeast_biomass_yield_kg_per_kg_sugar`, default
0.08) is a standard bioprocess-engineering parameter for anaerobic/
microaerobic Saccharomyces cerevisiae ethanolic fermentation -- Bailey
& Ollis, "Biochemical Engineering Fundamentals", 2nd ed. (already cited
in `fermentation.py` for the Gay-Lussac stoichiometry) gives typical
biomass yield coefficients in the 0.05-0.12 g dry cell mass / g sugar
consumed range for this fermentation mode; this module defaults to the
range's midpoint. Commercial DDGS is dried to 8-12% moisture (IMSBC
bulk-cargo code caps it at under 13%; feed-industry sources commonly
cite 8-12% as the target range) -- this module defaults to 10%."""
from __future__ import annotations

from dataclasses import dataclass

DEFAULT_YEAST_BIOMASS_YIELD_KG_PER_KG_SUGAR = 0.08
DEFAULT_DDGS_MOISTURE_FRAC = 0.10


@dataclass
class DDGSResult:
    non_starch_solids_kg_s: float
    unconverted_starch_kg_s: float
    yeast_biomass_kg_s: float
    total_ddgs_solids_kg_s: float
    ddgs_flow_kg_s: float
    ddgs_flow_tonne_day: float


def characterize_ddgs(grain_mass_flow_kg_s: float, starch_mass_frac: float, hydrolysis_efficiency: float,
                      fermentable_sugar_consumed_kg_s: float,
                      yeast_biomass_yield_kg_per_kg_sugar: float = DEFAULT_YEAST_BIOMASS_YIELD_KG_PER_KG_SUGAR,
                      ddgs_moisture_frac: float = DEFAULT_DDGS_MOISTURE_FRAC) -> DDGSResult:
    """`fermentable_sugar_consumed_kg_s` is the actual glucose that reached
    the fermenter (`starch_hydrolysis.hydrolyze_starch()`'s output mass
    flow), used here to size yeast growth -- pass the same value used to
    call `fermentation.ferment()` so the two stay consistent."""
    if not 0 <= ddgs_moisture_frac < 1.0:
        raise ValueError("ddgs_moisture_frac must be in [0, 1)")

    non_starch_solids = grain_mass_flow_kg_s * (1 - starch_mass_frac)
    unconverted_starch = grain_mass_flow_kg_s * starch_mass_frac * (1 - hydrolysis_efficiency)
    yeast_biomass = fermentable_sugar_consumed_kg_s * yeast_biomass_yield_kg_per_kg_sugar

    total_solids = non_starch_solids + unconverted_starch + yeast_biomass
    ddgs_flow_kg_s = total_solids / (1 - ddgs_moisture_frac)

    return DDGSResult(
        non_starch_solids_kg_s=non_starch_solids,
        unconverted_starch_kg_s=unconverted_starch,
        yeast_biomass_kg_s=yeast_biomass,
        total_ddgs_solids_kg_s=total_solids,
        ddgs_flow_kg_s=ddgs_flow_kg_s,
        ddgs_flow_tonne_day=ddgs_flow_kg_s * 86.4,
    )
