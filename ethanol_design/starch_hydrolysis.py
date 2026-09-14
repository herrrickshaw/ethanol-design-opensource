"""Starch liquefaction and saccharification for a grain-based (dry-grind)
fuel-ethanol distillery -- the extra enzymatic conversion step a cane/
molasses distillery skips entirely, since molasses/cane juice already
carries ready-to-ferment sugar. Grain starch must first be broken down:

1. **Liquefaction**: ground grain slurried with water, gelatinized, and
   liquefied by a thermostable alpha-amylase at 95-105 C, pH 6.0-6.5
   (endo-acting: cleaves internal alpha-1,4 bonds, producing dextrins
   and oligosaccharides from the starch polymer) -- standard dry-grind
   process description, e.g. the corn dry-grind process literature this
   module cites in docs/METHODOLOGY.md.
2. **Saccharification**: the dextrins are further broken down to glucose
   by glucoamylase (exo-acting: cleaves alpha-1,4 bonds from the
   non-reducing chain ends) at a lower temperature, either as a separate
   step or concurrently with fermentation (simultaneous saccharification
   and fermentation, SSF) -- this module treats it as a distinct
   conceptual step for clarity, consistent with a first-pass conceptual
   sizing tool rather than a full SSF kinetic model.

The (C6H10O5)n + n H2O -> n C6H12O6 stoichiometric mass gain
(180.156/162.14 = 1.1112) is the SAME exact ratio `feedstock.grain_feedstock()`
already uses -- imported directly here rather than re-derived, since it
is a fixed molecular-weight fact independent of process step. What this
module adds is the missing piece that function assumed away: a real,
sub-100% `hydrolysis_efficiency` for the liquefaction+saccharification
step itself, separate from `fermentation.py`'s own (separately
calibrated) fermentation efficiency. Published lab-scale enzymatic
studies report combined starch-to-ethanol conversion above 95% under
optimized conditions (e.g. a glucoamylase/alpha-amylase corn dry-grind
study reporting 95.1% combined conversion efficiency at bench scale --
see docs/METHODOLOGY.md); this module defaults to that figure as an
optimistic ceiling, but docs/VALIDATION.md shows real, full-scale India
grain-distillery output implies notably LOWER combined efficiency once
fermentation is included too -- a genuine, disclosed gap between
lab-optimized and real commercial-scale performance, not something this
module's default should be read as guaranteeing."""
from __future__ import annotations

from .feedstock import FeedstockAnalysis

STARCH_TO_GLUCOSE_MW_RATIO = 180.156 / 162.14  # exact MW ratio, same as feedstock.grain_feedstock()

# Real, cited starch mass fractions (dry basis) for the India grain-ethanol
# feedstocks in common use -- see docs/METHODOLOGY.md for sourcing.
MILLED_RICE_STARCH_MASS_FRAC = 0.80    # milled/polished rice, commonly cited 75-80%, this module uses 80%
BROKEN_RICE_STARCH_MASS_FRAC = 0.80    # same grain, same starch content as milled rice (fragments, not a different composition)
MAIZE_STARCH_MASS_FRAC = 0.725         # FAO: 72-73% of dry kernel weight, this module uses the midpoint

DEFAULT_HYDROLYSIS_EFFICIENCY = 0.95  # lab-scale-optimized ceiling -- see module docstring and docs/VALIDATION.md


def hydrolyze_starch(grain_mass_flow_kg_s: float, starch_mass_frac: float,
                     hydrolysis_efficiency: float = DEFAULT_HYDROLYSIS_EFFICIENCY,
                     name: str = "grain (liquefied + saccharified)") -> FeedstockAnalysis:
    """Converts a raw grain mass flow into a `FeedstockAnalysis` carrying
    the ACTUAL fermentable glucose fraction after real (sub-100%)
    liquefaction+saccharification conversion -- feeds directly into
    `fermentation.ferment()` exactly like a molasses `FeedstockAnalysis`
    does, so the rest of the toolkit (fermentation, distillation,
    dehydration) is reused unchanged downstream of this step."""
    if not 0 < starch_mass_frac < 1.0:
        raise ValueError("starch_mass_frac must be strictly between 0 and 1")
    if not 0 < hydrolysis_efficiency <= 1.0:
        raise ValueError("hydrolysis_efficiency must be in (0, 1]")
    glucose_mass_frac = starch_mass_frac * STARCH_TO_GLUCOSE_MW_RATIO * hydrolysis_efficiency
    if glucose_mass_frac > 1.0:
        raise ValueError("implied fermentable-glucose mass fraction exceeds 1.0 -- check inputs")
    return FeedstockAnalysis(name, grain_mass_flow_kg_s, glucose_mass_frac)


def milled_rice(mass_flow_kg_s: float, hydrolysis_efficiency: float = DEFAULT_HYDROLYSIS_EFFICIENCY) -> FeedstockAnalysis:
    return hydrolyze_starch(mass_flow_kg_s, MILLED_RICE_STARCH_MASS_FRAC, hydrolysis_efficiency, "milled rice (hydrolysed)")


def broken_rice(mass_flow_kg_s: float, hydrolysis_efficiency: float = DEFAULT_HYDROLYSIS_EFFICIENCY) -> FeedstockAnalysis:
    return hydrolyze_starch(mass_flow_kg_s, BROKEN_RICE_STARCH_MASS_FRAC, hydrolysis_efficiency, "broken rice (hydrolysed)")


def maize(mass_flow_kg_s: float, hydrolysis_efficiency: float = DEFAULT_HYDROLYSIS_EFFICIENCY) -> FeedstockAnalysis:
    return hydrolyze_starch(mass_flow_kg_s, MAIZE_STARCH_MASS_FRAC, hydrolysis_efficiency, "maize (hydrolysed)")
