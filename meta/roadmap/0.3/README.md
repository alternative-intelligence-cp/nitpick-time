# Cycle 0.3 — The host boundary

**`src/host/`: the clocks, the system-zone discovery, and the test double.**
Five functions, and the check that nothing else in the library is impure.

## Why here, and why it is small

Because it is the only impure module (TM-018), and everything above it is
testable without it. Putting it early gets the syscall shapes verified while
the library is small; keeping it to five functions is what makes the purity
claim worth making.

## Decisions in

TM-008 (Linux x86-64), TM-018 (purity), TM-019 (no implicit local time). All
settled.

**And one open question reaches it, blocking nothing: `meta/OPEN_QUESTIONS.md`
Q-7**, the author's — whether `instant_of`'s name should say it takes a raw
reading. `host_now_instant` and `host_now_boot` build their readings through
`instant_of` (0.3.0's checklist); under the recommended answer nothing here
changes, and under the other the rename lands first, by a decision of its own,
and 0.3.0's plan reads it. *(From cycle 0.2's close, `done/0.2/0.2.4.md`;
the question is the cycle audit's C2, TM-243.)* *(Answered 2026-10-02 by the
author, the workbench's question 21: **A, keep `instant_of`**. Nothing here
moves; `0.3.0.md`'s gate reads the answer before its step 2 builds on the
name, and its decision for the clocks records it and strikes Q-7.)*

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.3.0 | **The clocks** — `clock_gettime` through `sys`, the three readings — **[`0.3.0.md`](0.3.0.md)**, written at cycle 0.2's close, measured at `5fbaf4a`, and rehearsed from its blocks in its real position on 2026-10-07 and 2026-10-08 (its §8); it opens with the instrument the close handed on | a `Timestamp` from the machine, range-checked |
| 0.3.1 | **`check_purity` goes live** — the dormant check from 0.0.3, turned on | the library's reproducibility claim, enforced |
| 0.3.2 | **The system zone** — the four-step discovery, and what it reports | a program can ask, and is told which mechanism answered |
| 0.3.3 | **The double** — the test host module, in `tests/` | every clock-dependent behaviour reproducible |
| 0.3.4 | **Close** | `done/0.3/`, `0.4.0.md` written |

## Checklist

