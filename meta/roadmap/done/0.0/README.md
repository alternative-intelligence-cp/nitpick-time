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
- [x] `probe/probe06b_element_leak.npk` and `probe06c_element_drop.npk` — **added 2026-09-04.** The TM-106 leak pair, restored as committed files: 0.0.0 measured them in scratch and committed only the numbers, so at the re-pin there was nothing to re-run. They differ in one line and **both exit 0**. Re-measured **unchanged** (125 184 KiB; `HeapOom` at a 64 MiB cap), which is the finding — D-246 and D-247 do not touch this. **The remedy half's "under 768 KiB" was WRONG and is corrected at 0.0.4 (TM-128, TM-131): peak RSS 1 660 KiB, and exit 0 at the same 64 MiB cap the leaking half takes 92 at.** Below ~2.8 MiB nothing on this machine execs, `/bin/true` included, so no run was ever "clean at 768"
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
- [x] every `src/` subdirectory has a placeholder module that parses, so the `parse` stage has something to sweep — six, each naming its spec, its cycle and what it may import; `host/`'s carries the purity rule. All seven `src/` files compile at 844 793 B of IR. ~~and `harness/run.py` **asserts the count is at least 7**~~ — **STRUCK AT 0.0.6, AND IT WAS NEVER TRUE (D1, TM-142).** No such assertion was in the tree: 0.0.2 replaced `run.py` rather than extending it and the minimum went with the old file, so the stated failure mode — *a directory whose placeholder was deleted rather than replaced is invisible to the sweep* — was live for four subcycles inside this ticked box. **A magic minimum was the wrong repair anyway**, since it goes stale the moment a directory is added. `check_layering` now asserts the rule the sentence was really about: **every layer B-17 names holds at least one module**, planted separately in the self-check because the fault is a file that is NOT there
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
- [x] the `parse`, ~~`accept`~~, `check` and `golden` stages, with the **exact-code** rule (B-7). **`accept` is STRUCK and the strike is a decision, TM-124**: `BUILD.md` B-4b and `TESTING.md` §1 both already said this library does not use it, and the specifications are the authority (TM-002). It is refused **by name with its reason**, which is a different refusal from "not implemented yet" — *"not yet"* invites a later session to add the one stage whose shape (*"accepted in silence"*) this repository holds the reproduction against. `parse` is a **whole-tree** stage rather than a `[[test]]` entry and asks `$NPKC` rather than the compiler's `tools/parse_check`, which is a `.npk` source file importing twenty frontend modules — **TM-123**, measured
- [x] the `sweep` stage, and `--quick` that skips it **with a loud line** — through the SAME `Report` object as every other verdict, so a `SKIP` line lands in `--verdicts` too and the transcript and the summary cannot disagree about what ran
- [x] `--only`, and output that says twice that a filtered run concludes nothing. **`--quick` says it twice as well**, and neither will print the unqualified word `GREEN`
- [x] O-X5 decided: **TM-125, no** — struck through in `meta/OPEN_QUESTIONS.md` with its number. The recorded reason is deliberately *not* "the sweeps are cheap", which would stop being an argument the moment one got slow — which is exactly when somebody would reach for the flag
- [x] `harness/selfcheck.py` with all seven cases from `specs/TESTING.md` V-14 — six live, **case 6 pending until 0.5** and printed as `PEND` rather than passing — including case 7, **a silently skipped sweep**. Case 7 needed a new marker to be answerable at all: `// sweep-count: N` plus a `swept <N>` line from the program (**TM-122**), because an exhaustive loop that returns early exits 0 exactly like one that ran
- [x] the self-check runs **first** in every full invocation, and its failure is **fatal** — nothing below it runs
- [x] `check_layering`, `check_error_budget`, `check_constants_named`, `check_no_owning_fields` live (several will have nothing to check yet, which is the right answer, not a reason to skip). **And each is COMMISSIONED**: `selfcheck.py` §B plants a violation per check and requires it to be found, then runs the same check over a clean control and requires silence — 9 plants, 10 controls, on every run
- [x] **`npkc` exit 0 is not "well-formed"** — the `program` stage runs all four steps (`npkc`, `llc`, `ld.lld`, run) **and** asserts `grep -c '^define i32 @npk_failsafe'` is 1; it does both rather than either. **The parenthetical in `SAFETY.md` §2 that said REACH-003 is "not in the pinned toolchain" was stale and is amended**: at `0dfddac` `case1_no_failsafe.npk` IS refused `NITPICK-REACH-003`, exit 1, no `.ll`. The constraint stands anyway, and for a better reason than the one given — a rule justified by "our compiler does not do this yet" evaporates the day it does, taking the belt with it
- [x] **`selfcheck.py` gains an eighth case**: a program whose `failsafe` has been deleted. Driven through an `npkc` **wrapper** that renames the define after emission, because at this pin the source-level spelling no longer reaches the belt — the technique 0.0.2 used for the symbol scan, with the positive control through the identical code path
- [x] `check_failsafe_arms` / the S-6 generator built to TM-107's three constraints. **And the compiler is its oracle**: `NITPICK-REACH-003` LISTS the identities owed, so the generated table is diffed against that list in both directions — which is what makes constraint 3 ("and no more") mechanical rather than aspirational, since a superset compiles and no build would ever say so. **Six rows generated today**, not "0 of 0", and calibrated against the three support modules at 4 / 5 / 8 arms
- [x] `tests/probe/support/` and `tests/probe/defect/` **excluded from the probe glob**, each with the reason written next to it — already true at 0.0.1 and **re-verified by reading `nitpick.toml` and by the run's own denominators**: `probe: 26 of 26`, and `50 = 7 src/ + 26 probe + 3 support + 13 defect + 1 conformance`. The `parse` stage is what now covers the 16 the glob excludes
- [x] **`check_raw_index`** — no `.items[` outside `src/core/vec.npk` and no
      `.ptr[` outside `src/core/bytes.npk`. `Vec<T>.items` and `Bytes`' buffer
      body are **bare pointers**, which the language does not bounds-check
      (TM-108, `SAFETY.md` S-17b), so the accessor pair is the only bound there
      is and this check is what keeps it that way
