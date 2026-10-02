# Cycle 0.2 — Instants and timestamps

**`src/span/`: `Instant`, `Timestamp`, and the `Duration` interop.** The types
that make the three scales three types.

## Decisions in

TM-004 (the prelude's `Duration` is the one exact span type), TM-010 (three
scales, no monotonic↔absolute conversion), TM-011 (`Timestamp`'s layout and
field order). All settled.

**Open questions to settle:** O-X3 — whether `Instant` exposes its clock kind
publicly. Recommendation on file: yes, read-only. *(Settled at 0.2.0, TM-216:
the clock is the sealed field, read anywhere, and there is no accessor.)*

**And O-X6 — which `int128` sites `SPAN_MODEL.md` N-20 counts — must be answered
before `check_int128_sites` goes live** (0.2.3's last item). `OPEN_QUESTIONS.md`
says cycle 0.3, `checks.PENDING` and this README say 0.2, and the note cycle
0.1's close added to O-X6 hands the order to this cycle; the recommendation on
file stands — make §5's table the authority and drop N-20's count. *(From cycle
0.1's close, `meta/roadmap/done/0.1/0.1.5.md` §8.5.)* *(Answered at 0.2.3a,
where the item went when 0.2.3 was split, TM-229: the table, in an `int128`
column of its own, three rows marked; and the check live, TM-230.)*

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.2.0a | **The adoption of compiler `5fbaf4a`** — the fifteen `cstring` copies, the target pinned and held, the per-site count, `Pod` retired into `Copy`, CI's pin and its emission asserted, and the ecosystem audit's EC3, EC6 and ED1 — **[`0.2.0a.md`](0.2.0a.md)**, planned and rehearsed 2026-09-27; it runs FIRST | the tree `GREEN` at `5fbaf4a`, locally and in CI |
| 0.2.0b | **`Vec<T: Copy>`** — `nitpick-regex`'s answer to the question TM-194 left open (its RX-188), ported: the bound on the type and on every verb, TM-150's churn pair retired, `case5` at six sites, no element check — **[`0.2.0b.md`](0.2.0b.md)**, planned and rehearsed 2026-09-30; it runs SECOND, after 0.2.0a and before 0.2.0 | an owning element refused wherever it is written, and the IR of every program that compiles both ways unchanged |
| 0.2.0 | **`Instant`** — the type, the clock tag, `instant_since`, and the refusals — **[`0.2.0.md`](0.2.0.md)**, written at cycle 0.1's close, its §1 re-measured at `5fbaf4a` over 0.2.0a's tree on 2026-09-27, and its steps rehearsed from their blocks over 0.2.0b's tree on 2026-09-30 | a timeout cannot be written against a wall clock |
| 0.2.1 | **`Timestamp`** — the type, the normalisation invariant, the range check, and M-3's refusal at the type both ways — **[`0.2.1.md`](0.2.1.md)**, planned and rehearsed 2026-10-01 at `5fbaf4a`; it opens with 0.2.0's test gap | one representation per instant |
| 0.2.2 | **Conversion** — `timestamp_to_utc`, `civil_to_utc`, and the round trip — **[`0.2.2.md`](0.2.2.md)**, planned and rehearsed 2026-10-01 at `5fbaf4a`; it closes with the glossary misuse 0.2.1's verifier found, in a commit of its own | the second gate |
| 0.2.3a | **The instruments** — split from 0.2.3 at its planning: `check_check_registry` first, then `check_no_view_returns` and `check_int128_sites` live — O-X6 answered, §5's table the authority — then `check_constants_named` reading every spelling of a literal and the owner of 1 000 000 000, and the GitHub note the workbench's question 17 reworded — **[`0.2.3a.md`](0.2.3a.md)**, planned and rehearsed 2026-10-01 at `5fbaf4a`; it runs FIRST | the family one list, and every spelling of an owned number seen |
| 0.2.3 | **`Duration` interop** — the added constructors, `timestamp_add`, `timestamp_since` and its ±292-year refusal — **[`0.2.3.md`](0.2.3.md)**, planned and rehearsed 2026-10-01 at `5fbaf4a` over 0.2.3a's tree; it runs after 0.2.3a | the mismatch handled honestly |
| 0.2.4 | **Close** | `done/0.2/`, `0.3.0.md` written |

## Checklist

### 0.2.0a — the adoption of `5fbaf4a` (its §5 is the acceptance list)
- [x] the fifteen `cstring` copies read in place or moved, the lexer re-read, O-N25 answered (PD-57) — TM-208, `1390b80`: both probes compile at both pins, `cstring copies left: 0`, `GREEN -- 113`
- [x] `triple` and `datalayout` pinned, held to what `opt` derives, every emission held to them; cases 10, 11 (PD-58) — TM-209, `563c320`: the `ok    target` line, `10 of V-14's 11`, `GREEN -- 113`
- [x] a refusal names each code once per site; F24's four files; cases 12, 13 (PD-59) — TM-210, `7cc19c6`: `0 count(s) differ` at both pins, the four old headers each `FAILS the count`, `12 of V-14's 13`, `GREEN -- 113`
- [x] `Pod` retired into the prelude's `Copy`; 58 names re-exported (PD-60) — TM-211, `b930df3`: `Pod in src/ code: 0`, probe 19 `TYPE-087`, `case5` `TYPE-017` ×2, the control refused, IR 226 493 B, `GREEN -- 113`
- [x] CI pinned to `5fbaf4a` in a commit of its own, and asserting `npkc.ll` against the pin's row (PD-61, EC6) — `b241e86`, then TM-212, `2c3ccb2`: run 36364840105 printed `npkc.ll == the pin's emission, 30232291 B / 5630c2b4…`
- [x] EC3's three sites and every other phrasing of the claim corrected (PD-62); ED1 (PD-57) — TM-213, `23cb2da`, and TM-208; block 7b's sweep read line by line, no omission (`0.2.0a.md`'s execution record)
- [x] `GREEN` at `5fbaf4a` locally and in CI, read from the job log — `GREEN -- 113` on block 7's run over `23cb2da`, and in CI run 36364840105's job log with `compiler HEAD == 5fbaf4a40a2f6b213754cd71b6c69700f8aa2c87 (clean)` and `12 of V-14's 13`

### 0.2.0b — `Vec<T: Copy>` (its §5 is the acceptance list)
- [x] `struct:Vec<T: Copy>` and the bound on the eight verbs that lacked it; TM-150's churn pair retired; `case5` at six sites; `SAFETY.md` S-18b … S-18h, `BUILD.md` B-12 and `TESTING.md` V-17 amended (PD-63) — TM-214, `bd0212c`: the struct's bound alone refused at the eight definitions, `case5` `TYPE-017` ×6 and ×2 against `HEAD`'s `vec.npk`, an unbounded `vec_push` refused at its definition, `verdicts: 125 of 128 unchanged`, `GREEN -- 111`
- [x] the masked IR of every program and root that compiles before and after the bound identical — the site-line table the one mask — block 0b `IR: 89 of 89 identical byte for byte`; block 1 82 of 89 byte for byte and 89 of 89 masked; block 2 79 and 89 of 89 masked
- [x] no element check, by PD-63's declined alternative — measured: a `Copy` struct holding a pointer or a slice is a legal element, and drops nothing — block 0b: `#[derive(Copy)]` over `int64->` and over `uint8[]` each `compiles` as the element; the compiler's `check_copy_impl` refuses any `Copy` impl whose target drops, read at `5fbaf4a` (`0.2.0b.md`'s execution record)
- [x] the prose, and block 3's sweep read line by line — `ac8ee4a`, `GREEN -- 111`, `0 unresolved`; block 3 `SAME`, its 153 lines read and a second sweep's 390 more, no omission, no patch amended (`0.2.0b.md`'s execution record)
- [x] `GREEN` at `5fbaf4a` locally and in CI, read from the job log — `GREEN -- 111` on block 2's run over `ac8ee4a`'s tree, and in CI run 36823366390's job log with `compiler HEAD == 5fbaf4a40a2f6b213754cd71b6c69700f8aa2c87 (clean)`, `npkc.ll == the pin's emission, 30232291 B / 5630c2b4…` and `12 of V-14's 13`

### 0.2.0 — `Instant`
*(Restated 2026-09-30, at 0.2.0's rehearsal, to the plan's decisions: the first item read `Instant { int64:ns; uint8:clock }` with the clock tag from H-6, and none named `instant_of`, `instant_cmp`'s refusal or the generator's fix.)*
- [x] `Instant { sealed int64:ns; sealed InstantClock:clock }`, `InstantClock` an enum; both `Copy`, neither `Ord` (PD-53) — TM-215, `94f708a`: `span.npk` compiles at `5fbaf4a`; a consumer's literal `TYPE-079` twice (`probe20`) and a field write `TYPE-079`; without `Copy` the unit's six `Vec` sites `TYPE-017`, and `Copy` on `Instant` alone `TYPE-087` (blocks 0b and 4)
- [x] `instant_of`, `instant_since`, `instant_add`, `instant_cmp` (PD-54) — TM-216, `94f708a`: `tests/unit/instant_ops.npk` 0 on both legs; `instant_add` subtracting 13, `instant_since`'s operands swapped 11; its exit 15 reads the `ns` of both `Vec` reads — the plan's line read the second through its clock alone, whose expected value is the vacant one, and a vacant second read passed it at 0, measured
- [x] **`instant_since` and `instant_cmp` refuse a pair from different clocks** with `ETimeValue`, `ValueFault.ClockMismatch` (TM-010.1, PD-54), and a test proves it — TM-216: the unit's 16 and 17, each red on its mutant, the check deleted (16 and 17 on both legs, block 4); `ClockMismatch` the fifteenth variant, appended
- [x] **there is no `instant_to_timestamp` and no `timestamp_to_instant`** — a rejection test asserts that a program attempting the conversion does not compile, so the refusal is checked rather than merely absent. **It is the library's next refusal, and it is a probe**: `nitpick.toml`'s `check` stage is still empty, and every refusal the library has asserted so far is a probe under `tests/probe/` dispatched by its own header (`BUILD.md` B-4c) — `0.2.0.md` says which probes, and why not a `check` entry — TM-218, `94f708a`: `probe20b` `NITPICK-RESOLVE-002` at 24:15 and `probe20` `NITPICK-TYPE-079` twice at 32:17, each refused with exactly its codes; neither name is declared in `src/` (`git grep`, 0 lines); the refusal at the type is 0.2.1's item below, one of M-3's two directions (`0.2.0.md`'s execution record)
- [x] O-X3 decided: `instant_clock(i)` read-only accessor, or not — PD-54: the sealed field, and no accessor — TM-216; O-X3 struck (`O-X3 struck: 1`, block 5)
- [x] the compiler's `npk_mono_now` comment quoted in the module header, because it is the argument — from `git show 5fbaf4a:runtime/npkrt.ll`, where it heads the monotonic-clock block above `npk_chain_reset` — `src/span/span.npk`'s header, its four lines checked by script against lines 3502–3506 there
- [x] the S-6 generator names an identity by the module that declares it, and part C's fourth specimen was red before the fix and silent after (PD-55) — TM-217, `94f708a`: block 1, part C over 4 specimens `RED` with `HEAD`'s `arms.py` (*"generator overstates: probe11_relay_lib.EProbeZone"*) and `silent` after; `compute_bill` 11 and 7 where it read 12 and 8; `GREEN -- 114` on block 6's run and in CI run 36827751780's job log, with `compiler HEAD == 5fbaf4a40a2f6b213754cd71b6c69700f8aa2c87 (clean)`, `npkc.ll == the pin's emission, 30232291 B / 5630c2b4…` and `12 of V-14's 13`

### 0.2.1 — `Timestamp`
*(Restated 2026-10-01, at 0.2.1's planning, to the plan's decisions. The first item and the last are new: 0.2.0's test gap, which 0.2.0's verifier found, and the reverse direction of M-3 with the cast both ways, from 0.2.0's record. The type's item read `Timestamp { int64:secs; uint32:nanos }`, and the sealed fields' item said nothing of `hidden`, which the author's answer to the workbench's question 15 settles.)*
- [x] **FIRST, 0.2.0's test gap**: `tests/unit/instant_ops.npk` reads a `Boottime` reading through `instant_add` and through the `Vec`, so no clock is checked against the vacant value alone; exits 10, 12 and 14 each seen red on a mutant; and its header's claim that each exit "was seen red on its mutant at planning" corrected — `0.2.1.md` step 1 — `a8525c8`, its own commit: block 1, the unit 0 on both legs and every exit red on its mutant on both legs — 10 and 12 the clock tests inverted, 14 `instant_add` hard-coding `Boottime` and hard-coding `Monotonic`, 15 a vacant element and one that loses its clock — and `HEAD`'s unit 0 against the hard-coded `Monotonic`; `GREEN -- 114`
- [x] `Timestamp { sealed int64:secs; sealed uint32:nanos }`, deriving `Eq`, `Ord`, `Clone`, `Debug` and `Copy`; field order asserted against probe 01's verdict, on the type itself (PD-64) — TM-219, `e9bec4b`: `span.npk` compiles at `5fbaf4a`; `tests/unit/timestamp_order.npk` 0 on both legs, and 11 with the two fields declared the other way round; without `Ord` its three `cmp` calls `NITPICK-TYPE-019`, without `Copy` `timestamp_construct`'s six `Vec` sites `NITPICK-TYPE-017` (block 4)
- [x] **the normalisation invariant** `nanos < 1_000_000_000` established by every constructor and re-established by every operation (M-7) — at 0.2.1 the one constructor, `timestamp_of`, which refuses rather than carries (PD-65) — TM-220, `e9bec4b`: `tests/unit/timestamp_construct.npk` 0 on both legs over 132 pairs, 35 accepted and 97 refused; 34 with each of the four checks deleted, the `nanos` bound one high, and the `nanos` checks made after the narrowing; 33, M-7 itself, with the tables and the bound wrong together (block 4)
- [x] a property test that no sequence of operations produces a denormalised value — this is `VERIFICATION.md` P-4's obligation, standing in (PD-65: every boundary the constructor decides, and the seal's two probes) — TM-220: `timestamp_construct` with `probe21` and `probe21b`, P-4's and §6's row dated; the stand-in's extension to `civil_to_utc` and to `timestamp_add` is in 0.2.2's and 0.2.3's checklists below (step 5)
- [x] the range check against `NTIME_SECS_MIN`/`MAX`, returning `ETimeValue` before D-210's trap (PD-65) — TM-220, `ValueFault.YearRange`: `timestamp_construct` 30 with the lower bound one high, 34 with either `secs` check deleted, and `int64`'s two ends among the refused (block 4)
- [x] a negative-`secs` timestamp with positive `nanos` compares correctly against its neighbours — the representation's one subtlety, and the test that catches getting it backwards — `tests/unit/timestamp_order.npk`'s eight-value chain, −1.000000001 s … 1 s, every pair compared both ways and with `eq`: 21 with a negative second's remainder counted toward zero, 20 with a negative `secs` refused (block 4)
- [x] `Timestamp`'s fields `sealed`, by TM-215's reason: a consumer builds one only through a validating constructor *(added at 0.2.0, `0.2.0.md` §7)* — and `hidden` declined, here and for `Instant`'s `ns`, with its reason, and the public README's "yields only differences" softened (PD-64; the workbench's question 15, answered 2026-10-01) — TM-219 and its marker on TM-215: block 0b's consumer literal `NITPICK-TYPE-079` twice and its write once, the literal compiling against unsealed fields, `hidden` reads `NITPICK-TYPE-080` at each, `mono_now()` compiling in a consumer; the README's sentence and its dated note (step 5)
- [x] a probe asserts an `Instant` passed where a `Timestamp` is taken is refused, with its code measured then — the conversion refusal `probe20b` could not ask without `Timestamp` *(added at 0.2.0, TM-218)* (PD-66) — TM-221: `probe20c`, `NITPICK-TYPE-007` at 27:38, refused with exactly its code (block 4)
- [x] **and the reverse**, a `Timestamp` where an `Instant` is taken, as a probe of its own — M-3 says "in either direction" *(from 0.2.0's record)* — and the language's unchecked cast, `=>!`, each way, each a probe of its own (PD-66) — TM-221: `probe20d` `NITPICK-TYPE-007` at 25:44, `probe20e` `NITPICK-TYPE-032` at 26:21, `probe20f` `NITPICK-TYPE-032` at 23:25, and the seal's `probe21` `NITPICK-TYPE-079` twice at 28:19 and `probe21b` once at 24:5 (block 4); `GREEN -- 122` on block 6's run and in CI run 36861243420's job log on `e9bec4b`, with `compiler HEAD == 5fbaf4a40a2f6b213754cd71b6c69700f8aa2c87 (clean)`, `npkc.ll == the pin's emission, 30232291 B / 5630c2b4…` and `12 of V-14's 13`

### 0.2.2 — conversion — THE GATE
*(Restated 2026-10-01, at 0.2.2's planning, to the plan's decisions. The first five keep their words and gain the plan's names and choices — the vectors 0.2.1 handed on, the two members of the gate, the forged side of P-4's stand-in, the stage's measured default; the last two are new: `SAFETY.md` S-16's owner for 86 400, found at planning, and the glossary misuse 0.2.1's verifier found.)*
- [x] `timestamp_to_utc` and `civil_to_utc`, over `cal`'s algorithms — `timestamp_to_utc` `never fails`, its day number a FLOOR division of the seconds; `civil_to_utc` fallible, through `timestamp_of`, and total over every field value; and `tests/unit/utc_vectors.npk`, sixteen instants held to their civil readings both ways, `tests/unit/timestamp_order.npk`'s chain among them (PD-67) — TM-222, `2d0db2d`: `span.npk` compiles at `5fbaf4a` (block 1); `NITPICK-REACH-003` 11 identities for `span` and 13 for the umbrella, and 68 `pub use` lines (block 2); `utc_vectors` 0 on both legs, and red on its mutants on both legs — `truncate` 95, `floor_twice` and `day_late` 15, `minute_61` 16, `nanos_high` 17, `c2u_short` 11, `c2u_minute_59` 12, `c2u_nanos_dropped` 13 (block 3)
- [x] the round trip over **every day boundary** in the range (7 304 484 cases — 7 304 485 until cycle 0.1.1 corrected the range's first day, TM-161) — from both sides, `tests/unit/sweep/every_day_boundary.npk` (PD-69) — TM-224, `2d0db2d`: exit 0 on both legs, `swept 7304484`, on block 6's two runs and in CI run 36915583038's job log; red on its mutants on both legs — `truncate` and `floor_twice` 95, `floor_day_kept` 23, `day_late` 18, `minute_61` 24, `walk_short` 25 (block 3)
- [x] the round trip over **every second of 512 randomly chosen days**, with the seed committed so the run is reproducible (~44 M cases — 44 236 800) — `tests/unit/sweep/every_sampled_second.npk` (PD-69) — TM-224, `2d0db2d`: exit 0 on both legs, `swept 44236800`, on block 6's two runs and in CI run 36915583038's job log; the seed 20 261 001's 512 days the program's equal to a Python transcription's, 321 before the epoch (block 0b); red on its mutants on both legs — `truncate` 95, `c2u_days_1000` 12, `hour_short` 17 (block 3)
- [x] **`VERIFICATION.md` P-4's stand-in extended to `civil_to_utc`**: every `Timestamp` it returns asserted normalised, in `tests/unit/timestamp_construct.npk`'s manner (TM-220) *(added at 0.2.1)* — `tests/unit/civil_to_utc_edges.npk`, both sides of every boundary the conversion decides, the refusing side built through C-8c's opt-out (PD-70) — TM-225, `2d0db2d`: exit 0 on both legs over 30 pairs, 12 accepted and 18 refused; `c2u_literal` 37 there and 0 at the vectors and at both members of the gate; `secs_max_deleted` 37; the forge's own mutants 31, 32, 36 and 38 (block 3)
- [x] a `sweep`-stage test, with the wall-clock cost recorded — **measured before it lands against `BUILD.md` B-9's 30 s threshold**, which the stage stood 7.6 s under at cycle 0.1's close (22.4 s for its six members, both legs); the stage whole and B-9 amended to its cost is the default if the stage stays under 60 s (B-9's dated note, cycle 0.1.5) — measured at planning, `0.2.2.md` §1 (PD-69) — TM-224, `2d0db2d`: the stage 43.1 s on both of block 6's runs (43.3 s at planning), under 60 s, so it stays whole and `BUILD.md` B-9's threshold is 60 s; `GREEN -- 126`, `0 unresolved`, `check_refs` clean
- [x] `SAFETY.md` S-16 and `check_constants_named`'s owner map move together, as both say they must when a second module wants 86 400: its owner is `core` alone, and `span` divides by `NTIME_SECS_PER_DAY`, by name *(found at 0.2.2's planning)* (PD-68) — TM-223, `2d0db2d`: a literal 86400 refused in `span` and in `cal`, permitted in `core`, the tree 0 findings (block 4); the self-check's row planting in `span`, 44 planted violations caught and 44 controls silent (block 6)
- [x] **the glossary**: a point on the UTC scale called "a wall-clock reading" or "time" — the words `meta/specs/GLOSSARY.md` keeps for a civil reading — at the five sites 0.2.1's verifier named (`README.md`'s status and its paragraph on the clocks, `src/lib.npk`, `probe20`'s header, TM-216) and the two the measurement found beyond them (`probe03`'s comment, TM-215's example), with `probe20d`'s header judged: six reworded and two settled decisions marked, in a commit of its own *(added at 0.2.2's planning, from 0.2.1's verifier)* (PD-71) — TM-226, `eff4f2f`: `probe20` `NITPICK-TYPE-079` twice at 32:17 and `probe20d` `NITPICK-TYPE-007` at 25:44, their sites unmoved; `probe03` 0 on both legs; the two markers counted; `GREEN -- 126` and `check_refs` clean (block 7); block 7b read line by line, no omission (`0.2.2.md`'s execution record); `GREEN -- 126` in CI run 36915583038's job log on `eff4f2f`, with `compiler HEAD == 5fbaf4a40a2f6b213754cd71b6c69700f8aa2c87 (clean)`, `npkc.ll == the pin's emission, 30232291 B / 5630c2b4…` and `12 of V-14's 13`

### 0.2.3a — the instruments
*(Split from 0.2.3's checklist at its planning, 2026-10-01: its four instrument items — the registry check, the two checks that go live with O-X6 between them, and the owner of 1 000 000 000 — and the two the planning dispatch added, `check_constants_named`'s reader and the GitHub note of the workbench's question 17. They are the harness's and the documents', not the library's, and two of them guard the interop's code, so they run first; `0.2.3a.md` says why the subcycle is two.)*
- [ ] **`check_check_registry` built FIRST, because this subcycle adds a check** (TM-201, `TESTING.md` V-14e): `TESTING.md` §2's table, `checks.LIVE`, `checks.PENDING` and the checks `run.py` drives outside step 5 diffed as one family, and seen red on a planted drift in each of the four — before the family moves — V-1a's three numbers tagged and held to it (PD-72)
- [ ] **`check_no_view_returns` live** (`SAFETY.md` S-22, TM-204 — the cycle audit's C3, placed here at cycle 0.1's close): every function in `src/` whose result is a `uint8[]`, a `cstring` or a struct holding one is a finding but S-22's named exemption, `bytes_view`, whose reason is re-derived on every run rather than its name merely matched (TM-137) — a planted view return red, the exemption naming a function that is gone red, and `bytes_view` silent; §2's table gains its row and V-1a's arithmetic moves with it, in the same commit. **Before cycle 0.4**, whose parsers are the first code that could want a view back. *(And one question for it, from 0.2.0b's planning: a `#[derive(Copy)]` struct holding a slice is a legal `Vec` element under `Vec<T: Copy>`, so whether S-22's "a struct containing one" reaches through a `Vec`'s element type is this check's to decide when it reads a result's type — `0.2.0b.md` §1.5 and §8.)* *(Answered by the check: a type argument is reached, `Vec<uint8[]>`; a type parameter is not.)* (PD-73)
- [ ] O-X6 answered before the check goes live: `SPAN_MODEL.md` §5's table the authority, in an `int128` column, and N-20 without its count — `bytes_put_int`'s loop measure a marked row, a site since cycle 0.1.0b that no row named *(found at 0.2.3's planning)* (PD-74)
- [ ] `check_int128_sites` goes live: `int128` at exactly the sites `SPAN_MODEL.md` §5 names (PD-75)
- [ ] **`check_constants_named` reads a literal as the compiler's lexer does** (`LEXICAL_REFERENCE.md` §6.2): every spelling of an owned number seen — digit separators, a leading zero, hex, binary, octal, the balanced bases, a width past `u64`, a character literal, a bound after `..` — where sixteen passed the check before it, measured; and part E asks the pinned compiler about every spelling *(added at 0.2.3's planning, from its dispatch: the check's pattern read no digit separator, and `86_400i64` passed it)* (PD-76)
- [ ] `check_constants_named`'s owner of 1 000 000 000, by TM-223's reasoning: `core` alone if every module reads it by name, as 86 400 is since 0.2.2, and `SAFETY.md` S-16 with it *(added at 0.2.2 — `0.2.1.md` §7 handed the question here, and the checklist did not carry it)* — after the reader sees it in every spelling (PD-77)
- [ ] `meta/scratch/github.txt` holds the live GitHub description, the workbench's question 17's rewording, and its count line says 258, where it said 218 of a line of 246 *(added at 0.2.3's planning)*

### 0.2.3 — `Duration` interop
*(Restated 2026-10-01, at its planning, to the plan's decisions: the first six keep their words and gain the plan's choices; `timestamp_until` moves to cycle 0.7.3 (PD-82); the four instrument items are 0.2.3a's.)*
- [ ] `duration_mins`, `duration_hours`, `duration_days`, `duration_weeks`, all `never fails`, all over the prelude's constructors — each one line over `duration_secs`, and the trap one past a day's two ends asserted (PD-78)
- [ ] `duration_days` documented as **exactly 86 400 × 10⁹ ns** and explicitly *not* a calendar day (N-2's note) (PD-78)
- [ ] `timestamp_add(t, d)` with its range check — the constructor's, relayed (PD-79)
- [ ] **`VERIFICATION.md` P-4's stand-in extended to `timestamp_add`** — the first operation that must re-establish M-7 rather than refuse: no sequence of additions, negative durations included, yields `nanos` outside one second (TM-220) *(added at 0.2.1)* — a hundred thousand seeded additions held to an `int128` count, forged inputs, and every boundary it decides (PD-80)
- [ ] `VERIFICATION.md` P-3's `timestamp_add` sample names `SECS_MIN` and `SECS_MAX`, which `src/core/limits.npk` spells `NTIME_SECS_MIN` and `NTIME_SECS_MAX` (`BUILD.md` B-15) — restated when the function is written *(found at 0.2.1's planning)* (PD-80)
- [ ] **`timestamp_since` returns `ETimeValue`/`Overflow` past ±292 years** (M-18) — and the test computes the exact boundary rather than approximating it — computed in `int128`, each end taken exactly from both sides (PD-81)
- [ ] ~~`timestamp_until(a, b, unit)` in whole days, months or years, as the calendar-scale answer (M-19)~~ — moved to cycle 0.7.3, beside `date_until`: whole months and years are `Period` addition's clamped steps, and `Period` is 0.7.0's (PD-82)

## The adoption, when the pin moves

> **Planned 2026-09-27 as [`0.2.0a.md`](0.2.0a.md), at `5fbaf4a`** — the board's
> re-pin of 2026-09-27 10:54, the author's go (its question 12: the latest, not
> the staged `44ec7e9`). Each item below is a step there or was measured to need
> none: 1 is its step 2; 2 and 3 its step 4; 4 and 6 its step 1 (the fifteen
> copies — the census's twelve `to_cstring` lines moved nothing but the seven
> `c.value` copies; the loop hold lifts; `NITPICK-BORROW-015` reaches no file of
> ours); 5 its step 1 (the lexer moved a character literal's width only); 7 its
> steps 5 and 6. The list below is left as written.

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
   *(This repository's reader only — W-7; `nitpick-regex`'s is its own, under
   its own re-read rule (its RX-176): TM-208, the ecosystem audit's ED1.)*
6. **`NITPICK-BORROW-015`** (the compiler's D-325, O-N25) if the new pin
   carries it: `tests/unit/bytes_view_lifetime.npk` holds a `bytes_view` view
   across a growth on purpose, and is the first file to read.
7. **Each CI's pin bump**, in the adoption's own commit, as 0.1.0b and 0.1.4c
   did.

**Until the adoption lands, no `for`, `loop` or `till` is added** — the
compiler's loop defects at `c970483` are why (DEF-127 … DEF-130, item 4, and
the workbench board's hold on them). *(LIFTED 2026-09-27 by 0.2.0a: the four
are in `5fbaf4a`, the compiler's landing 75 — TM-208.)*

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