### 0.3.0 — the clocks
*(Restated 2026-10-02, at cycle 0.2's close, to `0.3.0.md`'s drafted decisions, PD-91 … PD-94. The first item is new — the instrument the close handed on; the `sys.npk` item is struck for the shape PD-93 drafts; `HostClock`, `timespec_ns` and the arm bill are named; and the H-3 item says how a test sees it. The rest keep their words.)*
- [x] **FIRST, the instrument cycle 0.2's close handed on, in a commit of its own**: `check_int128_sites` reads a numeric literal's width suffix as it reads a type's name, so `(3i256 * 5i256) =>! int64` in a function `SPAN_MODEL.md` §5 does not mark is a finding; two plants, and `TESTING.md` §2's row restated (PD-91) *(found by 0.2.4a's verifier after the cycle audit; `done/0.2/0.2.4.md`)* — **done, TM-246**: both plants unseen by the check before it, its first control read as a stale mark, and both caught after; the tree 0 findings, the headline's count 15 with `bytes_put_int`'s `0i128`; its own commit green with 94 plants
- [ ] ~~`src/host/sys.npk` with the four syscall numbers, each carrying the header it came from as a comment~~ — restated by PD-93, the item below: two numbers this subcycle needs, kept in `host.npk`, and no header on this machine their source
- [x] the two syscall numbers — `clock_gettime` 228 and `clock_getres` 229 — and the clock ids 0, 1 and 7, as private `fixed int64`s in `src/host/host.npk`, each with its source in a comment: the compiler's runtime at the pin and the kernel's own table (PD-93) — TM-248, and `meta/research/CURRENCY.md`'s row
- [x] the 16-byte `timespec` laid out in a `buffer`, asserted by `#size_of` and by offsets (probe 03's shape) — `probe03` asserts both on every run, and the module's three readings are its shape, the reads in bounds by construction and said so at each (S-17b's fourth row)
- [x] `host_now_utc` (CLOCK_REALTIME 0), `host_now_boot` (CLOCK_BOOTTIME 7) — `host_now_boot`'s nanoseconds through a private `timespec_ns`, which refuses a reading an `int64` cannot hold before it multiplies (PD-93) — TM-248
- [x] `host_now_instant` calls the floor's `mono_now()`, **not** `clock_gettime` (H-5) — so an `ntime` `Instant` and an executor deadline are on the same timeline by construction — TM-248; its IR calls `mono_now` and no `npk_sys6`
- [x] `host_clock_res` over `clock_getres`, on `HostClock` — `{ Realtime; Monotonic; Boottime; }`, declared in `host`, which H-1 names and no specification declared (PD-93) — TM-248, H-1 and H-4 dated
- [x] **`BUILD.md` B-17 gains `host` → `span`, by decision, when `host` first imports it** (PD-92): `host_now_instant` and `host_now_boot` return `Instant`s, and both fields of an `Instant` are sealed, so `host` builds them through `span`'s public `instant_of` (TM-215, TM-216) — B-17 draws `host` → `zone`, `cal`, `core` today *(handed on by `done/0.2/0.2.0.md` §7)* — and `host_now_utc`'s `Timestamp` through `timestamp_of`, its fields sealed since cycle 0.2.1 (TM-219, TM-220) — TM-247; `check_layering`'s new plant, `host` importing `fmt`, red beside `host` importing `span`
- [x] errnos **forwarded verbatim** (H-7), so this module declares no error and costs no arm — asserted by `check_error_budget`; and its bill measured, 11 for `host` alone and 13 for the umbrella with its five names (PD-93) — `check_error_budget` silent; 11 by `arms.compute_bill` and by `NITPICK-REACH-003`, 13 the umbrella's, both tagged
- [x] the returned `Timestamp` range-checked (H-8): an unset machine clock is `ETimeValue`, not a value that fails somewhere less obvious — by `timestamp_of`, whose `YearRange` refusal is H-8's (TM-220) — and the unit's exit 10 is red when `host_now_utc` hands it a nanosecond field a second high
- [x] **no state in the module** (H-3): a test asserts two calls are two syscalls — each reading ADVANCES within a million reads, which a cached or computed one never does; the module's IR holds no global that is not `constant`; and the four mutants no test can see named (PD-94) — TM-249: ten of fourteen one-line mutants red at their exits on both legs, the four named in the unit's header and under H-3
- [x] `// stress: 40` on every clock test — `tests/unit/host_clocks.npk`, forty runs a leg on every full invocation

### 0.3.1 — `check_purity` goes live
*(Stale in its title, found at cycle 0.2.0's planning: `check_purity` has been live since cycle 0.0.3, TM-126. What this subcycle owes is the review of its ban list against a `src/` with a real `host/` — the last item below — and the two plants. `done/0.2/0.2.0.md` §7.)*
- [ ] the dormant check from 0.0.3 turned on and green
- [ ] **seen to fail**: a deliberately planted `mono_now()` in `src/cal/` fails the build, by name
- [ ] `check_host_isolation` likewise: a planted `host_now_utc()` call in `src/fmt/` fails
- [ ] both checks' ban lists reviewed against what `src/` actually contains now, rather than what 0.0.3 guessed

### 0.3.2 — the system zone
- [ ] `SystemZone` and `ZoneSource` as `HOST.md` §4 defines them
- [ ] the four steps in order, stopping at the first that answers (H-13)
- [ ] `$TZ` with a leading `:` stripped; **a POSIX rule string refused** with `ETimeZone`/`Unknown` (H-13.1), not parsed
- [ ] `/etc/localtime` read as a **symlink target**, never as bytes (H-14)
- [ ] `readlink`'s four facts honoured (H-15): the length is the authority, the result is not NUL-terminated, `NTIME_PATH_MAX` bounds it, a truncated result is not-found
- [ ] `/etc/timezone` as step 3
- [ ] **not-found is `found: false`, not UTC** (H-13.4) — a test asserts it on a machine with none of the three
- [ ] the descriptor closed on every path (S-20)

### 0.3.3 — the double
- [ ] the fake host module in `tests/`, **not** in `src/` (H-10)
- [ ] `fake_set_utc`, `fake_set_instant`, `fake_advance`
- [ ] the harness links whichever host object it is told to, and a test proves the substitution works
- [ ] a demonstration that a clock-dependent behaviour is reproducible: the same fake reading twice gives the same answer, and a fixed sequence gives a fixed transcript

## The adoption, when the pin moves

**Cycle 0.2 closed at compiler `5fbaf4a`, and the next re-pin is the
orchestrator's to place**, as an adoption subcycle of its own that measures the
unchanged tree at both pins before it changes anything, as 0.1.0b, 0.1.4c and
0.2.0a did. What it owes here, from cycle 0.2's close (`done/0.2/0.2.4.md`):

1. **The statement form of `#unreachable()`** — `if (r.is_error) {
   #unreachable(); }` before a read of `r.value` — re-measured at the new pin:
   at `5fbaf4a` it is `NITPICK-TAINT-001`, the compiler's defect the workbench
   registry holds and `meta/OPEN_QUESTIONS.md` restates (TM-245). If it
   compiles, a decision keeps `span`'s two `?| #unreachable()` or respells
   them, and strikes the question with its number.
2. **`timestamp_since`'s `int128` multiplication and `instant_since`'s `int128`
   subtraction** linked at both legs against `npkrt.o` alone, as
   `done/0.2/0.2.3.md` §7 and `done/0.2/0.2.4b.md` §1.7 measured them: at
   `5fbaf4a` each is inline — `llvm.smul.with.overflow.i128` and
   `llvm.ssub.with.overflow.i128` — and no libcall is called, `__muloti4`,
   which `npkrt.o` does not define, among them.
3. **The compiler's lexer re-read** whatever part E says (TM-202), and
   `harness/lexical.py` brought to it; part E's third half re-run against the
   literal reader `check_constants_named` uses (TM-231).
4. **`src/`'s `#wild_slice` sites** — nine in code, in `bytes.npk` and
   `vec.npk`, fourteen lines naming it with the comments, measured at cycle
   0.2's close — are the first to read at a pin that carries the compiler's
   D-341; cycle 0.2 added none.
5. **Each CI's pin bump**, and the emission row CI asserts (TM-212), in the
   adoption's own commit.

## Gate

`check_purity` green **and seen to fail**, and every clock test green under
`// stress: 40`.

## Watch for

- **This module is the only place `ntime` can be non-deterministic**, so it is
  the only place a `stress` run can find something. Forty runs is not
  ceremony here.
- **`fd` is a type, not a name**, and this is the module that wants it.
- **The system-zone discovery is where a careless implementation is wrong four
  ways at once** — H-15 names all four, and each is a test.
- **Resist adding a sixth function.** Every addition to this module is a
  subtraction from the purity claim, and the claim is what makes the other
  cycles testable.
