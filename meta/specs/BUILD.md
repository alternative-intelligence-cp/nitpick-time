# Building, testing, and the module conventions

How `ntime` is built today, how it will be built when the tooling catches up,
and the file-and-import conventions everything in `src/` follows.

---

## 1. What cannot build this yet, measured

Read at the compiler's commit for cycle 1.5.0 (2026-09-03):

- **`npkg build` is the compiler's own bootstrap ladder.** It assembles
  `runtime/npkrt.ll` and `bootstrap/seed/stage1.ll` into a builder, has that
  builder compile `[build] entry`, scans, links, and names the result `npkc`.
  There is no generic-project path and no `target = "library"` behaviour; the
  key is accepted by the schema and read by nothing.
- **`[dependencies]` resolves to nothing.** The loader's dependency-root list
  (`RootList`, `src/frontend/resolve_path.npk`) is created empty in
  `src/driver/pipeline.npk` and `rootlist_add` is never called from anywhere.
  A `use "ntime/cal.npk"` path — the dependency-root form — therefore resolves
  against an empty set. Only `./` and `../` paths work.
- **`npkg` has no `install` and no `update`.**

None of this is a criticism of `npkg`; D-206 scoped it to the compiler's own
suite. It is written down because a plan that assumes tooling it has not
checked is a plan that discovers the gap at the first step.

**Decision TM-003: `harness/` builds and tests `ntime` until `npkg` can, and
retires into it** — the same relationship `bootstrap/harness/` has to `npkg`,
including both running side by side with a parity check before the older is
retired. Python is not a dependency violation: **zero-dependency governs the
artifact, not the workbench** (the compiler's `ORCHESTRATION.md` §6 says so in
as many words), and the compiler's own harness is Python for the same reason.

---

## 2. The build, step by step

```
src/lib.npk  (and every module it reaches by `use`)
   → npkc              →  build/ntime.ll         the emitted LLVM IR text
   → opt -O2           →  build/ntime.opt.ll     only on the check leg
   → llc               →  build/ntime.o          at the manifest's flags
   → undefined-symbol scan against the runtime allowlist
   → ld.lld -static    →  build/<program>        one program object + npkrt.o
```

**Rule B-1.** Every tool invocation is built from `nitpick.toml`'s
`[toolchain]` lists. No tool ever runs at its own defaults — `llc` defaults to
`-O2` and would optimise a build the manifest declined, which cost the compiler
project a measured 25× on one module.

**Rule B-2.** The undefined-symbol scan is a **build step, not a test**. Every
object is scanned and the build fails on any undefined symbol outside the
runtime allowlist derived from `runtime/npkrt.ll`'s own `define`s plus `main`.
This is what makes "no C, ever" structural rather than a convention.

**Rule B-3.** The optimised leg runs on every program, every time: the same
program re-emitted through `opt -O2` + `llc -O2` must produce the **same exit
code**, and the zero-dependency scan is repeated on the optimised object. This
is the compiler's 1.3.8 instrument, and its first run there found a real defect
that had passed for six cycles.

**Rule B-4 — reproducibility.** Two builds of the same tree from different
working directories produce byte-identical IR (D-078, D-204, D-236), and the
harness has a `repro` stage that measures it. Doubly important here: **the
generated zone tables are the largest source file in the tree**, and a
generator whose output varied by dictionary iteration order would break
reproducibility in a way no other check would notice.

---

## 3. Test stages

The harness mirrors the compiler's stage vocabulary (`BUILD_REFERENCE.md`
§7.1), so the eventual move to `npkg` is a change of runner and not of suite.

| Stage | Directory | Passes when |
|---|---|---|
| `compile` **(the default)** | `tests/conformance/` | held to its `kind`: `positive` **compiles, links, runs and exits with the expected code**; `negative` fails to compile emitting **exactly** the expected diagnostics; `diagnostic` compiles emitting exactly the expected warnings |
| `parse` | every `.npk` in the tree | accepted by `tools/parse_check` with no diagnostic |
| `accept` | *(not used by this library — see below)* | accepted by `tools/check` in silence |
| `check` | `tests/rejection/` | refused by the frontend with **exactly** the expected codes |
| `program` | `tests/unit/`, `tests/probe/` | emitted, scanned, assembled, linked, run at -O0 and again under `opt -O2`, the same exit both times |
| `golden` | `tests/golden/` | as `program`, and the emitted text matches the committed golden byte for byte |
| `sweep` | `tests/unit/sweep/` | as `program`, but **long** — the exhaustive calendar and zone sweeps, run in full on a full invocation and skipped loudly under `--quick` |
| `fixture` | `tests/fixtures/` | built and never run; its uppercased stem becomes an `// argv:` token |

