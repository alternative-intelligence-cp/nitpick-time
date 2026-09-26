# `harness/` — the build and test runner

Python, because `npkg` cannot build a library yet
(`../meta/specs/BUILD.md` §1) and zero-dependency governs the artifact, not the
workbench. It retires into `npkg` the way `bootstrap/harness/` does in the
compiler repository, with both running side by side and a parity check first
(TM-003).

```
$ NPKC=… NPKRT=… python3 harness/run.py [--only SUBSTRING] [--quick]
                                        [--verdicts PATH] [--root DIR]
```

## The files

| File | What it is |
|---|---|
| `manifest.py` | `nitpick.toml`, parsed and **schema-checked in both directions** — an unknown key is named and refused, a required key that is missing is named too. P-12: nothing here hardcodes a path, a flag or a version |
| `toolchain.py` | asks `llc`, `opt` and `ld.lld` their versions and holds each to `[toolchain] llvm` **exactly**. It asks the three tools it invokes, and not `llvm-config`, which ships in a `-dev` package the build never needs |
| `elf.py` | the ELF64 symbol table, read with `struct`. The undefined-symbol scan and the runtime allowlist. **Read its header before citing the scan as a guarantee** |
| `build.py` | the pipeline — `npkc` → `opt` → `llc` → scan → `ld.lld` — every argv built from the manifest's flag lists (B-1) |
| `stages.py` | the marker grammar, and the `program`, refusal, `parse`, `golden` and `sweep` stages — and, since cycle 0.1.4b, the `heap:` and `cap:` markers: the runtime's own `NPK_HEAP_STATS` line held to a file's bounds, and the address-space belt with the floor program as its control (`TESTING.md` V-17) |
| `checks.py` | the **tree checks** — `TESTING.md` §2's family, each one diffing the library against a document that describes it |
| `arms.py` | `check_failsafe_arms`: the S-6 arm generator, and `NITPICK-REACH-003` as its oracle |
| `repro.py` | B-4: two builds of one tree must be the same bytes. Also a command in its own right, with `--between` for `check_tables_regenerate` |
| `selfcheck.py` | **the only thing here that demonstrates the checks can fail.** V-14's nine cases, the tree checks on planted violations, and the arm generator against the compiler |
| `run.py` | the driver: stage order, per-unit verdict lines, the summary and its counts |

## The stage order, and each line is a reason

```
1  self-check   V-15: a harness that has not proven it can fail has not proven
                anything, so this is FIRST and its failure is fatal
2  manifest     nothing else can start; every path and flag comes from it
3  toolchain    a wrong `llc` makes every later result meaningless
4  tree sweep   cheap, and it is the check that finds files no test owns
5  tree checks  the documents diffed against the tree, before anything builds
6  parse        every `.npk` in front of the real parser, each exactly once
7  library      one build per run, and it is a check in its own right
8  repro        before the suite, because it builds the library again
9  suite        the `[[test]]` entries, in manifest order
```

## The self-check, which is the load-bearing half

`selfcheck.py` plants a fault, runs **this runner** against a scratch tree under
`.internal/scratch/selfcheck/` with `--root`, and requires a **red** run that
names it. Three parts:

- **V-14's nine cases** — a wrong `expect-exit`, a missing code, an unexpected
  code (D-237), a golden differing by one byte, a file that does not parse, a
  sweep that ran short, a program whose `failsafe` has been deleted, and —
  since cycle 0.1.4b — a program whose managed memory disagrees with its
  header, five ways beside one control (TM-187). Case 6
  (a generator differing by one line) is **pending until 0.5** and prints as
  pending rather than passing.
- **Twenty-three planted violations across the tree checks** — each check
  shown red on a violation and silent on a clean control, in milliseconds, with
  no compilation. *(This bullet said "nine" from cycle 0.0.3, when it was true,
  to 0.1.1, "twenty" at 0.1.1 and "twenty-one" at 0.1.2; the run prints the
  number, derived from `selfcheck.TREE_PLANTS`, and it is 20 since
  `check_literal_divisors` brought four rows — TM-163 — 21 since cycle 0.1.2
  gave `check_denominators` a row for a sweep's declared domain — TM-168 — and
  23 since cycle 0.1.3b gave `check_no_owning_fields` an owning element and an
  owner two structs down — TM-177.)*
- **The S-6 arm generator** diffed against `NITPICK-REACH-003`'s own identity
  list on three modules whose bills cycle 0.0.0 measured.

**Every case carries a CONTROL in the same run.** Without one, a red proves only
that *something* went wrong — the tree, the manifest, the toolchain — and a
self-check satisfied by a broken harness is worse than none.