- [~] `check_purity` and `check_host_isolation` ~~written now and dormant~~ — **written now and LIVE, TM-126**, which supersedes P-21's dormancy half and keeps its reasoning. `src/host/` already exists, so both run today over six files and report `0` with the denominator printed; and being pure functions of a directory they are commissioned in the same pass. **0.3 therefore inherits a check that is on and has been red**, rather than one to switch on. The clean control is not decoration: `src/host/host.npk`'s own header names `mono_now()` and `src/lib.npk`'s names `host_now_utc`, both in prose, so a check that read comments would fail this repository on its own documentation — and the first draft did

### 0.0.4 — `src/core/`
- [x] `src/core/limits.npk` — **13 constants**, each with the rule that set it. Two beyond §4's table: `NTIME_OFFSET_MIN` (Z-19 states a two-sided range) and `NTIME_DIGITS_MAX`. `tests/unit/limits_named.npk` asserts the RELATIONS between them (`DAY_MAX − DAY_MIN + 1 = 7 304 485`, `SECS_MIN = DAY_MIN × 86 400`, `SECS_MAX = DAY_MAX × 86 400 + 86 399`); the **recomputation** test remains cycle 0.1's, and the difference is stated in the file
- [x] `src/core/vec.npk` — all nine, **at a NON-OWNING `T`** (TM-132). ~~exercised at both `T` shapes~~ — **struck, and the reason is a compiler defect rather than a choice:** O-N17 blocks `T:x = move(v.items[i])` in a generic function at an owning `T`, which is the primitive under **five** of the nine rows. Measured with a non-owning control per case; `tests/probe/defect/generic_element_move/case5`. The owning shape is exercised CONCRETELY instead, where `SAFETY.md` S-18b already puts element lifetime — `probe06`'s `free_names`, `probe12b`'s `vec_set_string`
- [x] `src/core/bytes.npk` — `init`, **`reserve`**, `push`, `extend`, `extend_str`, `put_uint`, `put_int`, `len`, `view`, `take`, `clear`. ~~`free`~~ — **struck (TM-133):** the body is a managed `buffer` and `TYPE_REFERENCE.md` §23 lists `buffer_free` among the things deliberately not landed, so a `bytes_free` could only be a no-op. The reclaim-on-overwrite was **measured**, not assumed: 256 MiB of churn peaks at 1 660 KiB
- [x] `put_uint` allocation-free — `tools/ir_alloc_scan.py`, exit 0, `allocator=NONE` over 549 function bodies — and correct across the digit boundaries and at `uint64` maximum. **The maximum must be a `fixed` constant**: D-148's `0u64 - 1u64` traps as a runtime statement (TM-134)
- [x] `put_int` correct at `int64` **minimum** — `tests/unit/bytes_put_int.npk`, **written before the implementation existed** and run against the absent file (`npkc` exit 1, no `.ll`). It accumulates in the negative direction and never changes the value's sign
- [x] `Bytes` growth amortised linear — `tests/unit/bytes_growth.npk`, a million single-byte pushes in **0.02 s**, reallocation count bounded at **21** (and at ≥ 1, so it cannot pass by over-allocating at birth)
- [x] every accessor's obligation written as a `requires`/`ensures` comment, with tests standing in. **`result` → `answer`**: `result` is a reserved `VerificationKeyword` (TM-130), so the planned spelling could not have compiled even as a comment
- [x] **and the bound is CODE in every accessor, not only a comment** (TM-108, `SAFETY.md` S-17b) — **discharged by TM-129/S-17c, and NOT by two hand-written comparisons.** Each accessor lays a `#wild_slice` over `count` and indexes that, so the guard is the compiler's own `emit_bounds_guard`; one `icmp ult` rejects both ends, because `index_as_i64` sign-extends first. `vec_at_past_end`, `vec_set_past_end` and `vec_pop_empty` each **exit 94**, the negative case is `probe13c`, and `check_raw_index` now reports **0 raw-index sites in the whole library**. The original text follows: `vec_at`/`vec_set` and every `Bytes` accessor check **`0 <= i` as well as `i < count`** — an index derived from a narrower signed field can be negative, `i < count` accepts it, and the read goes backwards off the block. The negative case gets its own test
- [x] the suite's programs exit 0, which asserts that **no `wild` allocation is live** at exit — `Vec<T>`'s block is `wild` (P-23), so an unpaired `vec_free` on any path is a trap rather than a pass (D-151)
- [x] and, because that is the whole of what D-151 covers, a **memory assertion for the managed half** — **and the cap in this item is corrected by TM-131: `ulimit -v` sized *low* measures the loader, not the library.** `probe06c` and `/bin/true` flip at the same cap (2688→2816 KiB). The gate is ONE SHARED 64 MiB cap with opposite outcomes — 92 against 0 — plus the peak-RSS pair. Original text follows: a `Vec<string>` whose block is freed and whose elements are not retains its elements and **still exits 0** (TM-106, measured at 125 MiB over 2 000 000 elements). Until the instrument below exists, each owning-`T` container test runs a second time under a `ulimit -v` cap sized to fail if the elements are orphaned — the form TM-106 itself used, where the orphaning form gives `HeapOom` (exit 92) and the correct form exit 0
- [~] **the hook for the real gate. CARRIED INTO `../../0.1/0.1.0.md` §8 AT THE 0.0 CLOSE, verbatim and with the commissioning order written out** — `NPK_HEAP_STATS` is still not in pin `aaffb87`, so there is still nothing to assert against. It is this cycle's ONE unticked box and 0.0.6's checklist did not carry it forward, so it would have closed by falling off the list (F7). §8 also says what to do if it is still absent when 0.1 closes: carry the section into `0.2.0.md` verbatim. **It has now survived one close by being written down; it will not survive one by being remembered.** The compiler's cycle 1.5.1b step 0 builds `NPK_HEAP_STATS`, an allocator-level instrument reporting `allocated`, `peak_live` and `count` for **managed** memory, plus a `cost` harness stage. Run on this repository's own two container probes it reported **`peak_live` 41 321 bytes against 400 101 320**. At the re-pin, this checklist item becomes a **`peak_live` assertion** with a stated bound per test, and the `ulimit -v` cap above is retired to a belt. Write the tests now so the bound is the only thing that has to be added.
      **STILL OPEN AT 0.0.4, DELIBERATELY — `NPK_HEAP_STATS` is not in the
      pinned toolchain, so there is nothing here to assert against yet. The
      "write the tests now" half IS done:** `probe06b`/`probe06c`,
      `probe12`/`probe12b` and `tests/unit/bytes_growth.npk` are committed, each
      differing from its twin in one line or watching one counter, so the re-pin
      adds a bound and changes no test. **And TM-131 changed what the interim
      belt may claim:** a `ulimit -v` sized near the floor measures the loader,
      not the library, so the belt is one shared 64 MiB cap with opposite
      outcomes rather than a low cap on the clean half alone

