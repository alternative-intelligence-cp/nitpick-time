# Cycle 0.1 — The civil calendar

**`src/cal/`: the civil types, Hinnant's algorithms, and the exhaustive
sweep.** The most purely arithmetic cycle in the plan and the one with the
strongest gate.

> **`0.1.0.md` is written execution-grade at cycle 0.0's close** (0.0.6, step
> 6), so this cycle is openable by a session that was not present for the
> probes. That is the convention for every cycle: the opening subcycle file is
> written by the cycle before it.
>
> **`0.1.0b.md`, `0.1.0c.md` and `0.1.1.md` were written by a planner on
> 2026-09-25**, when the libraries resumed after the pause on compiler
> `c3bdae2` (the close of its cycle 1.5) and this tree — last verified at
> `aaffb87` — no longer compiled there. Each was checked by a dry run in a
> scratch copy of the tree at `c3bdae2` before it was written; each says which
> numbers came from that run and how to re-derive them.
>
> **`0.1.2.md` was written by a second planner the same day, after 0.1.1's
> close**, and was rehearsed in the REAL checkout at `c3bdae2` rather than in a
> copy: every fenced command in it was run verbatim there, the harness went
> `GREEN -- 81 unit(s)` with the subcycle applied, and the tree was then put
> back to `c7a60ac` exactly. Its §13 says which command ran where.
>
> **`0.1.3.md` and `0.1.3b.md` were written by a third planner the same day,
> after 0.1.2's close**, and rehearsed in the REAL checkout at `c3bdae2` — 0.1.3
> from its own fenced blocks, extracted and applied by the plan's `apply.py`,
> and 0.1.3b on top of 0.1.3's applied state — the tree put back to `7689432`
> exactly after each pass. Each file's last section says which command ran
> where. **0.1.3b is the re-measurement the workbench owed this repository** when
> it found `PLAYBOOK.md` §2's TYPE-046 row false; it is placed after 0.1.3,
> which carries the cycle's gate, and before 0.1.3c.
>
> **`0.1.4.md` was written by a fourth planner the same day, after 0.1.3b's
> close**, and rehearsed in the REAL checkout at `c3bdae2` from its own fenced
> blocks, extracted and applied by the plan's `apply.py`, the tree put back to
> `b0f9b62` exactly after each pass; its last section says which command ran
> where. **It runs BEFORE 0.1.3c, by the orchestrator's order of
> 2026-09-25**: 0.1.3c ports `nitpick-regex`'s 0.0.4d and is gated on that
> landing and being verified (W-9), and 0.1.4 holds no `Vec` and no `Bytes`,
> so nothing in it waits on 0.1.3c (`0.1.4.md` §15). **It also found a
> compiler defect at planning** — a `fixed` binding's declared type resolves in
> the importing module's scope — recorded with its reproduction in `0.1.4.md`
> §3 and raised by path.
>
> **`0.1.4b.md` was written by a fifth planner the same day, after 0.1.4's
> close**, and rehearsed in the REAL checkout at `c3bdae2` from its own fenced
> blocks — every group applied by the plan's `apply.py`, the tree put back to
> `648590f` exactly after each pass; its last section says which command ran
> where. **It runs BEFORE 0.1.3c, by the orchestrator's order of 2026-09-25**:
> 0.1.3c ports `Vec` move-only, whose loan rules change at the re-pin to the
> commit carrying the compiler's 1.6.0 step 3h, so it is planned against that
> pin. **It found two things at planning, from the runtime's own output**: a
> library defect — `bytes_take` hands back a view typed as an owned `string` —
> which it fixes (`0.1.4b.md` §4); and that TM-131's `/bin/true` control no
> longer controls for this runtime (§3).
>
> **`0.1.4c.md` was written by a sixth planner on 2026-09-26, after 0.1.4b's
> close, when the workbench re-pinned to compiler `c970483`**, the end of its
> 1.6.0 chain — and rehearsed in the REAL checkout at both `c3bdae2` and
> `c970483` from its own fenced blocks, every step compared with its block by
> the plan's `same.py`, the tree put back to the plan's commit after each pass;
> its last section says which command ran where. **The unchanged tree was
> measured first**: RED at 90 of 91 at the new pin, and a per-file sweep of all
> 108 `.npk` at both pins moved exactly four files — `fixed_move_out/`'s three,
> whose defect has landed (O-N20, the compiler's DEF-99), and `probe13d`,
> whose generic accessor the compiler's DEF-104 now refuses; nothing in `src/`.
> **The order is the orchestrator's, 2026-09-26: 0.1.4c, then 0.1.3c, then
> 0.1.5.**

## Why here

Because everything converts through it. `Timestamp ↔ civil`, every zone lookup,
every format and every parse ends up calling `date_to_days` or `days_to_date`.
Putting it first means every later cycle builds on something that has been
checked over its **whole domain** rather than sampled.

## Decisions in

TM-014 (the range and astronomical numbering), TM-015 (proleptic Gregorian
only), TM-016 (Hinnant's algorithms as given), TM-017 (`cal` declares
`ETimeValue` and nothing else), TM-026 (the sweep is the gate). All settled.
~~**Nothing in this cycle is blocked on a question.**~~ **Two things wait, and
neither stops the next dispatch** (2026-09-25):

- ~~**the exit codes 108 and 109** (`DecreasesViolated`, `LimitViolated`) are
  proposed in `0.1.0b.md` §2 and are the orchestrator's to confirm for both
  streams — a gate of 0.1.0b's step 6 and of 0.1.0c;~~ **confirmed by the
  orchestrator for both streams, 2026-09-25, and recorded as TM-152;**
- **`../../OPEN_QUESTIONS.md` Q-6** — what replaces `VERIFICATION.md` P-1 now
  that every construct it names is live — is the author's. 0.1.1 is written to
  proceed on its recommended answer and states the exact alternative
  (`0.1.1.md` §6), so no answer needs a new plan.

**And one number this cycle has carried since TM-014 is wrong**: the first day
of the range is −4 371 587, not −4 371 588 — so the range holds 7 304 484 days,
not the 7 304 485 the checklist and gate below say. Found at planning;
`0.1.1.md` §1 has the evidence, and 0.1.1 corrects it — specification first,
with the test that recomputes it — which is why the numbers below are flagged
rather than silently changed. **CORRECTED AT 0.1.1 (TM-161)**, with the test
seen red at the old constant first; the numbers below now carry the corrected
values, and 0.1.2's month count moved with them — 239 976 was 19 998 years ×
12, and `[−9999, +9999]` is 19 999 years, so **239 988** (found at 0.1.1's
execution, not at planning).

**Decisions OUT, taken at 0.1.0 because the work revealed them:** TM-147 (an
`error:` cannot carry a payload, so C-5's "`ETimeValue` with a `ValueFault`" is
amended to C-5b and the delivery mechanism is O-X8) and TM-148 (the struct
literal is an unchecked constructor the language will not let us remove, so
C-8's guarantee is about the values this library PRODUCES — C-8b, and
`check_civil_literal` covers the half that is enforceable). Both are
specification corrections measured at pin `aaffb87`, not compiler defects, and
**neither blocks 0.1.1**: `date_to_days` is branch-free arithmetic that is
total over every field value, so it is safe by construction rather than by
C-8's guarantee. That is worth knowing before writing it.

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.1.0 | **The types** — `CivilDate`, `CivilTime`, `CivilDateTime`, `Weekday`, `Month`, and the validating constructors | **DONE 2026-09-06.** Every date `ntime` PRODUCES is a date that exists — and C-8b is why that sentence is no longer "a date that exists is a date that exists": the struct literal is an unchecked constructor the language will not let us remove (TM-148) |
| 0.1.0b | **The adoption to compiler `c3bdae2`** — the CI pin as its own commit, a measure on every loop, the two new floor arms, `~0u64`, `vec_reserve` by `ralloc`, the defect corpus's landings, and the prose the pin made false — **[`0.1.0b.md`](0.1.0b.md), DONE 2026-09-25** | `GREEN -- 70 unit(s)` at `c3bdae2`, and CI green on the same pin — run `36152772081` |
| 0.1.0c | **The access properties** — `Vec`/`Bytes` hidden, sealed and under `ListLen` (the board's item 13), `CivilDate`/`CivilTime` sealed, `check_civil_literal` retired — **[`0.1.0c.md`](0.1.0c.md), DONE 2026-09-25** | C-8 holds of the TYPE again for every module but `cal` (C-8c); `GREEN -- 75 unit(s)`, and CI green — run `36158556785` |
| 0.1.1 | **The algorithms** — `date_to_days`, `days_to_date`, the leap rule, `days_in_month` — **[`0.1.1.md`](0.1.1.md), DONE 2026-09-25** | the published algorithms, cited, with their divisions by literals — and the range's first day corrected by the test that recomputes it (TM-161); `GREEN -- 78 unit(s)`, and CI green — run `36164292563` |
| 0.1.2 | **The sweep** — the exhaustive round trip both ways, monotonicity and month lengths, each assertion shown to fail; the weekday rider moves to 0.1.3 with `weekday()` (TM-165) — **[`0.1.2.md`](0.1.2.md), DONE 2026-09-25** | the round trips and two of the gate's three riders (TM-166, TM-167); `GREEN -- 81 unit(s)`, and CI green — run `36176251416` |
| 0.1.3 | **Derived fields** — weekday, day-of-year, ISO week date, ordinal date — and **the weekday cycle on 0.1.2's walk** (TM-165) — **[`0.1.3.md`](0.1.3.md), DONE 2026-09-25** | computed, never stored; **the cycle's gate complete** (TM-169 … TM-176); `GREEN -- 86 unit(s)`, and CI green — run `36198540622` |
| 0.1.3b | **`check_no_owning_fields`' premise, re-measured** — owed since the workbench found `PLAYBOOK.md` §2's TYPE-046 row false: the premise was false at every kept pin, the check had three blind spots, and a move out of `fixed` storage compiles and faults, a compiler defect raised as O-N20, the compiler's DEF-99 — **[`0.1.3b.md`](0.1.3b.md), DONE 2026-09-25** | S-19b (TM-177), and cycle 0.5's version string held behind the defect (TM-178); the check widened and commissioned; `GREEN -- 90 unit(s)`, and CI green — run `36201639726` |
| 0.1.3c | **`Vec` move-only by construction** — question 9, answered 2026-09-25 — porting `nitpick-regex`'s 0.0.4d, which has landed and been verified (2026-09-25) — **NOT PLANNED YET; plan it before it is dispatched, against compiler `c970483`, which 0.1.4c adopts — where a lent owning parameter admits no write path (DEF-102) and a generic pass-out of a `T` place through a pointer is refused (DEF-104). It runs AFTER 0.1.4c** (the orchestrator, 2026-09-26), and it ports `nitpick-regex`'s 0.0.4e as well as its 0.0.4d — `vec_get<T: Pod>` through a `Pod` trait and a `move` in `vec_pop`, beside the marker field — with P-1's A′ replacement (`0.1.4c.md` §11); 0.1.4 ran first while that 0.0.4d was still pending | no whole-`Vec` copy and no by-value `Vec` compiles |
| 0.1.4 | **The cross-oracle** — Python's `datetime` against every date of years 1 … 9999, by a generated corpus of one digest per year; and a compiler defect found at planning — **[`0.1.4.md`](0.1.4.md), DONE 2026-09-25** | agreement over years 1 … 9999 — every date, not a sample (TM-179 … TM-183); `GREEN -- 91 unit(s)`, and CI green — run `36210527554` |
| 0.1.4b | **The managed-memory gate** — `NPK_HEAP_STATS`'s `peak_live`, carried from cycle 0.0 by `0.1.0.md` §8 — **[`0.1.4b.md`](0.1.4b.md), DONE 2026-09-26; it ran before 0.1.3c** | the four named — two twin pairs and two `Bytes` tests, six files — held to the runtime's own count, each remedy with a work floor; the `ulimit -v` cap a belt the harness runs, beside the floor program; and `bytes_take` owning its answer (`0.1.4b.md` §4; TM-184 … TM-188); `GREEN -- 91 unit(s)`, and CI green — run `36217173756` |
| 0.1.4c | **The adoption to compiler `c970483`** — the end of the compiler's 1.6.0 chain: O-N20 and O-N23 landed, each reproduction asserted with its old verdicts as the control; `probe13d` at `int64`, since DEF-104 refuses its generic accessor; the hold on 0.5's version string lifted; CI at the new pin in the same commit — **[`0.1.4c.md`](0.1.4c.md), DONE 2026-09-26; it ran before 0.1.3c** | every file meeting its header at `c970483` — `GREEN -- 101 unit(s)` — and RED at `c3bdae2` exactly where the landings are asserted, 94 of 101; CI green on the same pin — run `36236385937` (TM-189 … TM-192) |
| 0.1.5 | **Close** — and what earlier subcycles found and did not own: the public `README.md`'s *"Status: planning. No code yet."*; `nitpick.toml`'s `check` item still saying *"cycle 0.0.4"*; `src/core/core.npk`'s *"the other five placeholders point AT it"* (four do); `check_error_budget`'s *"expected: no module raises anything before cycle 0.1"*; and `tests/probe/README.md`'s table, which never listed probes 12 to 16; **and from 0.1.4's planning**: ~~the `fixed`-import defect's reproduction (`0.1.4.md` §3) committed to `tests/probe/defect/` once the registry has numbered it~~ — **moved to 0.1.4c, where its fix landed (TM-192)**; the public `README.md`'s and `CLAUDE.md`'s `tools/` line, which names only the tzdb tables, and the `sweep` stage's headroom against its 30 s threshold (`0.1.4.md` §15) — 22.2 s at 0.1.4's execution; **and from 0.1.4's execution**: `.gitignore`'s *"NOT ignored, deliberately"* line for `tests/fixtures/`, which names the corpora planned — the tzdb's test material, the format vectors, the fuzzer's finds — and not the one committed; **and from 0.1.4c's execution**: `harness/run.py`'s `run_defect_corpus` docstring, which says the corpus is *"six subdirectories"* and that one manifest entry per subdirectory would be *"six places"* — six at cycle 0.0.6, when it was written, seven since 0.1.3b's `fixed_move_out/`, and eight since 0.1.4c's `fixed_import_scope/` | `done/0.1/`, `0.2.0.md` written |

**Why 0.1.4b exists — a premise found false at planning, 2026-09-25.**
`0.1.0.md` §8 carried the `peak_live` gate on the reading that `NPK_HEAP_STATS`
*"is not in pin `aaffb87`"*. **It is**: the runtime object at `aaffb87` and at
`c3bdae2` both carry it, and `NPK_HEAP_STATS=1` makes a program print
`heap: allocated=… peak_live=… count=…` at exit. Measured on this tree's own
pairs at `aaffb87`: `probe06b` **70 000 024** against `probe06c` **59**;
`probe12` **70 000 059** against `probe12b` **94**; `bytes_growth` 2 048 587;
`bytes_view_lifetime` 160 — the discrimination §8 asked for, at the numbers it
predicted would need an instrument. §8's rule was *"if it is still not at the
pin when 0.1 closes, carry it forward"*; it is at the pin, so the cycle owes the
gate, and 0.1.4b is where it is placed — after the algorithms, before the close,
touching nothing 0.1.1–0.1.4 depend on. Its three steps are §8's; its plan owes
the harness's reading of the line (a header marker and the constructed
environment) and a control that fails.

## Checklist

### 0.1.0 — the types — **DONE 2026-09-06**
- [x] `CivilDate`, `CivilTime`, `CivilDateTime` with the field orders from `CALENDAR.md` §3 — **declaration order is comparison order** (C-6), and a test asserts it for each — `tests/unit/civil_order.npk`, per FIELD and with the DOMINANCE case for each, because a type whose fields were swapped still orders correctly on each field alone
- [x] `#[derive(Eq, Ord, Clone, Debug)]` on each, with probe 01's verdict cited in a comment — and **D-123 cited for declaration order, never D-051**, which is a real heading about `ostring` that `src/core/vec.npk` mis-cited for four subcycles (TM-143)
- [x] `Weekday` and `Month` as enums, Monday first (C-7), with `weekday_number()` 1…7 and the Sunday-first helper beside it — all seven values of both asserted, because the numbering is read off the enum's TAG rather than written as a seven-arm `pick`, so the test is what makes the tag mapping checked
- [x] **validating constructors only** (C-8): `civil_date(y, m, d)` returns `Result<CivilDate>` and refuses February 30th, month 13, day 0. **No unchecked constructor exists** — *in the module.* **AMENDED BY C-8b (TM-148): a CONSUMER can still write the struct literal**, measured at pin `aaffb87` — it compiles, links and runs at exit 0 with `month == 99`. `check_civil_literal` keeps `src/` inside the guarantee; nothing can keep a consumer inside it
- [x] `CivilTime` refuses hour 24 (C-9); the normalising acceptance belongs to the parser at 0.4, not here — and second 60 likewise
- [x] `ETimeValue` and `ValueFault` declared here and nowhere else — `check_error_budget` reports **1 of 3**, naming the two not yet declared
- [x] ~~`check_failsafe_arms` goes live: a program importing only `cal` owes exactly one arm~~ — **the prediction was WRONG BY EIGHT and the corrected item is the measurement.** `check_failsafe_arms` was already live at 0.0.3; what went live here is its first non-floor row. **A program importing only `cal` owes the arms `NITPICK-REACH-003` names, measured and recorded: NINE** — `cal.ETimeValue`, `Unreachable`, `HeapOom`, `HeapBadRequest`, `WildLeak`, `DivByZero`, `DivOverflow`, `IntOverflow`, `OutOfBounds`. `9 = 4 (floor) + 1 (identity) + 4 (cal's own arithmetic, charged to the consumer)`. That is TM-107 exactly, `0.1.0.md` §4 predicted the falsification, and `SAFETY.md` S-4's totals column now carries the number with the command that produced it
- [x] **added, not planned:** `check_civil_literal`, commissioned with two planted violations and two controls — one of them the banned form in a COMMENT, since `src/lib.npk`'s own header spells it out in prose

### 0.1.0b — the adoption to compiler `c3bdae2` — `0.1.0b.md` §7 is the full list — **DONE 2026-09-25**
- [x] commit 1 is the CI pin alone (`c3bdae2`, both digests), RED locally at the self-check and never pushed alone
- [x] `vec_reserve<T>` relocates with `ralloc`; `vec.npk` holds no loop (D-264, TM-150)
- [x] every `while` states its measure — 29 by the tool, 19 by the committed reading `decreases_read.txt`, none `unbounded`
- [x] `U64_MAX = ~0u64` at both sites (D-311, TM-149)
- [x] the tzdb spike's templates carry clauses and arms, and a re-run reproduces TM-135's table sizes exactly
- [x] every `failsafe` names what `REACH-002` asks — `StackExhausted` 106 and `MachineFault` 107 in 61 roots, `DecreasesViolated` 108 in 20 — and nothing more
- [x] the harness: floor six, calibration 6 / 7 / 10, the umbrella a generated row (12) — TM-155
- [x] O-N18 and O-N19 asserted by markers, their exemptions gone, their controls at `aaffb87` recorded; `case3_hash_and_clone` answers 17 (TM-154, TM-152)
- [x] RX-120's evidence corrected (TM-153); P-1's and P-9's notes in `VERIFICATION.md`; the pin-dependent prose swept with its denominators
- [x] `GREEN -- 70 unit(s), 0 failures; 5 pending` at `c3bdae2`, and CI green on the pushed adoption — run `36152772081`, read from its own log

### 0.1.0c — the access properties — `0.1.0c.md` §4 is the full list — **DONE 2026-09-25**
- [x] `Vec<T>`: `items` hidden, `count`/`cap` sealed under `ListLen`; `Bytes`: `body` sealed, `len` sealed under `ListLen` (TM-156) — and what the seal does not stop, measured and with the author: a write THROUGH `b.body.ptr`, and a whole-struct copy of a `Vec` (the workbench's question 9)
- [x] `CivilDate` and `CivilTime` sealed; `CALENDAR.md` C-8c added (TM-157)
- [x] `LimitViolated` 109 in exactly the nine roots REACH names — plus `probe16e`, a tenth, which the plan's own step 6 adds; the umbrella 13, generated (TM-159)
- [x] `probe15` asserts `TYPE-079`; `probe16`…`probe16e` pin the seal and its positive twin
- [x] `check_civil_literal` retired (TM-158)
- [x] `GREEN -- 75 unit(s), 0 failures; 5 pending`, and CI green — run `36158556785`
- [x] **added, not planned:** O-N8 discharged — fixed since pin `94874ce` by the compiler's D-248 (TM-160); the dispatch carried it

### 0.1.1 — the algorithms — `0.1.1.md` §8 is the full list — **DONE 2026-09-25**
- [x] `date_to_days` / `days_to_date` as Hinnant's `days_from_civil` /
      `civil_from_days`, cited in the module header with the source — `never fails` and total, and range-first and built through `civil_date`, respectively (TM-162)
- [x] every division by a nonzero **literal** (C-11), so D-007's obligation is discharged by inspection — and a test that greps the module for a division by a non-literal — **`check_literal_divisors`, a live tree check, with FOUR plants, not three (TM-163)**: C-11 now says *positive* and carries no list, and the check reads 17 divisions in `src/cal/`
- [x] intermediates in `int64` (C-12, amended by TM-162: its −4.4 × 10⁶ was the day number, not `era * 146097`)
- [x] ~~`is_leap_year` and `days_in_month`, applied uniformly across negative years~~ — **DONE AT 0.1.0**, because `civil_date` cannot refuse February 30th without them and a constructor that validates three of its four conditions is not a validating constructor (`0.1.0.md` §3 took that decision at planning). `tests/unit/leap_rule.npk` covers the four century cases, their negative mirrors, and −1/−4/−100/−400 by name. **The negative-year correction turned out NOT to be needed in the leap rule** — every clause compares a remainder against ZERO, and zero has no sign — but it IS still owed by `days_from_civil`'s `era`, which uses a non-zero remainder
- [x] the range constants **recomputed by a test** rather than trusted from `limits.npk` (0.0.4's note) — **and the test is seen RED first: at planning it exits 10 against today's `NTIME_DAY_MIN`, which is one day off (`0.1.1.md` §1)** — `tests/unit/range_constants.npk`, red at exit 10 and then green; `NTIME_DAY_MIN` is −4 371 587 and the range 7 304 484 days (TM-161). `tests/probe/probe07_negative_div.npk` had asserted −4 371 587 since cycle 0.0.0, and nothing compared it with the constant
- [x] **in `0.1.1.md`'s plan and not in this checklist:** `tests/unit/day_number_vectors.npk` (§4a's twenty-six, both ways) and `days_to_date_refused.npk` (§4c), each shown to fail under a one-line mutation; and the contracts as comments per Q-6's A′ (TM-164), `cal` still 11 arms
- [x] **found at execution, not planned:** 0.1.2's month-length count, 239 976, corrected to 239 988 — the range is 19 999 years (TM-161)

### 0.1.2 — the sweep — [`0.1.2.md`](0.1.2.md) §11 is the full list — **DONE 2026-09-25**
> ⚠ **Read `0.1.1.md` §1 before this section.** The first day of the range is
> −4 371 587 and the range holds **7 304 484** days; the bound and the two
> counts below were corrected by 0.1.1's worker together with `CALENDAR.md` §2
> (PD-12, recorded as **TM-161**) — they read −4 371 588 and 7 304 485 until
> then — and the month count with them: it read **239 976**, which is 19 998
> years × 12, and the range is 19 999 years.
> **And measured at planning, for this subcycle's own plan:** a forward round
> trip over the whole corrected range took 1.23 s at `-O0` and 0.19 s under
> `opt -O2`; `for (int64:i in lo..hi)` is inclusive and needs no measure and no
> arm, while `till`/`loop` arm `BadStep` even with a literal step.
- [x] every day number in `[−4 371 587, +2 932 896]` satisfies `date_to_days(days_to_date(n)) == n` — 7 304 484 cases — `tests/unit/sweep/every_day_number.npk` — both legs, `swept 7304484` (TM-166)
- [x] every date in the range satisfies `days_to_date(date_to_days(d)) == d` — 7 304 484 cases — `every_civil_date.npk`, its dates generated by the leap rule and the month table and never by `days_to_date` — both legs, `swept 7304484`
- [x] **monotonicity**, on the same walk: each date's day number is the previous one's **plus one** — stronger than "strictly increasing", which a leap rule missing its 400-year day passes (TM-167, measured at planning) — re-measured at execution: on that mutant the `+ 1` chain exits 13 and a `>` chain exits 0 having printed `swept 7304435`; `CALENDAR.md` C-17 now says it this way
- [x] ~~**the weekday cycle**: advances by exactly one mod seven per day, across every century and 400-year boundary~~ — **MOVED TO 0.1.3 (TM-165)**, where `weekday()` is written — struck, not done: it is 0.1.3's second item; 0.1.2 asserts the `+ 1` chain it rests on, at every one of the range's 7 304 483 steps
- [x] **month lengths**: match the leap rule for every (year, month) in range — 239 988 cases — `every_month_length.npk`, as the next month's first less this month's first, not "last less first plus one" (TM-167, measured at planning) — both legs, `swept 239988`; the chosen form exits 12 on the century-rule, 400-year-rule and April-31 mutants, where the declined one exits 0 with the full count
- [x] the sweep is a `sweep`-stage test, runs in full on a full invocation, and `--quick` skipping it is caught by the self-check's case 7 — **and on the real entry**: the `SKIP` line read from a `--quick` run, and the stage seen to reject the real `every_day_number.npk` cut one day short — `swept 7304483 of the 7304484` on both legs, and the uncut control silent
- [x] **every assertion in the three files shown to fail** — the mutation matrix, `0.1.2.md` §5, fourteen rows — including M5, a mutant nothing else in the suite catches — both tables, 0 differences from the plan; M5's extent, 24 days, re-derived by an independent model
- [x] **each domain recomputed three ways and diffed against every statement of it** (`0.1.2.md` §2), and every live statement tagged, so `check_denominators` diffs it on every run (TM-168) — 19 sites, then 22 with the three headers, 0 disagreements, the control red; thirteen tags, the plan's eleven and two in the CI header's new sentence
- [x] the wall-clock cost recorded; if it is over ~30 s, say so and decide whether to keep it in the default run — **measured at planning: 4.5 s for the three members, both legs, compile included, against a 30 s threshold set in advance (`0.1.2.md` §6)** — at execution 4.5 s, and 4.6 s on the gating run: kept in the default run, and `BUILD.md` B-9 carries the number

### 0.1.3 — derived fields — [`0.1.3.md`](0.1.3.md) §13 is the full list — **DONE 2026-09-25**
- [x] `weekday()` derived from the day number (C-13), **never stored** — through one private `weekday_index`, whose correction is range-checked before `weekday` manufactures the tag (S-15c; TM-171): measured at planning, a forged `Weekday` falls through every arm of an exhaustive `pick` — **re-measured at execution**: `forge.npk` exit 0 on both legs, and the checked `=>` to an enum is `NITPICK-TYPE-009`
- [x] **the weekday cycle, C-17's second rider, on `tests/unit/sweep/every_civil_date.npk`'s walk** — moved here from 0.1.2 by TM-165 (`0.1.2.md` §9): each day's `weekday()` equals a count begun at −9999-01-01's **Monday** and advanced by one per day, so it is Monday … Sunday on every day of the range. **Not** "advances by one, mod seven": that check passes a weekday whose modulus correction is missing, over the whole range (measured at 0.1.2's planning), so that mutant is the rider's control and must exit red — **re-measured at 0.1.3's planning: the rider exits 17 on it, and on a weekday one day late, where the declined form exits 0 with the full count; and with the belt kept, the missing correction stops at 95 instead of answering** — re-measured at execution, `0.1.3.md` §7's rows D1, D2 and D3, 0 differences
- [x] `day_of_year()` and the ordinal-date round trip — ~~the round trip~~ **the reverse, `ordinal_to_date`, handed a COUNT of the year's days rather than `day_of_year`'s answer, and asked to refuse the day after every year's last** (V-4b; TM-174): measured, the round trip as worded passes a reverse that accepts day 366 of every year — at execution, `every_ordinal_date.npk` `swept 7304484` on both legs, and red at 15 on that mutant (D5) where the declined round trip exits 0
- [x] `iso_week_year`, `iso_week_number` (1…53), `iso_weekday`, by the standard rule (C-14) — week 1's Monday as the Monday on or before 4 January, one private function read in both directions (TM-172); ISO 8601-1:2019 with Amd 1:2022, `../../research/iso-8601-week-date.md`
- [x] ~~the ISO boundary cases as explicit tests: 1 January falling on each of the seven weekdays, in leap and common years — fourteen cases, each hand-checked~~ **the boundary cases indexed by the year that ENDS** — for each of the fourteen year shapes, its 1 January, its 31 December and the next 1 January, **41 dates derived three ways** (TM-175): measured at planning, a common year beginning on a Saturday opens in week 52 or week 53 of the year before depending on THAT year, so C-14's fourteen as worded leave one answer to the choice of year — at execution, the three methods agree on all 41 and the control is red on its one row; C-14 restated (TM-175)
- [x] ~~the ISO week round trip on the same exhaustive sweep as 0.1.2~~ **the ISO week date against a walk of ISO 8601's rule over every date, the reverse handed the walk's values, and the week after every week-year's last refused** — its own member, `every_iso_week_date.npk` (TM-174): measured, the round trip as worded passes week 1 taken as the week holding 5 January — at execution, `swept 7304484` on both legs, and red at 16 on that mutant (D8) and on week 53 accepted everywhere (D9), where the declined round trip exits 0
- [x] **found at planning:** `BUILD.md` B-15 required a `cal_` prefix that none of `cal`'s eight public names has ever had, and promised a check nobody scheduled — restated (TM-176); `TESTING.md` V-2's weekday row still stated the declined formulation; V-4 counted three round trips — all three restated, V-4b added
- [x] **found at execution, not planned:** two comments that said `date_to_days` carries the negative-year correction — `is_leap_year`'s header and `tests/unit/leap_rule.npk`'s — false once TM-170 moved the formula, corrected; `CALENDAR.md` C-5b's and O-X8's *"eleventh"* no-fault variant, the fifteenth once TM-173 appended four, corrected; and Q-6's note records the author's answer, A′, where the plan's text said the question stays open

### 0.1.3b — `check_no_owning_fields`' premise, re-measured — [`0.1.3b.md`](0.1.3b.md) §9 is the full list — **DONE 2026-09-25**
- [x] the premise measured false at every kept pin, and the rule restated on the reason that holds — a copy out refused, a move out faulting (S-19b; TM-177) — re-measured at execution: the transcript equal to the plan's, 84 builds
- [x] the check widened to an owning element, an owner at any depth, and a field's type rather than its name — each planted and seen red first — three problems against the old check, each attributed to its blind spot by running it on each fixture; then 23 plants and 23 controls
- [x] `probe17`, `probe17b`, `probe17c`, and `tests/probe/defect/fixed_move_out/` with its control and generated transcript; the defect raised by path — **and registered as O-N20, the compiler's DEF-99**, whose refusal, `NITPICK-TYPE-084`, is its 1.6.0 step 3f and at no pin of ours yet; the committed text cites the ids, and this repository carries an O-N20 entry
- [x] `ZONE_MODEL.md` Z-4 and Z-6's version string held behind the defect (TM-178) — O-X10 open, cycle 0.5 settles it, and 0.5's checklist item now points at the hold
- [x] **found at execution, not planned:** the defect corpus's present-tense arithmetic in `TESTING.md` V-1g and `run_defect_corpus`' docstring, now `28 = 3 exempt + 25 asserted`; the defect table's note that every defect in it is fixed, false beside the O-N20 row; and a plain `pass` of a `fixed string` scalar — the shape of Z-6's obvious body, in no committed case — measured at all six kept pins, `run:95` on both legs

### 0.1.3c — `Vec` move-only by construction — NOT PLANNED YET
- [ ] planned against compiler `c970483`, after 0.1.4c adopts it — `nitpick-regex`'s 0.0.4d has landed and been verified (2026-09-25), and its 0.0.4e adoption to the same pin carries the rest of the design (`vec_get<T: Pod>`, the `move` in `vec_pop`) — porting it (question 9); and `vec_at<T>`'s `#wild_slice` read, which DEF-104's gate does not reach and which moves an owning element out (`0.1.4c.md` §1.3, §11)
- [ ] **from 0.1.4b's planning:** TM-150's `vec_pop` churn pair — two million push-then-pop cycles, `peak_live` 120 against `vec_clear`'s 48 000 096 — committed as a program with `heap:` bounds; it was measured in a scratch directory at 0.1.0b and no program stands behind the number (`0.1.4b.md` §15)

### 0.1.4 — the cross-oracle — [`0.1.4.md`](0.1.4.md) §13 is the full list — **DONE 2026-09-25**
- [x] ~~`tools/gen_civil_oracle.py` emitting `(y, m, d, day_number, weekday, iso_week, day_of_year)` rows from Python's `datetime`, committed under `tests/fixtures/civil/`~~ **`tools/gen_civil_oracle.py` writing, from Python's `datetime`, one row per year 1 … 9999 — the day number of its 1 January, its length, and a digest of nine fields of every one of its days — as `tests/fixtures/civil/civil_oracle.npk`** (TM-179, TM-180): measured at planning, a few hundred thousand explicit rows is 33.7 MB of source and 44 s of `npkc`, and a sample misses what falls between its rows — at execution 1 001 690 bytes, its `sha256` the plan's at Python 3.12.3
- [x] ~~the agreement test over every row~~ **`tests/unit/sweep/every_oracle_date.npk`, over every date of years 1 … 9999 — 3 652 059 — equal to every row, each assertion seen to fail** (`0.1.4.md` §7), its row type imported by name beside the table (TM-181; the defect of `0.1.4.md` §3) — at execution `swept 3652059` on both legs the first time it ran, and the matrix 0 differences, twice
- [x] **the limitation stated in the fixture's header**: Python covers years 1 … 9999 only, so the negative half has the self-consistency of 0.1.2 and nothing else (C-18) — and in the member's, C-18's and V-6's; measured, `days_to_date`'s era one day late passes the member with the full count
- [x] **added at planning:** the corpus derived a second way — a count that reads no `datetime` — and diffed against the corpus and every vector the tree states for years ≥ 1 (`0.1.4.md` §4); regenerated after the documents and `cmp`-identical (TM-183) — at execution 9 999 rows and 12 + 28 vectors, 0 disagreements, the control red on year 2000 alone; `cmp exit 0`
- [x] **found at execution, not planned:** `harness/run.py`'s `_verdict` comment that the `none` bucket *"is the support modules"*, false once the corpus joined it — rewritten; `.gitignore`'s *"NOT ignored, deliberately"* line for `tests/fixtures/`, which names the corpora planned and not the one committed — carried to 0.1.5; and the registry's id for the defect, with the compiler's, carried by §11 into this repository's own entry and the three sites §11 names

### 0.1.4b — the managed-memory gate — [`0.1.4b.md`](0.1.4b.md) §13 is the full list — **DONE 2026-09-26**
- [x] the instrument established from the runtime's source and output, and every fact re-derived at the dispatched pin before anything changes, the anchor unchanged (`0.1.4b.md` §2, §11) — at execution, `baseline.py` equal to §11's block, 44 lines and 0 differences, the anchor `162b8975…` at 72 576 bytes
- [x] a `// heap:` marker and the constructed environment: the runtime's `NPK_HEAP_STATS` line held to a file's bounds on both legs, exactly one line per run, the evidence in the verdict line (TM-184)
- [x] **six files bounded** — the two twin pairs and the two `Bytes` tests that `0.1.0.md` §8 names, which this row called four pairs until planning — each leaking twin at or above its leak, each remedy under its ceiling and over its work floor, each `Bytes` test under its ceiling; every ceiling placed by TM-185's rule, and every bound seen red on its mutant (`0.1.4b.md` §7) — at execution the matrix 44 lines and 0 differences, and under CI's own build of `npkc` — run `36217173756` — the six units' printed evidence equal to the workbench's
- [x] the `ulimit -v` pair run by the harness as a belt, with the floor program as its control, where TM-131's was `/bin/true` (TM-186) — 92 against 0 under 64 MiB on both legs, on the workbench and in CI
- [x] V-14's ninth case: a program whose managed memory disagrees with its header — five plants beside one control (TM-187)
- [x] **found at planning:** `bytes_take` hands back an owned copy, and `bytes_growth` asserts that it survives a reuse and a growth of its sink (TM-188, `SAFETY.md` S-18f) — the old take restored, `bytes_growth` exits 28 at the reuse, and with the reuse cut 30 at the growth (K7, K8)
- [x] `0.1.0.md` §8 discharged — the gate cycle 0.0 carried unticked. Its three steps: the instrument commissioned against a known-leaking and a known-clean control — `probe06b`'s floor and `probe06c`'s ceiling, on every run; a bound on each of the pairs — the six files; and the `ulimit -v` cap kept as a belt — run by the harness, its control the floor program where §8 named `/bin/true` (TM-186)

### 0.1.4c — the adoption to compiler `c970483` — [`0.1.4c.md`](0.1.4c.md) §9 is the full list — **DONE 2026-09-26**
- [x] the unchanged tree measured at both pins before anything changed: RED at 90 of 91 at `c970483`, GREEN 91 at `c3bdae2`, and a per-file sweep of all 108 `.npk` moving exactly four (`0.1.4c.md` §1) — at execution, step 0's two runs and `facts.py`'s 44 lines each equal to the plan's block, 0 differences
- [x] O-N20 landed (the compiler's DEF-99): `fixed_move_out/`'s three asserted as `NITPICK-TYPE-084` refusals, their `EXPECT_EXEMPT` entries gone, their `c3bdae2` verdicts the control, appended to `TRANSCRIPT.txt` (TM-189) — the new `c3bdae2` rows 7 of 7 equal to the ones 0.1.3b committed
- [x] `probe13d`'s accessor names `int64` — DEF-104 refuses its generic pass-out through a pointer — and it still reads the sentinel unguarded (TM-190) — exit 0 on both legs, locally and in CI
- [x] the hold on `ZONE_MODEL.md` Z-4 and Z-6 lifted, Z-4's shape measured across an import; O-X10 settled (TM-191) — re-measured at execution: the importer's move and `pass` refused `TYPE-084`, its clone and lend `run:0` on both legs
- [x] O-N23 landed (DEF-105): its reproduction committed as `tests/probe/defect/fixed_import_scope/`, seven cases asserted at their fixed verdicts with a transcript at every kept pin (TM-192) — the transcript's 56 lines equal to the plan's, and cases 1, 2, 3 and 6 red at `c3bdae2`
- [x] the carried checks — DEF-95, DEF-96, DEF-97, DEF-98, DEF-102, DEF-103, DEF-106 — and DEF-108's `FLOW-001` measured, each new refusal planted once as the sweep's control (`0.1.4c.md` §1.6) — none met in the tree at either pin, each plant refused at `c970483` only, and 88 of 88 functions in the 30 refused files leaving on their last line
- [x] CI at `c970483` in the adoption's own commit; `GREEN -- 101 unit(s)` locally and in CI, and RED at `c3bdae2` exactly where the landings are asserted — the work commit `55abc99`, three `ci.yml` lines moving the pin; `GREEN -- 101` in 125.6 s locally and in CI run `36236385937`, read from its own log, 0 differences; RED at `c3bdae2`, 94 of 101, the seven landed cases and nothing else
- [x] **found at execution, not planned:** `run_defect_corpus`' docstring's *"six subdirectories"*, true at 0.0.6 and eight since this subcycle — carried to 0.1.5's row

## Gate

**Every day in the supported range round-trips, in both directions, in full.**
7 304 484 cases each way (7 304 485 until 0.1.1, TM-161), plus monotonicity,
the weekday cycle and month lengths on the same sweep. This is the strongest
statement `ntime` makes and it costs seconds.

*(Since 0.1.2's planning, TM-165: the round trips, monotonicity and month
lengths landed at 0.1.2, and the weekday cycle at 0.1.3 with the function it
asserts — so the gate was completed at 0.1.3, not 0.1.2: every item of it is
asserted on every full invocation since 0.1.3's work commit, and CI run
`36198540622` is the first to run them all. And each rider is stated
in the form a wrong implementation fails, TM-167: every one of C-17's three, as
first written, is passed by a mutant the plan measured.)*

## Watch for

- **The negative years are where the bugs are.** Probe 07 pinned that `/`
  truncates toward zero, and Hinnant's algorithm carries the correction for it —
  but any *new* arithmetic written in this cycle has to carry it too. A
  reviewer's question for every division added here: what does this do at
  year −1?
- **`weekday` computed, not stored** (C-13), and the same for every other
  derived field. A stored derived field is a second representation of a fact
  the date already carries, and the two can disagree.
- **The validating constructor is the whole contract — and READ C-8b BEFORE
  RELYING ON IT.** Everything `ntime` returns is a real date because
  `civil_date` is the only thing in `src/` that builds one, and
  `check_civil_literal` is what keeps that true. But a CONSUMER can write
  `CivilDate{ … }` directly: measured at pin `aaffb87`, month 99 and day 99
  compile, link and run at exit 0 (TM-148). So the sentence "everything
  downstream skips the question" is **not** available to 0.1.1: write
  `date_to_days` to be total over every field value — Hinnant's is, by
  construction — rather than to be correct only on valid input. A single
  unchecked constructor added for convenience would remove the library-side
  half of the guarantee as well.
  **From 0.1.0c the consumer half closes too**: at compiler `c3bdae2` a field
  can be `sealed`, and every field of `CivilDate` and `CivilTime` is, so the
  struct literal is `NITPICK-TYPE-079` outside `cal` (measured at planning;
  `0.1.0c.md` §1). `date_to_days` stays total anyway — it costs nothing, and
  `wild` storage is still an opt-out. **And `check_civil_literal`, named above as
  what keeps the library half true, is retired at 0.1.0c (TM-158)**: the same
  `TYPE-079` refuses the literal in every module but `cal`, `src/` included.
- **The arm codes are cross-stream** (`0.1.0b.md` §2): 106 `StackExhausted`,
  107 `MachineFault`, 108 `DecreasesViolated`, 109 `LimitViolated`. A test whose
  computed exit equals one of them cannot tell its answer from that trap — the
  one such test in this tree is re-encoded at 0.1.0b.
- **`limit` and `end` are keywords**, and a range-bounds module wants both.
