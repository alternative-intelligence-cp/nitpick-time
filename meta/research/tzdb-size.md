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

## The spike (cycle 0.0.5)

*(Filled by 0.0.5. Its whole purpose is to replace the estimate above with a
measured object size before cycle 0.1 starts, because a decision the entire
specification set rests on does not get to be wrong quietly.)*

| Quantity | Measured |
|---|---|
| zones | |
| transitions (v2+ block) | |
| types | |
| emitted `.npk` bytes | |
| emitted `.ll` bytes | |
| **linked object bytes** | |
| tables emitted as `@global constant` | |
| startup cost | |

## The real generator (cycle 0.5)

*(Filled by 0.5.2, from `tools/gen_tzdb.py`'s actual output.)*

## The decision this feeds

`meta/roadmap/0.0/0.0.5.md` §3 has the thresholds. In short: at or under
~500 KiB the estimate stands and O-X2 closes; above ~1 MiB, O-Z1 reopens
**before cycle 0.1 starts** and the candidates are, in order — drop the pre-1900
LMT transitions, delta-encode the transition times, or a build-time zone
subset.
