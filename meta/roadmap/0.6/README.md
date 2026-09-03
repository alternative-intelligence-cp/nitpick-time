# Cycle 0.6 — Zoned time

**`src/zone/`'s lookup, `ZonedDateTime`, and the two edges every DST zone
has.** The cycle where a date library is usually wrong.

## Decisions in

TM-020 (four resolution modes, no default), TM-007 (the compiled table). Both
settled.

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.6.0 | **The lookup** — the binary search, the accessors, fixed offsets | an offset for any instant in any zone |
| 0.6.1 | **Extrapolation** — the POSIX rule applied past the last transition | correct answers past 2037 |
| 0.6.2 | **`ZonedDateTime`** — the type, its invariant, and the instant as source of truth | civil fields that cannot disagree with the instant |
| 0.6.3 | **The edges** — the four resolution modes | ambiguity and gaps answered explicitly |
| 0.6.4 | **The sweeps** — transitions, the per-zone round trip, the cross-oracle | the cycle's gate |
| 0.6.5 | **Close** | `done/0.6/`, `0.7.0.md` written |

## Checklist

### 0.6.0 — the lookup
- [ ] `zone_by_name` — binary search over the sorted name index (Z-9); an unknown name is `ETimeZone`/`Unknown`
- [ ] `zone_offset_at(zone, instant)` — binary search over the zone's transition slice (Z-8)
- [ ] **one accessor pair guards the slice bound** (S-17), and nothing outside `src/zone/` indexes the raw tables
- [ ] the search's invariant and termination as `prove`-shaped comments (`VERIFICATION.md` §6)
- [ ] **before the first transition**, the zone's first type (Z-13) — usually LMT, and the documentation says so
- [ ] `zone_fixed(offset_secs)` in `[−64 800, +64 800]` (Z-19), taking the same code path with a one-element type table
- [ ] `ZONE_UTC` as `zone_fixed(0)` with a stable identity (Z-20)
- [ ] **nothing assumes an hour, a direction, or that a transition is DST** (Z-18) — a test over Lord Howe (30 minutes) and Samoa's 2011 date-line crossing

### 0.6.1 — extrapolation
- [ ] the `PosixRule` applied past the last explicit transition (Z-11)
- [ ] a test at a date past 2037 in a DST zone, against the cross-oracle — **this is the case that is silently wrong without the rule**
- [ ] a zone with `posix_rule: -1` extrapolates as its last type, constantly, and the documentation says so
- [ ] the rule's own week-of-month arithmetic (`Mm.w.d`) tested at `w == 5`, which means "last", not "fifth"

### 0.6.2 — `ZonedDateTime`
- [ ] the type with the instant as **source of truth** and the civil fields as a cache (M-14)
- [ ] every operation that could make them disagree recomputes them
- [ ] a property test asserting the invariant after **every** operation the type has
- [ ] `zone_at(timestamp, zone)` — the always-unique direction

### 0.6.3 — the edges
- [ ] `zoned_strict`, `zoned_earlier`, `zoned_later`, `zoned_compatible` (Z-16)
- [ ] **no default**: there is no `zoned(civil, zone)` — a test asserts the four names are the only entry points
- [ ] `zoned_compatible`'s gap behaviour is *shift forward by the gap width*, and its ambiguity behaviour is *the earlier* — each with a test naming a real transition
- [ ] `ZoneFault` with `Unknown`, `Ambiguous`, `Nonexistent`
- [ ] the worked cases from `ZONE_MODEL.md` §5 — `Europe/London` 2026-03-29 01:30 and 2026-10-25 01:30 — as named tests

### 0.6.4 — the sweeps — THE GATE
- [ ] **the transition sweep**: every transition in the table, the second before and the second after, resolving to the offsets the table says (Z-21)
- [ ] **the per-zone round trip**: for a representative zone set, every hour from 1970 to 2040, `zoned_compatible(civil_of(i, z), z) == i` except where ambiguous (Z-22)
- [ ] **the cross-oracle**: `tools/gen_zone_oracle.py` emitting rows from Python's `zoneinfo` at the *same pinned release*, and agreement over every row (Z-23)
- [ ] the three are separate: the sweep checks the table against itself, the round trip checks the lookup, and the oracle checks that the **generator** read the database correctly

## Gate

All three sweeps green: the table's own claims, the lookup's round trip, and
agreement with `zoneinfo` at the same release.

## Watch for

- **The first and last element of a transition slice** are where a binary
  search is wrong, and the transition sweep hits both for every zone — which is
  why it is the gate rather than a sample.
- **Past 2037 is silently wrong without the POSIX rule**, and it is inside the
  supported range and inside plenty of software's lifetime. 0.6.1's test is not
  optional.
- **`w == 5` means "last", not "fifth"** in a POSIX rule. Getting it wrong
  moves a transition by a week in some years and not others.
- **The cross-oracle must use the same release** the tables were generated
  from, or it will disagree for reasons that are not defects.
