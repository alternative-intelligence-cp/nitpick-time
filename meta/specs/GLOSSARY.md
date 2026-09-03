# Glossary

One word per concept, one concept per word. Where the time world uses a word
two ways, this table says which one `ntime` means and what the other is called
instead.

| Term | Means, in `ntime` |
|---|---|
| **instant** | a point on the monotonic timeline, with no epoch. The type is `Instant`. Never a wall-clock reading. |
| **timestamp** | a point on the absolute UTC timeline. The type is `Timestamp`. Never monotonic. |
| **civil** | a wall-clock reading with no zone — what a clock on a wall says. `CivilDate`, `CivilTime`, `CivilDateTime`. |
| **zoned** | a civil reading plus the zone that makes it an instant. `ZonedDateTime`. |
| **offset** | the signed seconds a zone is ahead of UTC *at a moment*. Not a zone: `+01:00` is an offset, `Europe/London` is a zone. |
| **zone** | a named rule set from the IANA database, with a history of offsets. |
| **duration** | an exact count of nanoseconds. **The prelude's `Duration`.** Never a calendar span. |
| **period** | a calendar span — years, months, days, and an exact sub-day part. `Period`. Never convertible to a duration without a starting point. |
| **transition** | the moment a zone's offset changes. |
| **ambiguous** | a civil reading that occurs twice, at a fall-back transition. |
| **nonexistent** | a civil reading that never occurs, in a spring-forward gap. |
| **day number** | days since 1970-01-01, the integer the calendar algorithms work in. |
| **epoch** | 1970-01-01T00:00:00Z, and only that. An `Instant` has no epoch (M-2). |
| **the range** | `year ∈ [−9999, +9999]` — `CALENDAR.md` §2, checked at every constructor. |
| **layout** | a typed list of `FmtPart`s describing a format. Never a string. |
| **the host** | `src/host/`, the one impure module. |
| **the table** | the generated zone data in `src/zone/`. |
| **the sweep** | an exhaustive test over a whole domain, as opposed to a sampled one. |
| **the budget** | the three public error identities, and the rule that there are three. |
| **arm** | one `pick` case in a consuming program's `failsafe`. |

## Words deliberately not used

| Not used | Because |
|---|---|
| "date" alone as a type name | ambiguous between a civil date, a zoned date and an instant; `CivilDate` says which |
| "datetime" as a type name | same reason; `CivilDateTime` and `ZonedDateTime` say which |
| "UTC offset" for a zone | a zone has many offsets over its history; the word for the current one is "offset" |
| "local time" without a zone | there is no implicit local zone (S-11); the phrase is always "local time in *zone*" |
| "wall clock" for `Timestamp` | a `Timestamp` is UTC and has no wall; a wall reading is civil |
| "elapsed" for a `Timestamp` difference | elapsed time is an `Instant` difference; a `Timestamp` difference is a nominal one, which leap seconds make different (M-12) |
| "naive" for a civil time | Python's word. "Civil" is the term the standards and the literature use and it is not pejorative |
| "aware" for a zoned time | same |
| "timezone" as one word | the IANA term is "time zone"; the type is `ZoneId` |
| "format string" | there is none (F-1); the word is "layout" and it is a value |
