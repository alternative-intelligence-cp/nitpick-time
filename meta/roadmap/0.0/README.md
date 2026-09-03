# Cycle 0.0 — Foundations

**The probes, the harness, `src/core/`, and the tzdb size spike.** Nothing in
this cycle computes a date. What it produces is the ability to find out whether
the rest of the plan is buildable, and the machinery every later cycle is
tested by.

## Why this shape

Three of the compiler project's lessons decide this cycle's contents:

- **"A construct that parses is not a construct that works."** Its cycle 0.4
  was mostly repair, and every repair dated to the cycle that had parsed the
  construct. `ntime`'s design leans on several language shapes that have never
  been exercised in this combination — a `#[derive(Ord)]` whose comparison must
  follow declaration order, `int128` arithmetic with a narrowing `=>!`, a
  large `fixed` module-state table, a `timespec` in a `buffer` handed to `sys`.
  **0.0.0 asks the compiler about all of them before anything is built on
  them.**
- **"Diagnostics come first, not last — they are how every later cycle is
  tested."** Here that is the harness.
- **"The riskiest thing early."** TM-007's compiled tzdb rests on a size
  estimate taken from the *system* database. 0.0.5 emits a real table and
  reports its real size, because finding at cycle 0.5 that the answer is 4 MiB
  would reopen a decision the whole library rests on.

## Decisions in

TM-001, TM-002, TM-003, TM-005, TM-008, TM-011, TM-017, TM-018, TM-027,
TM-030. All settled. **Nothing in this cycle is blocked on a question.**

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| [0.0.0](0.0.0.md) | **The language probes** — programs asking the compiler whether the design is spellable | a recorded verdict per probe, and any design change the answers force |
| [0.0.1](0.0.1.md) | **The skeleton** — the module layout, `src/lib.npk`, the manifest's test table, CI | `npkc` compiles an empty library and a program that imports it |
| [0.0.2](0.0.2.md) | **The harness, part 1** — build, the `program` stage, the toolchain pin, `repro` | one test program builds, links, runs, and its exit code is judged |
| [0.0.3](0.0.3.md) | **The harness, part 2** — `parse`, `accept`, `check`, `golden`, `sweep`; the self-check; the tree checks | the self-check proves the harness can fail, seven ways |
| [0.0.4](0.0.4.md) | **`src/core/`** — `Vec<T>`, `Bytes`, `limits.npk` | the primitives, with their suites and their obligations written |
| [0.0.5](0.0.5.md) | **The tzdb size spike** — the generator's core loop, far enough to emit a table and measure it | a real number recorded against `ZONE_MODEL.md` §3's estimate |
| [0.0.6](0.0.6.md) | **Close** — the findings, the spec amendments the probes forced, the handoff to 0.1 | `done/0.0/`, and 0.1 openable by a fresh session |

## Checklist

### 0.0.0 — the probes
- [ ] `probe/probe01_derive_ord.npk` — a two-field struct with `#[derive(Ord, Eq)]`; assert the comparison follows **declaration order** (the fact `Timestamp` depends on, TM-011)
- [ ] `probe/probe02_int128.npk` — `int128` add, compare, and a narrowing `=>!` to `int64`; assert the value and assert the trap on a value that does not fit
- [ ] `probe/probe03_timespec_sys.npk` — a 16-byte `timespec` in a `buffer`, `clock_gettime(CLOCK_REALTIME)` through `sys`, both fields read back; assert `#size_of` and the offsets
- [ ] `probe/probe04_big_fixed_table.npk` — a `fixed` module-state array of ~30 000 structs; assert it is read-only memory, costs no startup work, and that the emitted IR does not initialise it at run time
- [ ] `probe/probe05_payload_enum.npk` — a tagged enum with payloads, destructured in a `pick`, stored in a `Vec`
- [ ] `probe/probe06_generic_vec.npk` — `Vec<T>` with `move T:v`, at both a scalar `T` and an owning one; and an inherent `impl:<T>:Vec<T>` with a mutating `Vec<T>->:self` receiver
- [ ] `probe/probe07_negative_div.npk` — the floor-division and modulus behaviour the calendar algorithms need at **negative** operands; assert against hand-computed values, because C-style truncation and mathematical floor differ here and Hinnant's algorithm assumes one of them
- [ ] `probe/probe08_readlink.npk` — `readlink` through `sys` into a `buffer`, with a non-NUL-terminated result and the returned length as the authority
- [ ] `probe/probe09_environ.npk` — `environ()` read, a `KEY=VALUE` entry located and split, with the borrow rules exercised
- [ ] `probe/probe10_string_bytes.npk` — `string_bytes` into a scanner and `string_from_bytes` back, at every borrow edge
- [ ] `probe/probe11_failsafe_arms.npk` — a program importing a module that declares one `error:`, whose `failsafe` names exactly the arms REACH-002 requires; and a negative twin that omits one and **must not compile**
- [ ] a verdict line per probe recorded in `0.0.0.md`, with the exact diagnostic where one was refused
- [ ] every design consequence written into `meta/specs/` **and** `meta/DECISIONS.md` before 0.0.1 starts

### 0.0.1 — the skeleton
- [ ] `src/lib.npk` exists and `pub use`s nothing yet (`use` is not transitive, so the surface is a deliberate list)
- [ ] every `src/` subdirectory has a placeholder module that parses, so the `parse` stage has something to sweep
- [ ] `nitpick.toml`'s `[[test]]` table has its first entries
- [ ] a consumer program under `tests/conformance/` imports `src/lib.npk` by relative path and compiles
- [ ] CI: a workflow running `harness/run.py` on push, with LLVM 20.1.2 and the compiler built from a **pinned commit**
- [ ] `CLAUDE.md` and `CONTRIBUTING.md` re-read against 0.0.0's verdicts and extended (both were written at repository setup; this is the check that they are still true)

