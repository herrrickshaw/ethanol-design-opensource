# Ethanol Plant Technology Provider Reference

Same purpose as the sibling lng-design-opensource/coal-to-urea-design-
opensource/cbg-design-opensource repos' `docs/VENDOR_REFERENCE.md`:
does a named provider's own public page publish a genuine, verifiable
technical detail this project's sizing can be cross-checked against —
not vendor endorsement, not a procurement recommendation. Every entry
was fetched and inspected at the time of writing (September 2026).

| Provider | Public resource (verified) | What it confirms | Relevance to this repo |
|---|---|---|---|
| **Vogelbusch Biocommodities** | [Molecular Sieve Dehydration](https://www.vogelbusch-biocommodities.com/en/process-units/dehydration/molecular-sieve-process/) (vogelbusch-biocommodities.com, own site) | Real, quantified, Austrian-vendor spec sheet: **two-bed pressure-swing adsorption** ("one bed in dehydration service, while the other bed is regenerated under vacuum") -- the exact two-bed structure `dehydration.py` sizes; economic minimum unit capacity **10,000 L/day**, standard skid-mounted plants **up to 400,000 L/day**, and a real showcase project at **1.3 million L/day**; feed water content up to **15%** processed economically; product water content from **0.5% down to 0.01%** (pharmaceutical-grade "super dry") depending on target. | The **0.5% water figure is a real, directly comparable data point against this module's BIS IS 15464 target (<=0.8% v/v)**: a real commercial vendor's own standard fuel-ethanol product spec clears the Indian regulatory floor with real margin, not just this project's own literature-derived assumption. The two-bed vacuum-regenerated structure independently confirms `dehydration.py`'s `n_beds` logic. The 15% max feed water figure comfortably brackets this project's own near-azeotrope feed (~4.5-5.5% water). |
| **Interra Global** | [mSORB® 3A EDG](https://www.interraglobal.com/products/molecular-sieve/ethanol-dehydration-molecular-sieve) (interraglobal.com, own site) | Real, quantified US-vendor adsorbent datasheet: **water adsorption capacity >= 21.5 wt% (at 75% RH, 25 C, static/equilibrium basis)**, **heat of adsorption 1,800 BTU/lb H2O (4.19 MJ/kg water)**, crush strength >= 120 N, bulk density >= 0.77 g/mL. | The static 21.5% equilibrium capacity being far above `dehydration.py`'s cited 3-5% DYNAMIC working-capacity default is itself a real, expected adsorption-engineering relationship (a real cycle never reaches static equilibrium capacity), not a contradiction -- a genuine, useful sanity check on the direction of that gap. The heat-of-adsorption figure is real thermodynamic data this module's own regeneration-duty calculation did NOT previously account for (see the code change below, made directly in response to finding this real number). |
| **Zeochem** | [Ethanol Dehydration](https://zeochem.com/our-applications/ethanol-dehydration/) (zeochem.com, own site) | Real Swiss/US adsorbent manufacturer; states its Z3-03 product is used across "many of the world's ethanol plants" with service life "approaching 20 years in some plants" -- no quantified capacity/purity figures on this specific page. | A third independently confirmed real 3A-sieve vendor, reinforcing that vapor-phase molecular-sieve dehydration is the dominant, multiply-sourced real technology this module models -- not a single-vendor or hypothetical process. |
| **Praj Industries** | [1G Ethanol — Dehydration](https://praj.net/businesslines/1g-ethanol/offerings/dehydration/) (praj.net, own site) | Real, India-headquartered (Pune) market leader; **EcoMol** (base molecular-sieve dehydration) and **MaxImol** (capacity-uplift variant, "zero evaporation and drift losses, no blow-down, no makeup water required") as real named products. No quantified purity/capacity/energy figures published on this page. | Confirms this is the real, currently marketed India-market-leading technology (not a generic textbook abstraction) -- the same real gap the LNG sibling document flags for several vendors whose commercial performance data sits behind direct engagement rather than a public page. |

## A real vendor number this project's model previously omitted -- now added

Interra Global's published heat of adsorption (4.19 MJ per kg of water
removed) is a real energy cost `dehydration.py`'s `regen_heater_duty_kW`
calculation did not previously include -- the original version summed
only the SENSIBLE heat to raise the regeneration purge stream to
regeneration temperature, omitting the LATENT energy actually needed to
desorb the water itself from the zeolite. Both are real, additive
components of the same regeneration duty; the sensible-heat term stays
(the purge gas genuinely must be heated), and the latent term is now
added explicitly, cited to this real vendor figure rather than folded
in silently. See `dehydration.py`'s own docstring for the updated
formula and this module's test suite for the regression this addition
required.

## What didn't clear the verification bar

No quantified dehydration purity/capacity/energy figures could be found
on Zeochem's or Praj's specific ethanol-dehydration pages (commercial
performance data of this kind is evidently held back for direct
commercial engagement at both companies) — flagged honestly rather
than filled in with an unverified number from a secondary source.

## Note on this document's scope vs. the sibling repos'

Unlike the earlier (single-vendor, Praj-only) version of this document,
this one found real, quantified, independently verifiable specs from
two vendors (Vogelbusch, Interra Global) directly comparable to this
project's own cited defaults -- closer in spirit to the LNG/coal-to-
urea sibling document's per-component numeric cross-checks than to the
"named but unquantified" pattern the earlier CBG/ethanol documents in
this family more often found.
