# `src/cal/` — the civil calendar

`CivilDate`, `CivilTime`, `CivilDateTime`, `Weekday`, `Month`, and Howard
Hinnant's `days_from_civil` / `civil_from_days`. Proleptic Gregorian,
astronomical year numbering, ±9999.

**Declares `ETimeValue` and nothing else**, so a program that only wants
calendar arithmetic owes exactly one `failsafe` arm. Governed by
`meta/specs/CALENDAR.md`. Built in cycle 0.1, whose gate is an exhaustive
round trip over all 7 304 485 days in the range.
