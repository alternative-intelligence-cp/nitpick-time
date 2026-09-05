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
- [x] `probe/probe01_derive_ord.npk` — a two-field struct with `#[derive(Ord, Eq)]`; assert the comparison follows **declaration order** (the fact `Timestamp` depends on, TM-011)
- [x] `probe/probe02_int128.npk` — `int128` add, compare, and a narrowing `=>!` to `int64`; assert the value and ~~assert the trap on a value that does not fit~~ — **there is no trap.** The clause was written against an assumption the probe falsified; the trap half became `probe02b` and `probe02c` below, and the consequence is TM-105
- [x] `probe/probe02b_narrow_unchecked.npk` — **added at 0.0.0, when probe 02's twin came back the other way.** `=>!` at an `int128` that does not fit `int64`: it truncates silently, in four shapes, one of them a positive value narrowing to a negative one
- [x] `probe/probe02c_narrow_refused.npk` — the negative twin: the checked `=>` at the same narrowing is refused at compile time, `NITPICK-TYPE-009`. Together the two say there is **no checked narrowing** in the language, which is what TM-105 is about
- [x] `probe/probe03_timespec_sys.npk` — a 16-byte `timespec` in a `buffer`, `clock_gettime(CLOCK_REALTIME)` through `sys`, both fields read back; assert `#size_of` and the offsets
- [x] `probe/probe04_big_fixed_table.npk` — a `fixed` module-state array of ~30 000 structs; assert it is read-only memory, costs no startup work, and that the emitted IR does not initialise it at run time
- [x] `probe/probe04b_emission_shape.npk` — **added at 0.0.0's verification.** The same declaration at 300 rows, with the IR, `readelf` and segment evidence committed verbatim in `probe04b_emission_shape.txt`. Probe 04 costs 281 s and 30.9 GiB under O-N4, so its emission-shape answer was a one-time observation nobody could re-derive; the form is a property of the lowering and not of the size, so 300 rows evidences it for 0.16 s
- [x] `probe/probe05_payload_enum.npk` — a tagged enum with payloads, destructured in a `pick`, stored in a `Vec`
- [x] `probe/probe05b_derive_eq_refused.npk` — **added at 0.0.0.** `#[derive(Eq)]` on a payload enum did not compile, and `#[derive(Ord)]` on the same declaration compiled and ignored the payload. O-N10, the subcycle's third stop. **O-N10 DISCHARGED 2026-09-04 (TM-111)**: both derives are fixed, `Literal(7).cmp(Literal(9))` now answers `Less`, and the derived `eq` was checked for correctness rather than for compiling. The file's `expect-` header is corrected and it is now a regression case
- [x] `probe/probe06b_element_leak.npk` and `probe06c_element_drop.npk` — **added 2026-09-04.** The TM-106 leak pair, restored as committed files: 0.0.0 measured them in scratch and committed only the numbers, so at the re-pin there was nothing to re-run. They differ in one line and **both exit 0**. Re-measured **unchanged** (125 184 KiB; `HeapOom` at a 64 MiB cap; the remedy half under 768 KiB), which is the finding — D-246 and D-247 do not touch this
- [x] `probe/probe06_generic_vec.npk` — `Vec<T>` with `move T:v`, at both a scalar `T` and an owning one; ~~and an inherent `impl:<T>:Vec<T>` with a mutating `Vec<T>->:self` receiver~~ — **struck.** The form exists and works (the compiler's own `tests/backend/programs/impl_target.npk` has `impl:<T>:Box<T>` with a `Box<T>->:self` receiver), and `0.0.4.md` §2 has since settled this library's API as free functions following the compiler's `list_*` functions, which D-239 moved from `src/frontend/list.npk` into the prelude (TM-113). A probe for a form the design does not use pins a fact nothing depends on
- [x] `probe/probe07_negative_div.npk` — the floor-division and modulus behaviour the calendar algorithms need at **negative** operands; assert against hand-computed values, because C-style truncation and mathematical floor differ here and Hinnant's algorithm assumes one of them
- [x] `probe/probe08_readlink.npk` — `readlink` through `sys` into a `buffer`, with a non-NUL-terminated result and the returned length as the authority
- [x] `probe/probe09_environ_split.npk` — **worked 2026-09-04 at the re-pin**, with `probe09b_environ_view_returned.npk`. `environ()` read; every entry asserted `KEY=VALUE` with a non-empty key; `TZ` located by prefix and split into an **offset pair**; the block shown stable across two calls, **same pointers**. 09b returns a view of an entry and reads it after the frame died. Named `_environ_split` rather than `_environ`, since the split is what it measures
- [x] `probe/probe10_view_edges.npk` — **worked 2026-09-04**, with `probe10b_view_of_temporary_refused.npk` and `probe10c_view_of_move_param_refused.npk`. Both were HELD by the ruling on Q-5, and both ARE O-N9's own measurement, so they were run against a compiler that has DEF-3 rather than one that does not. **§1 is the discriminator** — an `alloc`'d block viewed and returned, no parameter in the root chain — and it settles that the rule keys on the **root's shape**, not on parameterhood. **TM-110**
- [x] `probe/probe11_failsafe_arms.npk` — a program importing a module that declares one `error:`, whose `failsafe` names exactly the arms REACH-002 requires; and a negative twin that omits one and **must not compile**. **Both answers are the good ones**: nine arms compile and run, and the omission is `NITPICK-REACH-002`, so TM-017's budget is a constraint
- [x] `probe/probe11c_import_arm_cost.npk`, `probe11d_floor_only.npk`, `probe11e_unused_import_refused.npk`, `probe11f_declared_unraised.npk` — **added at 0.0.0.** The two-file answer above would have been true and misleading: the reachable set is computed over **every module in the graph**, so an import charges a consumer for its *arithmetic* too — four arms from a module that declares no error at all, measured against 11d's floor. **TM-107**, `SAFETY.md` S-4b/S-4c and three constraints on S-6's generator
- [x] `probe/support/` — the three modules probe 11 imports, kept apart so each refusal changes one variable. Not probes: no `main`, no `failsafe`, and `tests/probe/*.npk` must not glob them, exactly as `defect/` must not be globbed
- [x] `probe/defect/missing_failsafe/` — **the subcycle's fourth stop.** A program with `main` and no `failsafe` compiled at `npkc` exit 0; `llc` refused it a long way from the cause. **O-N11 DISCHARGED 2026-09-04 (TM-112)**: it is now refused `NITPICK-REACH-003` at `main`, and the diagnostic **lists the identities owed** — the full ask, granted. `case1` owes **four** (S-4b's floor) and `case3` owes **six**; a board carried six for `case1` and the six belonged to the other file. Both transcripts re-recorded as a Part A above the verbatim Part B
- [x] a verdict line per probe recorded in `0.0.0.md`, with the exact diagnostic where one was refused — **complete at the 2026-09-04 re-pin**, including 09, 09b, 10, 10b and 10c, and with the four defect rows rewritten from DEFECT to FIXED against measured output
- [x] every design consequence written into `meta/specs/` **and** `meta/DECISIONS.md` before 0.0.1 starts — TM-105 … TM-109 from the original run, and **TM-110, TM-111, TM-112** from the re-pin, with `SAFETY.md` S-15b, S-17b, S-18b, S-22 and S-4b/S-4c carrying them