**Rule B-4b (TM-114) — `tests/conformance/` is `compile`/`positive`, and NOT
`accept`.** This table said `accept` until 0.0.1 and that was a defect, not a
simplification: `accept` stops at *"accepted in silence"*, and this repository
holds the reproduction of what that misses. A root file with `main` and no
`failsafe` was accepted by `npkc` at exit 0 and refused only by the linker
(`tests/probe/defect/missing_failsafe/`, O-N11, TM-112). **`npkc` exit 0 is not
well-formedness**, so the conformance suite is judged on the RUN. `accept` is
kept in the table because the stage exists upstream, with the note that this
library does not use it.

**Four further stages exist upstream and are deliberately absent here**, each
to be added by the cycle that can honour it rather than sit dormant:
`resolve` (loader refusals), `runtime` (a hand-written `.ll`), `verify`
(`--obligations` under the pinned z3, the compiler's D-218) and `cost` (the
allocator's own `NPK_HEAP_STATS` numbers held to a stated bound — the
instrument cycle 0.0.4's managed-memory gate is waiting for, and the reason
that gate is a `ulimit -v` cap today).

**Rule B-5 — expectations live in the test file**, marker for marker as the
compiler's:

```
// expect-exit: 7            the exit a run must produce (0 when absent)
// expect-error: NITPICK-TYPE-046
// expect-error-at: 14:9
// stress: 40                run it that many times, the SAME answer every time
// argv: …
// expect-golden: name       the golden file this test asserts against
```

**Rule B-6 — assert on codes and exit codes, never on message text.**

**Rule B-7 — unexpected diagnostics fail a test as surely as missing ones**
(D-237): the set of codes a rejection test reports must **equal** the set its
expectations name.

**Rule B-8 — the harness is itself tested.** A self-check feeds it wrong
expectations and requires it to report every one as a failure. A suite that
only ever agrees with what it is handed reports green while checking nothing.

**Rule B-9 — the `sweep` stage is separable but not optional.** The exhaustive
calendar round trip (`CALENDAR.md` §5) takes seconds, not minutes, so it runs on
every full invocation; `--quick` skips it **with a loud line**, and nothing is
concluded from a `--quick` run.

---

## 4. Dependencies

**Rule B-10 (TM-027).** `ntime` depends on the language, its prelude, and
nothing else.
`[dependencies]` is empty and stays empty until a decision says otherwise.

Specifically and deliberately:

- **not the compiler's `src/`** — reaching into a compiler's internals for a
  growable array couples this library's correctness to a file whose own header
  says it exists for the compiler's tables.
- **not the compiler's `lib/`** — `lib/nsys.npk` and friends are on their way
  out of that repository into an `nlibc` sibling, so importing them today is
  importing a path that is scheduled to change. The four syscall numbers
  `ntime` needs are x86-64 ABI facts and are declared in `src/host/sys.npk`
  with the same shape `nsys` uses.
- **not `nitpick-parse`**, even though the two overlap on datetime scanning —
  `nparse`'s TOML plugin needs the four TOML datetime types and `ntime` is
  where they belong. Recorded as O-X1 and resolvable when dependency
  resolution lands; until then each library carries its own, and the *test
  vectors* are shared by being committed in both.
- **not `/usr/share/zoneinfo`, not `libc`, not any system database**
  (TM-007; `ZONE_MODEL.md` §1).

**Rule B-11.** The prelude is fair game and is used heavily: `Duration`,
`Ordering`, the derivable traits, the named errnos, `environ`, `read_file`,
and the trap error identities. Every module has it bound with no import.

---

## 5. Storage primitives

**Rule B-12 (TM-005).** `ntime` declares its own storage primitives, in
`src/core/`:

- **`Vec<T>`** — `{ wild T->:items; int64:count; int64:cap; }`, the compiler's
  `List<T>` in shape because that shape is right and has been exercised across
  twenty-two families, and **ours** because a library must not import a
  compiler's internals (B-10).