### 0.0.5 — the tzdb size spike — **DONE 2026-09-05**
- [x] ~~`tools/gen_tzdb.py`~~ **`meta/scratch/tzdb_spike/`** far enough to read the pinned tzdata release's TZif files and emit the four tables from `ZONE_MODEL.md` §3 — **struck as written and done as P-28 requires**: this checklist named `tools/`, and P-28 says the spike is throwaway and is *named* throwaway, so it lives under `meta/scratch/` with a README whose first line says so
- [x] the emitted `.npk` compiled by `npkc`, and **the object's size measured** — source bytes, IR bytes, and object bytes, plus the linked binary and the **per-symbol table sizes**, which are what the estimate was actually a claim about
- [x] the number recorded in `0.0.5.md` §4 and in `meta/research/tzdb-size.md`, against §3's ≈348 KiB estimate — **475 006 B for the four tables and two pools, 489 310 B with `POSIX_RULES`** (TM-135)
- [x] `#size_of` of each table row asserted, so the estimate's arithmetic is checkable — **and measured first**: two of the three estimated widths were wrong (`ZoneTransition` 12→16, `ZoneEntry` 16→28), so asserting the estimate would have reddened the run instead of correcting the document
- [x] **nothing committed from the spike but the number** — the generator is committed under `meta/scratch/` because a number whose program is not committed is a claim rather than evidence (`PLAYBOOK.md` §6); its two-megabyte emitted `.npk` is **not**, and goes to `.internal/` so the harness never sweeps it
- [x] if the number is above ~1 MiB: **stop** — **it is not.** 477.8 KiB is row one of `0.0.5.md` §3, so O-X2 closes and O-Z1 is settled as "ship them all", with the 4.4% margin written into `ZONE_MODEL.md` as Z-7b
- [x] **not on this list, and it is the more consequential half:** TM-132's restriction was re-examined at the new pin because O-N17 is fixed. It **stays** — `NITPICK-TYPE-046` does not fire inside a generic body, `vec_pop<T>` had shipped a duplicate-owner read and now writes the `move`, and `vec_at<T>` at an owning `T` removes the element (TM-136, `tests/probe/defect/generic_owning_copy/`)
- [x] **nor this:** O-N17's two `EXPECT_EXEMPT` entries had expired and the mechanism that promised to expire them checked only that the file existed. Both files now carry `// expect-exit: 0`, and `check_exemptions_live` re-derives every exemption's recorded verdict on every run (TM-137)

