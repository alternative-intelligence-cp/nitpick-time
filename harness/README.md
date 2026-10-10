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
| `manifest.py` | `nitpick.toml`, parsed and **schema-checked in both directions** — an unknown key is named and refused, a required key that is missing is named too. P-12: nothing here hardcodes a path, a flag or a version. Since cycle 0.2.0a `[toolchain]` carries `triple` and `datalayout`, as `npkg` requires (TM-209) |
| `toolchain.py` | asks `llc`, `opt` and `ld.lld` their versions and holds each to `[toolchain] llvm` **exactly**. It asks the three tools it invokes, and not `llvm-config`, which ships in a `-dev` package the build never needs. And since cycle 0.2.0a `check_target` holds `[toolchain] datalayout` to what the pinned `opt` derives from `triple` (`BUILD.md` B-1a, TM-209) |
| `elf.py` | the ELF64 symbol table, read with `struct`. The undefined-symbol scan and the runtime allowlist. **Read its header before citing the scan as a guarantee** |
| `lexical.py` | **the harness's one reading of `.npk` source** (cycle 0.1.5, `TESTING.md` V-1k): every `.npk` file is opened here as bytes, and read as code — comments and literals blanked, `use` paths decoded — by the compiler lexer's rules. `nitpick-regex`'s reader, its code ported statement for statement |
| `build.py` | the pipeline — `npkc` → `opt` → `llc` → scan → `ld.lld` — every argv built from the manifest's flag lists (B-1); and since cycle 0.2.0a every emission's two `target` lines held to the manifest's pins, in `Build.emit` (B-1a, TM-209) |
| `stages.py` | the marker grammar, and the `program`, refusal, `parse`, `golden` and `sweep` stages — and, since cycle 0.1.4b, the `heap:` and `cap:` markers: the runtime's own `NPK_HEAP_STATS` line held to a file's bounds, and the address-space belt with the floor program as its control (`TESTING.md` V-17) |
| `checks.py` | the **tree checks** — `TESTING.md` §2's family, each one diffing the library against a document that describes it |
| `arms.py` | `check_failsafe_arms`: the S-6 arm generator, and `NITPICK-REACH-003` as its oracle |
| `repro.py` | B-4: two builds of one tree must be the same bytes. Also a command in its own right, with `--between` for `check_tables_regenerate` |
| `selfcheck.py` | **the only thing here that demonstrates the checks can fail.** V-14's thirteen cases, the tree checks on planted violations, the arm generator against the compiler, the verdict mechanisms, and — since cycle 0.1.5 — the reader against the compiler's lexer (part E), and since cycle 0.2.3a `check_constants_named`'s literal reader against its numeric scan |
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
names it. Five parts *(this said "Three parts" and listed three until cycle
0.1.5, when the fifth joined; the fourth, the verdict mechanisms, had been
running unlisted since cycle 0.0.6)*:

- **V-14's thirteen cases** — a wrong `expect-exit`, a missing code, an unexpected
  code (D-237), a golden differing by one byte, a file that does not parse, a
  sweep that ran short, a program whose `failsafe` has been deleted, since
  cycle 0.1.4b a program whose managed memory disagrees with its header, five
  ways beside one control (TM-187), and since cycle 0.2.0a a layout pin `opt`
  does not derive, a tree pinned consistently to another target (TM-209), and
  a code named once for two sites and three times for two (TM-210). Case 6
  (a generator differing by one line) is **pending until 0.5** and prints as
  pending rather than passing.