- **`Bytes`** — an owning byte sink over `buffer`, with `push`, `extend`,
  `extend_str`, `put_uint` (decimal, allocation-free) and `take`. Every
  formatter writes into one. It exists because `string_concat` allocates per
  call and formatting a million rows should allocate once — the compiler
  measured exactly that shape as quadratic in `npkg`'s first full run,
  seventeen minutes of fifty-six spent in the kernel.
- **`limits.npk`** — every named bound in one file.

**Rule B-13 — `ntime` declares no other container.** In particular no hash map:
the zone lookup is a binary search over a sorted index (`ZONE_MODEL.md` Z-9),
which at 447 entries beats a hash and has one invariant instead of four.

---

## 6. Modules, files, and imports

**Rule B-14.** One module per file, and **a file's `mod:` name must equal its
basename** — the loader reports `NITPICK-RESOLVE-005` at line 1 otherwise, and
says nothing about the name.

**Rule B-15.** Public names carry the module's short prefix and nothing else
carries it: `cal_`, `span_`, `zone_`, `fmt_`, `host_`. A `pub struct` takes
PascalCase (`Timestamp`, `CivilDate`, `ZonedDateTime`); constants are
`SCREAMING_SNAKE`.

**Rule B-16 — imports are relative today.** Until dependency roots are
populated (§1), every internal import is `use "./x.npk".*;` or
`use "../y/z.npk".*;`, and a consumer imports `ntime` by a relative path to
`src/lib.npk`, which is the umbrella: it `pub use`s the public surface so a
consumer writes one import.

> **`use` is not transitive** (`MODULE_REFERENCE.md` §2.3), so `src/lib.npk`
> re-exports deliberately — which is a feature: the public surface is a list in
> one file a reviewer can read.

**Rule B-17 — the layering, and the direction of every arrow.**

```
        fmt  ──►  zone  ──►  span  ──►  cal  ──►  core
         │                     │         │          ▲
         └─────────────────────┴─────────┴──────────┘

        host ──►  zone (for the name lookup)
             ──►  cal  (for the range check)
             ──►  core
```

`core` depends on nothing. **Nothing depends on `host`** except `src/lib.npk`
and an application — which is `SAFETY.md` §3's purity boundary expressed as a
layering rule, and `check_layering` enforces it.

A `use` cycle is legal in the language (D-086) and is still a decomposition
mistake; `ntime`'s layers are acyclic and the harness says so.

---

## 7. Reserved words that will bite

The compiler's list, filtered to the ones a date library reaches for. Each of
these reads like an ordinary local name and is not:

| Wanted as a name | Actually |
|---|---|
| `unit` | the unit-declaration keyword — and "unit" is what a rounding granularity wants to be called |
| `end` | the `when`/`then`/`end` terminator — and "end" is what a range's upper bound wants to be called |
| `in` | the `for … in` keyword |
| `on` | a keyword — `Zone?:on = …` does not parse |
| `limit` | the verification keyword — and "limit" is what a range bound wants to be called |
| `move`, `drop`, `pass`, `fail`, `relay`, `give`, `pick`, `fall` | keywords |
| `error` | the declaration keyword; `Result`'s field is `.err` |
| `buffer`, `raw` | type and keyword |
| `any`, `as`, `with`, `where`, `is`, `is_err`, `never`, `fails`, `defaults` | keywords |
| `fixed` | the immutability keyword — and "fixed offset" is this library's own term |
| `range` | the builtin generic type name |
| `mod` | the module keyword — and "mod" is what a modulus wants to be called |
| `Ordering` | the prelude's enum (which we want, and must not shadow) |

The names this library uses instead, fixed here so they are used consistently:
**`gran`** for a rounding granularity, **`hi`** and **`lo`** for range bounds,
**`rem`** for a modulus result, **`zone_off`** for a fixed offset in seconds,
**`bound`** for a limit, **`src`** for an input byte slice, **`sink`** for an
output `Bytes`.

---

## 8. Three more shapes that are not what a C or Rust habit expects

- **Adjacent string literals do not concatenate.** `"a" "b"` is two literals; a
  long format is built with `Bytes`.
- **`discard(expr);` takes parentheses; `defer { … }` takes no trailing
  semicolon.**
- **Struct/trait/impl/function declarations end `};`. Control-flow blocks do
  not.**

---

## 9. Open items

- **O-B1 — when `npkg` can build a library.** Gated on O-N1. Neither
  `target = "library"` nor dependency-root population is on the compiler's 1.5
  or 1.6 map, so this is a request to be made, not a date to wait for.