### 0.0.6 — close — **DONE 2026-09-06**
- [~] ~~**delete `meta/scratch/tzdb_spike/`**~~ (P-28) — **KEPT, both halves, with the reason in `0.0.6.md` §4.** 0.0.5's own checklist committed the generator *because a number whose program is not committed is a claim rather than evidence*, so deleting it reverses a decision taken one subcycle earlier and reduces TM-135's 475 006 to a claim. P-28's "throwaway" is discharged by NAMING it throwaway and keeping it out of `tools/`; the expensive part — the two-megabyte emitted `.npk` — was never committed
- [x] every probe verdict recorded, every forced spec amendment landed — **and two had NOT landed**: probe 01's declaration-order verdict was cited to the wrong compiler decision (E2, D-051 for D-123) and probe 13b's `count`-versus-`cap` distinction was stated in S-17c as an absolute three live sites violate (F2). Both now in the specifications
- [x] the harness self-check green, the full run green — **62 units, 62.1 s**, self-check first with 7 planted cases, 14 tree-check violations, 3 arm specimens and the verdict mechanisms
- [x] `meta/DECISIONS.md` updated — **TM-138 … TM-145**, eight decisions, one per audit finding class
- [x] `0.1/0.1.0.md` written execution-grade before the cycle closes — and **it caught a plan error while being written**: `CALENDAR.md` §3 declares NARROW fields (`int32:year`, `uint8:month`) and the first draft wrote `int64`. The specification is the authority (TM-002), so §2 now copies it verbatim and §3 carries the validate-then-narrow rule with `m = 268` as a named test case
- [x] cycle moved to `done/0.0/`, `ROADMAP.md` updated, and **every reference fixed in the same commit** — the audit's B3 warned that two `CITATION_EXEMPT` keys are `meta/roadmap/0.0/…` paths and that `check_specs_current` reported rather than failed, so the move would have broken them in silence. It fails now (TM-145)
- [x] **W-22: all 30 audit findings triaged** — `0.0.6.md` §1

