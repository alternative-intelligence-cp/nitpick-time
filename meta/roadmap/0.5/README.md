# Cycle 0.5 — The zone table

**`tools/gen_tzdb.py` and the committed tables.** The generator runs at
development time; the build needs only the compiler.

## Decisions in

TM-007 (the database is compiled in from a pinned release), TM-028 (reading the
system database is post-1.0). Both settled.

**Open questions to settle:** Q-1 — the tzdata release to pin. O-X2 — the real
emitted size, which cycle 0.0.5's spike has already measured once; this cycle
records the number for the *real* generator.

## Decisions this cycle inherits from 0.0.5

The size spike (0.0.5) ran the generator's core loop and measured the emitted
object. **If it came in above ~1 MiB, O-Z1 was reopened and answered before
cycle 0.1 started**, and this cycle implements whatever that answer was. If it
came in as estimated, this cycle is the estimate made real.

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.5.0 | **The TZif reader** — in Python, at generation time, never at run time | the release read correctly |
| 0.5.1 | **The POSIX rule parser** — also at generation time, emitting structured rows | extrapolation past the last transition |
| 0.5.2 | **The emitter** — the four tables, the name pool, the version file | committed Nitpick source |
| 0.5.3 | **The checks** — regeneration and the table invariants | a hand-edited table is caught |
| 0.5.4 | **Close** | `done/0.5/`, `0.6.0.md` written |

## Checklist

### 0.5.0 — the TZif reader
- [ ] Q-1 answered: the release pinned, recorded in `src/zone/version.npk` as `pub fixed string:TZDB_VERSION`, and named in every generated file's header
- [ ] the v2+ block read (64-bit transitions), not the v1 block
- [ ] canonical zones only: symlinks resolved as links (Z-10), the `posix/` and `right/` trees excluded — `right/` is the leap-second variant and TM-006 does not model leap seconds
- [ ] the generator **hard-fails** on a zone it cannot read, naming it, rather than emitting a row it cannot honour
- [ ] the source release's own name and checksum recorded beside the tables

### 0.5.1 — the POSIX rule parser
- [ ] the footer string parsed **by the generator** (Z-12), emitting a `PosixRule` row
- [ ] the `Mm.w.d/time` form, which is what modern tzdata emits
- [ ] the forms it does **not** handle — `Jn`, bare `n`, negative-DST oddities — cause a **named refusal**, not a silent `-1`
- [ ] a zone with no DST gets `has_dst: 0` and a single offset, not a rule
- [ ] `posix_rule: -1` only where the release genuinely has no footer

### 0.5.2 — the emitter
- [ ] the four tables and the name pool in `ZONE_MODEL.md` §3's shape
- [ ] links (aliases) resolved at generation time into two `ZoneEntry` rows sharing one transition range (Z-10), with the link set recorded for the documentation
- [ ] the zone-name index **lexicographically sorted**, because Z-9's lookup is a binary search over it
- [ ] **deterministic output**: no dictionary iteration order, no `set` iteration, no timestamps in the header — the `repro` check (B-4) is what catches a violation and this is the largest file in the tree
- [ ] `#size_of` of each row asserted, so §3's arithmetic stays checkable
- [ ] **the real emitted size measured and recorded** in `meta/research/tzdb-size.md`, beside 0.0.5's spike number and §3's estimate

### 0.5.3 — the checks
- [ ] `check_tables_regenerate` — the committed tables byte-identical to a fresh generator run, and **seen to fail** against a one-character hand edit
- [ ] `check_table_invariants` — every transition slice sorted and **strictly** increasing; every `type_index` in its zone's range; every name-pool offset and length in range; the name index sorted
- [ ] both run on every full invocation

## Gate

The tables regenerate byte-identically, every invariant holds over the
committed data in one pass, and the real emitted size is a recorded number.

## Watch for

- **Determinism in the generator is not optional.** A Python `set` or an
  unsorted `dict` iteration is enough to make the emitted file differ between
  runs, which breaks `repro` (B-4) in a way that looks like a compiler bug. Sort
  everything, explicitly, and say so in the generator's header.
- **`right/` is the leap-second variant** and must be excluded, or the tables
  will describe a scale TM-006 says the library is not on.
- **A zone the reader cannot parse is a stop, not a skip.** A silently missing
  zone is a lookup that fails for one user in one country, months later.
- **The largest file in the tree lands here**, so read `git diff --stat` before
  committing and make sure the number matches the measurement.
