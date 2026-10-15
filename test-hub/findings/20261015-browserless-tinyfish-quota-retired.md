# Browserless and TinyFish temporarily retired by quota

STATUS: PROVEN
AREA: architecture
DATE: 2026-10-15
RUN: none
JOB: none
COMMIT: pending
SUPERSEDES: none

## Decision
Browserless and TinyFish must not be selected as operational browser/execution paths while their quotas are exhausted.

## Canonical consequence

- Browserless is not Anthares Browser and must never be confused with it.
- Anthares Browser/Reserva remains the internal browser system.
- TinyFish is also excluded from routing/fallback until explicitly re-enabled after quota/capacity revalidation.
- A failure that would otherwise route to Browserless or TinyFish must be classified as provider-capacity/quota routing work, not as proof that Anthares Browser itself is broken.
- Render and CircleCI remain retired separately.

This finding is a routing constraint for subsequent phases.