- **One hundred and sixteen planted violations across the tree checks since
  cycle 0.3.2** (one hundred and twelve from cycle 0.3.1, one hundred and six
  after its first step, ninety-five from
  cycle 0.3.0, ninety-two from cycle 0.2.4a, eighty-two from cycle 0.2.3a,
  forty-four from cycle 0.1.5's second half, forty after its first half,
  twenty-three before it; 0.3.2's four are `check_call_edges`' three — a
  generic function no emission holds an instance of, an instance reaching the
  kernel, and no instances' emission where `src/` declares a generic — and
  `check_wide_types`' wide instance in the instances' emission (TM-254);
  0.3.1's second step's six are `check_purity`'s
  five — a thread count, an error's chain and a standard stream, which its six
  names passed, `open` beside a pure `reopen`, and a method of a banned name —
  and `check_host_isolation`'s `HostClock`; its first step's eleven
  are `check_call_edges`' eight — a runtime symbol outside the allowlist
  called directly and through the prelude, a call into `host`, inline
  assembly, a call through a value, a declared function the emission lacks,
  a stale row and the reader's own control — and `check_wide_types`' three,
  a call's wide result, a wide module-level value and a generic's wide
  instance, each plant an emission's text;
  0.3.0's three are `check_int128_sites`' wide literals, one in a function
  and one at module level, and `check_layering`'s `host` importing `fmt`
  beside `host` importing `span`; 0.2.4a's ten are
  `check_constants_named`'s six — a `core` number in `core` outside
  `limits.npk`, a `cal` number in `core`, a bound spelled by its value, the
  folded minimum by its value, a small bound left to review, and an
  initializer it cannot read — and `check_no_view_returns`' two optionals and
  `check_int128_sites`' two wider types; 0.2.3a's thirty-eight are
  `check_check_registry`'s six, `check_no_view_returns`' five and its
  exemption's five,
  `check_int128_sites`' six, and `check_constants_named`'s sixteen — its
  literal reader's fifteen and the owner of 1 000 000 000; the 0.1.5 first
  half's seventeen are V-1k's reader rows and V-1l's token rows, the second
  half's four `check_error_budget`'s module-qualified pair (TM-203),
  `check_raw_index`'s line end after the dot (V-1l) and a written arm bill for
  `check_denominators` (TM-205)) — each check shown red on a violation and
  silent on a clean control, in milliseconds, with no compilation. *(This bullet said "nine" from cycle 0.0.3, when it was true,
  to 0.1.1, "twenty" at 0.1.1 and "twenty-one" at 0.1.2; the run prints the
  number, derived from `selfcheck.TREE_PLANTS`, and it is 20 since
  `check_literal_divisors` brought four rows — TM-163 — 21 since cycle 0.1.2
  gave `check_denominators` a row for a sweep's declared domain — TM-168 — and
  23 since cycle 0.1.3b gave `check_no_owning_fields` an owning element and an
  owner two structs down — TM-177.)*
- **The S-6 arm generator** diffed against `NITPICK-REACH-003`'s own identity
  list on four modules — three whose bills cycle 0.0.0 measured, and since
  cycle 0.2.0 one that raises an identity it imports (`probe11_relay_lib`).
- **The verdict mechanisms** — `run._verdict` on four specimens, and
  `check_exemptions_live`, `run_defect_corpus` and `check_expect_headers` each
  driven red and silent on a control (`TESTING.md` V-14c; TM-141).
- **The reader, against the compiler's lexer** — since cycle 0.1.5, part E:
  one text of every lexical form read back from a file through `lexical.py`,
  and one program of the forms `selfcheck._FORMS_EXIT` names — each literal's
  value asserted since the close's second half — compiled and run by the
  pinned compiler, which must exit 0 while the reader sees exactly the code
  that ran (`TESTING.md` V-1k, TM-202) — and since cycle 0.2.3a a third
  half: one program of every spelling of a number `check_constants_named`
  reads, each against the plain decimal it must equal, run to 0 while that
  check's literal reader reads each the same (TM-231). A re-pin that moves
  the lexer on one of those forms is a red run; one that moves it on a form
  the program does not hold is not, so the adoption re-reads the compiler's
  lexer anyway.

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
in step 9 carries its own copy of everything. That costs about 0.3 s per
program at compiler `c970483`, both legs, and it is printed rather than hidden.
*(This said about 2.5 s until cycle 0.1.5 — the cost before the compiler's
1.5.2d emitted only the prelude functions a module references.)*

