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

**Rule P-1.** Until a construct is live, its obligation is stated **as a
comment beside the code in the exact syntax it will take**, and is enforced by
a property test. The switch is then deleting a comment marker rather than
inventing the clause. The compiler's rungs refuse the constructs by name today,
so a premature `ensures` is a build failure, not a silent no-op.

---

## 2. What the language discharges for free

- **Every index is bounds-checked and traps** (D-070). The question is only
  whether a *reachable* index is out of bounds — §3.
- **Every plain integer `+ - *` traps on overflow** (D-210). Calendar
  arithmetic cannot silently produce a wrong year.
- **Division by zero and `MIN / −1` trap** (D-007), and `CALENDAR.md` C-11
  makes every divisor in the calendar algorithms a nonzero literal, so those
  are discharged by inspection.
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
Rules:DayNumber = { $ >= -4371588i64; $ <= 2932896i64; };
```

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
| after `days_to_date` | the result is in the supported range, and `date_to_days` of it returns the input |
| after `date_to_days` | the result is in `[DAY_MIN, DAY_MAX]` |
| after every `Timestamp` construction | `nanos < 1_000_000_000` (P-4) |
| in the transition binary search | the invariant `trans[lo].at_utc <= target < trans[hi].at_utc` holds at every step |
| after an offset lookup | `|offset| <= 64_800` |
| after the three `int128` narrowings | the value fits (P-5) |
| after weekday computation | the result is `0 … 6` |
| after ISO week computation | the week is `1 … 53` and the week-year is within one of the calendar year |
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
| the exhaustive sweeps (tests) | the day range |

`ntime` has **no unbounded loop and no recursion at all**. That is worth
stating as a property rather than an accident: the calendar algorithms are
closed-form, the searches are logarithmic, and the parsers are linear scans.

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
