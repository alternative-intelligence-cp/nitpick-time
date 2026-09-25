# Open questions

Everything that is not settled, each with a recommendation, so that nothing
lives only in a conversation. Three prefixes:

| Prefix | Whose |
|---|---|
| `O-x` | **ours** — a design question this project decides, at the cycle named |
| `O-N` | the **compiler's** — a gap in the language or its tooling that `ntime` needs closed, to be raised as a request |
| `Q-` | the **user's** — a question that wants an answer before the work it gates begins |

A question that gets answered moves to `DECISIONS.md` as a numbered decision
and is struck through here with the decision's number, **never deleted** — the
question is part of the record of how the answer was reached.

> **`O-N` numbering is per repository.** `ntime`'s O-N1 and `nitpick-tui`'s
> O-N2 are the *same underlying request* to the compiler; the numbers differ
> because each library numbers its own list. Where that happens it is said, so
> that raising one raises both.

---

## Q — for the user

### ~~Q-1 — the tzdata release to pin~~ — **SETTLED, TM-100**
The latest release at cycle 0.5, in `src/zone/version.npk`; a bump is a minor
version (TM-013), not a patch, because a zone rule change alters answers for
dates the program already handled.

### ~~Q-2 — intervals and recurrence~~ — **SETTLED, TM-101**
Post-1.0, cycle 1.3, `Interval` before `RRULE` — `RRULE` is a small language
with its own conformance surface and deserves its own scrutiny rather than
being bundled with a two-field struct.

### ~~Q-3 — humanised / relative formatting~~ — **SETTLED, TM-102: no, ever**
No two products agree on the rounding policy, and the question is
localisation-shaped. `period_between` and the numeric parts ship instead, so a
program's own two-line function says what that program means.

