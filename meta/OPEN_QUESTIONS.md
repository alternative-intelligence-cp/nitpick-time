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
