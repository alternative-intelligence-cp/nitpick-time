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
| `stages.py` | the marker grammar, and the `program`, refusal, `parse`, `golden` and `sweep` stages |
| `checks.py` | the **tree checks** — `TESTING.md` §2's family, each one diffing the library against a document that describes it |
| `arms.py` | `check_failsafe_arms`: the S-6 arm generator, and `NITPICK-REACH-003` as its oracle |
| `repro.py` | B-4: two builds of one tree must be the same bytes. Also a command in its own right, with `--between` for `check_tables_regenerate` |
| `selfcheck.py` | **the only thing here that demonstrates the checks can fail.** V-14's eight cases, the tree checks on planted violations, and the arm generator against the compiler |
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

- **V-14's eight cases** — a wrong `expect-exit`, a missing code, an unexpected
  code (D-237), a golden differing by one byte, a file that does not parse, a
  sweep that ran short, and a program whose `failsafe` has been deleted. Case 6
  (a generator differing by one line) is **pending until 0.5** and prints as
  pending rather than passing.
- **Nine planted violations across the tree checks** — each check shown red on a
  violation and silent on a clean control, in milliseconds, with no compilation.
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

**The undefined-symbol scan cannot see a syscall** (TM-118, RX-120).
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

- **Not that the library works.** There is none yet; `src/` is placeholders.
  The first computation is `src/core/` at 0.0.4.
- **Not that the tree checks have anything to check.** Nine are live and most
  report `0` over a small denominator, which is the right answer and is why the
  denominator is always printed (V-1b). Four print as `PEND` with the cycle that
  turns them on.
- **Not that CI is green.** This repository pushes at a cycle's end.

## Cost, measured at cycle 0.0.3 on the workbench

| Step | Wall |
|---|---|
| self-check (8 cases, 9 planted violations, 3 arm specimens) | 78.3 s |
| tree checks | 4.2 s |
| parse (50 files) | 40.1 s |
| library + repro + suite (27 units) | ~61 s |
| **full invocation** | **184 s** |

78.3 + 4.2 + 40.1 + 61.4 = 184.0. The floor under all of it is TM-117's: every
root re-emits the prelude, 844 793 B of IR for a library that computes nothing,
so a `npkc` invocation on anything that compiles costs ~0.8 s and the run makes
about 130 of them. One that does *not* compile costs 0.03 s.
