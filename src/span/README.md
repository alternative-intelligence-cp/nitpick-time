# `src/span/` — spans

`Instant`, `Timestamp`, and `Period`, plus the constructors that extend the
prelude's `Duration` (`duration_mins`, `duration_hours`, `duration_days`,
`duration_weeks`). **`ntime` declares no `Duration` of its own** (TM-004).

Governed by `meta/specs/TIME_MODEL.md` and `meta/specs/SPAN_MODEL.md`. Built in
cycles 0.2 and 0.7 — the types first, the calendar arithmetic after zones
exist, because `Period` addition on a zoned value needs them.

**What is here since cycle 0.2.0:** `span.npk` — `Instant` and `InstantClock`,
`instant_of`, `instant_since`, `instant_add` and `instant_cmp` (TM-215, TM-216);
since cycle 0.2.1 `Timestamp` and `timestamp_of` (TM-219, TM-220); and since
0.2.2 `timestamp_to_utc` and `civil_to_utc`, the conversions to and from the
civil scale, read as UTC (TM-222); and since 0.2.3 the four `Duration`
constructors, `timestamp_add` and `timestamp_since` (TM-233, TM-234,
TM-236). `Period` is 0.7's, and so is `timestamp_until` (TM-237). (Until cycle
0.2.2 this said the conversions were that cycle's, and until 0.2.3 that the
constructors were.)
