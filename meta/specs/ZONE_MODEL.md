# Time zones

The defining decision of this library, the table it produces, and what happens
at the two edges every zone has.

---

## 1. The decision: the database is compiled in

**Rule Z-1 (TM-007).** `ntime` carries the IANA time-zone database **generated
from a named release and committed as Nitpick source**. It does not read
`/usr/share/zoneinfo`, it does not parse TZif at run time, and it does not
consult `$TZ` unless a program asks it to (`HOST.md` §4).

The argument, in the order the reasons matter:

1. **A TZif reader is an untrusted-input binary parser** inside a library whose
   claim is that it has none. The files are system-owned, but "system-owned" is
   not "trusted" in a language whose selling point is that a bad input is a
   controlled stop rather than a surprise.
2. **Its answers depend on machine state.** The same program on two machines
   would disagree about what time it is, which takes the whole library out of
   `SAFETY.md` §3's purity rule and makes every zoned test a test of the
   machine it ran on.
3. **The ecosystem has already answered the analogous question twice.** The
   compiler generates its builtin signature table and its flag tables and
   commits them; the sibling TUI library refused terminfo (T-003) and generates
   its Unicode tables (T-021) for exactly these reasons. A third answer here
   would be an inconsistency, not a nuance.
4. **The size objection does not survive measurement.** §3.

**Rule Z-2 — the cost is stated rather than argued away.** The tzdb changes
several times a year, usually because a government changed its mind at short
notice. **A program built with release *R* believes *R* until it is rebuilt.**
For most software that is fine and is what a static binary means. For software
where it is not — a long-running server that must track the current database —
the answer is Z-3, and the answer is *not* to make everybody's build
non-deterministic.

**Rule Z-3 (TM-028) — reading the system database is post-1.0, opt-in, and
never the default.** Cycle 1.1 adds `ntime/tzif.npk`: a TZif reader with its own bounds,
its own fuzzer and its own error, which a program must import on purpose and
call on purpose. It does not replace the compiled table; it produces a
`ZoneId` into a *separate*, runtime-built table, so a program using both can
say which answered. It is deferred to 1.1 rather than shipped at 1.0 because
1.0 should not ship a binary parser nobody has needed yet.

---

## 2. The pinned release

**Rule Z-4.** The release name lives in exactly one file,
`src/zone/version.npk`, as `pub fixed string:TZDB_VERSION` — `"2026c"`, or
whatever cycle 0.5 pins — and appears in the header comment of every generated
file.

**Rule Z-5 — upgrading is a recorded decision**, not a routine refresh. It
regenerates every table, re-runs the transition sweep, and the diff is reviewed
as *which zones changed and when*. A tzdb bump that silently moves an offset is
exactly the change a review should see.

**Rule Z-6 — `ntime_tzdb_version()` is public**, so a program can log what it
believes, and `COMPAT.md` §3 states the policy: a release bump is a **minor**
version of `ntime`, never a patch, because it changes computed answers.

---

## 3. The table, and its measured size

**MEASURED, at cycle 0.0.5 (TM-135), against tzdata 2026c**, over the canonical
zones only (symlinks and the `posix/` and `right/` trees excluded). The four
tables and two pools were emitted as real Nitpick source, compiled, linked and
run, and the bytes below were read off the object with `nm -S` rather than
computed:

| | measured | the 0.0.3 estimate |
|---|---|---|
| canonical zones | 447 | 447 |
| transitions, all zones | **27 183** (the v2+ block) | 26 838 (the v1 block) |
| local-time types | **2 513** | 2 484 |
| largest single zone | **`Asia/Hebron`, 310** | `Europe/London`, 242 |
| `#size_of<ZoneTransition>` | **16** | 12 |
| `#size_of<ZoneType>` | 8 | 8 |
| `#size_of<ZoneEntry>` | **28** | 16 |
| `#size_of<PosixRule>` | **32** | — |
| **the four tables and two pools** | **475 006 B = 463.9 KiB** | ≈ 356 119 B |
| **the same, with `POSIX_RULES`** | **489 310 B = 477.8 KiB** | not estimated |

434 928 (`TRANSITIONS`) + 20 104 (`TYPES`) + 12 516 (`ZONES`) + 6 592
(`NAME_POOL`) + 866 (`ABBR_POOL`) = **475 006**, plus 14 304 for 447
`PosixRule` rows.

