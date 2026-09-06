# The compiled tzdb: size measurements

TM-007 — the time-zone database is compiled in — rests on the claim that the
whole IANA database fits comfortably in a static binary. This file is where
that claim is a number.

## The estimate (2026-09-03, from the system database)

Measured on the workbench against **tzdata 2026c** at `/usr/share/zoneinfo`,
over canonical zones only: symlinks excluded (they are links, resolved at
generation time by `ZONE_MODEL.md` Z-10), and the `posix/` and `right/` trees
excluded — `right/` is the leap-second variant, which TM-006 says the library
is not on.

| Quantity | Value |
|---|---|
| canonical zones | 447 |
| transitions (v1 block) | 26 838 |
| local-time types | 2 484 |
| largest single zone | `Europe/London`, 242 transitions |

Estimated compiled size, in `ZONE_MODEL.md` §3's representation
(`{int64 at_utc, int32 type_index}` per transition, `{int32 offset, uint8
is_dst, uint16 abbr_offset}` per type, 16 bytes per zone entry, plus the name
pool):

| Table | Bytes |
|---|---|
| transitions | 322 056 |
| types | 19 872 |
| zone index | 7 152 |
| name pool | 7 039 |
| **total** | **356 119 ≈ 348 KiB** |

Two things this estimate does **not** account for, both of which the real
measurement will:

1. **The v2+ block has more transitions than the v1 block** it was measured
   from — v1 stops at 2038 by construction. The real generator reads the 64-bit
   block (`ZONE_MODEL.md` Z-11's reason), so the transition count will be
   higher.
2. **The emitted Nitpick source, the emitted IR and the linked object are three
   different sizes**, and only the third is what a consumer pays.

## The spike (cycle 0.0.5) — 2026-09-05, pin `aaffb87`, TM-135

Emitted from the **same** tzdata 2026c at `/usr/share/zoneinfo`, compiled,
linked and run. Spike: `meta/scratch/tzdb_spike/` (P-28, throwaway);
`TRANSCRIPT.txt` there has every command with its exit status beside the
artefact it produced, and the instrument was commissioned positive and negative
before any number was believed.

| Quantity | Measured | Estimated above |
|---|---|---|
| zones | 447 | 447 |
| transitions (v2+ block) | **27 183** | 26 838 (v1) |
| types | **2 513** | 2 484 |
| largest single zone | **`Asia/Hebron`, 310** | `Europe/London`, 242 |
| `#size_of<ZoneTransition>` | **16** | 12 |
| `#size_of<ZoneType>` | 8 | 8 |
| `#size_of<ZoneEntry>` | **28** | 16 |
| `#size_of<PosixRule>` | **32** | — |
| emitted `.npk` bytes | 2 040 106 | — |
| emitted `.ll` bytes | 1 900 429 | — |
| object (`.o`) bytes | 510 872 | — |
| linked static binary | 543 432 | — |
| **the four tables and two pools** | **475 006 B = 463.9 KiB** | ≈ 356 119 B |
| **the same, with `POSIX_RULES`** | **489 310 B = 477.8 KiB** | not estimated |
| tables emitted as `constant` | **yes, all of them** | assumed |
| startup cost | **zero** — `llvm.global_ctors` absent, `.data` 112 B | assumed |

**The table figure is the one that answers the question, and it is not the
object size.** Read off the object with `nm -S`:

| symbol | bytes | = rows × width |
|---|---|---|
| `TRANSITIONS` | 434 928 | 27 183 × 16 |
| `TYPES` | 20 104 | 2 513 × 8 |
| `ZONES` | 12 516 | 447 × 28 |
| `NAME_POOL` | 6 592 | 6 592 × 1 |
| `ABBR_POOL` | 866 | 866 × 1 |
| **total** | **475 006** | |
| `POSIX_RULES` (second variant) | 14 304 | 447 × 32 |

**The control that makes that a measurement rather than a subtraction.** The
same program emitted at **one zone** gives a 36 096 B object carrying 82 B of
tables, so the program-and-prelude share is 36 014 B — against 510 872 −
475 006 = 35 866 B taken the other way. Two routes, agreeing to 148 B. In the
linked binary the two routes give 68 414 and 68 426, agreeing to 12 B.

**Both predictions in the estimate's own list came true, and two it did not
make cost more.** The v2+ block does hold more transitions than the v1 block
(+345), and the three artefact sizes are indeed different. What it did not
foresee: two row widths were derived from field sums instead of measured
(`ZoneTransition` 12 → 16, `ZoneEntry` 16 → 28), which is most of the 37% gap;
and `ZoneType.abbr_offset` needs an abbreviation pool that the estimate's
single "name pool" row was not.

**Caution for anyone re-deriving these.** The `.ll` byte count embeds
`npk.site.paths`, so emitting the same source from two directories whose names
differ by one character changes it by 14 bytes — one per site — while the
object and the binary do not move at all. Quote the object.

## The real generator (cycle 0.5)

*(Filled by 0.5.2, from `tools/gen_tzdb.py`'s actual output.)*

## The decision this feeds — ANSWERED

`meta/roadmap/done/0.0/0.0.5.md` §3 has the thresholds, decided before the
measurement. **477.8 KiB is row one: TM-007 stands, O-X2 closes, O-Z1 is
settled as "ship them all", and cycle 0.5 proceeds.** None of the fallbacks —
dropping the pre-1900 LMT transitions, delta-encoding the transition times, or
a build-time zone subset — is reached.

**The margin is 22 690 bytes**, which is 512 000 − 489 310, and at 16 bytes a
row that is **1 418 transitions** — about 4.4%. tzdata adds transitions every
release. 0.5's regeneration check re-measures and `COMPAT.md` carries the
number, so a bump that crosses the line is a red run rather than a discovery.
