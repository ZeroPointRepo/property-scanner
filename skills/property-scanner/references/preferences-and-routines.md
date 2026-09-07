# Preferences and routines

## Learn from feedback

Read and update the user's profile, not the shared skill:

- “Exclude homes with pools” is a hard filter. “I'd prefer no pool” is a soft preference. A question about a pool is neither.
- “I don't like #2” excludes that listing from future unsolicited recommendations; ask what bothered them before generalizing to other homes.
- Replace conflicting old preferences with explicit new ones; briefly acknowledge the change. Keep one-off requests separate.

Unknown preference matches stay unresolved; show material ones with the result. Correct mistaken facts/calculations in saved results and affected replies. Preference feedback does not silently change valuation formulas or thresholds.

## Repeat the job

When the user requests a routine, use the host's scheduler with their frequency, local time, and time zone. Reuse its identity when changing the schedule. The routine should invoke this skill and read the current profile/state, not embed a stale copy of their preferences.

Each run reads the credit ledger, reuses the saved sold pool, and refreshes it only when due and budgeted. Then search, rank, and compare with the last successful scan:

- Send newly qualifying homes and meaningful changes to previously sent homes: asking-price/status changes, crossing the qualification threshold, or new material listing concerns.
- Do not resend an unchanged shortlist or send an empty “nothing changed” update unless requested. A user-requested scan may show the full current shortlist.
- Losing availability is a status update, not a new recommendation. A home absent from a capped search is not proof it sold or was withdrawn; check its details before reporting that change.

Update state with property observations, dismissed/sent IDs, delivery facts, and successful coverage. Partial failures must not erase older observations. Replace the numbered mapping only when delivering a new shortlist.
