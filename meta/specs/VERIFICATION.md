# Verification obligations

The compiler's cycle 1.5 makes `prove`, `requires`/`ensures`, `limit<Rules>`
and Z3 real. Its orchestration rules say that **every branch records its own
verification obligations and the orchestrator merges them** (R9), because
obligations discovered in a branch and never collected are the cheapest way to
lose the campaign.

This document is `ntime`'s list. It is written **before** the code, kept
current as the code lands, and is what `ntime` hands to the compiler's
obligation manifest when the verified build reaches libraries.

`ntime` is a good candidate for this: it is almost entirely integer arithmetic
over a stated range, which is the shape Z3 is best at.

---

## 1. Where this stands

| Compiler subcycle | What it gives us | Our state |
|---|---|---|
| 1.5.0 (done) | the SMT writer, z3 under a pinned profile, the obligation manifest, `llvm.assume` elision | §3's division and bounds obligations are already decidable |
| 1.5.1 | `limit<R>` names resolve, `Rules` bodies type, contracts type | §5's `limit` types become writable |
| 1.5.2 | `limit<Rules>` live | §5 lands |
| 1.5.3 | contracts live | §4's `ensures` clauses land |
| 1.5.4 | `prove` / `assert_static` | §6's inline proofs land |

> **SUPERSEDED by rule P-1b below (TM-197, cycle 0.1.3c)** — its safety
> argument, that every construct it names refuses, is false at every pin since
> `c3bdae2`. Kept as written, with its dated status note: how the premise
> failed is part of the record.

**Rule P-1.** Until a construct is live, its obligation is stated **as a
comment beside the code in the exact syntax it will take**, and is enforced by
a property test. The switch is then deleting a comment marker rather than
inventing the clause. The compiler's rungs refuse the constructs by name today,
so a premature `ensures` is a build failure, not a silent no-op.

> **Status at compiler `c3bdae2` (cycle 0.1.0b): P-1's premise is false and its
> replacement is `../OPEN_QUESTIONS.md` Q-6.** Every construct this rule names is
> live and none refuses. Measured: a live `requires`, `ensures`, `invariant` or
> `limit<R>` adds one trap identity to every consuming program's `failsafe`
> (`RequiresViolated`, `EnsuresViolated`, `InvariantViolated`, `LimitViolated`);
> `prove` and `assert_static` add none, and a plain build lowers `prove` to
> nothing. Until Q-6 is answered, no comment-form obligation in `src/` becomes a
> live clause, and **no comment-form obligation is evidence of anything** — it is
> checked by nothing, at any pin.

**Rule P-1b (TM-197, cycle 0.1.3c) — A′: an obligation is a comment unless a
numbered decision accepts the arm its live clause costs every consumer.** The
author's answer to `../OPEN_QUESTIONS.md` Q-6, 2026-09-25: *"the
recommendation on q-6 seems fine to me."* A `requires`, `ensures`,
`invariant` or `limit` is written LIVE only where a numbered decision says the
check earns the one `failsafe` identity it adds to every consuming program —
today that is TM-156's `ListLen` on the containers' lengths alone, which costs
every consumer of `core` `LimitViolated`. Every other obligation stays a
comment in the syntax it would take, `answer` and `outgoing` for `result` and
`old` (TM-130), is **evidence of nothing**, and is stood in for by a property
test — the sweeps of cycle 0.1, which check every day of the range, stand in
for `cal`'s. And:

