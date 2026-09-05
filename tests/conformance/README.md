# `tests/conformance/` — the consumer's view

Programs that use `ntime` **the way an application will**, through
`src/lib.npk` and by relative path, and that are judged on **what they do when
run** rather than on being accepted.

## The stage, and why it is not `accept`

`compile` with `kind = "positive"`: *compiles, links, runs, and exits with the
expected code* (`../../meta/specs/BUILD.md` §3 and B-4b, TM-114). It reads like
over-engineering for a directory whose only program exits 0 doing nothing, and
it is not: `npkc` accepted a root file with `main` and no `failsafe` at exit 0
until the compiler's DEF-5 landed, emitting IR that nothing could link
(`../probe/defect/missing_failsafe/`, O-N11, TM-112). A stage that stopped at
"accepted in silence" passed that file. **The run is the verdict.**

## What is here

| File | Asserts |
|---|---|
| `import.npk` | that the public surface is **importable** — not that it works |

`import.npk` imports an umbrella that re-exports nothing, which is the point:
it goes on compiling as names are added to `src/lib.npk`, and the day it does
not, the surface changed incompatibly — a MAJOR version by TM-013, and better
as a red run than as a discovery.

**Measured at 0.0.1, pin `0dfddac`:** its emitted `.ll` is **845 282 bytes and
byte-identical to `../probe/probe11d_floor_only.npk`'s** — the program that
imports nothing at all. Both declare only `main` and `failsafe`, which are
root-level and unqualified, so there is nothing for a module name to
distinguish. Two things follow. First, **importing `ntime` today costs a
consumer exactly nothing**: no arms beyond `SAFETY.md` S-4b's floor of four
(removing any one is `NITPICK-REACH-002`, checked), and no bytes. Second, the
day `src/lib.npk` exports its first name **these two files must stop being
identical**, and that divergence is the first observable evidence that the
surface became real.

Both files are also canaries for the compiler's 1.5.2d (D-262), which prunes
the fixed per-program prelude cost. **That number is expected to move at that
landing**; a change there is the landing, not a regression.