`--root` exists for this and nothing else. An inner run skips the self-check
(it would not terminate otherwise) and says so.

**Two of the faults it found on its own first runs were in its own fixtures**,
which is the argument for the control half in one sentence: an `npkc` wrapper
that renamed `@npk_failsafe` to `@npk_failsafe_DELETED` left the belt's
substring intact, so the fault was planted and the check sailed past; and
`invoke()` built the child environment and never passed it, so case 8 ran its
control twice and reported that nothing had been caught. It was right.

## Four things worth knowing before you trust a green run

**The library object is linked into nothing** (TM-117). `npkc` takes one root
and emits the whole module graph it reaches, prelude included, so there is no
separate compilation and `ld.lld p.o ntime.o npkrt.o` is a duplicate-symbol
error. Step 7 builds the library because *building it is a check*; every program
in step 9 carries its own copy of everything. That costs about 2.5 s per program
and it is printed rather than hidden.

**The undefined-symbol scan cannot FLAG a syscall** (TM-118, TM-153, RX-120).
`npk_sys6` is the runtime's own trampoline, so it is in the allowlist by
construction. The scan supports B-2's claim — no C, ever — and nothing wider.
**`check_purity` is a SOURCE-level check and is the only thing in this
repository that answers "did this module touch the kernel".** Do not cite one
for the other.

**The `parse` stage asks `npkc`, not `tools/parse_check`** (TM-123). Those
frontend tools are `.npk` source files; building one is building the compiler,
from a tree that moves ahead of our pin. The stage roots every file at the
pinned `npkc` and reads the diagnostic's code *family* — `LEX` and `PARSE` are
the parse phase, everything else is later, so a file refused at `TYPE-009` or
`REACH-002` necessarily parsed.

**A `--only` or `--quick` run concludes nothing.** Each says so twice, at the
top and at the bottom, and neither will print the unqualified word `GREEN`.
CI passes no flags, and that is a rule (TM-125, B-9b) asserted by the workflow
against the summary line rather than left to review.

## What a green run does NOT mean

