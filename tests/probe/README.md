# `tests/probe/`

Small Nitpick programs that ask the **compiler** a question. Each one pins a
language fact that `meta/specs/` depends on, so that a change to that fact is a
red run here rather than a wrong date in cycle 0.6.

Written in cycle 0.0.0; governed by
[`../../meta/roadmap/0.0/0.0.0.md`](../../meta/roadmap/0.0/0.0.0.md), which
carries the verdict table. Picked up by the harness as ordinary `program`-stage
entries from cycle 0.0.2.

## The rules

- **A probe is a program**, never a library file (0.0.0 P-1). It has its own
  `main` and `failsafe` and imports nothing from `src/`.
- **A probe is never deleted** (P-5). The verdicts are a regression suite; a
  probe that has served its purpose has not stopped being evidence.
- **Every probe exits 0 on success** and a distinct positive code per assertion
  it fails, so a failure names itself. `exit 0` additionally asserts, through
  D-151, that nothing leaked.
- **A probe that pins a fact the specification already states asserts the
  expected answer** (P-6) rather than printing what it found, so a change to
  that answer is a red run.
- **A file's `mod:` name equals its basename**, and no identifier may begin
  with a digit — hence `probeNN_topic.npk` and never `NN_topic.npk`.

## What is here

| File | Asks | Pins |
|---|---|---|
| `probe01_derive_ord.npk` | does a derived `Ord` follow declaration order? | TM-011, `SAFETY.md` S-14, `TIME_MODEL.md` M-6 |
| `probe04_big_fixed_table.npk` | is a large `fixed` table read-only data with no startup cost? | TM-007, `ZONE_MODEL.md` Z-7/Z-8, `SAFETY.md` S-19 |
| `probe04b_emission_shape.npk` | the same, at 300 rows, so the answer stays re-derivable | the same rules |

Probes 02, 03, 05–11 are planned in `0.0.0.md` §4 and not yet written; the
subcycle stopped at the defect below before reaching them.

### Why 04 has a `b`

O-N4 makes `probe04_big_fixed_table.npk` cost **281 seconds and 30.9 GiB**, so
it is not runnable in CI and not re-runnable by a reader. Its two questions
separate cleanly, though: whether **30 000 rows compile at all** needs 30 000
rows, and what the declaration is **lowered to** does not — the emission form is
chosen by the same path at any element count. So `probe04b_emission_shape.npk`
is the identical declaration at 300 rows, it costs 0.16 s, and
`probe04b_emission_shape.txt` beside it holds the IR line, the `readelf` output
and the segment permissions **quoted verbatim with their exit codes** rather
than summarised in prose.

That split is the general rule this directory now follows: **where a probe's
answer is expensive to re-derive, evidence the part that is cheap and mark the
part that is not.** `0.0.0.md` §7 marks 04's 30 000-row row as a one-time
observation for exactly that reason.

**A note for cycle 0.0.2**, which picks this directory up as `program`-stage
entries: `probe04_big_fixed_table.npk` cannot be one of them while O-N4 is open.
It needs an exclusion with the reason written next to it, and `04b` is what the
suite runs in its place.

## `defect/`

Not probes. A reproduction of a compiler defect that cycle 0.0.0 found and that
this library must not work around — see
[`defect/README.md`](defect/README.md). It is deleted only when the defect is
closed. The committed reproduction there costs about **6 seconds and 580 MiB**;
`probe04_big_fixed_table.npk` costs 281 seconds and 30.9 GiB.