**The undefined-symbol scan cannot FLAG a syscall** (TM-118, TM-153, RX-120).
`npk_sys6` is the runtime's own trampoline, so it is in the allowlist by
construction. The scan supports B-2's claim — no C, ever — and nothing wider.
**`check_purity` is a SOURCE-level check and is the only thing in this
repository that answers "did this module touch the kernel".** Do not cite one
for the other. *(One of two since cycle 0.3.1: `check_call_edges` reads the
calls in the library's emission at step 7, TM-250 — the sentence said "the
only thing" until then. Neither is the symbol scan.)*

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
  evidence about both — and about `src/span/`'s `Instant` since cycle 0.2.0,
  its `Timestamp` since 0.2.1, the conversions between a `Timestamp` and its
  civil reading since 0.2.2, and the `Duration` interop since 0.2.3 — and
  about `src/host/`'s clocks since 0.3.0; the other two `src/` directories
  are still placeholders, so nothing here converts a time to a zone, or
  between a time and text. *(It said three placeholders until cycle 0.3.0,
  "a timestamp to a date" too until cycle 0.2.2, and four placeholders until
  cycle 0.2.0. This read "there is none yet; `src/` is
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
  held to the runtime's own `NPK_HEAP_STATS` count on both legs — six
  <!-- [[sweep: heap_bounded=6]] --> since cycle 0.2.0b, eight from cycle
  0.1.3c until it retired the churn pair (TM-214), six before — and four of
  them <!-- [[sweep: cap_belted=4]] --> again under a 64 MiB cap
  (`TESTING.md` V-17); every other file's managed memory is asserted by
  nothing.
- **Not that a view into a `Bytes` is used correctly.** Every gate here is a
  leak gate and a use-after-free is a WRONG ANSWER (S-18e, TM-139). Two shipped
  in cycle 0.0 and both were found by reading, not by a gate — and a third
  shipped with them, `bytes_take`'s answer, found at cycle 0.1.4b by the heap
  instrument's COUNT (S-18f).
- **Not that the tree checks have anything to check.** Nineteen
  <!-- [[sweep: family_live=19]] --> are live and several report `0` over a
  small denominator, which is the right answer and is why the denominator is
  always printed (V-1b). Three <!-- [[sweep: family_pending=3]] --> print as
  `PEND` with the cycle that turns them on. *(Fourteen were live from cycle
  0.1.0 to 0.1.0b — `check_civil_literal` — and this said thirteen; thirteen
  was true again after 0.1.0c retired that check, TM-158; cycle 0.1.1's
  `check_literal_divisors`, TM-163, made fourteen; and cycle 0.2.3a's
  `check_check_registry`, `check_no_view_returns` and `check_int128_sites`,
  TM-227, TM-228 and TM-230, made seventeen, and the four pending three; and
  cycle 0.3.1's `check_call_edges` and `check_wide_types`, TM-250 and TM-251,
  which `run.py` drives over the library's emission, nineteen.)*
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
`meta/roadmap/done/0.1/0.1.0.md` stopped quoting it; the unit count is the number to
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
against a 30 s threshold `meta/roadmap/done/0.1/0.1.2.md` §6 set in advance.

**At cycle 0.1.3, the same pin, 86 units**: the self-check unchanged — its 7
planted cases, 21 tree-check violations with 21 clean controls, 3 arm
specimens and the verdict mechanisms; the tree checks at `11 live`; parse over
99 files; the defect corpus at 24; and library + repro + suite at 62 (39
probe, 17 unit — three new, `derived_field_vectors`, `ordinal_to_date_refused`
and `iso_week_to_date_refused` — **5 sweep** — `every_ordinal_date` and
`every_iso_week_date` joined the three, TM-174 — 1 conformance).
`86 = 24 + 62`. The `sweep` stage's five units took **16.5 s** together —
2.7 + 1.9 + 7.9 + 0.5 + 3.5 s, both legs, compile included, the run's own
per-unit figures — against a 30 s threshold `meta/roadmap/done/0.1/0.1.3.md` §8 set
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
`meta/roadmap/done/0.1/0.1.4.md` §8 set in advance.

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
`probe13d` refused (`meta/roadmap/done/0.1/0.1.4c.md` §1). No library code
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

**At cycle 0.1.5, the close, the same pin, 112 units**: no test added. The
self-check plants 8 of V-14's 9 cases, **40** tree-check violations with 40
clean controls — the seventeen new are the reader's eight rows and the token
rows' nine (`TESTING.md` V-1k, V-1l) — 3 arm specimens, **4** verdict
specimens, and a fifth part, the reader against the compiler's lexer, which
compiles and runs one program — the close adds about a second to a full
run, measured at planning; the tree checks at
`11 live`; parse over 127 files, `90 + 35 + 2`; the defect corpus at 36 = 1
exempt + 35 asserted; and library + repro + suite at 77. `112 = 35 + 77`. At the
close's planning the six sweeps took 2.8 + 2.0 + 8.1 + 0.5 + 5.5 + 3.6 = 22.5 s,
7.5 s under the 30 s threshold, and `BUILD.md` B-9 says which member crosses it
next.

**At cycle 0.1.5's second half, the same pin, 113 units**: one test added,
`tests/unit/civil_total_edges.npk` (`CALENDAR.md` C-12 asserted at its edges,
the cycle audit's U1). The self-check plants 8 of V-14's 9 cases, **44**
tree-check violations with 44 clean controls, 3 arm specimens, 4 verdict
specimens, and part E's program now thirteen forms, each literal's value
asserted (TM-202); the tree checks at `11 live`, `check_error_budget` counting
module-qualified identities (TM-203) and `check_denominators` 31 measured
denominators, the seven arm bills among them (TM-205); parse over 128 files,
`91 + 35 + 2`; the defect corpus at 36 = 1 exempt + 35 asserted; and library +
repro + suite at **78** (**22 unit**). `113 = 35 + 78`.

**At cycle 0.2.0a, compiler `5fbaf4a`, 113 units**: no test added. The
self-check plants **12** of V-14's **13** cases — 10 and 11 the target pins,
12 and 13 the site count — 44 tree-check violations with 44 clean controls, 3
arm specimens, 4 verdict specimens and part E, which runs 0 at the new pin;
the tree checks at `11 live`; and the library's IR 226 493 B — 228 227 B at
`c970483`, 229 041 B for the unchanged tree at `5fbaf4a` (a `target datalayout`
line and `cstring`'s drop pair), then less `Pod`'s block. The unchanged tree
had run `RED -- 105 unit(s) of 113`: the eight files holding the fifteen
`cstring` copies (`meta/roadmap/done/0.2/0.2.0a.md` §1). No heap figure and no sweep
count moved.

**At cycle 0.2.0b, the same pin, 111 units**: two tests retired — TM-150's
churn pair, `vec_churn_pop` and `vec_churn_clear`, whose `Vec<string>`
`Vec<T: Copy>` refuses (TM-214). The self-check unchanged — 12 of V-14's 13
cases, 44 tree-check violations with 44 clean controls; parse over 126 files,
`89 + 35 + 2`; the defect corpus at 36 = 1 exempt + 35 asserted, `case5` a
refusal at six sites; two twin pairs and the two `Bytes` tests held to their
heap bounds, the twins under the cap; and library + repro + suite at **76**
(**20 unit**). `111 = 35 + 76`. The library's IR is 226 493 B, as it was: the
bound moves no emission. The churn pair's 3.4 s is off every full run.

**At cycle 0.2.0, the same pin, 114 units**: three tests added —
`tests/unit/instant_ops.npk` and the two refusals `probe20` and `probe20b`
(TM-215 … TM-218). The self-check plants 12 of V-14's 13 cases, 44 tree-check
violations with 44 clean controls, **4** arm specimens — the fourth,
`probe11_relay_lib`, raising an identity it imports (TM-217) — and 4 verdict
specimens; `exemption verdicts: 6 of 6`, the relay specimen at `none`; parse
over 130 files, `91 + 37 + 2`; the defect corpus unchanged at 36; the library
reaching **6** sources and its IR **245 637 B**, `span`'s body and
`ClockMismatch`; and library + repro + suite at **79** (**51 probe**, **21
unit**). `114 = 35 + 79`.

**At cycle 0.2.1, the same pin, 122 units**: eight tests added —
`tests/unit/timestamp_construct.npk` and `timestamp_order.npk`, and the six
refusals `probe20c` … `probe20f`, `probe21` and `probe21b` (TM-219 … TM-221)
— and `instant_ops` changed in place, for 0.2.0's test gap. The self-check
unchanged — 12 of V-14's 13 cases, 44 tree-check violations with 44 clean
controls, 4 arm specimens and 4 verdict specimens; `exemption verdicts: 6 of
6`; parse over 138 files, `93 + 43 + 2`; the defect corpus unchanged at 36;
the library reaching 6 sources and its IR **258 249 B**, `Timestamp` and
`timestamp_of`; and library + repro + suite at **87** (**57 probe**, **23
unit**). `122 = 35 + 87`.

**At cycle 0.2.2, the same pin, 126 units**: four tests added —
`tests/unit/utc_vectors.npk` and `civil_to_utc_edges.npk`, and the two members
of cycle 0.2's gate, `tests/unit/sweep/every_day_boundary.npk` and
`every_sampled_second.npk` (TM-222 … TM-225). The self-check's counts
unchanged — 12 of V-14's 13 cases, 44 tree-check violations with 44 clean
controls, `check_constants_named`'s 86 400 row planting in `span` beside the
one copy in `core` since TM-223, 4 arm specimens and 4 verdict specimens;
`exemption verdicts: 6 of 6`; parse over 142 files, `97 + 43 + 2`; the defect
corpus unchanged at 36; the library reaching 6 sources and its IR **270 070
B**, the two conversions; and library + repro + suite at **91** (**57 probe**,
**25 unit**, **8 sweep**). `126 = 35 + 91`. At planning the eight sweeps took
2.9 + 5.3 + 2.1 + 8.1 + 0.6 + 5.6 + 3.6 + 15.1 = 43.3 s — over B-9's 30 s,
under its 60 s, and B-9 is amended to that cost (TM-224) — and a full
invocation about 200 s, some 24 s more than at cycle 0.2.1.

**At cycle 0.2.3a, the same pin, 126 units**: no test added, and `src/`
changed in comments only. The self-check plants 12 of V-14's 13 cases,
**82** tree-check violations with 82 clean controls —
`check_check_registry`'s six, `check_no_view_returns`' five and the five of
its exemption, `check_int128_sites`' six, and `check_constants_named`'s
sixteen, the literal reader's fifteen and the owner of 1 000 000 000 (TM-227
… TM-232) — 4 arm specimens, 4 verdict specimens, and part E's third half,
one program of every spelling of a number, run to 0; the tree checks at
`14 live`, 3 pending, so the summary reads `4 pending` where it read 5; parse
over 142 files, `97 + 43 + 2`; the defect corpus unchanged at 36; and
library + repro + suite at 91. `126 = 35 + 91`. A full invocation about
200 s, as at cycle 0.2.2 within noise: the new plants cost
milliseconds, and part E's third half one compile and run.

**At cycle 0.2.3, the same pin, 131 units**: five tests added —
`tests/unit/duration_ctors.npk`, `duration_days_past_max.npk` and
`duration_days_past_min.npk`, `timestamp_add_edges.npk` and
`timestamp_since_edges.npk` (TM-233 … TM-236) — and `limits_named.npk`
changed in place, for `Duration`'s two ends. The self-check unchanged — 12
of V-14's 13 cases, 82 tree-check violations with 82 clean controls, 4 arm
specimens and 4 verdict specimens; `check_int128_sites` meets its first site
it did not find already written, `timestamp_since`; parse over 147 files,
`102 + 43 + 2`; the defect corpus unchanged at 36; the library reaching 6
sources and its IR **285 881 B**, the interop's six functions; and library +
repro + suite at **96** (**57 probe**, **30 unit**, **8 sweep**).
`131 = 35 + 96`. A full invocation about 205 s; the five units cost a few
seconds together, both legs, compile included.

**At cycle 0.2.4a, the same pin, 131 units**: no test added, and `src/`
changed in comments only. The self-check plants 12 of V-14's 13 cases,
**92** tree-check violations with 92 clean controls — the ten new are
`check_constants_named`'s six, `check_no_view_returns`' two and
`check_int128_sites`' two (TM-238 … TM-240) — 4 arm specimens and 4 verdict
specimens; the tree checks at
`14 live`, 3 pending; parse over 147 files, `102 + 43 + 2`; the defect corpus
unchanged at 36; and library + repro + suite at 96. `131 = 35 + 96`. A full
invocation about 200 s, as at cycle 0.2.3: the new plants cost milliseconds.

**At cycle 0.2.4b, the same pin, 133 units**: two tests added —
`tests/unit/instant_since_edges.npk` and
`tests/probe/probe20g_construction_from_numbers.npk` (TM-242, TM-243) — and
`timestamp_add_edges.npk` changed in place, for `timestamp_add`'s operand check
(TM-241). The self-check unchanged — 12 of V-14's 13 cases, 92 tree-check
violations with 92 clean controls, 4 arm specimens and 4 verdict specimens;
`check_int128_sites` meets `instant_since`, its third written site; parse over
149 files, `104 + 43 + 2`; the defect corpus unchanged at 36; the library
reaching 6 sources and its IR **288 795 B**, `instant_since`'s `int128` and
`timestamp_add`'s two checks; and library + repro + suite at **98** (**58
probe**, **31 unit**, **8 sweep**). `133 = 35 + 98`. A full invocation about
207 s; the two units cost about a second together, both legs, compile
included.

**At cycle 0.3.0, the same pin, 134 units**: one test added —
`tests/unit/host_clocks.npk`, the clocks under `// stress: 40` (TM-249) — and
`src/host/` given its body (TM-247, TM-248), after `check_int128_sites` began
reading a literal's width in a commit of its own (TM-246). The self-check
plants 12 of V-14's 13 cases, **95** tree-check violations with 95 clean
controls — the three new are `check_int128_sites`' two wide literals and
`check_layering`'s `host` importing `fmt` — 4 arm specimens and 4 verdict
specimens; `check_int128_sites` counts 15 wide spellings, `bytes_put_int`'s
`0i128` among them; parse over 150 files, `105 + 43 + 2`; the defect corpus
unchanged at 36; the library reaching **7** sources and its IR **309 729 B**,
`host`'s four readings; and library + repro + suite at **99** (**58 probe**,
**32 unit**, **8 sweep**). `134 = 35 + 99`. A full invocation about 211 s;
the unit costs under a second, both legs and eighty runs, compile included.

**At cycle 0.3.1, the same pin, 134 units**: no test added and `src/`
unchanged. The self-check plants 12 of V-14's 13 cases, **112** tree-check
violations with 112 clean controls — `check_call_edges`' eight and
`check_wide_types`' three, each an emission's text, and `check_purity`'s five
and `check_host_isolation`'s one —
4 arm specimens and 4 verdict specimens; step 7 reads the library's
emission twice, **90** functions of `src/`'s modules, 81 outside
`src/host/`, reaching 15 runtime symbols, every one in the allowlist, and 3
holding an integer wider than `i64`, the three §5 marks; parse over 150 files,
`105 + 43 + 2`; the defect corpus unchanged at 36; the library reaching 7
sources and its IR **309 729 B**; and library + repro + suite at **99**.
`134 = 35 + 99`. A full invocation about 210 s; the two readings of the
emission cost milliseconds.

**At cycle 0.3.2, the same pin, 143 units**: nine tests added —
`tests/unit/generic_instances.npk`, every generic function of `src/`
instantiated (TM-254); `tests/probe/probe22_private_etc.npk`, a program's own
`/etc` (TM-255); and the system zone's seven, `system_zone_etc`, five of `$TZ`
and `system_zone_tz_raw`, forty runs a leg (TM-257) — and `src/host/` given its fifth function
(TM-256). The self-check plants 12 of V-14's 13 cases, **116** tree-check
violations with 116 clean controls — `check_call_edges`' three and
`check_wide_types`' one over the instances' emission — 4 arm specimens and 4
verdict specimens; step 7 emits the instances beside the umbrella and reads
both, **108** functions of `src/`'s modules, 90 outside `src/host/`, reaching
17 runtime symbols, every one in the allowlist, `src/host/` reaching
`npk_environ`, `npk_mono_now`, `npk_ofd_close`, `npk_open`, `npk_read` and
`npk_sys6`; parse over 159 files, `114 + 43 + 2`; the defect corpus unchanged
at 36; the library reaching 7 sources and its IR **366 527 B**; and library +
repro + suite at **108**. `143 = 35 + 108`. A full invocation about 230 s; the
namespace unit's eighty runs cost about 11 s of it, each run a namespace,
thirty machines, the 4 095-byte link and file built byte by byte.

**At cycle 0.3.2a, compiler `7e91730`, 143 units**: no test added. The
self-check's cases 2 and 3 read a refusal of two type codes, the wide literal
being one code at the new pin (TM-259); every other figure as at 0.3.2 — 116
tree-check violations, the 108 functions of `src/`'s modules in the emissions
reaching the same 17 runtime symbols, parse `114 + 43 + 2`, the defect corpus
at 36, every heap figure — but the library's IR, **374 606 B** where it was
366 527 B, and the instances' 79 007 B where they were 78 317 B: a type id one
higher, the prelude's six frac sites, and the derived `Debug` bodies' template
drops. The unchanged tree had stopped at the toolchain check, and with its
LLVM row moved at the self-check and then at 35 units, landing 103's readers
and five headers' counts (`meta/roadmap/0.3/0.3.2a.md` §1). A full invocation
about 230 s at either pin.

The floor under all of it is still TM-117's: every root re-emits the prelude,
so a `npkc` invocation on anything that compiles costs a fixed amount and the
run makes about 200 of them. One that does *not* compile costs ~0.03 s.
