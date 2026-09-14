# Ethanol Plant Technology Provider Reference

Same purpose as the sibling lng-design-opensource/coal-to-urea-design-
opensource/cbg-design-opensource repos' `docs/VENDOR_REFERENCE.md`:
does a named provider's own public page publish a genuine, verifiable
technical detail this project's sizing can be cross-checked against —
not vendor endorsement, not a procurement recommendation. Every entry
was fetched and inspected at the time of writing (September 2026).

| Provider | Public resource (verified) | What it confirms | Relevance to this repo |
|---|---|---|---|
| **Praj Industries** | [1G Ethanol — Dehydration](https://praj.net/businesslines/1g-ethanol/offerings/dehydration/) and [Distillation](https://www.praj.net/businesslines/1g-ethanol/offerings/distillation/) (praj.net) | Praj is a real, India-headquartered (Pune) ethanol-technology market leader, confirming **EcoMol** (base molecular-sieve dehydration) and **MaxImol** (a capacity-uplift variant of the same technology, "zero evaporation and drift losses, no blow-down, no makeup water required") as real named products, plus **EcoSmart** integrated distillation/dehydration and Mechanical Vapor Recompression (MVR) as a steam-reduction option. The page does **not** publish quantified purity, capacity, or energy-consumption figures. | Directly confirms this repo's `dehydration.py` technology choice (vapor-phase molecular-sieve dehydration) is the real, currently marketed Indian-market-leading technology, not a generic textbook abstraction — but provides no numeric series to round a computed bed size against, so `dehydration.py`'s own sizing stays independently derived from the cited literature (docs/METHODOLOGY.md), not a vendor catalog lookup. |

## What didn't clear the verification bar

No quantified dehydration purity/capacity/energy figures could be found
on Praj's own public pages (commercial performance data of this kind is
evidently held back for direct commercial engagement, per the page's own
contact-for-details framing) — flagged honestly rather than filled in
with an unverified number from a secondary source.

## Note on this document's scope vs. the sibling repos'

Like the `cbg-design-opensource` sibling's own `VENDOR_REFERENCE.md`,
this is intentionally smaller in scope than the LNG/coal-to-urea
document: fuel-ethanol distillery technology in India is dominated by a
small number of turnkey EPC/technology-licensor firms (Praj foremost
among them) rather than a standardized component-catalog market, so
there is less of a numeric size-table tradition to cross-check against
in the first place.