### ~~Q-4 — the dogfood consumer~~ — **SETTLED, TM-103 and TM-104**
`date` **and** `crontab`/`at`, both in
[`nitpick-posix`](https://github.com/alternative-intelligence-cp/nitpick-posix)
rather than this repository's `examples/`. The CLI exercises format breadth;
the scheduler exercises DST edges, which is where a date library is actually
wrong. **TM-104** records that `date`'s `%` grammar is parsed in the *utility*
and mapped onto this library's typed layout — the compatibility layer lives in
the application, and the library stays principled.

### Q-6 — what replaces `VERIFICATION.md` P-1, now that every construct it names is live?

**Raised 2026-09-25 by the stream-2 planner, at the re-pin to compiler
`c3bdae2`.** P-1 writes an obligation as a comment *"in the exact syntax it
will take"* until its construct is live, and its safety argument is that *"the
compiler's rungs refuse the constructs by name today, so a premature `ensures`
is a build failure, not a silent no-op"*. **At `c3bdae2` none of them
refuses**: `limit<Rules>` is live since the compiler's 1.5.2, `requires`,
`ensures` and `invariant` since 1.5.3, `prove` and `assert_static` since 1.5.4,
and a loop's `decreases` since 1.5.8c. The argument is gone, and what P-1
should say instead is a design choice, so it is the author's.

**What each construct costs, measured at `c3bdae2`** — a consumer importing one
module that uses it once, `NITPICK-REACH-003`'s list against the six-identity
floor:

| Construct, live | Arm every consumer owes | In a plain build |
|---|---|---|
| `requires` | `RequiresViolated` | checked at the callee's entry, traps |
| `ensures` | `EnsuresViolated` | checked at every return, traps |
| `invariant` | `InvariantViolated` | checked at the loop head, traps |
| `limit<R>` (a parameter or a field) | `LimitViolated` | checked after every write, traps |
| `assert_static` | none | folded at compile time; a false one refuses the build |
| `prove` | none | **lowers to nothing** — only the verified build (`npkg verify`, D-219) checks it, and refuses an undischarged one (`VERIFY-001`) |

One arm per construct KIND, not per use: the set is a set.

**The options:**

- **A′ — comments by default, and a live clause is a budget decision
  (RECOMMENDED).** `decreases`/`unbounded` are the language's and always live;
  `assert_static` is live wherever it helps, at no cost. `requires`, `ensures`,
  `invariant` and `limit` are written live **only where a numbered decision says
  the check is worth the arm it adds to every consumer**, recorded in
  `SAFETY.md` S-4 — and never a `requires` on an argument a caller supplies,
  because S-12 answers caller input with a `Result`, not a trap. `prove` stays a
  comment until the harness runs the verified build (cycle 0.8), because a
  plain build lowers it to nothing and nothing here would check it. **A
  comment-form obligation is documentation, and is never cited as a check.**
- **A — live now.** `requires`/`ensures`/`invariant` written live from 0.1.1
  on; `prove` still a comment until 0.8. Gains: every contract checked on every
  call of every test — 0.1.2's sweep would run 0.1.1's one `ensures` 14.6
  million times. Costs: an arm per kind in every consumer (0.1.1 alone takes
  `cal` from 11 to 12 and the umbrella from 13 to 14, measured), a cross-stream
  exit code per kind, and a check per call until the verified build elides the
  discharged ones.
- **B — every obligation a comment until cycle 0.8**, `assert_static` included.
  The simplest, and the weakest: nothing checks a comment's syntax or its
  truth.
- **C — everything live now, `prove` included.** A live `prove` in a plain
  build is exactly the silent no-op P-1 was written against, until 0.8.

**Recommendation: A′.** It keeps P-1's mechanism — property tests stand in, and
the switch is mechanical — and gives the true reason for it: the arm and the
run-time cost, not a refusal that no longer happens. It charges consumers
nothing until a decision says a check earns it, and it never claims something a
plain build does not check. A's strongest argument, a contract checked on every
call, is weakest in cycle 0.1, whose algorithms 0.1.2 proves over their whole
domain; it is strongest at 0.4–0.6 (parsing, the zone lookup), where no
exhaustive sweep exists — and A′ lets exactly those cycles choose live
contracts, by decision.

**What waits on it:** 0.1.1's contract form — `meta/roadmap/0.1/0.1.1.md` §6 is
written for A′ and states A's exact alternative, so either answer is executable
without re-planning — and every later cycle's. *(0.1.1 was worked on A′, at the
orchestrator's instruction, while this stays open: TM-164. Its arm cost was
measured both ways there — `cal` 11 and the umbrella 13 as committed, 12 and 14
with the one live `ensures` — and A's arm, `EnsuresViolated`, would exit 117
in this ecosystem, not the 110 the plan proposed.)* *(0.1.2 was worked on A′
too, and `meta/roadmap/0.1/0.1.2.md` §8 measured what A would change there —
re-measured at execution, a scratch copy of `src/` with `date_to_days`
carrying the live `ensures`: each of the three sweeps then owes **twelve**
identities rather than eleven, the extra one `EnsuresViolated`, and runs within
noise of A′ at -O0 — 1.29 s → 1.34 s, 1.42 s → 1.44 s and 0.02 s → 0.02 s —
with the `ensures` checked at every return, once per day in each day walk and
once per month in the month walk. **So under A the cost at 0.1.2 is the arm,
not the time; and the live check adds no evidence the civil walk does not
already give**, because that walk asserts every day number in the range
directly — this question's own argument for A′ in cycle 0.1, now measured. The
question stays the author's.)* *(0.1.3 was worked on A′ as well, and
`meta/roadmap/0.1/0.1.3.md` §11 measured A on the derived fields: live
`ensures` on the four integer-valued ones — `weekday_index` 0 … 6,
`day_of_year` 1 … 366, `iso_week_number` 1 … 53, `iso_weekday` 1 … 7 — take a
consumer of `cal` from eleven identities to **twelve**, the extra one
`EnsuresViolated`, and leave the three sweeps that call them within noise of
A′ at -O0 (1.97 s → 2.01 s, 2.58 s → 2.61 s, 6.57 s → 6.71 s). **And it found a
third option for a single site: A′ with the check written as code.** The one
range that guards something — the weekday index, from which `weekday`
manufactures a tag the compiler cannot check — is checked by an
`#unreachable()` line in the body (`SAFETY.md` S-15c), which stops the program
exactly as a live `ensures` would, through `Unreachable`, an arm every consumer
already owes. So under A′ a contract can still be enforced where it earns it,
at no arm cost, and the question is only about the rest. **The author
answered it the same day: A′** — *"the recommendation on q-6 seems fine to
me"*, 2026-09-25 15:56, recorded on the workbench's board — and the numbered
decision that puts A′ in P-1's place is owed to 0.1.3c's plan, which strikes
this question through with that decision's number.)* **What does not:** 0.1.0b and
0.1.0c; 0.1.0b adds a dated note under P-1 saying its premise is false and this
question is its replacement. **The same P-1 is in all six work repositories'
`VERIFICATION.md`**, so one answer can serve all six, recorded in each.

### O-N1 — `npkg` cannot build a library, and `[dependencies]` resolves to nothing
Measured at the compiler's 1.5.0 and recorded in `specs/BUILD.md` §1.
`npkg build` is the compiler's own bootstrap ladder; `target = "library"` is
accepted by the schema and read by nothing; the loader's dependency-root list
is created empty in `src/driver/pipeline.npk` and `rootlist_add` is called from
nowhere, so the dependency-root `use` form resolves against an empty set.
**Consequence:** `ntime` builds through its own Python harness (TM-003), every
import is relative, and the `nparse` overlap (O-X1) cannot be resolved.
**Ask:** `npkg build` honouring `target = "library"`, and the driver populating
the resolver's roots from `[dependencies]`.
**This is the same request as `nitpick-tui`'s O-N2.** Neither is on the
compiler's 1.5 or 1.6 map, so it is a request, not a date.

### O-N2 — there is no wall-clock builtin in the floor
`mono_now()` gives `CLOCK_MONOTONIC` and there is no equivalent for
`CLOCK_REALTIME`, so `ntime` reads it through `sys(228, …)` with a `timespec`
laid out in a `buffer`. That works and is `nlibc`-tier business, so it is not a
blocker.
**Recorded, not asked:** if `nlibc` ever grows a typed wall-clock reader,
`ntime`'s `host_now_utc` should become a caller of it rather than a second
path to the same syscall. Nothing to do until then.

### O-N3 — `Duration`'s ±292-year range, recorded so nobody "fixes" it
The prelude's `Duration` is `int64` nanoseconds, which cannot express a
calendar-scale span (`TIME_MODEL.md` §8). **This is not a gap and no change is
wanted:** widening it would change the deadline substrate's representation for
every consumer in the ecosystem, to serve a case that wants `Period` instead.
Recorded here because the mismatch looks like a defect on first sight and
somebody will eventually propose the "fix".
**Ask: none.**

### ~~O-N4 — `npkc` is quadratic in the size of one declaration~~ — **DISCHARGED, RE-MEASURED HERE AT PIN `aaffb87` ON 2026-09-06**

> **The heading said BLOCKING until cycle 0.0.6 and it had not been for two
> subcycles.** The compiler's 1.5.1b fixed it — three text builders in
> `src/backend/` that re-concatenated an accumulator per element, per trap site
> and per byte — and the workbench verified that on 2026-09-04. Cycle 0.0.5's
> tzdb spike then RAN, which this question was the block on, so its own gate
> had already been passed. **This entry is exactly the shape E1 named**: a
> status that is true on the workbench board and unfindable from inside the
> repository. Struck here on this repository's own measurement rather than on
> the board's report.
>
> **Re-measured at the close**, `/usr/bin/time` on the pinned `npkc` against
> `tests/probe/probe04_big_fixed_table.npk`, the 30 000-row case this entry is
> about:
>
> | | time | peak |
> |---|---|---|
> | at `950bb1d`, cycle 0.0.0 | **281 s** | **30.9 GiB** |
> | at `aaffb87`, cycle 0.0.6 | **1.20 s** | **26 900 KiB** |
>
> **And the speed is not bought by emitting less**, which is the check that
> would have made this a hollow discharge (O-N11 is precisely that shape):
> `npkc` exit 0 is paired with a **2 266 485 B** `.ll` that carries
> `[30000 x %"npk.probe04_big_fixed_table.ZoneTransition"]` — the rows are
> there. The relation is no longer quadratic either: at 4 000 rows the same
> recipe is 0.24 s, so 7.5× the rows costs 5× the time where quadratic would
> cost ~56×.
>
> **Nothing waits on it.** `ZONE_MODEL.md` §3's 26 838 transition rows are
> inside the measured envelope, TM-135 sized the whole database at 475 006 B,
> and cycle 0.5's generator is unblocked. The record below is what was raised
> at `950bb1d` and is left standing.

**Measured at cycle 0.0.0, 2026-09-03**, against the pinned toolchain (compiler
commit `950bb1d`). Compile time and peak memory grow as the square of the number
of elements in one array initialiser, the number of statements in one function
body, and the number of bytes in one string literal. The reproduction, the three
curves and the exact commands are in
[`../tests/probe/defect/README.md`](../tests/probe/defect/README.md).

**Consequence:** TM-007 compiles the whole tzdb in as `fixed` module state, and
`ZONE_MODEL.md` §3 sizes that at 26 838 transition rows. Probe 04 built a table
that size: it compiles, in **281 seconds** and **30.9 GiB of resident memory**.
A 16 GiB machine cannot build it, CI cannot build it, and every consumer pays it
because the table is in the library it imports. Z-7's fourth table is a name
pool — a single large string constant — which is the third axis.

**Ask:** the array-initialiser and function-body paths made linear, or near
enough that 30 000 rows costs seconds and hundreds of megabytes; and the
string-literal path made linear in time. Nothing in the *language* changes.

**Meanwhile `ntime` does nothing.** Shrinking the table, splitting it across
modules, or shipping it as a byte blob decoded at first use would each buy the
number back, and each is a workaround for a compiler bug buried in library code.
Cycle 0.0.0 stopped rather than take one, and O-Z1 (ship every zone, or a
subset?) must **not** be answered "a subset" on the strength of this — that
would be the same workaround wearing a decision's clothes.

**Gates:** cycle 0.0.5's tzdb size spike, cycle 0.5's generator, and the rest of
0.0.0's probes only insofar as they wait on the toolchain being re-pinned. The
probes themselves are unaffected — the defect is a resource cost, not a
semantics change. *(Both gates are now passed: 0.0.5 ran and 0.5 is unblocked.
See the discharge note at the top of this entry.)*

### ~~Q-5 — is O-N9 a block for `ntime`, or a conformance rule plus a raised defect?~~ — **ANSWERED 2026-09-03: A BLOCK**
**The author ruled it BLOCKING, against the recommendation recorded below.**
The recommendation is left standing rather than rewritten, because a question
answered against its own recommendation is the most useful kind to be able to
re-read. The ruling reached this repository through the workbench board as its
question 8; the corresponding compiler work is **DEF-3**, the second of cycle
1.5.1b's five commits, where the borrow walk learns that a view-maker's result
borrows its operand.

**What follows here, and it is all that follows.** `src/fmt/` work waits, and
**probes 09 and 10 stay held** — they are not merely unwritten. The house rule
*"a view is a parameter, never a return value"* is kept as a **belt**, not as
the guarantee: it goes into `SAFETY.md` and onto 0.0.3's `check_no_view_returns`
list exactly as the recommendation proposed, but it no longer stands in for the
compiler's enforcement, which is what the ruling turned on. Nothing else in the
cycle changes: 0.0.1 through 0.0.4 carry no `uint8[]` parser.

**The recommendation as it was made, 2026-09-03, cycle 0.0.0.** O-N9 lets a `uint8[]` view escape its owning
frame with no diagnostic, and **every parser in `src/fmt/` takes a `uint8[]`**.
W-11 forbids reshaping a library to dodge a compiler defect, so the question is
whether adopting "a view is a parameter, never a return value" is a reshaping.

**Our recommendation: a conformance rule, not a block.** That sentence is not a
workaround — it is compliance with a rule the compiler's own
`TYPE_REFERENCE.md` §9.2.1 already states and enforces for `@`-borrows, and it
costs this library **nothing**: a parser returns a value and an offset, never a
slice of its input, which is what `FORMAT_MODEL.md` already specifies.
`tests/probe/defect/view_escape/case6_view_param_legal.npk` is the shape, and
it is the shape the design already called for. Contrast O-N4, where no correct
code avoids the cost and the subcycle therefore stopped.

**If it is a conformance rule**, three things follow and none of them waits:
raise O-N9 (done), add the rule to `SAFETY.md`, and put
`check_no_view_returns` on cycle 0.0.3's harness list so it is enforced rather
than remembered.

**What is deliberately NOT assumed while this is open.** Probes 09 and 10 — the
borrow-edge probes, which are what found this — are **held**, because their
shape is exactly what a "block" answer would change.
### ~~O-N8 — `npkc` merges a sibling file when a root file's `mod:` name mismatches~~ — **DISCHARGED: FIXED since pin `94874ce` by the compiler's D-248, verified here 2026-09-25 at every kept pin (TM-160)**

> **Discharged on this repository's own measurement, and the entry had been
> stale at four of this repository's five pins.** The six-line pair at the foot of
> [`../tests/probe/defect/README.md`](../tests/probe/defect/README.md), `npkc
> beta.npk` with the sibling present, at every pin this workbench keeps:
>
> | Pin | Verdict |
> |---|---|
> | `950bb1d` — cycle 0.0.0, where this was found | exit 0, `.ll` written with **two** `define i32 @main` — the defect |
> | `94874ce`, `0dfddac`, `aaffb87`, `3d15ac9`, `c3bdae2` | exit 1, no `.ll`, **`NITPICK-RESOLVE-012`** — *"a file's header names the file"* |
>
> That is the ask below, met by the compiler's **D-248**, which landed at its
> 1.5.1b step 1 and reached this repository with the `94874ce` re-pin on
> 2026-09-04. Without the sibling the refusal is the same code, and the
> matching-header control compiles. This entry went on describing a live
> defect through three more re-pins after that one (`3d15ac9` was never this
> repository's pin); cycle 0.1.0b's note below was the first to
> see it, and the workbench registry struck it on 2026-09-25. The compiler's
> own suite pins the refusal (`tests/modules/rejection/header_mismatch.npk`).
> The entry is kept as written.

**Met by accident at cycle 0.0.0, 2026-09-03**, while staging probe 04 under
the wrong filename, and it is why a one-second compile appeared to take three
hundred. A root file whose `mod:` name differs from its basename is accepted
when a *sibling* file carries that basename: `npkc` compiles the sibling too,
merges both into one module, emits IR with two `define i32 @main`, and **exits
0**. `llc` then refuses the IR, a long way from the cause. Delete the sibling
and the diagnostic is exemplary — `NITPICK-RESOLVE-005` names the rule and even
anticipates the self-header case — so the resolver knows the rule and does not
apply it when the name resolves to a different file. The six-line reproduction
is at the foot of [`../tests/probe/defect/README.md`](../tests/probe/defect/README.md).

**Ask:** apply the basename rule regardless of whether the named module
resolves elsewhere.

**It costs `ntime` nothing and blocks nothing** — the house rule is already
`mod:` = basename. Raised alongside O-N4; nothing here is shaped around it.

> **Measured at compiler `c3bdae2`, cycle 0.1.0b: the reproduction no longer
> reproduces.** The six-line pair is refused `NITPICK-RESOLVE-012` at
> `beta.npk:1:1`, exit 1 and no `.ll` — *"a file's header names the file"*, the
> compiler's D-248 — which is exactly the ask above. Not struck here: striking
> an `O-N` is a decision, and this subcycle's scope did not include one, so it
> is reported to the orchestrator for the next dispatch.

### ~~O-N9 — D-004's escape rule is unenforced for slice views~~ — **DISCHARGED 2026-09-04 (TM-110)**
> **DISCHARGED, on this workbench's own measurement against pin `94874ce`, not
> on a correspondent's report.** The fix landed as the compiler's DEF-3
> (its D-249, cycle 1.5.1b step 2). `defect/view_escape/` cases 3, 4 and 5 are
> now **refused `NITPICK-BORROW-001`**, exactly as the ask below asked; case 6,
> the shape this library writes, still compiles and runs at exit 0. The
> transcript is `../tests/probe/defect/view_escape/TRANSCRIPT.txt` Part A, and
> the decision is **TM-110**. **`src/fmt/` and probes 09 and 10 are
> UNBLOCKED**; probes 09 and 10 were worked on 2026-09-04 and are committed.
>
> Two things in the text below are **wrong at the landed pin** and are
> corrected in place further down, rather than deleted: the three-row table
> (the rule keys on the root's SHAPE, not on parameterhood) and the claim that
> DEF-3 adds no new diagnostic code (it adds `NITPICK-BORROW-012`).

**Measured at cycle 0.0.0, 2026-09-03.** `string_bytes` on a local `string`
yields a `uint8[]` that is **returned out of its owning frame with no
diagnostic**, and reading it afterwards reads freed memory — the runtime's own
`0xAA` free-poison, deterministically. The identical program with an
`@`-borrow, and the identical program with the borrow inside a returned struct
literal, are both refused `NITPICK-BORROW-001`. The six cases, the contrast and
the transcript with every exit code are in
[`../tests/probe/defect/view_escape/README.md`](../tests/probe/defect/view_escape/README.md).

**Ask:** `NITPICK-BORROW-001` for a returned slice, exactly as for a returned
`@`-borrow. Nothing in the language changes — `TYPE_REFERENCE.md` §9.2.1
already says *"a slice is a second-class borrow (D-004): it passes down the
call stack and never up"*.

**Consequence for `ntime`:** every parser in `src/fmt/` takes a `uint8[]`, so
the library is in the blast radius. ~~It is **not blocking**, because the house
rule *a view is a parameter, never a return value* is compliance with the
documented rule rather than a workaround for its absence, and it costs nothing:
a parser returns a value and an offset.~~ **The author ruled it BLOCKING at
Q-5**, so `src/fmt/` and probes 09 and 10 wait; the paragraph above is left
standing because a recommendation decided against is the most useful kind to be
able to re-read. `check_no_view_returns` — **proposed** for cycle 0.0.3's
harness list, not yet on it — is what would make the rule enforced rather than
remembered.

**ACCEPTED as the compiler's DEF-3**, the second commit of its cycle 1.5.1b,
proposed there as its **D-249**: builtins gain a `Views` column naming which
argument's storage a result aliases, and the escape analysis treats such a call
as a borrow **rooted where that argument is rooted**, as if `@` had been written
at the argument.

**The fix distinguishes shapes the house rule conflates, and `src/fmt/`
planning turns on it** — the full statement is `SAFETY.md` **S-22** and
**TM-110**. ~~This was the summary as predicted on 2026-09-03 from DEF-3's
written plan:~~

| ~~Shape~~ | ~~After DEF-3, as predicted~~ |
|---|---|
| ~~a view of a **local**, returned~~ | ~~**refused**~~ |
| ~~a view of a **temporary**, returned~~ | ~~**refused**; bind the intermediate~~ |
| ~~a view rooted at a **parameter**, returned~~ | ~~**legal** (`borrows_only_param_rooted`)~~ |

**AND THIS IS WHAT WAS MEASURED**, 2026-09-04, at pin `94874ce`. Two rows are
new and one prediction was wrong:

| Shape, returned out of its frame | Measured | Evidence |
|---|---|---|
| a view of a **local** | **refused** `NITPICK-BORROW-001` | `view_escape/case3`–`case5` |
| a view of a **temporary** | **refused** `NITPICK-BORROW-012` | `probe10b` |
| a view of a **`move` parameter** | **refused** `NITPICK-BORROW-001` | `probe10c` |
| a view rooted at a plain **parameter** | **legal** | `probe10` §2, §3 |
| a view rooted at a **pointer-shaped binding** | **legal** | `probe10` §1, `probe09b` |

So the house rule is **conservative, not the truth**, and it is conservative in
two ways rather than one: it forbids the parameter-rooted view *and* the
pointer-shaped-rooted view, both of which are legal. It is kept as a belt
regardless (TM-110).

**~~DEF-3 introduces no new diagnostic code~~ — FALSE, corrected 2026-09-04.**
It introduces **`NITPICK-BORROW-012`** (`BORROW_VIEW_OF_TEMPORARY`), which
`probe10b` fires. The claim came from DEF-3's plan, which its own step 2
overtook: `@` of a temporary cannot be spelled, so no existing code's text was
true of that shape and it needed one of its own. This sentence stood in six
documents here and every one is corrected in the same commit.

**~~One sub-question this leaves open, and it is the compiler's to answer.~~
ANSWERED 2026-09-04 BY MEASUREMENT — it is LEGAL.** Whether a view over a
**locally allocated `wild` block** may be returned —
`string_from_bytes(buf, n)` where `buf` came from `alloc` in this frame — was
recorded as unsettled, because DEF-3's test list appeared to put
`string_from_bytes(local.ptr, local.len)` among the *new refusals*.
`tests/probe/probe10_view_edges.npk` §1 is exactly that program, with no
parameter anywhere in its root chain, and it **compiles and runs at exit 0**.
The root is pointer-shaped, so the view aliases the pointee rather than the
frame. No question is outstanding for the compiler here; S-22 forbids the
shape as a belt, by this repository's choice rather than the language's.

### ~~O-N10 — the derives on a payload enum: `Eq` will not compile, `Ord` is silently wrong~~ — **DISCHARGED 2026-09-04 (TM-111)**
> **DISCHARGED, on this workbench's own measurement against pin `94874ce`.**
> The fix landed as the compiler's DEF-4, widened and ratified as its D-250
> (cycle 1.5.1b step 3b). **Both halves are fixed, and the quiet half was
> checked for correctness rather than for compiling:**
> `defect/derive_payload_enum/case1_eq_refused.npk` now **compiles and runs at
> exit 0** where it was `NITPICK-TYPE-034`, and `case2_ord_ignores_payload.npk`
> now answers **`Less`** for `Literal(7).cmp(Literal(9))` where it answered
> `Equal`. A separate check confirmed the derived `eq` distinguishes payloads
> (`7 == 9` false, `7 == 7` true, different tags false) — a derive that merely
> compiles would be the hollow version of this green.
>
> **The committed `expect-` headers on those two files are now stale** and are
> corrected in the same commit as this note. See TM-111 for `case2`'s
> arithmetic slip, which nearly made a correct fix look like a wrong one.

**Measured at cycle 0.0.0, 2026-09-03**, by probe 05. On
`enum:Part = { Literal(uint16); Year4; }`:

- `#[derive(Eq)]` emits a derived module that **does not compile** —
  `NITPICK-TYPE-034` inside `<derived-1>`, saying `Part` has no built-in `==`.
  The derived `Eq` is being told to derive `Eq`, and the file it points at is
  synthetic, so there is nothing for a user to open or fix.
- `#[derive(Ord)]` on the same declaration is **accepted**, and its `cmp`
  compares tags only: `Literal(7).cmp(Literal(9))` answers **`Equal`**.

The second is the serious one. A refusal is a bad afternoon; two different
values reporting `Equal` is a wrong answer nobody looks for, and a sort or a
binary search over such an enum is quietly incorrect. `Hash` likewise hashes
the tag alone; `Clone` is **correct** and keeps the payload. The reproduction,
the isolation and the transcript with every exit code are in
[`../tests/probe/defect/derive_payload_enum/README.md`](../tests/probe/defect/derive_payload_enum/README.md).

**It is untested territory, not a regression:** no file anywhere in the
compiler's tree derives any trait on an enum with a payload. Its derive tests
cover three payload-less enums and three structs.

**Ask:** `Eq` to emit an implementation that compiles, and `Ord`/`PartialOrd`
to compare the payload after the tag — plus a test in the compiler's own tree
that derives on a payload enum, since the gap is coverage.

**Consequence for `ntime`: one type, and nothing today.**
`FmtPart.Literal(uint16)` (`FORMAT_MODEL.md` F-4) is the only payload-carrying
variant in the whole specification set, and no rule requires `Eq` or `Ord` on
it — `TESTING.md`'s round trips compare formatted strings and parsed values,
never two `Layout`s. So it is raised rather than blocking, and what the cycle
that builds `src/fmt/` must carry is the **second** half: `#[derive(Ord)]
enum:FmtPart` would compile and be wrong.

**The id is allocated and the defect is accepted.** `O-N` numbers are the
workbench registry's and are assigned there; the registry allocated **O-N10**,
and the compiler session accepted it as its **DEF-4** at this repository's
commit `eb8d6b4`. It was then **widened after their own measurement and ratified
as the compiler's D-250**, landing as step 3b of its cycle 1.5.1b: the fault is
not confined to payload enums — a derived `Eq`/`Ord` over a **struct with a
derived-struct field** fails the same way inside `<derived-1>` — so the step
covers named types in structs and enums alike, and an owning payload will refuse
the derive **by name** rather than silently generate.

### ~~O-N11 — a program with `main` and no `failsafe` compiles at exit 0~~ — **DISCHARGED 2026-09-04 (TM-112)**
> **DISCHARGED, on this workbench's own measurement against pin `94874ce`.**
> The fix landed as the compiler's DEF-5 (cycle 1.5.1b step 1b). **The ask was
> granted in full**, including the part that was a stretch: the refusal is
> `NITPICK-REACH-003`, it lands at `main`, and it **lists the identities the
> absent handler would owe**. An `npkc` refusal now replaces what was an `llc`
> failure, so the diagnostic arrives one step earlier and names the cause.
>
> **The arm counts, measured rather than relayed: `case1` owes FOUR**
> (`Unreachable`, `HeapOom`, `HeapBadRequest`, `WildLeak` — S-4b's floor, since
> it has no import, no arithmetic and no allocation), **and `case3` owes SIX**
> (the floor plus `probe11_arms_lib.EProbeZone` and `IntOverflow`). A board
> carried "six" for `case1`; the six was real but belonged to the other file.
> The control still holds: an ordinary library module with neither `main` nor
> `failsafe` is still accepted at exit 0, so REACH-003 is asked only of a root
> that declares `main`. Transcript:
> `../tests/probe/defect/missing_failsafe/TRANSCRIPT.txt` Part A.
>
> **Cycle 0.0.3's harness still must not read `npkc` exit 0 as
> "well-formed"** — that constraint came from this defect but does not depend
> on it, and O-N11's own reasoning is why (`npkc` exit 0 is not a claim about
> the IR; the `llc` leg is).

**Measured at cycle 0.0.0, 2026-09-03**, by probe 11 while establishing the arm
contract. `npkc` does not require a root file that declares `main` to declare
`failsafe`. A four-line program with neither import nor arithmetic is accepted
at **exit 0**; `llc` then refuses the IR with `use of undefined value
'@npk_failsafe'` at a generated line, naming an internal symbol and neither
`failsafe`, D-013, nor the user's file.

The rule exists and is settled — the compiler's **D-013**, "Exactly one
`failsafe` per program, supplied by the executable … It is required only for
executables and must be provided by the end user."

**The defect is a missing check, not the undefined symbol.** An ordinary
library module emits the same seven calls to an undefined `@npk_failsafe` and
that is harmless, because it emits no `@main` and nobody links it alone. `npkc`
holds both halves already: it emits `define i32 @main` for the program and not
for the library module, and `reach_settle` tests `if (x.failsafe_decl == 0i32)
{ pass NIL; }` and returns early on exactly this case. It never joins them.

**Why it matters here.** That early return is the whole REACH-002 contract.
A program that imports a module raising `EProbeZone`, calls the raiser, and has
no `failsafe` compiles at exit 0 with no diagnostic; the same program *with* a
`failsafe` omitting that one arm is refused `NITPICK-REACH-002`. So TM-017's
budget, `SAFETY.md` §2's arm table and TM-013's major-version rule are enforced
against a program that has a handler and asked of nothing that has none.

**Ask:** refuse a root declaring `main` and no `failsafe`, naming D-013 and the
file — and, since `reach_settle` has just computed it at the point it currently
returns early, **list the arms the absent handler would owe**. Close kin to the
compiler's own outstanding item that D-014's injected `ensures result > 0` on
`failsafe` and its non-empty-body check "both currently exist nowhere"; one
pass over the root's declarations answers all three.

**Consequence for `ntime`: nothing blocked, one harness constraint.** Every
program this library ships or tests has a `failsafe`, and a missing one is
caught by `llc` in the next step of the same recipe. What it costs is that
**`npkc` exit 0 does not mean a program is well-formed**, so cycle 0.0.3's
`program` stage runs all four steps rather than stopping at `.ll`, or asserts
`grep -c '^define i32 @npk_failsafe'` is 1 — and `selfcheck.py` gains an eighth
case for a program whose `failsafe` has been deleted. Full statement in
[`../tests/probe/defect/missing_failsafe/README.md`](../tests/probe/defect/missing_failsafe/README.md).

**The id is allocated and the defect is accepted**, on the same terms as O-N10
above: the registry allocated **O-N11** and the compiler accepted it as its
**DEF-5**, committed at cycle 1.5.1b step 1b. **The ask was granted in full, and
the landing diagnostic is already known:** `NITPICK-REACH-003`, reported at
`main` rather than at the file, naming D-013 and **listing every identity the
absent handler would owe**, counted. A root with neither `main` nor `failsafe`
stays silent, because a library checked alone has nothing to settle against.
What is still owed here is the re-recording of
[`../tests/probe/defect/missing_failsafe/`](../tests/probe/defect/missing_failsafe/README.md)'s
transcripts at the re-pin, where an `npkc` refusal replaces today's `llc`
failure — deliberately not done before then, because today's transcript is the
before-half of a before-and-after.

**A note on the numbering.** O-N5 … O-N7 do not appear here. `O-N` ids are the
**workbench registry's**, not this repository's, because a gap in the compiler
is raised once for the whole ecosystem and the per-repository numbers would
collide (`../PLAYBOOK.md` §7). O-N1 … O-N4 happen to coincide; from here the
registry's number is used as given.
---

## O-x — ours

### O-X1 — the `nitpick-parse` datetime overlap
TOML v1.0.0 has four datetime types and `nparse`'s TOML plugin must produce
them; those are `ntime`'s types and `ntime`'s parsers. `[dependencies]` cannot
express the relationship today (O-N1), and TM-027 keeps both libraries
standalone.
**Open by design until O-N1 closes.** The interim is stated in TM-027 and
`COMPAT.md` §5: each library carries its own scanner, and **the two share test
vectors by committing the same corpus in both**, so a divergence is a red run
somewhere rather than a silent disagreement. When O-N1 closes, the decision to
make `nparse` depend on `ntime` is a small diff and a recorded decision.

### O-B1 — when `npkg` can build a library
`specs/BUILD.md` §9's item, mirrored here. **Gated on O-N1**, and there is no
action until it closes: the harness and `npkg` then run side by side with a
parity check before the harness retires, exactly as in the compiler
repository. **No action.**

### ~~O-Z1 — ship every zone, or a selectable subset?~~ — SETTLED, TM-135
`specs/ZONE_MODEL.md` §8's item, mirrored here. **Answered at cycle 0.0.5:
ship them all.** The measured **477.8 KiB** falls in the first of
`meta/roadmap/done/0.0/0.0.5.md` §3's three bands, decided in advance so that a bad
number would produce a stop rather than an improvisation, so none of the
fallbacks — dropping the pre-1900 LMT transitions, delta-encoding the
transition times, or a build-time zone subset — is reached. **Not deleted**,
because Z-7b's margin is 4.4% and a future tzdata release could reopen it
against a number.

### ~~O-X2 — the real emitted tzdb size~~ — CLOSED, TM-135
`ZONE_MODEL.md` §3 estimated **≈348 KiB** from tzdata 2026c's 447 canonical
zones and 26 838 transitions. **Measured at cycle 0.0.5, a cycle earlier than
planned, because O-N4's discharge made it affordable:** the four tables and two
pools are **475 006 B**, and **489 310 B** with `POSIX_RULES` at its real
cardinality — read off the object with `nm -S`, against a one-zone baseline
that puts the program-and-prelude share at 36 014 B by one route and 35 866 B
by another. The estimate was low by 37% and wrong in four independent ways;
TM-135 has each with its number, and the spike is
`meta/scratch/tzdb_spike/`.

### O-X3 — whether `Instant` exposes its clock kind publicly
TM-010.1 makes `Instant` carry which clock produced it, so that
`instant_since` can refuse a mismatched pair. Whether the field is *readable*
by a caller is a smaller question: reading it lets a program log which clock it
used, and hiding it keeps the type opaque.
**Recommendation:** expose it read-only as `instant_clock(i) -> HostClock`.
Diagnosability beats opacity for a one-byte field, and the sibling library made
the same call with `Caps.source_of_*`. Decide at cycle 0.2.

### O-X4 — `Bytes` reuse in the formatters
`FORMAT_MODEL.md` F-10 says every emitter writes into a caller-supplied
`Bytes`, with the `string`-returning form a thin wrapper. Whether the wrapper
should keep a thread-local scratch buffer to avoid an allocation per call is a
performance question with a purity cost.
**Recommendation:** no scratch buffer — it would be state in a module TM-018
requires to be pure, and the caller-supplied form already solves the problem
for anybody who measured. **Open by design until cycle 0.8's benchmark** says
whether it matters; if it does, the answer is documentation pointing at the
`Bytes` form, not hidden state.

### ~~O-X5 — the `sweep` stage under `--quick`~~ — **SETTLED, TM-125**
~~`BUILD.md` B-9 makes the exhaustive sweeps skippable under `--quick` with a
loud line. Whether CI should ever use `--quick` is a policy question.~~
~~**Recommendation:** no. The sweeps run in seconds; the flag exists for a
developer iterating on one function, and a CI run that skipped the gate would
be a CI run that concluded nothing. Decide at cycle 0.0.3 when the harness
grows the flag.~~

**Settled at cycle 0.0.3 as TM-125, as the recommendation proposed: NO.** The
decision records a *different* reason from the one above, and deliberately —
"the sweeps run in seconds" is a fact about today's domain sizes and would stop
being an argument the moment a sweep got slow, which is exactly when somebody
would reach for the flag. The durable reason is what the sweeps ARE:
`TESTING.md` V-2 makes the exhaustive gate *the* gate and V-3 calls the civil
sweep the strongest statement this library makes, so a `--quick` CI run would
be publishing a green badge for something no run had checked. It is enforced by
shape rather than by policy — see `BUILD.md` B-9b.

### O-X6 — `SPAN_MODEL.md` N-20 says three `int128` sites and §5's table names one
**Found at cycle 0.0.0, 2026-09-03**, while writing N-20b against §5. N-20 says
the `int128` sites "are exactly three … named above", and the table above it
marks exactly **one**: `period_add`'s nanosecond step. The year/month step is
marked `int64` and the day step carries no widening at all. `TESTING.md`'s
`check_int128_sites` — which cycle 0.2 puts on the harness, and which V-1 calls
one of the two checks that matter — is specified as *"`int128` at exactly the
three sites `SPAN_MODEL.md` §5 names"*, so it cannot be written until they are
named.

**Not settled at 0.0.0, deliberately.** Choosing which three requires designing
`period_add` and `timestamp_since`, and no cycle has done that yet. A rule
invented to make a count come out right is worse than an acknowledged gap.

**Recommendation:** at the cycle that designs `period_add` (0.3 by
`ROADMAP.md`), either enumerate the sites in §5's table — marking each `int128`
row as such — or drop the count from N-20 and make the **table** the authority,
with `check_int128_sites` reading it. The second is the better shape: the count
was written before any code existed, "they are named above" says the
enumeration was always meant to be authoritative, and a number in a rule is a
thing that goes stale silently.

**Nothing waits on it.** N-20b binds to every narrowing site in §5's table
regardless of the count, so the range-check obligation TM-105 creates is
complete today.

---

### O-X8 — how does a refusing constructor hand back its `ValueFault`?

**Raised 2026-09-06 at cycle 0.1.0**, writing `civil_date` and `civil_time`.
**Not blocking: cycle 0.1 does not need it**, and it is recorded now because
the next session to meet it should inherit an input rather than a
rediscovery.

*The question.* `SAFETY.md` S-3 says the caller's distinctions ride as detail
fields rather than as errors, and `ValueFault` is that detail — ten variants
when this was raised, fourteen since cycle 0.1.3 appended four (TM-173), one
per refusal row. **TM-147 measured that an `error:` cannot carry a
payload** (`tests/probe/probe14_error_payload_refused.npk`,
`NITPICK-PARSE-001`, exit 1, no `.ll`), and a `Result<T>` is
`{ T value, tbb32 err }`, so the error half of every return is a code. There
is therefore no mechanism in the language that delivers the fault alongside
the refusal, and `civil_date` today returns `Result<CivilDate>` whose error
half says `ETimeValue` and nothing finer.

*Why it is open rather than decided.* Every candidate adds a **public name**,
which by TM-013 is a thing a MAJOR version is needed to take away. Neither the
cycle README's 0.1.0 checklist nor `0.1.0.md` asks for delivery — both ask for
`ValueFault` **declared** — and a name chosen without a caller is a name chosen
without a requirement. The constructors refuse every row of their table
correctly and completely without it, and every candidate below is a pure
addition, so **nothing about deciding this later is more expensive than
deciding it now.** That is the test that makes deferring it right rather than
merely comfortable.

*The recommendation, so it is an input:* **a `never fails` companion
classifier.**

```nitpick
pub func:civil_date_fault = ValueFault(int64:y, int64:m, int64:d) never fails;
```

`civil_date` becomes two lines over it, so the rules live in exactly one place
and the constructor cannot drift from the classifier. It needs a **"no fault"
`ValueFault` variant** — the eleventh when this was raised, the fifteenth since
cycle 0.1.3 — which amends `SAFETY.md` S-3's enum
and is the substantive part of the decision, not the function. It costs a
consumer nothing: a `never fails` function arms no identity, so the arm bill
does not move.

*Alternatives, with what each costs:*

- **An out parameter** — `civil_date(y, m, d, ValueFault->:fault)`. One name
  instead of two, but every caller that does not want the fault must supply a
  place for it, and a pointer parameter on the library's most-called
  constructor is the wrong default.
- **A richer success type** — return `Result<Checked>` where `Checked` carries
  both. It puts a fault field on the happy path, which is the shape S-3 exists
  to avoid.
- **`Optional<ValueFault>` from the classifier** rather than a "no fault"
  variant. Avoids amending the enum; costs an `Optional` at every call and a
  second way to spell "valid". Worth measuring before choosing — `Optional` is
  on DERIVE-006's refused list, so a `ValueFault` inside one cannot be derived
  over, which may decide it.

*What settles it:* the first caller that needs the distinction. `src/fmt/`'s
parser at cycle 0.4 is the likely one — it will want to tell a user *which*
field of a timestamp was out of range — and a decision taken with that call
site in view will be better than one taken here.

### ~~O-X7 — one `[[test]]` entry cannot cover `tests/probe/`, because seven of its twenty-six must not compile~~ — **SETTLED 2026-09-05, TM-119**

**Settled as recommended: the runner dispatches on the file's own header**,
and the divergence from `npkg`'s `kind` is written into `BUILD.md` §3 as
**B-4c** with its migration cost. The counts below were re-measured at 0.0.2
before the decision was taken and are confirmed: 26 files, 19 `expect-exit:`,
7 `expect-error:`, none with both, none with neither. The alternative — moving
the seven to `tests/probe/refused/` — stays cheap and remains the fallback if
`npkg` ever declines the rule. **The dispatch found something on its first
run**: `probe02d_wide_literal_refused.npk` reports two codes and its header
named one, which its own prose had said it should not.

*The question as it stood:*


**Raised 2026-09-05 at cycle 0.0.1 step 3**, writing the manifest's first
`[[test]]` entries.

**The measurement, with its denominator.** `tests/probe/*.npk` — the plain
non-recursive glob a `path` entry selects — is **26** files: **19** carrying
`// expect-exit:` and **7** carrying `// expect-error:`, none without a marker.
The seven are `probe02c_narrow_refused`, `probe02d_wide_literal_refused`,
`probe10b_view_of_temporary_refused`, `probe10c_view_of_move_param_refused`,
`probe11b_arm_omitted_refused`, `probe11c_import_arm_cost` and
`probe11e_unused_import_refused`.

**The count came from a command, not from reading the names**, and that matters
here: `probe05b_derive_eq_refused.npk` is called `_refused` and is a
**positive** regression case since O-N10 was fixed (TM-111). An eyeballed list
gets it wrong, and did, once, on this dispatch.

**Why one entry cannot cover them.** A `[[test]]` selects by **directory** —
the compiler's runner globs `<path>/*.npk`, or `<path>/**/*.npk` when the entry
says `recursive` — never by file. `kind` is per entry. And an entry a runner
cannot honour is refused **by name** before anything runs, never skipped. So a
`program`-stage entry over `tests/probe/` would try to link and run seven files
that are supposed to be refused.

**What the manifest does today.** The `probe` entry is `stage = "program"`,
non-recursive, and its comment names the seven files it is **not** true about.
That is honest and it is not a solution.

**Recommendation — dispatch by the file's own header, and say so in `BUILD.md`
§3.** B-5 already puts the expectation in the file, and B-7 already makes the
*set* of reported codes the criterion; a file carrying `expect-error:` is a
refusal case wherever it lives. The compiler's own runner already has per-file
membership rules inside a stage — *"a `resolve`/`check` file with no
`expect-error` is a fixture another file imports and is skipped; a
`compile`/`program` file some other file in its suite imports is skipped"* — so
this is an extension of an existing mechanism rather than a new one.

**The cost of that recommendation, stated because it is the argument against
it.** `BUILD.md` §3 opens by saying the harness mirrors the compiler's stage
vocabulary *"so the eventual move to `npkg` is a change of runner and not of
suite"*. Header dispatch is a divergence from that, and the day `npkg` can
build a library (O-N1, O-B1) it becomes a migration cost: either `npkg` grows
the same rule, or the seven move to a directory of their own.

**The alternative, and why it is second.** Move the seven to
`tests/probe/refused/` and give them a `check`-stage entry. It fits the schema
exactly and needs no new rule — but it churns paths that `0.0.0.md`'s verdict
table, `tests/probe/README.md`'s table and several decisions cite by name, and
P-5 says a probe is never deleted for the same reason those citations exist.

**Settled at 0.0.2**, which builds the runner. **Nothing waits on it**: no
probe changes either way, and the entry in the manifest is true about the 27
<!-- [[sweep: probe_exit=27]] --> today. *(That word was `nineteen` until cycle
0.0.6 — a settled question's prose is history and is normally frozen, but this
sentence is in the PRESENT tense about the tree as it is now, so it is a claim
and not a record. TM-142.)*

### O-X9 — should an IR call-edge scan answer "did this module touch the kernel"?

**Raised 2026-09-25 by the stream-2 planner**, from the board's RX-120 entry,
which recommends the call-edge scan for every library. At compiler `c3bdae2`
the undefined-symbol scan SEES a syscall — a floor program has 5 undefined
symbols and the same program calling `sys` has 8, the difference
`npk_chain_push`, `npk_raise` and `npk_sys6` — but it can never FLAG one,
because `npk_sys6` is the runtime's own and is in the allowlist. `check_purity`
(S-10b) is SOURCE-level and remains the only thing here that answers the
question; `meta/roadmap/0.1/0.1.0b.md` step 9 corrects the documents that said
the two undefined sets were identical.

*Recommendation:* build the call-edge scan — every `call` in the emitted IR of a
module outside `src/host/`, against a reviewed allowlist — **at cycle 0.3**, the
host boundary, where the first syscall enters `src/`. *Why it stays open until
then:* it waits for something to check. Today no module but the placeholder
`host` could name a syscall, `check_purity` refuses the spelling everywhere
else, and a scan with nothing to find would be commissioned only against
plants.

### O-X10 — how `ZONE_MODEL.md` Z-4's version string is held, while a move out of `fixed` storage compiles and faults

**Raised at cycle 0.1.3b's planning, 2026-09-25.** Z-4 puts the tzdb release
name in `pub fixed string:TZDB_VERSION`, and Z-6 makes `ntime_tzdb_version()`
public. Measured at every kept pin (`SAFETY.md` S-19b): a `fixed string` read
by lending or by `.clone()` is safe, and a `move` or a plain `pass` of it
compiles and stops the program when the moved value drops — so the obvious
body of Z-6's function, and any consumer's `move(TZDB_VERSION)`, is the
compiler defect in `tests/probe/defect/fixed_move_out/` — O-N20 below, the
compiler's DEF-99.

- **(a) Hold Z-4 and Z-6 as written, and write neither until the compiler
  refuses a move out of `fixed` storage — RECOMMENDED.** The defect is raised
  and confirmed: DEF-99's fix refuses the move as `NITPICK-TYPE-084`, at the
  compiler's 1.6.0 step 3f, which no pin of ours carried when this was written;
  cycle 0.5 is several cycles away; and the author's standing call is that a
  compiler defect holds the work that depends on it rather than being covered
  by a house rule.
- **(b) Z-4 made private, and Z-6 returning `.clone()`** — correct today, but
  the one thing between a caller and the fault would be this library
  remembering to write `.clone()` and never `pass`: a house rule standing in
  for the compiler's check.
- **(c) The version held as bytes and built into a `string` on request** —
  removes the owning value from `fixed` storage altogether, and is a
  representation chosen because of a defect, which is a workaround by another
  name.

**Settles at:** cycle 0.5's planning, reading the defect's status then. **Why
it stays open until then:** it waits on the compiler's fix, and nothing before
cycle 0.5 declares a version string. **What the fix changes, as the compiler
seat describes it** (unlanded, and so not measured here): a `move` or a `pass`
of `TZDB_VERSION` is then refused where it is written, so Z-6's body can only
be `.clone()` — (b)'s spelling, enforced by the compiler rather than
remembered — and Z-4's `pub` binding hands a consumer nothing that compiles
but a lend or a clone.

---

### ~~O-N17 — a generic function that MOVES OUT of an indexed element, at an owning `T`, calls an undefined `@npk.vacant.<dty>`~~ — **FIXED at pin `aaffb87`, verified here 2026-09-05 (TM-136)**

> **Verified, not assumed.** All five reproduction cases now compile, assemble,
> link and run at exit 0 —
> `tests/probe/defect/generic_element_move/TRANSCRIPT.txt` PART D, appended
> rather than substituted. Both `case1` and `case5` carry `// expect-exit: 0`
> and neither is in `EXPECT_EXEMPT` any more (TM-137).
>
> **IT DID NOT LIFT TM-132's RESTRICTION**, and the reason is a second and
> worse defect found while checking whether it had: `NITPICK-TYPE-046` does not
> fire inside a generic body, so a *bare* read of an owning element — no
> `move` at all — is accepted, links, runs, and produces two owners of one
> heap body. **It is now numbered: O-N19**, issued by the orchestrator from
> the workbench registry and carried below. Reproduction:
> **`tests/probe/defect/generic_owning_copy/`**. Reproduced at all four pins
> this workbench has used, so it is not a regression at `aaffb87`.
>
> The record below is what was raised at `0dfddac` and is left standing.

**Raised 2026-09-05 by cycle 0.0.4, at pin `0dfddac`. Registered in the
workbench's `meta/OPEN_QUESTIONS.md` and raised to the compiler session as a
catalogue-quality report, explicitly not an interrupt.**

`npkc` **accepts** the program at exit 0 and writes an 850 377-byte `.ll`;
`llc` then **exits 1 and writes no object**:

    use of undefined value '@npk.vacant.1876'

**The reproduction is five cases with controls:**
`tests/probe/defect/generic_element_move/`. `TRANSCRIPT.txt` prints every
command's status **beside the artefact it should have produced** — which is how
this was found at all, since a run recording only exit codes sees a clean
`npkc` and stops. It is the **third** instance here of *"`npkc` exit 0 is not
well-formedness"* (TM-112, DEF-5, this).

**The fault needs all three of GENERIC, OWNING and MOVE-OUT, and no two of
them** — `case2` (concrete), `case3` (scalar `T`) and `case4` (move *in*) all
link and run.

**Where it points, which is sharper than the error text.** All four original
cases **define** the same five `npk.vacant.*` helpers; the three controls each
**call three of those five**, every callee among the defined set; `case1`
**calls four**, the fourth being `1876`, which it never defined. Written out:

    case1:  5 defined = 3 called-and-defined + 2 defined-never-called
            4 called  = 3 defined            + 1 UNDEFINED (1876)

So the definition pass works and the **call site synthesises a `dty` the
definition walk never visits** — the demand walk rather than the emitter. The
paired `@npk.drop.1876` is referenced zero times.

**Extent (TM-132): it blocks FIVE rows of `Vec<T>`, not one.** The primitive is
`T:x = move(v.items[i])`, and `vec_pop`, `vec_set`, `vec_clear`, `vec_truncate`
and `vec_free` are all built on it; `case5_generic_drop_loop.npk` is the loop
shape. **`src/core/vec.npk` therefore ships at a NON-OWNING `T`**, stated in the
file, which is every use `ntime` has. Not worked around: the element-drop path
at an owning `T` is recorded as blocked, and `SAFETY.md` S-18b already puts
element lifetime at the instantiation.

**Recommendation:** fix the demand walk so a vacancy symbol referenced by a
generic instantiation is registered. Until then the restriction stands and is
checked rather than trusted.

---

### ~~O-N18 — `.len` on a fixed-size array `T[N]` is accepted by the frontend and cannot be lowered~~ — **FIXED at pin `c3bdae2`, verified here 2026-09-25 (TM-154)**

> **Verified, not assumed.** At compiler `c3bdae2`
> `tests/probe/defect/fixed_array_len/case1_local_array_len.npk` compiles,
> links, runs and exits 0. `check_exemptions_live` reported exactly the landing
> this entry predicted — *"the entry records that this file stops at `npkc`; it
> now stops at `run:0`"* — and the response was the one written below: the file
> carries `// expect-exit: 0`, its `EXPECT_EXEMPT` entry is deleted, and
> `run_defect_corpus` asserts it on every full run. Its control, the same text
> at the kept `aaffb87` pin, is `npkc` exit 1 with no `.ll` and
> `NITPICK-EMIT-002` (`meta/roadmap/0.1/0.1.0b.md`'s execution record).
>
> The record below is what was raised at `0dfddac` and is left standing,
> including its now-past heading status: *"FIXED UPSTREAM in the compiler's
> 1.5.2e, NOT YET AT OUR PIN"*.

**Raised** from this repository at cycle 0.0.4; **numbered O-N18** in the
workbench registry (`../../meta/OPEN_QUESTIONS.md`); **accepted by the compiler
as its DEF-22** and **fixed in its cycle 1.5.2e**, which is ahead of our pin
`aaffb87`.

**Reproduction:** `tests/probe/defect/fixed_array_len/case1_local_array_len.npk`,
with two controls in that directory's README — a slice `.len`, which lowers,
and the same array indexed without `.len`, which lowers. At our pin `npkc`
refuses the file with `NITPICK-EMIT-002`, whose own text says the program is
correct and the compiler is at fault.

**Why it carries a recorded verdict rather than an `expect-error:` marker**
(`harness/run.py`'s `EXPECT_EXEMPT`): asserting the refusal would turn the bug
into a committed expectation and go red on the day it is fixed. The entry
records `npkc` instead, and `check_exemptions_live` re-derives that on every
run (TM-137).

> **EXPECT THIS TO FIRE AT THE NEXT RE-PIN, AND IT IS THE MECHANISM WORKING.**
> When the pin moves past 1.5.2e, `case1_local_array_len.npk` will go from
> `npkc` to `run:0` and `check_exemptions_live` will FAIL with *"expired
> exemption"*. **That is the landing, not a regression.** The right response is
> to give the file `// expect-exit: 0`, delete its `EXPECT_EXEMPT` entry — at
> which point `run_defect_corpus` picks it up as an ordinary asserted member
> (TM-141) — and strike this question through with the pin that fixed it. It is
> exactly what happened to O-N17's two entries at `aaffb87`.

**Live consequence in the library:** `src/core/bytes.npk`'s decimal writers
never ask their scratch array its length; they use `NTIME_DIGITS_MAX`, which is
better style anyway (`src/core/limits.npk`).

---

### ~~O-N19 — `NITPICK-TYPE-046` is not enforced inside a generic function body~~ — **FIXED at pin `c3bdae2` by the compiler's D-264, verified here 2026-09-25 (TM-154)**

> **Verified, not assumed.** At compiler `c3bdae2` a bare type parameter is
> move-only in the body that names it (D-264, landed at its 1.5.2f step 1), so
> `T:answer = s[i]` is refused `NITPICK-TYPE-046` inside the generic body.
> `generic_owning_copy/case1` and `case4` went from `run:0` and `run:170` to
> refused, `check_exemptions_live` named both moves, and both now carry
> `// expect-error: NITPICK-TYPE-046`; their `EXPECT_EXEMPT` entries are
> deleted. **`case3`, the scalar control, is refused too** — D-264 checks the
> body once for every instantiation rather than at the one it is called with —
> and its marker changed from `expect-exit: 0` to the same refusal. The
> controls, the pre-adoption text at the kept `aaffb87` pin, reproduced the
> recorded verdicts exactly: `run:0`, `run:0`, `run:170`
> (`generic_owning_copy/TRANSCRIPT.txt` section 4).
>
> **What it changes for this library** (TM-150): `vec_reserve`'s element copy
> was refused by the same check, so it relocates with `ralloc`; `vec_pop`'s
> `move` is still the right spelling; and `Vec<T>` stays restricted to a
> non-owning `T`, now on one reason — the four element drops it does not
> perform. The record below is left standing.

**Raised** from this repository at cycle 0.0.5 while checking whether O-N17's
fix lifted TM-132's restriction; **numbered O-N19** in the workbench registry;
**accepted as a soundness hole in the checker**, and the decision about it sits
with the author.

**What it is.** `T:answer = s[i]` at an owning `T` — a COPY of an owner, which
`NITPICK-TYPE-046` exists to refuse — is accepted inside a generic body at exit
0, links, and runs. The identical statement with `string` written out IS
refused. So the check attaches to the concrete spelling and not to the
instantiated type.

**Reproduction:** `tests/probe/defect/generic_owning_copy/`, five cases and a
control. `case1` is the bare copy (`run:0`, and exiting 0 is the defect);
`case2` is the concrete twin (`NITPICK-TYPE-046`, which is the control that
makes `case1` a finding); `case4` reads through the second owner after the
first has dropped and exits **170**, the allocator's `0xAA` poison (D-183).

**What it cost this library**, which is why it is carried here and not only in
the registry: `vec_pop<T>` shipped at cycle 0.0.4 as exactly `case1`'s
statement — a duplicate owner on the public surface, under a green suite, with
a comment beside it claiming TYPE-046 refused such a copy. The `move` is
written now (`src/core/vec.npk`), and **TM-132's restriction of `Vec<T>` to a
non-owning `T` stands on this defect** rather than on O-N17 (`SAFETY.md` S-18d,
TM-136).

**Two entries in `EXPECT_EXEMPT` carry its verdict** (`case1` at `run:0`,
`case4` at `run:170`) for the same reason O-N18's does, and both will fire when
the check lands.

---

### O-N20 — a `move` out of `fixed` storage holding an owning value compiles, and the program faults

**Raised** from this repository at cycle 0.1.3b's planning, 2026-09-25, at pin
`c3bdae2`, by path; **numbered O-N20** in the workbench registry
(`../../meta/OPEN_QUESTIONS.md`); **confirmed by the compiler the same day as
its DEF-99.** Its fix refuses the move at compile time as `NITPICK-TYPE-084`
and is the compiler's 1.6.0 step 3f — **not landed when this was written, and
at no pin of ours**: `c3bdae2` accepts every case.

**What it is.** `fixed` storage is emitted as an LLVM `constant` global, and a
`move` out of an element, a row's field or a scalar of it — or the implicit
move of a plain `pass` — compiles, and the program faults. At -O0 the move
stores its vacancy into the constant: SIGSEGV, which `c3bdae2`'s runtime turns
into `MachineFault` (107). Under `opt -O2` the store is deleted and the moved
string's drop frees read-only bytes (`Unreachable`, 95). A scalar writes no
vacancy and stops at 95 on both legs. The COPY is already refused,
`NITPICK-TYPE-046` (`tests/probe/probe17b_fixed_row_copy_refused.npk`,
`probe17c_fixed_string_copy_refused.npk`), so the fix asked for is the same
refusal for the move. `SAFETY.md` S-19b carries the table.

**Reproduction:** `tests/probe/defect/fixed_move_out/` — three cases and the
control that makes them one, with a transcript at every kept pin: accepted at
all six, `0dfddac` to `c3bdae2`, so it is not a regression.

**What it holds here** (TM-178): `ZONE_MODEL.md` Z-4's version string and Z-6's
`ntime_tzdb_version()`, which are case 3's and case 2's shapes exactly — O-X10
above. Nothing else: no `fixed` value in `src/` owns, and S-19b with
`check_no_owning_fields` keeps it so.

> **EXPECT THIS TO FIRE AT THE RE-PIN THAT CARRIES STEP 3f, AND IT IS THE
> MECHANISM WORKING.** The three cases sit in `harness/run.py`'s
> `EXPECT_EXEMPT` at `run:107`, `run:107` and `run:95`; at that pin each stops
> at `npkc` instead and `check_exemptions_live` fails naming it. The response is
> TM-154's: each takes `// expect-error: NITPICK-TYPE-084`, its `EXPECT_EXEMPT`
> entry is deleted, `case4_clone_control.npk` keeps its `expect-exit: 0`, this
> question is struck through with the pin that fixed it, and O-X10 is read
> again.

---

## Ids reserved in the WORKBENCH registry, recorded here so they are not taken twice

**This section defines nothing. It exists because cycle 0.0.4 filed a question
under an id another repository already held, and the correction cost ten edits
across ten files.** `O-N…` ids are allocated in the workbench's
`meta/OPEN_QUESTIONS.md`, which is shared by every library — **not** in this
file, which only re-states the ones `ntime` raised or depends on. **Before
filing an `O-N`, read the workbench registry; do not take the next number after
the highest one here.**

### O-N12 — ~~`>>>` and `string_repeat`~~ — **NOT THIS REPOSITORY'S.** It is
`nitpick-regex`'s settled question about `>>>` and `string_repeat` being
documented in the compiler's specifications. Cycle 0.0.4 filed what is now
**O-N17** under this number and had to correct every citation.
`tests/probe/defect/generic_element_move/TRANSCRIPT.txt` names it in its own
header note, which is why the id appears in this tree at all.

### O-N16 — ~~reserved in the workbench~~ — **NOT THIS REPOSITORY'S.** Named
here only because O-N17's provenance note states the range the shared registry
had already used (O-N1…O-N16) at the moment O-N17 was assigned.
