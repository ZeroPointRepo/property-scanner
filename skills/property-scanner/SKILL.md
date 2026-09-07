---
name: property-scanner
description: Find potentially underpriced homes using ZillAPI MCP. Onboard buyers, remember preferences, deliver ranked photo shortlists, answer property follow-ups, and repeat scans on a routine.
---

# Property Scanner

## Every scan

- Read current preferences; use only ZillAPI. Limit active pulls to 10 and weekly comparison refreshes to 20; keep the 20/40-credit run limits and 900-credit billing-period cap.
- Compare matching homes using the saved mode: relaxed by default, or strict when requested. See [scanning](references/scanning.md).
- Use the saved threshold: 3% relaxed, 5% strict. Prefer actual closed-sale evidence; explicitly distinguish any asking-price fallback. Missing evidence is not proof that no homes qualify.
- Surface listing concerns. Price cuts support a recommendation; they cannot qualify a home alone. A reference gap is not an appraisal or guaranteed return.
- Send a TLDR, separate numbered property/photo messages, and an easy numbered follow-up. Save explicit preference changes for subsequent scans.

## Read for the current action only

| Action | Reference |
| --- | --- |
| First use or unfinished setup | [Onboarding](references/onboarding.md) |
| Connect or fetch property data | [ZillAPI](references/zillapi.md) |
| Select and rank homes | [Scanning](references/scanning.md) |
| Send results or answer a numbered reply | [Delivery](references/delivery.md) |
| Learn preferences or run on a schedule | [Preferences and routines](references/preferences-and-routines.md) |

Keep the user's profile/state outside this shared skill, with a persistent pointer for future conversations and routines. Save documents as Markdown.
