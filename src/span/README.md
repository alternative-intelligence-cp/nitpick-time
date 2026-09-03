# `src/span/` — spans

`Instant`, `Timestamp`, and `Period`, plus the constructors that extend the
prelude's `Duration` (`duration_mins`, `duration_hours`, `duration_days`,
`duration_weeks`). **`ntime` declares no `Duration` of its own** (TM-004).

Governed by `meta/specs/TIME_MODEL.md` and `meta/specs/SPAN_MODEL.md`. Built in
cycles 0.2 and 0.7 — the types first, the calendar arithmetic after zones
exist, because `Period` addition on a zoned value needs them.