- **Not that the WHOLE library works.** `src/core/` is real code since cycle
  0.0.4 and `src/cal/` since 0.1.0 — the civil types, Hinnant's two algorithms
  since 0.1.1, swept over the whole range since 0.1.2 — and the suite is
  evidence about both; the other four `src/` directories are still
  placeholders, so nothing here converts a time to a zone, a timestamp to a
  date, or text to either. *(This read "there is none yet; `src/` is
  placeholders" for two subcycles after `src/core/` landed — C6. And until
  cycle 0.1.2 it read "the other five `src/` directories are still
  placeholders, so nothing here dates anything" — false since 0.1.0 gave
  `cal/` a body, and since 0.1.1 converted a date to a day; the CI header
  carried the same sentence, found at 0.1.2's planning, and this one and
  `run.py`'s by the sweep for it.)*
- **Not a MEMORY result for the managed half — except for the files whose
  headers bound it.** D-151's exit-0 trap counts `wild` allocations and a
  `buffer` is managed (TM-106), so exit 0 says nothing about `Bytes`
  (`SAFETY.md` S-18b). Since cycle 0.1.4b the files whose headers bound it are
  held to the runtime's own `NPK_HEAP_STATS` count on both legs — eight
  <!-- [[sweep: heap_bounded=8]] --> since cycle 0.1.3c, six until then — and
  six of them <!-- [[sweep: cap_belted=6]] --> again under a 64 MiB cap
  (`TESTING.md` V-17); every other file's managed memory is asserted by
  nothing.
- **Not that a view into a `Bytes` is used correctly.** Every gate here is a
  leak gate and a use-after-free is a WRONG ANSWER (S-18e, TM-139). Two shipped
  in cycle 0.0 and both were found by reading, not by a gate — and a third
  shipped with them, `bytes_take`'s answer, found at cycle 0.1.4b by the heap
  instrument's COUNT (S-18f).
- **Not that the tree checks have anything to check.** Fourteen are live and
  several report `0` over a small denominator, which is the right answer and is
  why the denominator is always printed (V-1b). Four print as `PEND` with the
  cycle that turns them on. *(Fourteen were live from cycle 0.1.0 to 0.1.0b —
  `check_civil_literal` — and this said thirteen; thirteen was true again
  after 0.1.0c retired that check, TM-158; and cycle 0.1.1's
  `check_literal_divisors`, TM-163, makes fourteen.)*
- **Not that CI is green.** Until cycle 0.0.6 this repository had never pushed,
  so the workflow had never run; the 0.0 close is its first.

## Cost, re-measured at cycle 0.0.6 at pin `aaffb87`

| Step | Wall |
|---|---|
| self-check (7 planted cases, 14 tree-check violations, 3 arm specimens, the verdict mechanisms) | ~34 s |
| tree checks | < 1 s |
| parse (78 files) | ~7 s |
| defect corpus (21 units) | ~9 s |
| library + repro + suite (41 units) | ~12 s |
| **full invocation** | **62 s** |

**It was 184 s at cycle 0.0.3 and this table said so until 0.0.6 — a factor of
four out, over denominators (50 files, 27 units) that had also moved (C5).**
Two things changed and they pull opposite ways. The compiler's 1.5.2d close
made every emitted module carry only the prelude functions it references, which
took a full invocation from **241 s to 43 s** at unchanged content — that is
the whole of the speed-up, same units, same verdicts. Cycle 0.0.6 then added 21
defect-corpus units, one unit test, six placeholder modules per self-check
scratch tree and a fourth self-check part, which put ~19 s back.

**At compiler `c3bdae2`, cycle 0.1.0b, the table's rows are the same steps over
larger denominators, and its times are not re-quoted.** A full invocation is
**70 units**: the self-check's 7 planted cases (case 6 still `PEND`), 18
tree-check violations with 18 clean controls, 3 arm specimens and the verdict
mechanisms; parse over 83 files; the defect corpus at 24 units, all asserted;
and library + repro + suite at 46 (34 probe, 11 unit, 1 conformance). The wall
clock moves from run to run by more than any one change adds, which is why
`meta/roadmap/0.1/0.1.0.md` stopped quoting it; the unit count is the number to
compare.

**At cycle 0.1.0c, the same pin, 75 units**: the self-check's 7 planted cases,
**16** tree-check violations with 16 clean controls (`check_civil_literal`'s two
plants and two controls retired with it, TM-158), 3 arm specimens and the
verdict mechanisms; parse over 88 files; the defect corpus at 24; and library +
repro + suite at 51 (39 probe — five new, `probe16`…`probe16e` — 11 unit, 1
conformance). `75 = 24 + 51`, as `70 = 24 + 46` was.

**At cycle 0.1.1, the same pin, 78 units**: the self-check's 7 planted cases,
**20** tree-check violations with 20 clean controls (`check_literal_divisors`'
four, TM-163), 3 arm specimens and the verdict mechanisms; the tree checks at
`11 live`; parse over 91 files; the defect corpus at 24; and library + repro +
suite at 54 (39 probe, 14 unit — three new, `range_constants`,
`day_number_vectors` and `days_to_date_refused` — 1 conformance).
`78 = 24 + 54`.

**At cycle 0.1.2, the same pin, 81 units**: the self-check's 7 planted cases,
**21** tree-check violations with 21 clean controls (`check_denominators`' row
for a sweep's declared domain, TM-168), 3 arm specimens and the verdict
mechanisms; the tree checks at `11 live`; parse over 94 files; the defect
corpus at 24; and library + repro + suite at 57 (39 probe, 14 unit, **3
sweep** — `every_day_number`, `every_civil_date` and `every_month_length`,
the stage's first members, TM-166 — 1 conformance). `81 = 24 + 57`. **The
`sweep` stage is the one step whose cost is stated**, because B-9's "seconds,
not minutes" rests on it: its three units took **4.5 s** together — 2.1 +
1.9 + 0.5 s, both legs, compile included, the run's own per-unit figures —
against a 30 s threshold `meta/roadmap/0.1/0.1.2.md` §6 set in advance.

**At cycle 0.1.3, the same pin, 86 units**: the self-check unchanged — its 7
planted cases, 21 tree-check violations with 21 clean controls, 3 arm
specimens and the verdict mechanisms; the tree checks at `11 live`; parse over
99 files; the defect corpus at 24; and library + repro + suite at 62 (39
probe, 17 unit — three new, `derived_field_vectors`, `ordinal_to_date_refused`
and `iso_week_to_date_refused` — **5 sweep** — `every_ordinal_date` and
`every_iso_week_date` joined the three, TM-174 — 1 conformance).
`86 = 24 + 62`. The `sweep` stage's five units took **16.5 s** together —
2.7 + 1.9 + 7.9 + 0.5 + 3.5 s, both legs, compile included, the run's own
per-unit figures — against a 30 s threshold `meta/roadmap/0.1/0.1.3.md` §8 set
in advance; the ISO week member is the long pole.

**At cycle 0.1.3b, the same pin, 90 units**: the self-check's 7 planted cases,
**23** tree-check violations with 23 clean controls — `check_no_owning_fields`
gained an owning element and an owner two structs down (TM-177) — 3 arm
specimens and the verdict mechanisms; the tree checks at `11 live`; parse over
106 files; the defect corpus at **28 = 3 exempt + 25 asserted** — O-N20's
`fixed_move_out/`, three reproductions exempt at their recorded verdicts
(`run:107`, `run:107`, `run:95`) and its control asserted — with `exemption
verdicts: 6 of 6`; and library + repro + suite at 65 (42 probe — `probe17`,
which runs, and `probe17b` and `probe17c`, refused `TYPE-046` — 17 unit,
5 sweep, 1 conformance). `90 = 25 + 65`. No library code changed, and the five
sweeps took 2.8 + 2.0 + 7.9 + 0.5 + 3.5 = 16.7 s, as at 0.1.3 within noise.

**At cycle 0.1.4, the same pin, 91 units**: the self-check unchanged — its 7
planted cases, 23 tree-check violations with 23 clean controls, 3 arm
specimens and the verdict mechanisms; the tree checks at `11 live`; parse over
108 files; the defect corpus at 28 = 3 exempt + 25 asserted; `exemption
verdicts: 7 of 7` — the civil cross-oracle's corpus,
`tests/fixtures/civil/civil_oracle.npk`, named at `none`, a data module the
`parse` stage roots and no stage runs (TM-181); and library + repro + suite
at 66 (42 probe, 17 unit, **6 sweep** — `every_oracle_date` joined, the
cross-oracle against Python's `datetime`, TM-179 — 1 conformance).
`91 = 25 + 66`. No library code changed, and the six sweeps took 2.8 + 2.0 +
8.0 + 0.5 + 5.4 + 3.5 = 22.2 s, against the 30 s threshold
`meta/roadmap/0.1/0.1.4.md` §8 set in advance.

**At cycle 0.1.4b, no unit added**: the unit count is the subcycle's before
it, because nothing joined the suite — what changed is what six units assert
and what the self-check plants. The self-check plants **8** of V-14's **9**
cases: case 9, a program whose managed memory disagrees with its header,
joined (TM-187). The tree checks still run `11 live`, and `check_denominators`
measures two more denominators, `heap_bounded` and `cap_belted`. The two twin
pairs and the two `Bytes` tests carry `heap:` bounds on the runtime's own
`NPK_HEAP_STATS` line, and the twins a `cap:` belt under 64 MiB, each unit's
verdict line printing what it measured (`TESTING.md` V-17).

**At cycle 0.1.4c, compiler `c970483`, 101 units**: the self-check unchanged
— 8 of V-14's 9 cases, 23 tree-check violations with 23 clean controls, 3 arm
specimens and the verdict mechanisms; the tree checks at `11 live`; parse
over 116 files, `86 + 28 + 2`; the defect corpus at **36 = 1 exempt + 35
asserted** (20 run, 15 refusal) — O-N20's three reproductions asserted as
`NITPICK-TYPE-084` refusals now that the compiler refuses the move, and O-N23's
seven cases joined as `fixed_import_scope/`, beside their exempt declaring
module; `exemption verdicts: 5 of 5`; and library + repro + suite at 66,
unchanged. `101 = 35 + 66`. The unchanged tree at the new pin had run `RED --
90 unit(s) of 91`: the three exemptions expiring, as designed, and
`probe13d` refused (`meta/roadmap/0.1/0.1.4c.md` §1). No library code
changed, and the six sweeps' and six bounded files' numbers are the same at
both pins — the runtime is the same object.

**At cycle 0.1.3c, the same pin, 112 units**: the self-check unchanged — 8 of
V-14's 9 cases, 23 tree-check violations with 23 clean controls, 3 arm
specimens and the verdict mechanisms; the tree checks at `11 live`; parse over
127 files, `90 + 35 + 2`; the defect corpus at 36 = 1 exempt + 35 asserted,
now **19 run, 16 refusal** — `generic_owning_copy/case5` is refused
`NITPICK-TYPE-017` where it ran to 11 (TM-194); and library + repro + suite at
**77** (**49 probe** — `probe16f`, `probe16g`, `probe16h`, `probe16i`,
`probe18b` and `probe19` refused, `probe18` run — **21 unit** — `vec_moves`,
`vec_at_pod` and the churn pair `vec_churn_pop` and `vec_churn_clear` — 6 sweep,
1 conformance). `112 = 35 + 77`. The churn pair adds about 3.4 s on each full
run, its two capped runs included; no sweep's cost moved.

The floor under all of it is still TM-117's: every root re-emits the prelude,
so a `npkc` invocation on anything that compiles costs a fixed amount and the
run makes about 200 of them. One that does *not* compile costs ~0.03 s.