### 0.0.1 — the skeleton
- [x] `src/lib.npk` exists and `pub use`s nothing yet (`use` is not transitive, so the surface is a deliberate list). Its header carries the shape the lines will take and the rule **one line per public name, never a `.*` glob** — a glob would silently re-export `host`'s impure five
- [x] every `src/` subdirectory has a placeholder module that parses, so the `parse` stage has something to sweep — six, each naming its spec, its cycle and what it may import; `host/`'s carries the purity rule. All seven `src/` files compile at 844 793 B of IR, and `harness/run.py` **asserts the count is at least 7**, because a directory whose placeholder was deleted rather than replaced is invisible to the sweep
- [x] `nitpick.toml`'s `[[test]]` table has its first entries — `probe` (`program`, non-recursive so `support/` and `defect/` are excluded, with the reason written next to it) and `conformance` (`compile`/`positive`, **not** `accept`, TM-114). **O-X7 raised**: the `probe` entry cannot be true about all 26, because 7 carry `expect-error:` and the schema selects by directory, never by file
- [x] a consumer program under `tests/conformance/` imports `src/lib.npk` by relative path and compiles — **and links and runs and exits 0**, measured. Its `.ll` is byte-identical to `probe11d_floor_only.npk`'s, so importing `ntime` today costs a consumer nothing; the negative control (one floor arm removed) is `NITPICK-REACH-002`
- [~] CI: a workflow running `harness/run.py` on push, with LLVM 20.1.2 and the compiler built from a **pinned commit** — **written and validated locally, NOT YET SEEN GREEN.** `.github/workflows/ci.yml` pins compiler `0dfddac045bdab6abbd367b1ffb31de695b9bf22` and LLVM `20.1.2`, asserts both plus a clean checkout and the ladder's working directory, and reports the artefact digests against the workbench's rather than asserting cross-machine byte identity nobody has measured. The YAML parses and all six `run:` blocks pass `bash -n`. **The acceptance item says "green on a push" and 0.0.1 does not push** (`ROADMAP.md`: push at the end of a cycle), so this carries to the push that closes 0.0
- [x] `CLAUDE.md` and `CONTRIBUTING.md` re-read against 0.0.0's verdicts and extended (both were written at repository setup; this is the check that they are still true). **`CLAUDE.md`'s `## What this is` section was EMPTY** — its body had drifted under the next heading — and its "Status: planning, no library code exists" was about to become false; both fixed. Both files gained TM-105 … TM-108 and TM-112 as things that *were measured*, and `stack`, the reserved word that costs an hour by failing dozens of lines from where it was written

