# `tests/probe/support/`

**Modules that probes import. Not probes, and not library code.**

A probe is a program: it has its own `main` and `failsafe` and imports nothing
from `src/` (cycle 0.0.0 P-1). Probe 11 is the one probe whose *question* is
about importing, so it needs something to import, and this is where that lives.

Nothing here has a `main` or a `failsafe`, so nothing here is a program and
nothing here should ever be handed to the harness as one. **When the harness
picks `tests/probe/` up as `program`-stage entries from cycle 0.0.2, it globs
`tests/probe/*.npk` and must not descend into this directory** — the same
exclusion `defect/` already needs, for the same reason.

| File | What it is | Why it is shaped that way |
|---|---|---|
| `probe11_arms_lib.npk` | `SAFETY.md` S-4's `ntime/zone.npk` in miniature: one `pub error:`, and two `fail` sites that raise it | No division, no remainder, no indexing, no plain-integer `+ - *`. Importing it can therefore add **exactly one** thing to a consumer's arm set, and probe 11e's refusal names that one thing. |
| `probe11_calc_lib.npk` | `ntime/cal.npk` in miniature: three `%`, one `/`, an indexed `fixed` table, and `+ - *` | Declares **no** error identity at all, so every arm it costs a consumer is a *system* arm. That is probe 11c's whole measurement. |
| `probe11_silent_lib.npk` | one `pub error:` that is **declared and never raised**, and nothing else | The other end of the same question. Probe 11f imports it with a floor-only `failsafe` and compiles, which is how "a declaration arms nothing; a `fail` site does" stopped being an assertion. |

**The three are kept apart on purpose.** A single support module carrying an
error identity *and* arithmetic would make every refusal a mixture, and the
point of the 11 family is that each file changes one variable against a control
that compiles. `probe11d_floor_only.npk` is that control and it imports nothing
at all.

**A support module compiles on its own at exit 0**, and that is correct rather
than surprising: `npkc` emits no `@main` for it, so nobody links it alone. It is
*not* evidence about the missing-`failsafe` defect, and
[`../defect/missing_failsafe/TRANSCRIPT.txt`](../defect/missing_failsafe/TRANSCRIPT.txt)
runs exactly this command as the control that rules it out.
