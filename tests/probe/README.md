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
| `probe02_int128.npk` | `int128` add, compare, and a narrowing `=>!` that **fits** | `SPAN_MODEL.md` §5, `VERIFICATION.md` P-5 |
| `probe02b_narrow_unchecked.npk` | what `=>!` does at a value that does **not** fit | TM-105, `SAFETY.md` S-15b, `SPAN_MODEL.md` N-20b |
| `probe02c_narrow_refused.npk` | *(must not compile)* the checked `=>` at the same narrowing | the same rules |
| `probe02d_wide_literal_refused.npk` | *(must not compile)* can `int64`'s **minimum** be spelled as a literal? | `VERIFICATION.md` P-5 |
| `probe03_timespec_sys.npk` | a 16-byte `timespec` through `sys`, and the field order | `HOST.md` §2, H-4, H-7, H-8; `SAFETY.md` S-5 |
| `probe04_big_fixed_table.npk` | is a large `fixed` table read-only data with no startup cost? | TM-007, `ZONE_MODEL.md` Z-7/Z-8, `SAFETY.md` S-19 |
| `probe04b_emission_shape.npk` | the same, at 300 rows, so the answer stays re-derivable | the same rules |
| `probe07_negative_div.npk` | does signed `/` truncate toward zero and `%` take the dividend's sign? | TM-016, `CALENDAR.md`'s negative years |
| `probe08_readlink.npk` | `readlink` through `sys`, with the returned length as the authority | `HOST.md` H-13, H-14, H-15 |

Probes 05, 06, 09, 10 and 11 are planned in `0.0.0.md` §4. **09 and 10 are held,
not merely unwritten**: they are the borrow-edge probes, and the view-escape
defect this subcycle found may change their shape. `defect/` carries its
reproduction.

### Why 02 has three twins

Probe 02 asked one question — *is `=>!` a belt over `VERIFICATION.md` P-5's
`prove`, or the opt-out it is named for?* — and the answer needed three files,
because a program that must not compile cannot also exit 0 and there turned out
to be two different ways of not compiling:

- **02** is the positive half: `int128` arithmetic and a narrowing that fits.
- **02b** is `=>!` at a value that does not fit. It **truncates in silence**,
  and the file pins four shapes of it including a positive value narrowing to a
  negative one.
- **02c** is the checked `=>` at the same narrowing: refused at compile time,
  `NITPICK-TYPE-009`. With 02b it says there is **no checked narrowing** in this
  language.
- **02d** was not planned. Correcting `VERIFICATION.md` P-5 against 02b's
  verdict meant writing `int64`'s bounds in `int128`, and the **minimum cannot
  be spelled**: `NITPICK-LEX-004`, because the literal envelope is 64-bit and
  the minimum's magnitude is one too large. The maximum is fine, so the bound
  pair a reader writes by symmetry is exactly what fails.

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

Not probes. Reproductions of compiler defects that cycle 0.0.0 found and that
this library must not work around — see
[`defect/README.md`](defect/README.md). Each is deleted only when its defect is
closed. The O-N4 reproduction there costs about **6 seconds and 580 MiB**;
`probe04_big_fixed_table.npk` costs 281 seconds and 30.9 GiB.
