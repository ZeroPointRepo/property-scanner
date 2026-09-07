# ZillAPI

MCP endpoint: `https://api.zillapi.com/mcp`.
Prefer OAuth through the host's MCP connection flow. Use API-key setup only when OAuth is unavailable in the host or the user explicitly prefers an API key.

Discover the live schemas. Documented tools are `search_listings`, `lookup_property_by_zpid`, `lookup_property_by_address`, and `get_zestimate`; connector prefixes may differ. REST arguments and sub-resources are not automatically MCP arguments or tools.

## Fetch within a credit budget

Default to a focused area: up to 10 active results per scan and 20 sold results on initial setup, then at most once every seven days. Save the sold records as a reusable comparison pool; merge new records by property ID and transaction date rather than replacing the pool. Reapply the saved mode's age and similarity rules on every scan.

These caps limit new fetching, not reuse of already fetched records. Test a relaxed mode against the existing snapshot before spending credits on another search.

1. Freeze the saved criteria, bounds, and market-local date. Use a fixed supported sort, otherwise retain upstream default ordering. Prefer recently updated active listings when the schema supports that sort. Do not apply the buyer's price cap to sold homes. This is a bounded search, not complete citywide coverage.
2. Deduplicate by `zpid`. Fetch full details in ID order only for potentially matching **active** homes — their current price/status/estimate need a live check. **Sold comps do NOT need a detail lookup for the comp math**: their closed price (`unformattedPrice`), sale date (`dateSold`), and `livingArea` are already on the search card (see [Sold comparisons](#sold-comparisons)). Reuse records already saved; stored sold prices do not need re-downloading. Use one request at a time.
3. Apply hard filters to active homes. Verify current for-sale status and asking price. For comparisons, identify completed-sale prices/dates; “nearby” listings and old asking prices are not sold comparables. Search cards are not full property records.
4. Read Zestimate, history, photos, description, and property facts from details. Supplement only within the remaining budget. Retain source timestamps; conflicting/incomplete evidence cannot support a price claim.

Before calling sold prices unavailable, inspect all already returned fields that explicitly represent sale prices, not only `priceHistory[].price`. The documented `last_sold_price` is another possible source; use it only when its transaction/date can be verified. Never use an unlabeled listing `price` as a closed price. A missing field in this pull does not establish that the API never supplies it. [Property fields](https://zillapi.com/api/properties/)

## Sold comparisons

Sold comps are the valuation backbone; the Zestimate is only a conservative cap when it happens to be present. Two rules, and most collapsed comp pools trace to breaking one of them:

- **NEVER apply the buyer's price cap to the sold search.** The buyer's budget is for the homes you *shop*, not the evidence you *compare against*. A home that sold above the buyer's budget still tells you what the area is worth — filtering it out is exactly how a real comp pool shrinks to one or two records. Search sold by **area + bedroom band only** (no `price_max` on sold).
- **Read the closed price straight off the sold card — no per-comp detail lookup.** A `SOLD` / `RECENTLY_SOLD` card already carries `unformattedPrice` (the closed price), `dateSold` (the sale date), and `livingArea` — present on essentially every sold card, so the median-$/sq-ft math needs nothing more. The `homeStatus` + `dateSold` pairing is the label that makes `price` a *closed* sale; never treat an active listing's `price` as a closed price. A detail lookup on a sold comp is an optional supplement (extra facts), never required to obtain its sale price.

**Zestimate coverage varies widely by market and is frequently absent** — in some metros only ~1 in 5 homes has one. Never gate a valuation on it: its absence is expected, not a failure. Where present it only refines the reference as a cap (`min(comparison_reference, Zestimate)`, see [scanning](scanning.md)); the sold comps carry the valuation on their own.

## Budget defaults

- **Active scan: at most 20 credits**, including search, detail lookups, supplemental calls, and checks of previously sent homes.
- **Sold-pool refresh: at most 40 credits**, initially and no more than once every seven days. The initial scan therefore budgets at most 60 credits.
- **Scanner allowance: 900 credits per billing period**, leaving room within a 1,000-credit plan for other use. Count every scanner call, including manual reruns and follow-ups. Use the actual billing/reset dates and available account balance, not an assumed calendar month.

Search costs are per returned record, not per request. Reserve the maximum possible charge before each call; use reported usage when supplied, otherwise conservative published charges. Don't assume a lookup will be free merely because caching exists. Stop before a run or call exceeds its remaining allowance; explain a budget-limited result rather than loosening the comp rules. A changed area invalidates the old pool and may require a budgeted rebuild.

The ceilings permit up to 31 active scans (620 credits) plus five sold refreshes (200), totaling 820 before extra user requests. They do not guarantee five qualifying homes. A smaller pool trades coverage for cost; preserve the valuation rules and report fewer matches instead of weakening them.

Sources: [MCP](https://zillapi.com/ai-agents/), [search](https://zillapi.com/api/search/), [property details](https://zillapi.com/api/properties/), [pricing](https://zillapi.com/pricing/). Credit design revised September 7, 2026.