- **`prove` stays a comment until the harness runs the verified build** (cycle
  0.8), because a plain build lowers it to nothing (`../OPEN_QUESTIONS.md`
  Q-6's table, measured at `c3bdae2`).
- **`decreases` and `unbounded` are the language's and always live** (D-304,
  P-9's note); `assert_static` is live wherever it helps, at no arm cost.
- **A check that guards something may be CODE on an arm every consumer already
  owes** — `weekday_index`'s `#unreachable()` belt (`SAFETY.md` S-15c) — which
  is not a contract and needs no decision.
- **Never a `requires` on an argument a caller supplies**: `SAFETY.md` S-12
  answers caller input with a `Result`, not a trap. **Nor on an accessor whose
  body already stops**: `vec_at`'s slice traps `OutOfBounds` (94) on an index
  out of range, and a live `requires` there would stop it first, as
  `RequiresViolated` (116), and add that arm to every consumer — measured at
  compiler `c970483`, cycle 0.1.3c's planning.

The switch for any row is mechanical — uncomment the clause, and record the
decision that accepts its arm — which is what P-1 promised and still delivers.
`nitpick-regex` records the same answer as its rule P-1b (its RX-164).

---

## 2. What the language discharges for free

- **Every index is bounds-checked and traps** (D-070). The question is only
  whether a *reachable* index is out of bounds — §3.
- **Every plain integer `+ - *` traps on overflow** (D-210). Calendar
  arithmetic cannot silently produce a wrong year.
- **Division by zero and `MIN / −1` trap** (D-007), and `CALENDAR.md` C-11
  makes every divisor in `src/cal/` a positive integer literal — nonzero, and
  not −1 — so both are discharged by inspection, and `check_literal_divisors`
  holds the tree to it. *(Until cycle 0.1.1, TM-163: "every divisor in the
  calendar algorithms a nonzero literal", which discharges the zero and not,
  on its own, the −1.)*
- **`Result<T>` everywhere** with no unchecked unwrap outside a `never fails`
  callee (D-163).
- **Owning values are move-only** and borrows cannot escape, so no table is
  aliased.

The obligations below are the residue: where a trap is a crash we would rather
prove cannot happen, and where the property is `ntime`'s own rather than the
language's.

---

## 3. Bounds

**Rule P-2 — the zone tables are the largest class**, and every access goes
through one accessor pair (`SAFETY.md` S-17):

```nitpick
func:zone_trans_at = ZoneTransition(ZoneEntry:z, uint16:i)
    requires (i < z.trans_count)
    ensures  (result_index >= 0i64 && result_index < TRANSITIONS_COUNT)
    never fails { … };
```

Discharging it makes **every transition access in the library** safe by
construction and elides the runtime check — the D-218.9 payoff, on the inner
loop of the binary search.

| Site | Obligation | How discharged |
|---|---|---|
| `zone_trans_at` | slice index in range | contract, Z3 |
| `zone_type_at` | type index in range | contract, Z3 |
| name-pool read | `offset + len <= POOL_LEN` | contract, Z3 |
| `Vec<T>` `at`/`set` | **`0 <= i && i < count`** — both ends, and the negative half is not redundant: an index derived from a narrower signed field can be negative (F4) | contract, Z3 |
| transition binary search | `lo <= hi` maintained; terminates | invariant + variant, Z3 |
| zone-name binary search | the same | invariant + variant, Z3 |
| format writer | `Bytes` capacity ≥ written | contract, Z3 |
| parser cursor | `at <= src.len` at every step | invariant, Z3 |

---

## 4. Range — the class this library is really about

**Rule P-3.** Every constructor and every arithmetic entry point carries its
range as a contract, so that `SAFETY.md` S-12's "checked before the trap" is
proven rather than reviewed:

```nitpick
pub func:civil_date = CivilDate(int32:year, uint8:month, uint8:day)
    ensures (result.year >= YEAR_MIN && result.year <= YEAR_MAX)
    ensures (result.month >= 1u8 && result.month <= 12u8)
    ensures (result.day >= 1u8 && result.day <= days_in_month(result.year, result.month))
{ … };

pub func:timestamp_add = Timestamp(Timestamp:t, Duration:d)
    requires (t.nanos < 1000000000u32)
    ensures  (result.secs >= SECS_MIN && result.secs <= SECS_MAX)
    ensures  (result.nanos < 1000000000u32)
{ … };
```

**Rule P-4 — the normalisation invariant is the one to prove first.**
`nanos < 1_000_000_000` on every `Timestamp` that exists. It is a precondition
of comparison being correct, of formatting being correct, and of every
arithmetic result being canonical — one fact that a dozen other proofs lean on.

**Rule P-5 — the `int128` sites** (`SPAN_MODEL.md` §5, N-20, N-20b) each carry
a `prove` that the narrowing `=>!` cannot lose, **beside** the runtime range
check S-15b makes mandatory — not instead of it:

```nitpick
// period_add, the nanosecond step
fixed int128:I64_MAX = 9223372036854775807i128;
fixed int128:I64_MIN = (0i128 - 9223372036854775807i128) - 1i128;

int128:total = (a => int128) + (b => int128);       // WIDENING: the checked cast
if (total > I64_MAX) { fail ETimeValue; }           // S-15b: the check is ours
if (total < I64_MIN) { fail ETimeValue; }           // with Overflow as S-3's detail
prove(total >= I64_MIN && total <= I64_MAX);
int64:ns = total =>! int64;                          // the ONE unchecked cast
```

Three things in that sample are corrections made at cycle 0.0.0 by
`tests/probe/probe02_int128.npk` and its three twins, and each was wrong in a
way that reads as fine:

- **The widenings are `=>`, not `=>!`.** The checked cast is legal in the
  widening direction, and spelling it leaves exactly **one** `=>!` in the
  function — the dangerous one. Writing all three the same way hides which is
  which, and this document is where a reader learns the idiom.
- **`int64`'s minimum cannot be spelled as a literal**, in any width. This
  sample previously wrote `-9223372036854775808i128`, which is refused
  `NITPICK-LEX-004`: *"this literal is outside the 64-bit literal envelope
  (D-148); a type's outermost values are constructed arithmetically, not
  spelled"* — and then `NITPICK-PARSE-002`, because the refused token leaves
  no expression. The **maximum** is fine, so a bound pair written by symmetry
  from a working upper bound is exactly what stops compiling.
  `tests/probe/probe02d_wide_literal_refused.npk` pins it.
- **`uint64`'s maximum is spelled `~0u64`** (the compiler's D-311, TM-149). The
  `0u64 - 1u64` that D-148 gave as the example is refused `NITPICK-TYPE-076` at
  compiler `c3bdae2` even as a `fixed` initialiser — D-310 folds a constant
  `+ - *` and refuses one whose value does not fit — and written in a function
  body it was always an `IntOverflow` trap (TM-134). A bit operation cannot
  overflow; a named constant keeps the spelling in one place.
