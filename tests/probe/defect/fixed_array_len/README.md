# `fixed_array_len` — `.len` on a fixed-size array cannot be lowered

**`.len` on a `T[N]` is accepted by the frontend and refused by the emitter**
with `NITPICK-EMIT-002`, whose own text says *"a defect in the compiler rather
than in this program — report it with the construct at this position"*.

Found 2026-09-05 at pin `0dfddac` by cycle 0.0.4, writing `put_uint`'s
allocation-free digit buffer.

## The measurement

Each status beside the artefact it should have produced:

| spelling | `npkc` | `.ll` | code |
|---|---|---|---|
| local `uint8[20]`, `.len` | **1** | **NONE** | `NITPICK-EMIT-002` |
| module `fixed uint8[3]`, `.len` | **1** | **NONE** | `NITPICK-EMIT-002` |
| **slice** `uint8[]`, `.len` | 0 | wrote | — |
| local `uint8[20]`, indexed, no `.len` | 0 | wrote | — |

So it is `.len` **on the array type**, at either storage class, and it is not
indexing and not slices. The two controls are what place it there rather than
at "arrays are broken".

## What it costs this library, which is nearly nothing

`src/core/bytes.npk`'s digit buffer is a `uint8[20]` and never asks its length —
the bound is `NTIME_DIGITS_MAX`, a named constant in `src/core/limits.npk`,
which is what a reader should see anyway. So this is recorded because the
diagnostic asks to be, not because it blocked anything.

## Not yet numbered

The orchestrator assigns open-question ids. This subcycle's predecessor
assigned one itself and collided with a settled question in a sibling
repository, which cost a correction across ten sites in ten files. **Cite this
by path until an id is issued.**