That is the whole database, every zone, in a static binary — **37% above the
estimate and still inside the budget `0.0.5.md` §3 set in advance**, which is
what a threshold decided before the measurement is for. Four things the
estimate got wrong, all four in the same direction: two row widths derived from
field sums instead of measured, the transition count read from the v1 block
that stops at 2038, and no abbreviation pool at all. TM-135 has each with its
number.

**Rule Z-7b (TM-135) — the margin is part of the answer.** The gap to
`0.0.5.md` §3's next threshold is **22 690 bytes, which is 1 418 transitions**
— about 4.4%. tzdata adds transitions at every release, so cycle 0.5's
regeneration check re-measures this number and `COMPAT.md` carries it, rather
than anyone assuming the headroom is large.

**And there are two pools, not one.** Zone names need no terminator because
`ZoneEntry` carries `name_len`; `ZoneType.abbr_offset` has no length beside it,
so the abbreviation pool is NUL-terminated. 187 distinct abbreviations, 866
bytes.

**Rule Z-7 — the representation is four flat tables plus a name pool**, which
is the shape TZif itself uses and the shape the sibling library's range tables
use, for the same reason: one invariant per table, checkable in one pass.

```nitpick
pub struct:ZoneTransition = { int64:at_utc; int32:type_index; };   // sorted per zone
pub struct:ZoneType       = { int32:offset_secs; uint8:is_dst; uint16:abbr_offset; };
pub struct:ZoneEntry      = {
    uint32:name_offset; uint16:name_len;
    uint32:trans_first; uint16:trans_count;
    uint32:type_first;  uint16:type_count;
    int32:posix_rule;                       // index into POSIX_RULES, or -1
};
```

**Rule Z-8 — lookup is a binary search over the zone's transition slice**, and
the slice is `[trans_first, trans_first + trans_count)` of the one flat
transition array. One accessor pair guards the bound (`SAFETY.md` S-17), the
search's termination is a `prove` obligation, and the "sorted and strictly
increasing" invariant is checked over the committed table in one pass by
`check_table_invariants`.

**Rule Z-9 — zone names are looked up by binary search over a
lexicographically sorted index.** `zone_by_name("Europe/London")` is
`O(log 447)` string comparisons. An unknown name is `ETimeZone`/`Unknown`.

**Rule Z-10 — links (aliases) are resolved at generation time**, not at run
time. `US/Eastern` and `America/New_York` produce two `ZoneEntry` rows sharing
one transition range, so a lookup of either is one search and neither is a
special case. The generator records which names were links so the documentation
can say so.

---

## 4. Past the last transition

**Rule Z-11 — extrapolation uses the zone's POSIX rule, generated as
structured data.** TZif v2+ files end with a POSIX `TZ` string —
`GMT0BST,M3.5.0/1,M10.5.0` — describing the rule to apply past the last
explicit transition. Without it, every DST zone gives the wrong answer past
about 2037, which is inside the supported range and inside plenty of software's
lifetime.

**Rule Z-12 — the string is parsed by the GENERATOR, never at run time.** It
becomes a `PosixRule` row:

```nitpick
pub struct:PosixRule = {
    int32:std_offset_secs;  int32:dst_offset_secs;
    uint16:std_abbr_offset; uint16:dst_abbr_offset;
    // Mm.w.d/time, the only form modern tzdata emits
    uint8:start_month;  uint8:start_week;  uint8:start_dow;  int32:start_secs;
    uint8:end_month;    uint8:end_week;    uint8:end_dow;    int32:end_secs;
    uint8:has_dst;
};
```

A run-time parse of that string would be a second parser on a second input
format for a value that never changes after the build. The generator refuses a
form it does not recognise (`J n`, bare `n`, and the negative-DST oddities) and
says which zone, rather than emitting a row it cannot honour.

**Rule Z-13 — before the first transition**, the offset is the zone's first
type — which for most zones is Local Mean Time, an approximation to the second
that nobody has ever needed. Stated so the answer is not a surprise, and
`COMPAT.md` §4 records that pre-1900 offsets are LMT approximations carried
from the database rather than a claim about history.

---

## 5. The two edges