### 0.0.2 — the harness, part 1
- [x] `harness/run.py`: the manifest reader, the toolchain pin check, the module-graph walk — six modules, `manifest.py` (a schema check that refuses an unknown key **by name**, in both directions), `toolchain.py` (asks `llc`/`opt`/`ld.lld`, **not** `llvm-config`, which is a `-dev` package the build never invokes), `elf.py`, `build.py`, `stages.py`, `repro.py`
- [x] the build pipeline — `npkc` → `opt` (check leg) → `llc` → the undefined-symbol scan → `ld.lld`. **The plan's last step was wrong and it was measured, not argued**: there is no separate compilation, so a program links with `npkrt.o` alone and never with `build/ntime.o` (**TM-117**; the three-object link is `ld.lld` exit 1, 121 lines of `duplicate symbol`)
- [x] the undefined-symbol scan as a **build step**, not a test (B-2) — **and it has been seen to fail**, naming the symbol, exit 1. Its allowlist is derived from `$NPKRT`'s ELF symbol table and not from `runtime/npkrt.ll`'s `define`s, which is wrong by 56 in one direction and 2 in the other (**TM-118**), and the scan **cannot see a syscall**, which is written down rather than hoped about (RX-120)
- [x] the `program` stage, at -O0 and again under `opt -O2`, same exit required (B-3)
- [x] `// expect-exit:` and `// stress: N` honoured — plus `// expect-error:`, `// expect-error-at:`, `// argv:` and the new `// env:`
- [x] the `repro` check: two builds from different working directories, byte-identical IR (B-4) — **green, and seen to fail** against a deliberately non-deterministic generator, with the deterministic twin green through the same code path as the control
- [x] **the nine probes carrying the pre-TM-106 leak comment reworded.** Each
      said `// D-151: exit 0 additionally asserts that nothing leaked.`, which
      is not what D-151 proves: it watches `wild` allocations only, and a
      managed body is outside it entirely (TM-106). The wording used is
      `tests/probe/README.md`'s. **The list came from the command and not from
      the probes anybody compiled** —
      `git grep -l 'additionally asserts that nothing leaked' -- '*.npk'`,
      **9 files out of 50 tracked `.npk`** — because
      `probe04_big_fixed_table.npk` is the one probe nobody compiles (O-N4's
      281 s / 30.9 GiB case), so it drops out of any list built from what a
      session ran, and it was missed exactly once for that reason. It is in the
      nine, and it was reworded. `probe06` and `probe11` were **confirmed by
      reading** to be correctly outside the nine: both already carry the `wild`
      wording. **A WIDER sweep found a tenth line the exact one could not**:
      `git grep -n 'nothing leaked' -- '*.npk'` gives **10 lines across the same
      9 files**, the extra being `probe02_int128.npk:12`, a differently worded
      copy of the same wrong claim in that file's header prose. It was reworded
      too. Residual: **0** for both patterns
