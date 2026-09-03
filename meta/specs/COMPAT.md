# Compatibility and support

What `ntime` supports, what its version numbers mean, and what is deliberately
absent.

---

## 1. The platform

**Rule K-1 (TM-008) — Linux on x86-64 only, at 1.0.** `src/host/` is Linux syscalls with
Linux numbers: `clock_gettime` (228), `readlink` (89). A port to `aarch64`
Linux changes the numbers and nothing else, and is post-1.0 (cycle 1.2). A BSD
or macOS port changes more — different clock ids, a different `readlink`
behaviour, and no `/etc/timezone` — and is a cycle with its own decision rather
than something left half-done behind a conditional.

**Rule K-2 — everything outside `src/host/` is platform-independent by
construction**, because it is pure arithmetic over values (`SAFETY.md` §3). A
port is a rewrite of one module.

---

## 2. Standards

| Standard | Status |
|---|---|
| **proleptic Gregorian calendar** | implemented in full, ±9999 |
| **ISO 8601-1:2019** date, time, datetime, week date, ordinal date | implemented for the forms in `FORMAT_MODEL.md` §2 |
| **ISO 8601 expanded years** (`+012026`) | emitted and parsed **only** through the `_expanded` functions, because the standard requires prior agreement |
| **ISO 8601 durations** (`P1Y2M3DT4H5M6S`) | implemented for `Period` |
| **RFC 3339** | implemented in full, strict and lenient |
| **RFC 5322** date-time | implemented; obsolete forms (two-digit years, named military zones) parsed, never emitted |
| **RFC 9110** HTTP-date / IMF-fixdate | implemented; the two obsolete formats (RFC 850, asctime) parsed, never emitted |
| **IANA tzdb** | compiled in from a pinned release, §3 |
| **ISO 8601 intervals** (`start/end`, `start/duration`) | **not implemented** — §4 |
| **leap seconds** | **not modelled** — `TIME_MODEL.md` §5, by decision |

---

## 3. The tzdb version policy

**Rule K-3.** The compiled release is `ntime`'s, not the machine's, and
`ntime_tzdb_version()` reports it.

**Rule K-4 — a tzdb release bump is a MINOR version of `ntime`, never a
patch.** It changes computed answers: a zone whose government moved a
transition will produce different results for dates it covers. That is not a
bug fix and it should not arrive in a patch release.

**Rule K-5 — the upgrade is a reviewed diff.** Regenerate, run the transition
sweep and the cross-oracle, and review *which zones changed and over what
range*. A bump that silently moves an offset is exactly the change a review
should see.

**Rule K-6 — a long-running program holds the release it was built with**, and
that is what a static binary means. A program that must track the current
database uses the post-1.0 opt-in of `ZONE_MODEL.md` Z-3, and does so visibly.

---

## 4. Deliberately absent

Each of these is a decision, not an oversight, and each has a reason worth more
than the feature.

| Not supported | Why |
|---|---|
| **non-Gregorian calendars** (Hebrew, Islamic, Japanese eras, Chinese) | each is a substantial library with its own data and its own edge cases |
| **the Julian/Gregorian cutover** | it is a per-jurisdiction date, so honouring it would make the calendar itself zone-dependent (`CALENDAR.md` C-1) |
| **leap seconds** | `TIME_MODEL.md` M-11: the clock is not on that scale, and a table would expire |
| **localised month and weekday names** | a data problem the size of the tzdb with no canonical source (`FORMAT_MODEL.md` §4) |
| **`strftime`-style format strings** | `FORMAT_MODEL.md` §1 — against the grain of D-053, and the typed layout replaces it exactly |
| **business days, holidays** | per-jurisdiction data with a shorter shelf life than the tzdb; the caller supplies a predicate |
| **intervals and ranges** (`Interval`, `RecurringRule`) | genuinely useful, genuinely a separate concern, and easy to build on what is here; post-1.0 if a consumer asks |
| **relative/humanised text** ("3 hours ago") | localisation again, plus a policy about rounding that no two products agree on (Q-3) |
| **setting the system clock** | privileged, system-wide, and not a date library's business (`HOST.md` §5) |
| **NTP status** (`adjtimex`) | useful and separate |
| **reading `/usr/share/zoneinfo`** | `ZONE_MODEL.md` §1 at 1.0; opt-in at 1.1 |

---

## 5. Interoperation with the sibling libraries

**Rule K-7 (TM-027) — `ntime` has no dependencies, including on siblings**
(`BUILD.md` §4). The one real overlap is recorded rather than resolved:

**`nitpick-parse` needs datetime scanning.** TOML v1.0.0 has four datetime
types — offset date-time, local date-time, local date, local time — and its
parser must produce them. Those are `ntime`'s types and `ntime`'s parsers.
Until dependency resolution lands (O-N1), `nparse` carries its own scanner and
the two libraries **share test vectors by committing the same corpus in both**,
so a divergence is a red run somewhere rather than a silent disagreement.
Tracked as O-X1.

---

## 6. The `failsafe` arm contract

**Rule K-8 — this is part of the public API** and is published in `docs/` at
1.0, generated and checked rather than written (`SAFETY.md` S-6):

| If you import | Your `failsafe` must name |
|---|---|
| `ntime/cal.npk` only | `ETimeValue` |
| `+ ntime/span.npk` | `ETimeValue` |
| `+ ntime/zone.npk` | `ETimeValue`, `ETimeZone` |
| `+ ntime/fmt.npk` | `ETimeValue`, `ETimeZone`, `ETimeParse` |
| `ntime/lib.npk` (everything) | all three |

Plus whatever system identities the program's own machinery can raise, which
REACH-002 computes and is not ours.

**Rule K-9 — adding a fourth identity is a MAJOR version** (TM-013), because it
is a compiler-enforced source break in every consumer.
