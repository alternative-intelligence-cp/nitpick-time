# `harness/` — the build and test runner

Python, because `npkg` cannot build a library yet
(`../meta/specs/BUILD.md` §1) and zero-dependency governs the artifact, not the
workbench. It retires into `npkg` the way `bootstrap/harness/` does in the
compiler repository, with both running side by side and a parity check first
(TM-003).

```
$ NPKC=… NPKRT=… python3 harness/run.py [--only SUBSTRING] [--verdicts PATH]
```

## The files

| File | What it is |
|---|---|
| `manifest.py` | `nitpick.toml`, parsed and **schema-checked in both directions** — an unknown key is named and refused, a required key that is missing is named too. P-12: nothing here hardcodes a path, a flag or a version |
| `toolchain.py` | asks `llc`, `opt` and `ld.lld` their versions and holds each to `[toolchain] llvm` **exactly**. It asks the three tools it invokes, and not `llvm-config`, which ships in a `-dev` package the build never needs |
| `elf.py` | the ELF64 symbol table, read with `struct`. The undefined-symbol scan and the runtime allowlist. **Read its header before citing the scan as a guarantee** |
| `build.py` | the pipeline — `npkc` → `opt` → `llc` → scan → `ld.lld` — every argv built from the manifest's flag lists (B-1) |
| `stages.py` | the marker grammar, and the `program` and refusal stages |
| `repro.py` | B-4: two builds of one tree must be the same bytes. Also a command in its own right, with `--between` for `check_tables_regenerate` |
| `run.py` | the driver: stage order, per-unit verdict lines, the summary and its counts |

## The stage order, and each line is a reason

```
1  manifest    nothing else can start; every path and flag comes from it
2  toolchain   a wrong `llc` makes every later result meaningless
3  tree sweep  cheap, and it is the check that finds files no test owns
4  library     one build per run, and it is a check in its own right
5  repro       before the suite, because it builds the library again
6  suite       the `[[test]]` entries, in manifest order
```

## Three things worth knowing before you trust a green run

**The library object is linked into nothing** (TM-117). `npkc` takes one root
and emits the whole module graph it reaches, prelude included, so there is no
separate compilation and `ld.lld p.o ntime.o npkrt.o` is a duplicate-symbol
error. Step 4 builds the library because *building it is a check*; every program
in step 6 carries its own copy of everything. That costs about 2.6 s per program
and it is printed rather than hidden.

**The undefined-symbol scan cannot see a syscall** (TM-118, RX-120).
`npk_sys6` is the runtime's own trampoline, so it is in the allowlist by
construction. The scan supports B-2's claim — no C, ever — and nothing wider.
`check_purity` is a **source**-level check and is cycle 0.0.3's.

**A `--only` run concludes nothing.** It says so twice, at the top and at the
bottom, because that is what it is for.

## What a green run does NOT mean

- **Not that the library works.** There is none yet; `src/` is placeholders.
  The first computation is `src/core/` at 0.0.4.
- **Not that this runner can fail.** `../meta/specs/TESTING.md` V-14's
  `selfcheck.py` is cycle **0.0.3**, and V-15 puts it first in every full
  invocation. Until it exists, a green run is an *unfalsified* claim rather
  than a tested one.

**Three of its checks have been commissioned by hand**, at 0.0.2, each against a
deliberate fault, each seen red and then green again — the undefined-symbol scan
(an `npkc` wrapper renaming a call target: red, naming
`ntime_c_helper_that_does_not_exist`, exit 1), the toolchain pin (a shim
reporting 20.1.3 for one of the three tools: red, naming which tool, nothing
built, exit 1), and `repro` (a generator whose rows came out of an unsorted
`set`: red at the differing byte, exit 1 — with the same generator under
`sorted()` green through the identical code path, so the red came from the
non-determinism and not from the mechanism). **The transcripts with their exit
codes are in `../meta/roadmap/0.0/0.0.2.md`.** That is three checks, not the
whole runner, and it is weaker than V-14 — which is the point of saying so here.