- [x] one real test program green — **all 27 units are**: the 19 run members and 7 refusal members of `tests/probe/`, plus `tests/conformance/import.npk`, in **65 s**
- [x] **O-X7 settled** — **TM-119**, as recommended: dispatch on the file's own header, with the divergence from `npkg`'s `kind` written into `BUILD.md` §3 as **B-4c** together with its migration cost. The counts were **re-measured here before deciding** and confirmed: 26 files, 19 and 7, none with both markers, none with neither. The dispatch found `probe02d_wide_literal_refused.npk` naming one of the **two** codes it reports — in the file whose own prose states D-237's rule
- [x] **a way to state an environment variable in a test header** — `// env: NAME=VALUE` (**TM-120**), a marker and not a wrapper. **And its unasked-for half:** the run environment is *constructed*, never inherited, or the marker would be pointless — and the declared base is **non-empty**, because under a genuinely empty environment `probe09_environ_split` exits **10**, one of its substantive codes, which is TM-116's defect through a second door
- [x] **replaced `harness/run.py`, not extended it.** The floor's four hardcoded checks are gone; two things came across because they had earned it — `check_expect_headers` (TM-115), now reading headers through the *same* strict parser the suite dispatches on, and the artefact-pairing rule. The strict parser found two prose lines byte-identical to markers (**TM-121**)

### 0.0.3 — the harness, part 2
- [ ] the `parse`, `accept`, `check` and `golden` stages, with the **exact-code** rule (B-7)
- [ ] the `sweep` stage, and `--quick` that skips it **with a loud line**
- [ ] `--only`, and output that says twice that a filtered run concludes nothing
- [ ] O-X5 decided: whether CI may ever use `--quick` (recommendation on file: no)
- [ ] `harness/selfcheck.py` with all seven cases from `specs/TESTING.md` V-14 — including case 7, **a silently skipped sweep**, which is this library's most plausible way to be green and wrong
- [ ] the self-check runs **first** in every full invocation
- [ ] `check_layering`, `check_error_budget`, `check_constants_named`, `check_no_owning_fields` live (several will have nothing to check yet, which is the right answer, not a reason to skip)
- [ ] **`npkc` exit 0 is not "well-formed"** — the `program` stage runs all four steps (`npkc`, `llc`, `ld.lld`, run) or asserts `grep -c '^define i32 @npk_failsafe'` is 1. A program with `main` and no `failsafe` compiles at `npkc` exit 0 and is refused only by `llc` (`meta/OPEN_QUESTIONS.md` O-N11, measured at 0.0.0), so a stage that stops at `.ll` passes a program with no handler
- [ ] **`selfcheck.py` gains an eighth case**: a program whose `failsafe` has been deleted must be caught. It is this library's own "green and wrong" shape, and `TESTING.md` V-14's seven do not cover it
- [ ] `check_failsafe_arms` / the S-6 generator built to TM-107's three constraints: it counts `fail`/`?!`/`!!!` **sites** and never `error:` declarations; it includes the **system** arms the imported subgraph's arithmetic arms; and it asserts "no more" **itself**, because a superset of the required arms compiles and no build would catch an overstated table
- [ ] `tests/probe/support/` and `tests/probe/defect/` **excluded from the probe glob**, each with the reason written next to it — neither holds programs
- [ ] **`check_raw_index`** — no `.items[` outside `src/core/vec.npk` and no
      `.ptr[` outside `src/core/bytes.npk`. `Vec<T>.items` and `Bytes`' buffer
      body are **bare pointers**, which the language does not bounds-check
      (TM-108, `SAFETY.md` S-17b), so the accessor pair is the only bound there
      is and this check is what keeps it that way