- **The `prove` does not stand alone.** `=>!` does not check at run time and
  `=>` at a narrowing is refused at compile time (TM-105), so a `prove` that is
  a comment until the compiler's cycle 1.5 would be the *only* thing between a
  caller and a silently wrong answer. The runtime check goes in first; the
  `prove` records why it can never fire on a caller who kept the precondition.

This remains the single most valuable proof in the library: it is exactly the
place a silent wrong answer would live, and it is exactly the shape Z3
discharges without effort. What changed is that it is a proof about code that
checks, rather than a proof standing in for the check.

---

## 5. `limit<Rules>` — the component types

**Rule P-6.** When 1.5.2 lands, the component types become `limit`ed and the
checks inject at initialisation, at every assignment, and at parameter entry:

```nitpick
Rules:Year      = { $ >= -9999i32; $ <= 9999i32; };
Rules:MonthNum  = { $ >= 1u8;  $ <= 12u8; };
Rules:DayNum    = { $ >= 1u8;  $ <= 31u8; };
Rules:Hour      = { $ <= 23u8; };
Rules:Minute    = { $ <= 59u8; };
Rules:Second    = { $ <= 59u8; };
Rules:Nanos     = { $ <= 999999999u32; };
Rules:OffsetSec = { $ >= -64800i32; $ <= 64800i32; };
Rules:DayNumber = { $ >= -4371587i64; $ <= 2932896i64; };
```

*(Amended at cycle 0.1.1, TM-161: `DayNumber`'s lower bound read
`-4371588i64`, the day number of −10000-12-31 — `CALENDAR.md` §2's first day,
one day early. As a `limit` it would have admitted one day `days_to_date`
refuses.)*

The payoff is that a `limit`ed parameter's precondition is discharged **at the
caller** where the caller's own knowledge proves it, and retained as a runtime
check only where it cannot be — and the manifest records which is which, per
site. For this library that is most of the checking it does.

**Rule P-7 — `DayNum` is deliberately weaker than the real rule.** The type
cannot express "≤ the number of days in *this* month", so it bounds at 31 and
`civil_date`'s contract (P-3) carries the exact rule. A `limit` that half-states
a rule is worse than useless if it lets a reader think it states all of it, so
the gap is written down here.

---

## 6. `prove` sites

| Site | Proof |
|---|---|
| after `days_to_date` | the result is in the supported range, and `date_to_days` of it returns the input — **written as comments at 0.1.1 (Q-6, TM-164)**: `prove(date_to_days(answer) == n)`, and the range half as an `ensures` comment, since the result is `civil_date`'s. **Stood in for, over the whole range, by `tests/unit/sweep/every_day_number.npk` and `every_civil_date.npk` since cycle 0.1.2** (TM-166) — P-1's property test, and the row P-11 hands over |
| after `date_to_days` | the result is in `[DAY_MIN, DAY_MAX]` — **written as a comment at 0.1.1 (Q-6, TM-164)**: `ensures answer >= NTIME_DAY_MIN && answer <= NTIME_DAY_MAX`. **Stood in for, over the whole range, by `tests/unit/sweep/every_day_number.npk` and `every_civil_date.npk` since cycle 0.1.2** (TM-166) — P-1's property test, and the row P-11 hands over |
| after every `Timestamp` construction | `nanos < 1_000_000_000` (P-4) |
| in the transition binary search | the invariant `trans[lo].at_utc <= target < trans[hi].at_utc` holds at every step |
| after an offset lookup | `|offset| <= 64_800` |
| after the three `int128` narrowings | the value fits (P-5) |
| after weekday computation | the result is `0 … 6` — **written as a comment at 0.1.3 (Q-6, TM-164), and ALSO CHECKED IN CODE**: `weekday_index`'s `#unreachable()` belt stops the program on an index outside it, because `weekday` manufactures a `Weekday` tag from it (`SAFETY.md` S-15c). **Stood in for over the whole range by `tests/unit/sweep/every_civil_date.npk`'s weekday rider since cycle 0.1.3** |
| after ISO week computation | the week is `1 … 53` and the week-year is within one of the calendar year — **written as comments at 0.1.3 (Q-6, TM-164)**; **stood in for over the whole range by `tests/unit/sweep/every_iso_week_date.npk` since cycle 0.1.3**, which compares every week and week-year with a walk of ISO 8601's rule |
| in every parser loop | `at` strictly increases, so the loop terminates |