### 0.0.2 — the harness, part 1
- [ ] `harness/run.py`: the manifest reader, the toolchain pin check, the module-graph walk
- [ ] the build pipeline — `npkc` → `opt` (check leg) → `llc` → the undefined-symbol scan → `ld.lld`
- [ ] the undefined-symbol scan as a **build step**, not a test (B-2)
- [ ] the `program` stage, at -O0 and again under `opt -O2`, same exit required (B-3)
- [ ] `// expect-exit:` and `// stress: N` honoured
- [ ] the `repro` check: two builds from different working directories, byte-identical IR (B-4) — **doubly important here**, because the generated zone tables will be the largest source file in the tree
- [ ] one real test program green

### 0.0.3 — the harness, part 2
- [ ] the `parse`, `accept`, `check` and `golden` stages, with the **exact-code** rule (B-7)
- [ ] the `sweep` stage, and `--quick` that skips it **with a loud line**
- [ ] `--only`, and output that says twice that a filtered run concludes nothing
- [ ] O-X5 decided: whether CI may ever use `--quick` (recommendation on file: no)
- [ ] `harness/selfcheck.py` with all seven cases from `specs/TESTING.md` V-14 — including case 7, **a silently skipped sweep**, which is this library's most plausible way to be green and wrong
- [ ] the self-check runs **first** in every full invocation
- [ ] `check_layering`, `check_error_budget`, `check_constants_named`, `check_no_owning_fields` live (several will have nothing to check yet, which is the right answer, not a reason to skip)
- [ ] `check_purity` and `check_host_isolation` **written now and dormant** — they go live at 0.3 when `src/host/` exists, and writing them now means 0.3 turns them on rather than inventing them

### 0.0.4 — `src/core/`
- [ ] `src/core/limits.npk` — every named bound in one file, each with the specification rule that set it
- [ ] `src/core/vec.npk` — `Vec<T>`: `init`, `reserve`, `push`, `pop`, `at`, `set`, `truncate`, `clear`, `free`; exercised at both `T` shapes
- [ ] `src/core/bytes.npk` — `Bytes`: `init`, `push`, `extend`, `extend_str`, `put_uint`, `put_int`, `len`, `view`, `take`, `clear`, `free`
- [ ] `put_uint` allocation-free and correct at 0, 1, 9, 10, 99, 100, and `uint64` maximum
- [ ] `put_int` correct at `int64` **minimum**, where negation overflows — the case every hand-written decimal writer gets wrong
- [ ] `Bytes` growth amortised linear, proven by a test that appends a million bytes and bounds the reallocation count
- [ ] every accessor's bounds obligation written as a comment in the `requires`/`ensures` syntax it will take (`specs/VERIFICATION.md` P-1), with a property test standing in
- [ ] the suite's programs exit 0, so a missing `free` on any path is a trap rather than a pass (D-151)

### 0.0.5 — the tzdb size spike
- [ ] `tools/gen_tzdb.py` far enough to read the pinned tzdata release's TZif files and emit the four tables from `ZONE_MODEL.md` §3
- [ ] the emitted `.npk` compiled by `npkc`, and **the object's size measured** — source bytes, IR bytes, and object bytes
- [ ] the number recorded in `0.0.5.md` and in `meta/research/`, against §3's ≈348 KiB estimate
- [ ] `#size_of` of each table row asserted, so the estimate's arithmetic is checkable
- [ ] **nothing committed from the spike but the number** — the real generator is 0.5, and a half-finished one in the tree would be a thing somebody later mistakes for the real one
- [ ] if the number is above ~1 MiB: **stop**, reopen O-Z1, and decide before 0.1 starts

### 0.0.6 — close
- [ ] every probe verdict recorded, every forced spec amendment landed
- [ ] the harness self-check green, the full run green
- [ ] `meta/DECISIONS.md` updated with anything the probes settled
- [ ] `0.1/0.1.0.md` written execution-grade before the cycle closes
- [ ] cycle moved to `done/0.0/`

## Gate

**The cycle is complete when**: a full `harness/run.py` is green; the
self-check proves the harness fails seven ways; `src/core/`'s primitives each
have a suite; every probe has a recorded verdict with its consequences written
into the specifications; and **the tzdb's real emitted size is a number in this
repository** rather than an estimate.

## Watch for

- **Probe 07 asserts a fact rather than discovering one, and that is the
  point.** Read at the compiler's `TYPE_REFERENCE.md` §28: signed `/` lowers to
  `sdiv` and `%` to `srem`, so division truncates **toward zero** and the
  remainder takes the sign of the dividend — C semantics, which is exactly what
  Hinnant's algorithm is written against (its `(y >= 0 ? y : y - 399) / 400` is
  the correction for precisely this). The probe pins it, because if it were ever
  otherwise the calendar would be silently wrong for negative years only, and
  cycle 0.1's sweep would be the first thing to notice — a long way from the
  cause.
- **Probe 04's answer decides how the zone table is spelled.** If a large
  `fixed` module-state array is initialised at run time rather than emitted as
  read-only data, TM-007's whole cost model changes and `ZONE_MODEL.md` §3
  needs a different representation.
- **A probe that fails is a finding, not an obstacle.** Record the exact
  diagnostic, decide the design change, amend the specification, and only then
  continue. Working around a compiler refusal in library code is what the
  compiler's R6 forbids.
- **The reserved words** in `specs/BUILD.md` §7 bite in `src/core/`
  specifically: `buffer`, `raw`, `move`, `end`, `in`, `limit` and `any` are all
  words a container library reaches for.
