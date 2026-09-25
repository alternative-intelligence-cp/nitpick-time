# `src/cal/` — the civil calendar

`CivilDate`, `CivilTime`, `CivilDateTime`, `Weekday`, `Month`, and Howard
Hinnant's `days_from_civil` / `civil_from_days` as `date_to_days` /
`days_to_date` (since cycle 0.1.1). Proleptic Gregorian, astronomical year
numbering, ±9999.

**Declares `ETimeValue` and nothing else**, so a program that only wants
calendar arithmetic owes exactly one IDENTITY arm — and eleven arms in all at
compiler `c3bdae2`, because the floor and `cal`'s own arithmetic are charged to
the consumer too (`meta/specs/SAFETY.md` S-4, S-4b). Governed by
`meta/specs/CALENDAR.md`. Built in cycle 0.1, whose gate is an exhaustive
round trip over all 7 304 484 days in the range. <!-- [[sweep: domain_every_day_number=7304484]] -->

*(Until cycle 0.1.1 this file said the consumer "owes exactly one `failsafe`
arm" — the identity half of the bill, read as the whole of it, which cycle
0.1.0 measured at nine and 0.1.0b at eleven — and gave the range as 7 304 485
days, one too many: TM-161.)*
