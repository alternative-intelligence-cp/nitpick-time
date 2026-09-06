# CLAUDE.md

Guidance for Claude Code sessions working in this repository.

## What this is

`ntime` — a date, time and time-zone library for **Nitpick**, the
safety-critical systems language at `../../nitpick`.

**Status, after cycle 0.0.5: the first library code, and the tzdb sized.**
TM-007's compiled-in database is **475 006 bytes** of read-only data for the
four tables and two pools, **489 310** with `POSIX_RULES` — measured, not
estimated, against a 348 KiB estimate that was wrong in four ways (TM-135).
That is inside the budget `0.0.5.md` §3 set in advance, with 4.4% to spare, so
TM-007 stands and O-X2 and O-Z1 close.

**After cycle 0.0.4: the first library code.** `src/core/` holds
`vec.npk` (`Vec<T>`, nine functions), `bytes.npk` (`Bytes`, eleven) and
`limits.npk` (thirteen named bounds, each with the rule that set it). The
umbrella re-exports **35** names, one line each. The other five directories are
still placeholders that parse and are **replaced, not deleted**, by the cycle
named in each header. `harness/` is the runner `BUILD.md` describes — nine
stages, ten modules — and a full invocation is **40 units green in about
42 s** at pin `aaffb87`. It was **241 s** at `0dfddac`; the compiler's 1.5.2d
close made every emitted module carry only the prelude functions it references,
and that is the whole of the difference — same 40 units, same verdicts.

**Two things to know before touching `src/core/`.**

- **`Vec<T>` is for a NON-OWNING `T`** (TM-132, and the reason changed at
  0.0.5 — TM-136). **O-N17 is FIXED** at pin `aaffb87`; the restriction stays
  because **`NITPICK-TYPE-046` does not fire inside a generic function body**,
  so `T:x = s[i]` at an owning `T` — a copy of an owner — compiles, links,
  runs, and leaves two owners of one heap body. Reading through the second
  after the first has dropped returns the allocator's `0xAA` poison, exit 170
  (`tests/probe/defect/generic_owning_copy/`). It bit this file: `vec_pop<T>`
  shipped as that bare read at 0.0.4 and now writes the `move`. And
  **`vec_at<T>` at an owning `T` REMOVES the element** — `pass` of a place
  moves implicitly — which is the language behaving as specified and is why
  element lifetime at an owning `T` goes **at the instantiation**, where
  `SAFETY.md` S-18b and S-18d put it.
- **The bounds guard is the compiler's, not ours** (TM-129, S-17c). Each
  accessor lays a `#wild_slice` over `count` and indexes that, so
  `emit_bounds_guard` runs and one unsigned compare rejects both ends. The
  library now contains **no raw bare-pointer index at all**.

**What 0.0.3 added, and the first item is the one that matters.**
`harness/selfcheck.py` runs **first** in every full invocation (`TESTING.md`
V-15) and plants eight faults, nine tree-check violations and three arm-bill
specimens, requiring a red run that names each and a green control beside it.
Before it, three of the harness's checks had been commissioned by hand and that
was three checks, not a runner. Then: the `parse`, `check`, `golden` and `sweep`
stages; `--quick`; and nine live tree checks.

## Before starting a session here

Check **[`../BOARD.md`](../BOARD.md)** — it says whether this repository
is claimed by a stream, and by which. **One writer per repository, always.**
[`../WORKSTREAMS.md`](../WORKSTREAMS.md) is the dependency graph and the
stream partition: what gates this repository, what this repository gates, and
what to do when a cross-stream gate is not ready yet.

## Read these first, in this order

0. **`../PLAYBOOK.md`**, if you have the sibling checkouts — the shared house
   rules for every Nitpick library: the language constraints that bite, the
   error-budget rule, the repository and roadmap conventions, and the state of
   the tooling. It is a workbench document and lives beside the checkouts
   rather than inside one, because it belongs to none of them.
1. **`meta/specs/SAFETY.md`** — the constraints and where they come from.
2. **`meta/specs/TIME_MODEL.md`** — **the core.** Almost every bad idea in a
   date library is a type distinction it declined to make; this document is the
   set of distinctions and why each exists.
3. **`meta/specs/README.md`** — the index and the reading order for the rest.
4. **`meta/DECISIONS.md`** — every settled design decision with its reasoning.
   **Read this before proposing a change**, because it is recorded why.
5. **`meta/roadmap/ROADMAP.md`** — the cycle map; then the current cycle's
   `README.md`.
6. **`meta/OPEN_QUESTIONS.md`** — what is not settled, each with a
   recommendation.

## The rules that are not negotiable

- **The specifications are the authority** (TM-002). Code that disagrees with
  `meta/specs/` is a defect in the code. A specification that turns out to be
  wrong is amended by a decision recorded in `meta/DECISIONS.md`, in the same
  commit — never by editing the text and moving on, and never by a comment.
