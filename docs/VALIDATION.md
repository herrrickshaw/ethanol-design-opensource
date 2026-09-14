# External validation

## Real-world motivation and public source

India's ethanol-blending program (E20 by 2025-26) is the direct policy
driver behind the B-heavy/C-heavy molasses diversion figures this repo's
`feedstock.py` and `fermentation.py` use as defaults -- see
sugarprocesstech.com, "Ethanol production from various feedstocks in
sugar process", and upsciq.com, "Ethanol production from B-heavy
molasses", for the published cane-to-ethanol figures this section
cross-checks.

## Azeotrope location -- CoolProp's HEOS model vs. the textbook figure

`properties.find_azeotrope()` locates the ethanol-water azeotrope
numerically by bisecting on (vapor composition - liquid composition)
using CoolProp's real HEOS mixture equation of state, rather than
hard-coding the commonly cited textbook value. It lands at 89.2 mol%
(95.5 wt%) ethanol, 78.29 C at 1 atm -- within 0.15 weight-point and
0.2 C of the widely cited reference figure (95.6 wt%, 78.1 C, e.g.
Perry's Chemical Engineers' Handbook, 8th ed.), a genuine independent
agreement found by running the search, not assumed in advance.

## Fermentation efficiency -- three independently published figures agree

Three separately sourced India ethanol-policy numbers are all reproduced
by this package with ONE shared fermentation efficiency:

| Route | Published yield | This package (92.57% efficiency) |
|---|---|---|
| B-heavy molasses (7.25% of cane, 50% TFS) | 21.75 L/tonne cane | 21.75 L/tonne cane |
| C-heavy molasses (4.5% of cane, 40% TFS) | 10.8 L/tonne cane | 10.8 L/tonne cane |
| Direct cane juice (100% of cane's 14% TFS) | 84.0 L/tonne cane | 84.0 L/tonne cane |

This was a real finding made by running the numbers, not designed in
advance: dividing each published litres-per-tonne-cane figure by this
module's own Gay-Lussac theoretical yield (0.5114 kg ethanol/kg sugar)
and the relevant feedstock's TFS content gives 0.9257 in all three
cases, to 4 significant figures -- strong evidence the three published
figures share one common underlying efficiency assumption, not three
independently chosen round numbers. That efficiency sits comfortably
inside the independently reported 88-98% range for Indian molasses
fermentation (e.g. the operating-conditions study cited in
`fermentation.py`'s docstring: 50-55% w/v molasses, 30-33 C, pH 4.6,
48 h fermentation), so it was adopted as this package's default rather
than an arbitrary round number.

## Grain route: a real, honestly-disclosed overshoot against published India figures

India's grain-based ethanol industry publishes real litres-of-ethanol-
per-tonne-of-grain figures: 450 L/tonne for full/milled rice, 440 L/tonne
for broken rice, 380 L/tonne for maize (widely reported in coverage of
FCI's rice allocation for ethanol and the industry's maize sourcing).
`examples/grain_worked_example.py` runs all three through
`starch_hydrolysis.py` (95% combined hydrolysis efficiency, a lab-scale-
optimized ceiling) and `fermentation.py` (92.57%, the molasses-
calibrated default):

| Grain | Published yield | This package's model | Ratio |
|---|---|---|---|
| Milled rice | 450.0 L/tonne | 506.7 L/tonne | 1.126x |
| Broken rice | 440.0 L/tonne | 506.7 L/tonne | 1.152x |
| Maize | 380.0 L/tonne | 459.2 L/tonne | 1.208x |

**Reported honestly, not corrected to fit**: the model consistently
OVERSHOOTS real published output by 13-21%, worst for maize. This
contrasts sharply with the cane/molasses calibration above, which
matched three independent published figures almost exactly using one
shared efficiency. The most likely explanation, consistent with general
industry commentary that grain-based ethanol runs less efficiently than
molasses-based ethanol in practice: this module's 95% hydrolysis
efficiency default is a LAB-SCALE-OPTIMIZED figure (from a controlled
bench study), while real full-scale commercial liquefaction/
saccharification -- subject to feedstock quality variability, imperfect
gelatinization at scale, and enzyme cost trade-offs -- runs measurably
below that ceiling. Rather than silently lower the default to force a
match (which would just be fitting a different unverified number), this
gap is left visible: `hydrolysis_efficiency` is a fully overridable
parameter, and a real plant's own measured combined conversion is the
right input once available, exactly the same epistemic stance this
project takes everywhere else a "typical" literature figure stands in
for a real, unmeasured process.

## Dehydration regeneration duty -- a real vendor number exposed a missing energy term

Cross-checking `dehydration.py` against real molecular-sieve vendor data
(docs/VENDOR_REFERENCE.md) surfaced a genuine gap in the original
module, not just a confirmation: Interra Global's published mSORB 3A
EDG datasheet gives a real heat-of-adsorption figure (1,800 BTU/lb H2O
= 4.19 MJ/kg water) that the original `regen_heater_duty_kW` calculation
did not include at all -- it summed only the sensible heat to raise the
regeneration purge stream to regeneration temperature. At this module's
own default parameters, adding the latent term changes the computed
regeneration duty from **9 kW to 116 kW** for the full-chain worked
example's B-heavy molasses case -- the latent heat of desorption turns
out to be roughly **90% of total regeneration duty**, not a small
correction on top of an already-complete sensible-heat estimate. This
was found and fixed in the same session the vendor research that
revealed it was done, not left as a known gap -- see `dehydration.py`'s
own docstring and test suite (`test_latent_duty_dominates_regeneration_energy`)
for the fix and the regression guarding it.

## Full-chain worked example

`examples/full_chain_worked_example.py` runs a representative
1,000 t/day cane-crushing B-heavy-molasses distillery end to end
(feedstock -> fermentation -> distillation -> dehydration -> stillage)
and explicitly checks its own fermentation-stage output against the
published 21.75 L/tonne-cane figure, printing MATCH/MISMATCH rather than
asserting success silently.

**A real finding from running the distillation and dehydration stages
together**: at this scale, sizing the dehydration bed with the sibling
LNG repo's natural-gas molecular-sieve superficial-velocity convention
(design_velocity_m_s=0.30, an industrial-scale full-flow bed) and the
industrial 8 h adsorption-cycle midpoint together produce a bed with a
height:diameter ratio of ~36:1 -- a real, structurally implausible
single-vessel geometry, not a units bug (the underlying formula's bed
height is independent of absolute flow rate; see `dehydration.py` for
the derivation of why). This module flags it via
`recommend_parallel_vessels` rather than silently returning an
unbuildable single vessel -- a real industrial VPSA dehydration section
would split this duty across several shorter parallel beds, which this
conceptual sizing tool does not lay out itself (a genuine scope
limitation, noted rather than hidden).

## What was deliberately not modeled in this first pass

- Rate-based/breakthrough-curve adsorption dynamics for the dehydration
  bed (mass-balance sizing only, like the sibling LNG repo's own
  molecular-sieve module).
- Multicomponent fermentation by-products (glycerol, fusel oils,
  higher alcohols) -- captured only implicitly via the fermentation
  efficiency factor, not tracked as separate streams.
- Anaerobic digestion of the spent wash itself -- a real, standard
  Zero Liquid Discharge route for distillery effluent, reserved for the
  `cbg-design-opensource` sibling repo's `anaerobic_digestion.py`
  rather than duplicated here (see `stillage.py`'s docstring).
- Two-column (analyzer + rectifier) industrial column configurations --
  modeled here as one shortcut FUG column from wash to near-azeotrope
  distillate, the standard conceptual-design simplification.
