# Selecting opportunities

These are screening defaults. Apply hard filters first; retain explicit soft-preference misses for ordering. Unknown facts cannot satisfy a required filter.

## Matching modes

Use the saved mode. The default mode is `relaxed`; preserve `strict` as an option. Neither mode expands the credit budget. The table is the authoritative numeric specification.

| Rule | Strict | Relaxed |
| --- | --- | --- |
| Minimum comparisons | 3 | 1; prefer 2+ |
| Gap to pass screen | 5% | 3% |
| Distance | 1 mile | 2.5 miles |
| Bedrooms | Exact | ±1 |
| Bathrooms | ±0.5 | ±1 |
| Living area | ±15% | ±30% |
| Year built | ±20 years | ±30 years |
| Lot size ratio | 0.5–2×, both required | 0.4–2.5×, only when both known |
| Closed-sale age | Within 180 days | Within 180 days |
| Missing Zestimate | Cannot assess | Comparison reference alone; Needs review |
| Missing closed price | Exclude comparison | Last pending/contingent ask within 120 days; Needs review |
| Price/sq-ft spread flag | Greater than 30% | Greater than 40% |

Same property type in both modes. Exclude known material neighborhood, condition, ownership-interest, or amenity mismatches and explicit non-market transfers. Record unresolved descriptive differences. Missing core numeric matching fields disqualify a comparison, except relaxed lot size as specified above.

Exclude the subject and duplicate properties. Use the latest verified sale episode per comparison property; prefer its actual closed price. For a missing closed price in relaxed mode, use that episode's last dated pending/contingent ask, no more than 120 days before the run and no later than its associated Sold event. Preserve the price source and both dates. A generic asking price or old unrelated sale is not a valid substitute.

Choose up to five comparisons by distance, proportional size difference, sale recency, then numeric ID. Do not choose prices to make a home qualify. In relaxed mode a set may contain actual prices and asking-price fallbacks: retain the provenance of each. Any fallback makes the entire result indicative and Needs review; never label its median a sold-price reference.

## Calculate and rank

```text
comparison_reference = median(comparison price / living area) × subject living area
reference = min(comparison_reference, Zestimate) when Zestimate is valid
reference = comparison_reference when Zestimate is absent in relaxed mode
gap_dollars = reference − asking price
gap_percent = 100 × gap_dollars / reference
passes_screen = gap_percent >= (5 in strict mode, 3 in relaxed mode)
```

Use positive finite prices, estimates, and areas. Show the number and kind of comparisons: actual closed prices, pending asking prices, or a mixture. No priced comparison means unassessed. One comparison gets an explicit “Only one comparison” flag; it is not broad market support.

Needs review also covers missing Zestimate, explicit major repairs, cash-only restrictions, land leases, unresolved material comparisons, and price spread `(max $/sq ft − min $/sq ft) / median $/sq ft` above the mode's limit. No reported issue does not establish good condition.

Order results using only actual sale prices first, then those using any asking-price fallback. Next apply review groups, prefer 2+ comparisons over one, then fewer soft-preference misses, gap percentage descending, gap dollars descending, recent-cut percentage descending, and numeric ID ascending. Return up to the requested five; the count that passed the screen may be larger. Ten passing homes does not require ten message bubbles.

Use [rank_properties.py](../scripts/rank_properties.py) with an explicit saved mode after applying the matching rules above. Its `--help` describes input. Without Python, use the same rules in the host's calculation tool. These are leads meeting a screen, not verified bargains. Separate below-threshold assessments from unassessed homes with missing evidence.

## Price cuts

Within the current continuous for-sale episode, the latest distinct asking-price change must end at today's asking price. Use the immediately preceding ask as the baseline:

```text
cut_dollars = previous_ask − current_ask
cut_percent = 100 × cut_dollars / previous_ask
recent_cut = cut_percent >= 3 AND change occurred 0–30 calendar days ago
```

A sale, withdrawal, rental episode, or relisting breaks the baseline. Ambiguous history means unknown. Do not compare today's ask with an old sale or aggregate across relistings. A subsequent increase cancels the latest-cut signal.

Keep unrounded numbers for qualification and sorting; display percentages to one decimal, half-up. Retain comps, source facts, cut events, and review reasons for follow-ups.
