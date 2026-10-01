# `src/span/` — spans

`Instant`, `Timestamp`, and `Period`, plus the constructors that extend the
prelude's `Duration` (`duration_mins`, `duration_hours`, `duration_days`,
`duration_weeks`). **`ntime` declares no `Duration` of its own** (TM-004).

Governed by `meta/specs/TIME_MODEL.md` and `meta/specs/SPAN_MODEL.md`. Built in
cycles 0.2 and 0.7 — the types first, the calendar arithmetic after zones
exist, because `Period` addition on a zoned value needs them.

**What is here since cycle 0.2.0:** `span.npk` — `Instant` and `InstantClock`,
`instant_of`, `instant_since`, `instant_add` and `instant_cmp` (TM-215, TM-216).
`Timestamp` is cycle 0.2.1's, the `Duration` constructors 0.2.3's, `Period`
0.7's.
