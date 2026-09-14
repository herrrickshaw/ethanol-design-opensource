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

## Distillation (`ethanol_design/distillation.py`)

Fenske-Underwood-Gilliland (FUG) shortcut method (Seader, Henley &
Roper, "Separation Process Principles", 3rd ed., Wiley, ch. 5; McCabe,
Smith & Harriott, "Unit Operations of Chemical Engineering"). Relative
volatility is computed from CoolProp's HEOS ethanol-water mixture
equation of state at the column's bottoms and distillate compositions
(geometric mean, per Seader/Henley eq. 5-39's top/bottom convention),
not a single textbook alpha. Minimum reflux for a saturated-liquid feed
is derived directly from the McCabe-Thiele pinch-point geometry (the
rectifying operating line meets the equilibrium curve exactly at the
feed composition) rather than quoting Underwood's own published formula
from memory. The Gilliland number-of-stages step uses the Molokanov et
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
from the same sources.

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
