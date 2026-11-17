# Methodology & citations

Every correlation used in this package traces to a public source. This
page collects them in one place; each module's docstring repeats the
relevant citation next to the code that implements it.

## Feedstock (`ethanol_design/feedstock.py`)

Cane Total Fermentable Sugar (TFS) content (14% w/w) and the B-heavy
(7.25% of cane mass, 50% TFS) vs. C-heavy/final molasses (4.5% of cane
mass, 40% TFS) diversion routes are the commonly cited India ethanol-
policy figures reproduced across sugarprocesstech.com ("Ethanol
production from various feedstocks in sugar process") and upsciq.com
("Ethanol production from B-heavy molasses"). Grain-route starch
hydrolysis, (C6H10O5)n + n H2O -> n C6H12O6, uses the exact molecular-
weight ratio 180.156/162.14 = 1.1112, not a fitted conversion factor.

## Fermentation (`ethanol_design/fermentation.py`)

Gay-Lussac stoichiometry, C6H12O6 -> 2 C2H5OH + 2 CO2 (any biochemistry/
fermentation-technology text, e.g. Bailey & Ollis, "Biochemical
Engineering Fundamentals", 2nd ed., McGraw-Hill, 1986) gives the
theoretical mass yield, derived here from real molecular weights
(0.5114 kg ethanol/kg glucose) rather than quoted. Real fermentation
efficiency (88-98% of theoretical across independently reported Indian
molasses-fermentation studies -- see docs/VALIDATION.md) is applied on
top; this module's own default (92.57%) is the figure that three
independently sourced India ethanol-policy numbers (B-heavy, C-heavy,
direct cane-juice litres of ethanol per tonne of cane) all imply once
divided through by the theoretical yield -- a real cross-check derived
from the data, not chosen to make a demo work.

## Starch hydrolysis (`ethanol_design/starch_hydrolysis.py`)

Grain (milled rice, broken rice, maize) needs an enzymatic conversion
step molasses/cane juice skips entirely: liquefaction (thermostable
alpha-amylase, 95-105 C, pH 6.0-6.5, endo-acting on starch's alpha-1,4
bonds to give dextrins) followed by saccharification (glucoamylase,
exo-acting, dextrins to glucose) -- standard dry-grind process steps,
widely described in the corn dry-grind ethanol literature. Starch
content defaults (milled/broken rice 80%, cited range 75-80%; maize
72.5%, FAO's cited 72-73% of dry kernel weight) and the default 95%
combined hydrolysis efficiency (a lab-scale-optimized figure from a
glucoamylase/alpha-amylase corn dry-grind study reporting 95.1%
combined conversion) are all independently cited; see docs/VALIDATION.md
for the honest gap this ceiling leaves against real full-scale plant
output.

## DDGS (`ethanol_design/ddgs.py`)

Distillers Dried Grains with Solubles -- a grain distillery's real
co-product in place of molasses distillery's spent wash. Computed by
an exact mass balance (non-starch solids + unconverted starch + yeast
biomass, dried to a target moisture content), not a recalled yield
ratio. Yeast biomass yield (0.08 kg/kg sugar) is Bailey & Ollis's
typical 0.05-0.12 g/g range midpoint for anaerobic/microaerobic
S. cerevisiae ethanolic fermentation; DDGS moisture target (10%) is
inside the 8-12% commercial feed-grade range cited by both industry and
the IMSBC bulk-cargo code (which caps it under 13%).

## Distillation (`ethanol_design/distillation.py`)

Fenske-Underwood-Gilliland (FUG) shortcut method (Seader, Henley &
Roper, "Separation Process Principles", 3rd ed., Wiley, ch. 5; McCabe,
Smith & Harriott, "Unit Operations of Chemical Engineering"). Relative
volatility is computed from CoolProp's HEOS ethanol-water mixture
equation of state at the column's bottoms and distillate compositions
(geometric mean, per Seader/Henley eq. 5-39's top/bottom convention),
not a single textbook alpha (used for Fenske Nmin). Minimum reflux for a
saturated-liquid feed is taken from McCabe-Thiele geometry on the real
CoolProp equilibrium curve: the steepest rectifying line from (xD, xD)
that touches the curve anywhere between the feed and distillate, which
covers both the feed pinch and ethanol-water's tangent pinch. (An earlier
version put the pinch at the feed using the averaged alpha; for a ~8 wt%
wash that over-stated Rmin about 3x versus the textbook VLE curve.) The Gilliland number-of-stages step uses the Molokanov et
al. (1972) analytical fit to Gilliland's original empirical correlation
(reproduced in Seader/Henley eq. 5-48).

## Dehydration (`ethanol_design/dehydration.py`)

India's BIS IS 15464:2004 anhydrous-ethanol specification caps water at
0.8% v/v (tighter than the ~1 wt% ASTM D4806 implies for the US
denatured-blend spec). 3A molecular sieve vapor-phase pressure-swing
adsorption (VPSA) is the standard modern technology (OIM Chemical / SKJ
Group technical notes on 3A sieve ethanol dehydration; Kupiec, Rakoczy &
Zapotoczny-Pieniek, "Ethanol-water adsorption on commercial 3A
zeolites: kinetic and thermodynamic data", Brazilian J. Chem. Eng.,
2011) -- 3A's ~3-angstrom pore excludes the larger ethanol molecule
while still admitting water, the property that makes selective
adsorption of water FROM ethanol possible at all (vs. 4A sieve used for
trace water removal from natural gas in the sibling lng-design-
opensource repo, whose two-bed GPSA Ch. 20 sizing structure this module
reuses). Dynamic working capacity (3-5 wt%) and regeneration temperature
(200-250 C) and the industrial 4-12 h adsorption-cycle range are all
from the same sources. Regeneration duty sums the sensible heat to raise
the purge stream to regeneration temperature AND the latent heat of
adsorption (4.19 MJ/kg water, Interra Global's published mSORB 3A EDG
datasheet -- see docs/VENDOR_REFERENCE.md) -- a real energy term added
directly in response to finding that vendor figure; at this module's own
defaults it turns out to be the LARGER of the two components (~90% of
total duty), a real, disclosed correction to what the module originally
computed, see docs/VALIDATION.md.

## Stillage (`ethanol_design/stillage.py`)

Spent-wash generation ratio (8-15 L per L of alcohol) and the CPCB
(Central Pollution Control Board) fresh-water consumption cap (15 L per
L of alcohol) are both from CPCB's "Charter for Zero Liquid Discharge
(ZLD) in Molasses Based Distilleries" and widely reproduced in the
distillery-effluent literature (e.g. teamonebiotech.com, "How to Treat
Distillery Effluent"; wealthywaste.com, "Management of Spent Wash in
Distilleries"). COD range (110,000-205,000 ppm) is the commonly cited
range for raw distillery spent wash in the same literature.

## Related open-source work

Same related-project list as the sibling repos:
[DWSIM](https://github.com/DanWBR/dwsim5),
[IDAES](https://github.com/IDAES/idaes-pse) -- plus, specific to a
fuel-ethanol biorefinery, [BioSTEAM](https://github.com/BioSTEAMDevelopmentGroup/biosteam)
and its [Bioindustrial-Park](https://github.com/BioSTEAMDevelopmentGroup/Bioindustrial-Park)
model library (the Guest Group, University of Illinois Urbana-
Champaign), which includes real, published `sugarcane`, `cane`, `corn`
and `cornstover` biorefinery flowsheets -- the closest existing open-
source prior art for this repo's process, consulted for context (not a
dependency; this package's correlations are independently sourced and
reimplemented per-module as cited above).