- [ ] `check_purity` and `check_host_isolation` **written now and dormant** — they go live at 0.3 when `src/host/` exists, and writing them now means 0.3 turns them on rather than inventing them

### 0.0.4 — `src/core/`
- [ ] `src/core/limits.npk` — every named bound in one file, each with the specification rule that set it
- [ ] `src/core/vec.npk` — `Vec<T>`: `init`, `reserve`, `push`, `pop`, `at`, `set`, `truncate`, `clear`, `free`; exercised at both `T` shapes
- [ ] `src/core/bytes.npk` — `Bytes`: `init`, `push`, `extend`, `extend_str`, `put_uint`, `put_int`, `len`, `view`, `take`, `clear`, `free`
- [ ] `put_uint` allocation-free and correct at 0, 1, 9, 10, 99, 100, and `uint64` maximum
- [ ] `put_int` correct at `int64` **minimum**, where negation overflows — the case every hand-written decimal writer gets wrong
- [ ] `Bytes` growth amortised linear, proven by a test that appends a million bytes and bounds the reallocation count
- [ ] every accessor's bounds obligation written as a comment in the `requires`/`ensures` syntax it will take (`specs/VERIFICATION.md` P-1), with a property test standing in
- [ ] **and the bound is CODE in every accessor, not only a comment** (TM-108, `SAFETY.md` S-17b): `Vec<T>.items` and `Bytes`' buffer body are bare pointers, which the language does not bounds-check, so `vec_at`/`vec_set` and every `Bytes` accessor check **`0 <= i` as well as `i < count`** — an index derived from a narrower signed field can be negative, `i < count` accepts it, and the read goes backwards off the block. The negative case gets its own test
- [ ] the suite's programs exit 0, which asserts that **no `wild` allocation is live** at exit — `Vec<T>`'s block is `wild` (P-23), so an unpaired `vec_free` on any path is a trap rather than a pass (D-151)
- [ ] and, because that is the whole of what D-151 covers, a **memory assertion for the managed half**: a `Vec<string>` whose block is freed and whose elements are not retains its elements and **still exits 0** (TM-106, measured at 125 MiB over 2 000 000 elements). Until the instrument below exists, each owning-`T` container test runs a second time under a `ulimit -v` cap sized to fail if the elements are orphaned — the form TM-106 itself used, where the orphaning form gives `HeapOom` (exit 92) and the correct form exit 0
- [ ] **the hook for the real gate.** The compiler's cycle 1.5.1b step 0 builds `NPK_HEAP_STATS`, an allocator-level instrument reporting `allocated`, `peak_live` and `count` for **managed** memory, plus a `cost` harness stage. Run on this repository's own two container probes it reported **`peak_live` 41 321 bytes against 400 101 320**. At the re-pin, this checklist item becomes a **`peak_live` assertion** with a stated bound per test, and the `ulimit -v` cap above is retired to a belt. Write the tests now so the bound is the only thing that has to be added

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
