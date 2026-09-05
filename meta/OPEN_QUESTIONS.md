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

### O-N4 — `npkc` is quadratic in the size of one declaration — **BLOCKING**
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
semantics change.

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
### O-N8 — `npkc` merges a sibling file when a root file's `mod:` name mismatches
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

### O-Z1 — ship every zone, or a selectable subset?
`specs/ZONE_MODEL.md` §8's item, mirrored here. §3's measured ≈348 KiB says
ship them all, and a subset would be a build-configuration knob the ecosystem
does not have.
**Open by design until cycle 0.0.5's spike measures the real emitted object
size** (O-X2). `meta/roadmap/0.0/0.0.5.md` §3 has the thresholds and the
fallback candidates, decided in advance so that a bad number produces a stop
rather than an improvisation.

### O-X2 — the real emitted tzdb size
`ZONE_MODEL.md` §3 estimates **≈348 KiB** from a measurement of tzdata 2026c's
447 canonical zones and 26 838 transitions. **Open by design:** it is a
*measurement*, taken at cycle 0.5 against what the generator actually emits,
and recorded there with the number.
**If it comes in above ~1 MiB**, O-Z1's question — ship every zone or a
selectable subset — becomes real again, and the fallback is decided then
against the number rather than invented now.

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

### O-X5 — the `sweep` stage under `--quick`
`BUILD.md` B-9 makes the exhaustive sweeps skippable under `--quick` with a
loud line. Whether CI should ever use `--quick` is a policy question.
**Recommendation:** no. The sweeps run in seconds; the flag exists for a
developer iterating on one function, and a CI run that skipped the gate would
be a CI run that concluded nothing. Decide at cycle 0.0.3 when the harness
grows the flag.

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

### O-X7 — one `[[test]]` entry cannot cover `tests/probe/`, because seven of its twenty-six must not compile

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
probe changes either way, and the entry in the manifest is true about the
nineteen today.