Every DST zone has two kinds of local time that are not a single instant, and
this is where date libraries differ from each other.

**Rule Z-14 — a fall-back transition makes a wall reading AMBIGUOUS.** In
`Europe/London` on 2026-10-25, `01:30` happens twice: once at UTC 00:30 with
offset +01:00, and once at UTC 01:30 with offset +00:00.

**Rule Z-15 — a spring-forward transition makes a wall reading
NONEXISTENT.** In `Europe/London` on 2026-03-29, `01:30` never happens; the
clock goes from `00:59:59+00:00` to `02:00:00+01:00`.

**Rule Z-16 (TM-020) — the caller chooses, by name, with no default** (M-15):

| Function | Ambiguous | Nonexistent |
|---|---|---|
| `zoned_strict` | `ETimeZone` / `Ambiguous` | `ETimeZone` / `Nonexistent` |
| `zoned_earlier` | the first occurrence | the instant *before* the gap |
| `zoned_later` | the second occurrence | the instant *after* the gap |
| `zoned_compatible` | the **earlier** | shifted **forward** by the gap width |

`zoned_compatible` matches what ICU and Temporal call "compatible" and is what
most software wants. It is a name a caller has to type, because a default here
is a silent choice about an hour of somebody's day.

**Rule Z-17 — a `ZonedDateTime` always knows its offset**, so arithmetic on it
never has to re-resolve an ambiguity it already settled. Re-resolution happens
only when the *wall* fields change (N-13's year/month/day steps), and that is
where Z-16's mode is supplied again.

**Rule Z-18 — transitions are not always one hour and not always DST.** Lord
Howe Island shifts by 30 minutes; zones have changed their *standard* offset
outright (Samoa crossed the date line in 2011, losing a whole day). Nothing in
the lookup assumes an hour, a direction, or that a transition is
daylight-saving at all — it reads the type table. Stated because "add or
subtract an hour" is the shortcut every implementation reaches for.

---

## 6. Fixed offsets

**Rule Z-19 — a fixed offset is a `ZoneId` too**, produced by
`zone_fixed(offset_secs)`, valid in `[−64 800, +64 800]` (±18:00, the range
IANA and RFC 3339 permit). It has no transitions and no POSIX rule, so it takes
the same code path with a one-element type table.

*Reasoning:* the alternative is a `ZonedDateTime` whose zone is sometimes a
name and sometimes an offset, which is a tagged union in every function that
touches it. One type, one path.

**Rule Z-20 — `UTC` is `zone_fixed(0)` and is also available as the constant
`ZONE_UTC`**, with the same identity, so `zone_eq(z, ZONE_UTC)` answers.

---

## 7. The gates

**Rule Z-21 — the transition sweep.** For every zone, for every transition in
its table: the second before it and the second after it resolve to the offsets
the table says, and the wall readings either side are what the transition
implies. 26 838 transitions × a handful of probes each is a complete sweep of
the table's own claims, and it runs in seconds.

**Rule Z-22 — the round trip, per zone, over a swept range.** For a
representative set of zones and every hour from 1970 to 2040:
`zoned_compatible(civil_of(instant, zone), zone) == instant` except where the
wall reading is ambiguous, where the earlier is required. That is the property
that catches an off-by-one in the search.

**Rule Z-23 — the cross-oracle.** A Python generator emits, from the *same*
pinned release via `zoneinfo`, a corpus of `(zone, utc_second, offset, abbr,
is_dst)` rows covering every transition and a sampling between them, committed
under `tests/fixtures/zone/`. The library must agree with every row. This is
the check that the *generator* read the database correctly, which Z-21 cannot
see because it only checks the table against itself.

---

## 8. Open items

- ~~**O-Z1 — whether to ship every zone or a selectable subset.**~~
  **SETTLED at cycle 0.0.5 by TM-135: ship them all.** §3's measured **477.8
  KiB** is inside the first of `0.0.5.md` §3's three bands, decided before the
  measurement was taken, so the fallbacks it named — dropping the pre-1900 LMT
  transitions (Z-13), delta-encoding the transition times, or a build-time zone
  subset — are not reached. The question stays written here rather than deleted
  because the margin is 4.4% (Z-7b) and a later release could reopen it; it
  reopens against a number, not a fear.