**Rule P-8 — the parser's "strictly increases" is the one worth naming.** It is
the property a hand-written scanner loses when somebody adds a branch that can
consume zero bytes, and losing it turns a malformed input into a hang. A
`prove` there turns that into a compile error.

---

## 7. Termination

**Rule P-9.** Every loop in `ntime` is bounded by a value that decreases, and
the bound is stated:

| Loop | Variant |
|---|---|
| transition binary search | `hi − lo`, halving |
| zone-name binary search | `hi − lo`, halving |
| every parser | bytes remaining (P-8) |
| the decimal writer | the value, divided by ten each step |
| `Period` normalisation | fixed, four steps |
| the exhaustive sweeps (tests) | the day range — a `for` over it, bounded by construction (the compiler's CONTROL_REFERENCE §2) |

`ntime` has **no unbounded loop and no recursion at all**. That is worth
stating as a property rather than an accident: the calendar algorithms are
closed-form, the searches are logarithmic, and the parsers are linear scans.

> **Status at compiler `c3bdae2` (cycle 0.1.0b): P-9 is now the language's rule,
> and this tree meets it mechanically.** The compiler's D-304 refuses a `while`
> or `when` that states neither `decreases E` nor `unbounded`
> (`NITPICK-TYPE-072`), checks the measure at the loop's head in every build,
> and traps `DecreasesViolated` when it fails to shrink. Every one of this
> tree's **48** loops carries `decreases` — six in `src/core/bytes.npk`, the rest
> in `tests/` — 29 written by the compiler's sweep tool in its own proven shape
> and 19 by the committed reading `../roadmap/0.1/decreases_read.txt`, and
> **none is `unbounded`** (TM-151). So the property this rule claimed is
> executed rather than stated. The table above is still the plan for the loops
> later cycles write; each will carry its variant as the clause.
>
> *(Cycle 0.1.2: **the 48 are this tree's `while` loops**, and the sentence
> said "loops" — found at the 0.1.2 planning. A `for` over a range states no
> measure: it is bounded by construction, and D-304 asks the clause of `while`
> and `when` alone. The tree has held one `for` since cycle 0.0.0, in
> `tests/probe/probe10_view_edges.npk` (`36f0e0f`), and 0.1.2's three sweeps add
> six — seven, none of which states or needs a measure, and 48 `while`, every
> one with `decreases`, re-counted at 0.1.2.)*
>
> *(Cycle 0.1.3: its two sweep members add six more `for` — thirteen, none
> with a measure — and the derived fields add no loop at all: every one is
> closed-form. The `while` count stays 48.)*

---

## 8. What cannot be proven, and is stated instead

**Rule P-10 — the honest claim**, following the compiler's TCB doctrine
(`TCB.md`, D-218.11: *verified middle-end plus validated floor*). `ntime`'s
verification claim covers **its own arithmetic and its own bounds**, and does
not cover:

- **the kernel.** `clock_gettime` returns what the kernel says the time is, and
  the kernel's clock may be wrong, unset, or being stepped by NTP as it is read.
- **the tzdb.** The transition tables are IANA's data. Their *invariants* are
  checked (sorted, in range, every index valid) and their *contents* are the
  database's — if IANA is wrong about when Chile changes its clocks, so are we,
  and the cross-oracle (`TESTING.md` V-7) only proves we read it correctly.
- **the leap-second approximation.** M-12 states the residue: up to 27 seconds
  of divergence from true SI elapsed time across the whole era, by design.
- **`llc` and `ld.lld`**, which the compiler names as trusted components.

The residue is enumerated rather than mitigated, which is the seL4 precedent
the compiler cites and the only honest shape for a claim of this kind.

---

## 9. The handoff

**Rule P-11.** When the compiler's verified build reaches libraries, `ntime`
hands over: this document's obligation list, the `nitpick.obligations` rows its
own build produces, and the property tests that stood in for each unproven row.
Cycle 0.8 owns that handoff, and R9 is why it is a deliverable rather than a
hope.
