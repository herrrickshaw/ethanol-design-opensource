# Ethanol Design (open-source)

Conceptual sizing tools for a fuel-ethanol distillery, for process engineers, students and policy analysts
screening a plant before committing to a licensed simulator. It covers molasses/cane-juice and grain (rice,
maize) routes: batch fermentation, Fenske-Underwood-Gilliland shortcut distillation, 3A molecular-sieve
dehydration to anhydrous fuel ethanol, and the co-products (spent wash/vinasse for molasses, DDGS for grain).
It produces Python result objects, printed worked examples and a Streamlit app.

> Status: active, research-only. Textbook and public-domain correlations only; nothing derives from any
> proprietary vendor, licensor or client data. Educational use; not a substitute for detailed design.

New here? See [How to use this repo with AI (Claude, Gemini, ChatGPT)](HOW_TO_USE_WITH_AI.md).

## What it does
- Finds the ethanol-water azeotrope numerically from CoolProp HEOS and derives bubble points and relative volatility.
- Computes fermentable sugar from India cane-juice, B-heavy and C-heavy molasses routes, and from milled rice, broken rice or maize via starch hydrolysis.
- Applies Gay-Lussac stoichiometry with fermentation efficiency for ethanol/CO2 flows, wash strength and fermenter sizing.
- Sizes a Fenske-Underwood-Gilliland distillation column from mass-fraction specs.
- Sizes a two-bed 3A zeolite VPSA dehydration unit and checks BIS IS 15464 water spec compliance.
- Balances CPCB spent wash (molasses) and DDGS output (grain).

## Quick start
```bash
git clone https://github.com/herrrickshaw/ethanol-design-opensource
cd ethanol-design-opensource
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python examples/full_chain_worked_example.py     # cane -> ethanol, end to end
python examples/grain_worked_example.py          # rice/maize -> ethanol + DDGS
streamlit run streamlit_app.py                   # interactive app
```

## How it works
Stages run in order; each module is a set of pure functions returning dataclasses.

| Stage | Module | Method | Key outputs |
|---|---|---|---|
| Properties | `ethanol_design/properties.py` | CoolProp HEOS ethanol-water EOS | Azeotrope (cross-checked vs textbook), bubble points, relative volatility |
| Feedstock | `ethanol_design/feedstock.py` | India cane/molasses TFS routes, exact starch stoichiometry | Fermentable sugar mass flow by route |
| Starch hydrolysis | `ethanol_design/starch_hydrolysis.py` | Alpha-amylase liquefaction + glucoamylase saccharification, sub-100% efficiency | Fermentable glucose from rice/maize |
| Fermentation | `ethanol_design/fermentation.py` | Gay-Lussac stoichiometry + efficiency | Ethanol/CO2 flow, wash strength, fermenter size |
| Distillation | `ethanol_design/distillation.py` | Fenske-Underwood-Gilliland, CoolProp relative volatility | Min/actual stages, min/actual reflux, distillate purity |
| Dehydration | `ethanol_design/dehydration.py` | 3A zeolite VPSA (same two-bed GPSA-style structure as the sibling LNG repo's `molecular_sieve.py`) | Bed mass/diameter/height, beds, regen duty, IS 15464 check |
| Stillage | `ethanol_design/stillage.py` | CPCB spent-wash mass balance (molasses) | Spent-wash flow, COD/BOD load, fresh-water-cap compliance |
| DDGS | `ethanol_design/ddgs.py` | Mass balance: non-starch solids + unconverted starch + yeast (grain) | DDGS flow at commercial moisture spec |

Every correlation is cited per module in `docs/METHODOLOGY.md`; validation findings are in `docs/VALIDATION.md`.

## Repository layout
| Path | Purpose |
|---|---|
| `ethanol_design/` | Library modules listed above |
| `examples/` | `full_chain_worked_example.py` (1,000 t/day B-heavy molasses), `grain_worked_example.py` (500 t/day grain) |
| `streamlit_app.py` | Interactive front end |
| `tests/` | Unit tests per module plus characterisation tests against `tests/golden/` |
| `docs/` | `METHODOLOGY.md`, `VALIDATION.md`, `VENDOR_REFERENCE.md` |

## Data sources
No external data is fetched at run time. Published figures used as cross-checks (India ethanol-policy
litres-per-tonne figures, BIS IS 15464, CPCB spent-wash norms, vendor specs from Vogelbusch, Interra Global and
Praj Industries) are cited in `docs/VALIDATION.md` and `docs/VENDOR_REFERENCE.md`.

## Configuration
None required: no environment variables, no secrets. Design parameters are function arguments with documented
defaults (for example `DEFAULT_HYDROLYSIS_EFFICIENCY`, `reflux_ratio_factor=1.3`).

## Testing
```bash
pytest -q        # 47 tests
ruff check .
```
`tests/test_characterisation.py` asserts that module outputs and the two worked examples reproduce the
pre-refactor results exactly.

## Limitations and known issues
- Motivation: India's E20 blending programme. The fermentation-efficiency default is cross-checked against three independently published India figures (B-heavy molasses, C-heavy molasses, cane juice); see `docs/VALIDATION.md`.
- Validated: the 1,000 t/day B-heavy example reproduces the publicly quoted 21.75 L ethanol per tonne of cane, and the derived azeotrope lies within 0.15 weight-point of the textbook value.
- Grain route overshoots real plant output by 13-21% against 450 / 440 / 380 L per tonne (milled rice / broken rice / maize). The 95% starch-hydrolysis default is a lab-optimised ceiling; this is reported, not tuned away.
- At industrial scale the single dehydration vessel comes out unrealistically slender; the module flags it.
- The Interra Global heat-of-adsorption figure exposed a missing energy term in the regeneration duty (9 kW became 116 kW once fixed); documented in `docs/VALIDATION.md`.
- Conceptual screening only: validate against a licensed simulator and vendor data before specifying equipment.

## Related repositories
Siblings with the same discipline: [lng-design-opensource](https://github.com/herrrickshaw/lng-design-opensource),
[biomass-to-syngas-opensource](https://github.com/herrrickshaw/biomass-to-syngas-opensource),
[coal-to-urea-design-opensource](https://github.com/herrrickshaw/coal-to-urea-design-opensource).
Prior art consulted (not dependencies): [DWSIM](https://github.com/DanWBR/dwsim5),
[IDAES](https://github.com/IDAES/idaes-pse), [BioSTEAM](https://github.com/BioSTEAMDevelopmentGroup/biosteam)
and its [Bioindustrial-Park](https://github.com/BioSTEAMDevelopmentGroup/Bioindustrial-Park) flowsheets.

## Licence
MIT; see [LICENSE](LICENSE).
