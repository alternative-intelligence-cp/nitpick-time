# Cycle 0.2 — Instants and timestamps

**`src/span/`: `Instant`, `Timestamp`, and the `Duration` interop.** The types
that make the three scales three types.

## Decisions in

TM-004 (the prelude's `Duration` is the one exact span type), TM-010 (three
scales, no monotonic↔absolute conversion), TM-011 (`Timestamp`'s layout and
field order). All settled.

**Open questions to settle:** O-X3 — whether `Instant` exposes its clock kind
publicly. Recommendation on file: yes, read-only.

**And O-X6 — which `int128` sites `SPAN_MODEL.md` N-20 counts — must be answered
before `check_int128_sites` goes live** (0.2.3's last item). `OPEN_QUESTIONS.md`
says cycle 0.3, `checks.PENDING` and this README say 0.2, and the note cycle
0.1's close added to O-X6 hands the order to this cycle; the recommendation on
file stands — make §5's table the authority and drop N-20's count. *(From cycle
0.1's close, `meta/roadmap/done/0.1/0.1.5.md` §8.5.)*

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.2.0 | **`Instant`** — the type, the clock tag, `instant_since`, and the refusals — **[`0.2.0.md`](0.2.0.md)**, written at cycle 0.1's close | a timeout cannot be written against a wall clock |
| 0.2.1 | **`Timestamp`** — the type, the normalisation invariant, the range check | one representation per instant |
| 0.2.2 | **Conversion** — `timestamp_to_utc`, `civil_to_utc`, and the round trip | the second gate |
| 0.2.3 | **`Duration` interop** — the added constructors, `timestamp_add`, `timestamp_since` and its ±292-year refusal | the mismatch handled honestly |
| 0.2.4 | **Close** | `done/0.2/`, `0.3.0.md` written |

## Checklist

### 0.2.0 — `Instant`
- [ ] `Instant { int64:ns; uint8:clock }` with the clock tag from H-6
- [ ] `instant_since`, `instant_add`, `instant_cmp`
- [ ] **`instant_since` refuses a pair from different clocks** with `ETimeValue` (TM-010.1), and a test proves it
- [ ] **there is no `instant_to_timestamp` and no `timestamp_to_instant`** — a rejection test asserts that a program attempting the conversion does not compile, so the refusal is checked rather than merely absent. **It is the library's next refusal, and it is a probe**: `nitpick.toml`'s `check` stage is still empty, and every refusal the library has asserted so far is a probe under `tests/probe/` dispatched by its own header (`BUILD.md` B-4c) — `0.2.0.md` says which probes, and why not a `check` entry
- [ ] O-X3 decided: `instant_clock(i)` read-only accessor, or not
- [ ] the compiler's `npk_mono_now` comment quoted in the module header, because it is the argument

### 0.2.1 — `Timestamp`
- [ ] `Timestamp { int64:secs; uint32:nanos }`, field order asserted against probe 01's verdict
- [ ] **the normalisation invariant** `nanos < 1_000_000_000` established by every constructor and re-established by every operation (M-7)
- [ ] a property test that no sequence of operations produces a denormalised value — this is `VERIFICATION.md` P-4's obligation, standing in
- [ ] the range check against `NTIME_SECS_MIN`/`MAX`, returning `ETimeValue` before D-210's trap
- [ ] a negative-`secs` timestamp with positive `nanos` compares correctly against its neighbours — the representation's one subtlety, and the test that catches getting it backwards

### 0.2.2 — conversion — THE GATE
- [ ] `timestamp_to_utc` and `civil_to_utc`, over `cal`'s algorithms
- [ ] the round trip over **every day boundary** in the range (7 304 484 cases — 7 304 485 until cycle 0.1.1 corrected the range's first day, TM-161)
- [ ] the round trip over **every second of 512 randomly chosen days**, with the seed committed so the run is reproducible (~44 M cases)
- [ ] a `sweep`-stage test, with the wall-clock cost recorded — **measured before it lands against `BUILD.md` B-9's 30 s threshold**, which the stage stood 7.6 s under at cycle 0.1's close (22.4 s for its six members, both legs); the stage whole and B-9 amended to its cost is the default if the stage stays under 60 s (B-9's dated note, cycle 0.1.5)

### 0.2.3 — `Duration` interop
- [ ] `duration_mins`, `duration_hours`, `duration_days`, `duration_weeks`, all `never fails`, all over the prelude's constructors
- [ ] `duration_days` documented as **exactly 86 400 × 10⁹ ns** and explicitly *not* a calendar day (N-2's note)
- [ ] `timestamp_add(t, d)` with its range check
- [ ] **`timestamp_since` returns `ETimeValue`/`Overflow` past ±292 years** (M-18) — and the test computes the exact boundary rather than approximating it
- [ ] `timestamp_until(a, b, unit)` in whole days, months or years, as the calendar-scale answer (M-19)
- [ ] **`check_check_registry` built FIRST, because this subcycle adds a check** (TM-201, `TESTING.md` V-14e): `TESTING.md` §2's table, `checks.LIVE`, `checks.PENDING` and the checks `run.py` drives outside step 5 diffed as one family, and seen red on a planted drift in each of the four — before the family moves
- [ ] **`check_no_view_returns` live** (`SAFETY.md` S-22, TM-204 — the cycle audit's C3, placed here at cycle 0.1's close): every function in `src/` whose result is a `uint8[]`, a `cstring` or a struct holding one is a finding but S-22's named exemption, `bytes_view`, whose reason is re-derived on every run rather than its name merely matched (TM-137) — a planted view return red, the exemption naming a function that is gone red, and `bytes_view` silent; §2's table gains its row and V-1a's arithmetic moves with it, in the same commit. **Before cycle 0.4**, whose parsers are the first code that could want a view back
- [ ] `check_int128_sites` goes live: `int128` at exactly the sites `SPAN_MODEL.md` §5 names

## The adoption, when the pin moves

**Cycle 0.1's close ran at compiler `c970483` and pre-empted none of this.**
The author decided on ONE re-pin, at the end of the compiler's 1.6.1d (the
workbench board, 2026-09-26 10:40; unchanged at 12:14). **The adoption is its
own subcycle, lettered and placed by the orchestrator when the board re-pins**,
and it measures the unchanged tree at both pins before it changes anything, as
0.1.0b and 0.1.4c did. What it owes here, as the board's entries name the
landings (`meta/roadmap/done/0.1/0.1.5.md` §12.3):

1. **Notice 71 — the manifest's two new `[toolchain]` rows**, `triple` and
   `datalayout`, verbatim from the board's advance notice F15, beside
   `llvm = "20.1.2"`; every emission gains a `target datalayout` line, so the
   library stage's printed IR size moves and is re-recorded.
2. **Notice 73 — the prelude's `Copy` replaces `Pod`, by TM-198**: `vec.npk`'s
   `Pod` block (the trait and its nine impls) deleted; `vec_at` bounded
   `T: Copy` and its `pod_copy()` call respelled; the umbrella's `Pod` line
   gone (59 names to 58, its tag with it); `vec_at_pod`'s two impls and
   `probe19`'s one in `Copy`'s form, and `probe19`'s refusal code measured
   then; a decision replacing TM-194 and TM-198 in part, and `SAFETY.md` S-18h
   restated — **and the same in `nitpick-regex`**, which the orchestrator
   carries.
3. **Notice 69 — DEF-116's `NITPICK-TYPE-014`** on a `move`-adding impl: the
   sentences that say it is fixed *"at no pin of ours"* become history.
4. **The compiler's 1.6.1d, steps 1 to 4** — its memory faults, its loop
   counts (DEF-127 … DEF-130: a `for` binding outliving its loop in the
   emitter, and three loops that count wrong at a type's edges or by a sign —
   **after which the hold on `for`, `loop` and `till` lifts**), its leaks, and
   `cstring` owning its bytes, with the compiler seat's census:
   `0.1.5.md` §1.10 is this repository's side of it — 12 `to_cstring` lines in
   7 test files, none in the eight heap-bounded files, `environ()`'s
   `cstring[]` in two probes, and the harness's own generated programs.
5. **The reader** — part E says, at the new pin, whether the compiler's lexer
   moved on a form its second half names; **and the adoption re-reads
   `src/frontend/lexer.npk` at the new pin whatever part E says** (TM-202),
   bringing `harness/lexical.py` to it **in both libraries** if it moved.
6. **`NITPICK-BORROW-015`** (the compiler's D-325, O-N25) if the new pin
   carries it: `tests/unit/bytes_view_lifetime.npk` holds a `bytes_view` view
   across a growth on purpose, and is the first file to read.
7. **Each CI's pin bump**, in the adoption's own commit, as 0.1.0b and 0.1.4c
   did.

**Until the adoption lands, no `for`, `loop` or `till` is added** — the
compiler's loop defects at `c970483` are why (DEF-127 … DEF-130, item 4, and
the workbench board's hold on them).

## Gate

The `Timestamp` ↔ civil round trip over every day boundary and 44 million
individual seconds, plus a property test that the normalisation invariant
survives every operation.

## Watch for

- **`timestamp_since`'s boundary is exact, not approximate.** ±292.277 years is
  9 223 372 036 854 775 807 nanoseconds; the test asserts at that value and at
  one more. An "about 292 years" check is a check that is wrong by a day.
- **The negative-seconds representation** is where a reader's intuition fails:
  `−1 secs, 500 000 000 nanos` is half a second *before* the epoch, not one and
  a half. There is one representation and the constructors enforce it.
- **The refusals need rejection tests.** M-3's "there is no conversion" is only
  true if a program attempting it fails to compile, and only checked if a test
  says so.
