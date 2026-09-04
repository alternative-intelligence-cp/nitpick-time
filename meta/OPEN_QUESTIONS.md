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

### Q-5 — is O-N9 a block for `ntime`, or a conformance rule plus a raised defect?
**Asked 2026-09-03, cycle 0.0.0.** O-N9 lets a `uint8[]` view escape its owning
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

### O-N9 — D-004's escape rule is unenforced for slice views — **NOT BLOCKING**
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
the library is in the blast radius. It is **not blocking**, because the house
rule *a view is a parameter, never a return value* is compliance with the
documented rule rather than a workaround for its absence, and it costs nothing:
a parser returns a value and an offset. Its disposition is **Q-5**, and
`check_no_view_returns` — **proposed** for cycle 0.0.3's harness list, not yet
on it — is what would make the rule enforced rather than remembered.

### O-N10 — the derives on a payload enum: `Eq` will not compile, `Ord` is silently wrong — **NOT BLOCKING**
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

**The id is provisional.** `O-N` numbers are the workbench registry's and are
assigned there; O-N10 is this repository's expectation of the next free one and
the orchestrator may renumber it when it registers the defect.

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
