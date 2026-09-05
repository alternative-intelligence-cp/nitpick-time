# Contributing

`ntime` is planned before it is written, and the plan is in the repository.
That is unusual and it is deliberate: the specifications catch design mistakes
that would otherwise be found by writing the wrong code twice.

**Where it stands:** cycle 0.0.1 is done, so there is a skeleton — an empty
umbrella, one placeholder module per `src/` directory, a consumer that imports
and runs, and CI. The first code that computes anything is `src/core/` at
0.0.4. `harness/run.py` is a **floor** until 0.0.2 replaces it, and it has no
self-check yet, so a green run from it is an unfalsified claim rather than a
tested one.

## Before you write anything

Read, in this order:

1. `meta/specs/SAFETY.md` — the constraints
2. `meta/specs/TIME_MODEL.md` — the type set, and why each distinction exists
3. `meta/DECISIONS.md` — why things are the way they are
4. `meta/roadmap/ROADMAP.md`, then the current cycle's `README.md`

## The shape of a change

**Every change belongs to a subcycle.** The current cycle's `README.md` has the
checklist; a change that is not on it either goes on it or is a finding to be
recorded first.

**A specification change is a decision.** If your change requires the library
to behave differently from what `meta/specs/` says, the specification is
amended and a numbered decision recorded in `meta/DECISIONS.md`, **in the same
commit**. A settled decision's text is never rewritten — supersede it.

**Every change is green under the full harness.** `--only` and `--quick` are
for iterating and never for concluding; nothing is committed on the strength of
a filtered run.

## The six things that will surprise you

The first four are design. **The last two were measured** by cycle 0.0.0's
probes, against the real compiler, and each one falsified something a document
had asserted — which is why they are here rather than in a specification only.

1. **Every public `error:` this library declares becomes a mandatory `pick` arm
   in every consuming program's `failsafe`.** The language enforces it and
   forgetting one is a compile error. The budget is three, it is a ceiling, and
   adding a fourth is a major version. A distinction the *caller* cares about
   rides as a field on the returned value, not as a new error.

2. **Only `src/host/` may touch the machine.** Everything else is a pure
   function of its arguments — no clock, no syscall, no environment. That is
   what makes the library reproducible and testable to the nanosecond without a
   double, and `check_purity` fails the build if it stops being true.

3. **There is no format string, and there never will be.** No `strftime`, no
   `layout_from_pattern("%Y-%m-%d")`. A layout is a typed value the compiler
   checks. The temptation to add the convenience is obvious, which is why
   `check_no_format_string` exists.

4. **Calendar arithmetic is not associative and not invertible**, on purpose.
   `2026-01-31 + 1 month + 1 month` is not `+ 2 months`, and
   `+ 1 month − 1 month` does not return to the start. `SPAN_MODEL.md` §3 has
   the worked examples. Do not "fix" it — every alternative trades one surprise
   for a worse one, and this one is written down.

5. **`exit 0` does not mean nothing leaked, and `Vec<T>` is not
   bounds-checked.** Two measurements, one lesson: *the guarantee attaches to
   something narrower than the word suggests.* D-151 watches **`wild`**
   allocations only, so a `Vec<string>` whose block is freed and whose elements
   are not retains its elements — 125 MiB over two million of them — **and
   exits 0** (TM-106). And the bounds check attaches to the **type**: slices,
   arrays and simd lanes trap, **a bare pointer does not**, and `Vec<T>.items`
   and `Bytes`' body are both reached as one (TM-108). So every accessor checks
   its index **in code**, `0 <= i` as well as `i < count` — an index from a
   narrower signed field can be negative, and `i < count` accepts it.

6. **`npkc` exiting 0 is not "this program is well-formed".** It accepted a
   root file with `main` and no `failsafe` at exit 0, emitting IR whose trap
   paths called a `@npk_failsafe` nothing defined; only the linker refused it
   (TM-112, and `tests/probe/defect/missing_failsafe/` is the reproduction).
   The compiler has since fixed that particular case, and **the habit outlives
   it**: pair every exit code with the artefact it should have produced. A
   status that disagrees with an artefact is the tell.

## Tests

- **Expectations live in the test file**, as markers, and assert on codes and
  exit codes — never on message text.
- **A negative test with no expectation is a failing test.** And so is a test
  with **no marker at all**: `harness/run.py` partitions the tree and an
  uncovered `.npk` under `tests/` is a finding, not a silence (TM-115). Three
  files sat outside that sweep for two days and were exactly the three whose
  expectations had gone stale.
- **Every sweep prints its denominator.** A sweep that matched nothing and a
  sweep that opened nothing produce the same output otherwise, so the count of
  files opened is part of the result.
- **A test with a PRECONDITION says so in its header and exits a code no
  substantive assertion in that file uses** (TM-116). Otherwise an unmet
  precondition arrives dressed as a verdict, and a verdict is believed.
- **Unexpected diagnostics fail a test as surely as missing ones.**
- **Where a property can be checked over its whole domain, it is** — the civil
  round trip covers every day in the supported range, not a sample.
- **Anything that reads a clock runs forty times**, not once.
- **A red under stress is a stop sign, never a retry.**

## Compiler defects

You will find them; the library is written against a compiler that is itself
under construction. **Record the reproduction, stop, and raise it in the
compiler repository.** Do not work around it in library code: a workaround
buried here outlives the bug, is never removed, and is indefensible at
verification time.

## Style

Match the surrounding code. Public names carry their module's short prefix
(`cal_`, `span_`, `zone_`, `fmt_`, `host_`); types are PascalCase; constants
are SCREAMING_SNAKE. `meta/specs/BUILD.md` §7 lists the reserved words that
read like ordinary names and the substitutes this library uses instead — use
those, so the tree is consistent.

**And one that is not in that table: `stack`.** It is a memory qualifier beside
`wild`, it is the natural name for a parser local, and it does not fail where
you wrote it — `PARSE-002` at the declaration, then *"this `{` is never
closed"* pointing at `main`'s closing brace. It reads as a brace imbalance
dozens of lines away and gets bisected as one; a sibling library lost about an
hour to it. If a parse error claims an unclosed brace and the braces balance,
look for a local named after a qualifier before you touch the braces.