## Gate

**The cycle is complete when**: a full `harness/run.py` is green; the
self-check proves the harness fails seven ways; `src/core/`'s primitives each
have a suite; every probe has a recorded verdict with its consequences written
into the specifications; and **the tzdb's real emitted size is a number in this
repository** rather than an estimate.

### MET, 2026-09-06, at pin `aaffb87` — re-read clause by clause rather than remembered

| Clause | Evidence |
|---|---|
| a full `harness/run.py` green | `GREEN -- 62 unit(s), 0 failures; 5 pending, 62.1 s`, no flags |
| the self-check proves the harness fails **seven** ways | `this runner has been shown able to fail 7 ways (V-14), of the 8 V-14 names` — case 6 is `PEND` until 0.5. **This clause was the only place in the repository with the right number**; five other sites said eight (C3, TM-142) and now read it from `selfcheck.PLANTED_CASES` |
| `src/core/`'s primitives each have a suite | `vec.npk` → `vec_boundaries`, `vec_at_past_end`, `vec_set_past_end`, `vec_pop_empty`; `bytes.npk` → `bytes_put_int`, `bytes_growth`, **`bytes_view_lifetime`** (added at the close, TM-139); `limits.npk` → `limits_named` |
| every probe has a recorded verdict with its consequences in the specifications | `0.0.0.md` §7, re-read at the close. **Two consequences had not landed** and are now in the specifications rather than in a comment or a roadmap file: probe 01's declaration-order rule was cited to D-051 instead of D-123 (E2), and probe 13b's `count`-versus-`cap` distinction was stated in S-17c as an absolute three live sites violate (F2) |
| the tzdb's real emitted size is a number | **475 006 B** for the four tables and two pools, **489 310** with `POSIX_RULES`, against a ≈348 KiB estimate wrong in four independent ways (TM-135). Re-derived independently by the pre-close audit and it closes |

**And one gate clause that had quietly stopped being at risk:** ~~O-N4~~ is
discharged and was still marked **BLOCKING** in `meta/OPEN_QUESTIONS.md` at the
close — re-measured here at 30 000 rows, **1.20 s and 26 900 KiB against
281 s and 30.9 GiB**, with a 2 266 485 B `.ll` carrying all 30 000 rows so the
speed is not bought by emitting less. Struck on this repository's own
measurement, not on the board's report.

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