- **A settled decision's text is never rewritten.** Supersede it with a new
  numbered decision that says why (the compiler's D-085/D-202 pattern).
- **Three public error identities, and three is a ceiling** (TM-017). REACH-002
  makes every one an arm every consuming program's `failsafe` must name. A
  fourth needs a decision saying why a shutdown handler would treat it
  differently from all three — and it is a **major** version (TM-013).
- **Only `src/host/` is impure** (TM-018). No syscall, no clock, no environment
  read, no file read anywhere else. `check_purity` enforces it, and it is the
  single most important check in the suite.
- **`ntime` declares no `Duration`** (TM-004). The prelude's is the ecosystem's
  one span type. A second would immediately become the type everybody converts
  to and from.
- **There is no format string** (TM-009, TM-023). No `strftime`, no
  `layout_from_pattern`. A layout is a typed value, and
  `check_no_format_string` makes adding one a red run.
- **No dependencies** (TM-027). Not the compiler's `src/`, not its `lib/`, not
  `nitpick-parse`, not `/usr/share/zoneinfo`.
- **Never work around a compiler defect.** Record the reproduction, stop, and
  raise it. This is the compiler's own R6: a workaround buried in library code
  outlives the bug and is indefensible at verification time.

## The compiler constraints that shape everything

Full statement in `meta/specs/SAFETY.md` §1. The ones that bite hardest here:

- Plain integer overflow **traps**; division by zero traps; indexing traps.
  Every range is checked **before** the trap so the caller gets an answer.
- `Ord` derives in **declaration order**, so a struct's field order is
  semantic (`Timestamp` is seconds-then-nanos for exactly this reason).
- Owning values are **move-only**; a value stored in a table has no owning
  field.
- There are **no closures** and **no format-specifier language** (D-018,
  D-053).
- `defer` does **not** run on a trap; `failsafe` is the only code guaranteed to
  run.
- An `async` function can never be `never fails`, so `raw await …` is
  unspellable — but `ntime` has no `async` function at all, and should not
  grow one.

**And the four that cycle 0.0.0 MEASURED rather than read**, each of which
changed a document:

- **There is no checked narrowing** (TM-105). `=>!` truncates in silence, and
  the checked `=>` at the same narrowing is refused at compile time
  (`NITPICK-TYPE-009`). Every narrowing therefore carries its own range check —
  written by you, in code.
- **`exit 0` says nothing about managed memory** (TM-106). D-151 watches `wild`
  allocations only. A `Vec<string>` whose block is freed and whose elements are
  not retained 125 MiB over two million elements **and exited 0**.
- **An import's arm bill is its `fail` SITES plus its ARITHMETIC**, charged per
  module, not per call (TM-107). Importing a module that declares no error at
  all still cost four arms. Avoiding a failing *function* buys nothing; module
  boundaries are the only granularity there is.
- **`Vec<T>` and `Bytes` are NOT bounds-checked** (TM-108). The check attaches
  to the *type*: slices, arrays and simd lanes trap, **a bare pointer does
  not**, and both of those are reached as one. The accessor pair is the only
  bound there is, and it checks `0 <= i` as well as `i < count`.

**And one about the compiler itself: `npkc` exit 0 is not well-formedness**
(TM-112). It accepted a root with `main` and no `failsafe` until DEF-5 landed.
Pair every exit code with the artefact it should have produced; a status that
disagrees with an artefact is the tell.

## Reserved words that read like ordinary names

`meta/specs/BUILD.md` §7 has the table. The ones this domain wants most:
`unit` (a rounding granularity), `end` (a range's upper bound), `limit` (a
bound), `in`, `on`, `mod` (a modulus), `fixed` (as in "fixed offset"), `range`,
`error`, `buffer`, `raw`, `move`, `any`, `is`, `never`, `fails`.

The substitutes this library uses, so the tree stays consistent: **`gran`** for
a rounding granularity, **`hi`**/**`lo`** for range bounds, **`rem`** for a
modulus result, **`zone_off`** for a fixed offset in seconds, **`bound`** for a
limit, **`src`** for an input byte slice, **`sink`** for an output `Bytes`.

**And the ten VERIFICATION keywords, none of which was in any table here until
cycle 0.0.4** (TM-130, `BUILD.md` B-18): `prove`, `assert_static`, `requires`,
`ensures`, `acquires`, `gives`, `invariant`, **`old`**, **`result`**, `pure`.
All ten measured refused as local names at pin `0dfddac`. The last three are
the compiler's D-221, and `old` and `result` are the dangerous pair, because
this library's own contract syntax uses them — `ensures v.count == old(v.count)`
— so you meet them as things to write. Use **`outgoing`** and **`answer`**.

And **`stack`**, which is not in this library's own list and is the one that
costs an hour: it is a memory qualifier beside `wild`, and using it as a local
name gives `PARSE-002` at the declaration followed by *"this `{` is never
closed"* pointing at `main`'s closing brace — so it reads as a brace imbalance
dozens of lines away and gets bisected as one. A sibling library lost about an
hour to it. **If a parse error claims an unclosed brace and the braces are
balanced, check whether a local is named after a qualifier before you touch the
braces.**

Three shapes that surprise a C or Rust habit: adjacent string literals do not
concatenate; `discard(x);` takes parentheses and `defer { … }` takes no
trailing semicolon; declarations end `};` and control-flow blocks do not.

**And a file's `mod:` name must equal its basename** — the loader reports
`NITPICK-RESOLVE-005` at line 1 and says nothing about the name. Since D-248 a
module name is an **identifier**, so a file named after a reserved word, or
beginning with a digit, is refused: hence `probeNN_topic.npk` and never
`NN_topic.npk`.

## Building and testing

**`npkg` cannot build this yet** (`meta/specs/BUILD.md` §1): it is the
compiler's own bootstrap ladder, and `[dependencies]` resolves to nothing.
`harness/run.py` is the runner until that changes (TM-003).

**What the harness is after 0.0.3.**

```
$ NPKC=… NPKRT=… python3 harness/run.py [--only SUBSTRING] [--quick]
                                        [--verdicts PATH] [--root DIR]
```

Ten modules under `harness/` — `manifest`, `toolchain`, `elf`, `build`,
`stages`, `checks`, `arms`, `repro`, `selfcheck` — driven by `run.py` in nine
stages. It proves it can fail; reads `nitpick.toml` and hardcodes nothing;
holds `llc`, `opt` and `ld.lld` to the pinned patch release; sweeps every
`.npk` in the tree and prints the denominator; diffs the tree against the
documents describing it; roots every `.npk` at the real parser; builds the
library; proves the IR identical from two working directories; and runs each
test file at -O0 and again under `opt -O2`. `harness/README.md` is the guide
and carries the cost table.

**Four things it is easy to over-read, so they are written down.**

- **The library object is linked into nothing** (TM-117). There is no separate
  compilation: `npkc` emits the whole module graph a root reaches, so every
  program carries the prelude and `ld.lld p.o ntime.o npkrt.o` is a
  duplicate-symbol error. The library is built because *building it is a check*.
- **The undefined-symbol scan cannot see a syscall** (TM-118). `npk_sys6` is the
  runtime's own and is in the allowlist by construction. The scan supports
  B-2's "no C, ever" and nothing wider. **`check_purity` is SOURCE-level and is
  the only thing here that answers "did this module touch the kernel"** — never
  cite a green symbol scan for it (B-2c, S-10b, RX-120).
- **The `parse` stage asks `npkc`, not the compiler's `tools/parse_check`**
  (TM-123): those are `.npk` source files, and building one is building the
  compiler from a tree ahead of our pin. It reads the diagnostic's code
  *family* instead — `LEX` and `PARSE` are the parse phase and everything else
  is later.
- **A `--only` or `--quick` run concludes nothing**, says so twice, and will
  not print the unqualified word `GREEN`. CI passes no flags and that is a rule
  (TM-125, B-9b), asserted by the workflow rather than left to review.

**Two probes need `TZ=Europe/Kyiv`** (09 and 09b). They now say so in their own
headers — `// env: TZ=Europe/Kyiv`, TM-120 — and the harness **constructs** each
program's environment rather than inheriting yours, so a `TZ` in your shell
cannot change a verdict. Run by hand without it they exit **30**; with the wrong
value, **39**. Neither number is a verdict about the language — that is the
point of them (TM-116).

The compiler binary is the **pinned toolchain** the board names
(`../BOARD.md`, W-18): `$NPKC` and `$NPKRT` are supplied to every session by the
orchestrator, or set by hand from `../.internal/toolchain/<commit>/`. Never build the
compiler from here and never read its `build/` directly — the guard refuses
the first, and the second is rebuilt under you. LLVM 20.1.2 exactly, pinned —
and the harness asks `llc`, `opt` and `ld.lld` rather than `llvm-config`, which
ships in a `-dev` package the build never invokes and which can report a
different installation from the one on `PATH`.

## Where things go

```
src/       the library, Nitpick only, layered per meta/specs/BUILD.md §6
  core/      Vec, Bytes, the named limits
  cal/       the civil calendar and its algorithms
  span/      Duration interop and Period
  zone/      the GENERATED tz tables and the offset lookup
  fmt/       formatting and parsing, and the typed layout
  host/      THE ONLY IMPURE MODULE — five functions, nothing else
tests/     probe, conformance, unit, golden, rejection, fixtures
harness/   the Python build and test runner, until npkg can
tools/     generators — the tzdb tables; everything they emit is committed
examples/  runnable demonstrations, built and run by the harness
docs/      user-facing documentation, written at cycle 1.0
meta/      specs, decisions, open questions, the roadmap, research
.internal/ gitignored scratch — never commit anything from here
```

## When you find something

- A **compiler defect**: record the reproduction, stop, raise it. Do not work
  around it.
- A **specification error**: fix the specification and record the decision, in
  the same commit as the code that revealed it.
- A **finding that is neither**: write it into the current subcycle's execution
  record. This project's execution records are load-bearing; the compiler's
  cross-cycle patterns exist only because one writer kept them.
