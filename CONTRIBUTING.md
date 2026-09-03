# Contributing

`ntime` is planned before it is written, and the plan is in the repository.
That is unusual and it is deliberate: the specifications catch design mistakes
that would otherwise be found by writing the wrong code twice.

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

## The four things that will surprise you

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

## Tests

- **Expectations live in the test file**, as markers, and assert on codes and
  exit codes — never on message text.
- **A negative test with no expectation is a failing test.**
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
