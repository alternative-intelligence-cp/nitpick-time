# O-N10 — the derives on an enum with a payload

**`#[derive(Eq)]` emits derived code that does not compile, and
`#[derive(Ord)]` on the same declaration compiles and ignores the payload.**
Found by cycle 0.0.0's probe 05 on 2026-09-03, against the pinned toolchain
(compiler commit `950bb1d`, LLVM 20.1.2). The transcript with every command's
exit code is [`TRANSCRIPT.txt`](TRANSCRIPT.txt).

Nothing here is a workaround and nothing here is a probe.

---

## The two halves, and the quiet one is the serious one

| derive | on `enum:Part = { Literal(uint16); Year4; }` | verdict |
|---|---|---|
| `Eq` | **refused** — `NITPICK-TYPE-034` **in `<derived-1>`** | loud, and the diagnostic points at code the user cannot open |
| `Ord` | accepted; `Literal(7).cmp(Literal(9))` is **`Equal`** | **silent, and wrong** |
| `PartialOrd` | accepted | same expansion family as `Ord` |
| `Hash` | accepted; hashes the **tag only** | legal alone, useless beside a broken `Eq` |
| `Clone` | accepted; **the payload survives** | correct |
| `ToString`, `Debug` | accepted | payload content not measured |

### The loud half

```
NITPICK-TYPE-034 <derived-1>:2:73: `Part` has no built-in `==`: derive or
implement `Eq` and compare with `a.eq(b)`
```

Read it twice: **the derived `Eq` implementation is being told to derive `Eq`.**
The expansion compares two `Part` *values* with `==` rather than comparing tags
and then payloads, so the code the derive writes needs the trait the derive is
writing. `<derived-1>` is synthetic — there is no file to open and nothing in
the user's source is wrong.

### The quiet half

`case2_ord_ignores_payload.npk` exits **221**, three digits, one per
comparison, `1`=Less `2`=Equal `3`=Greater:

| comparison | measured | should be |
|---|---|---|
| `Literal(7).cmp(Literal(9))` | **2 — `Equal`** | `Less` |
| `Literal(7).cmp(Literal(7))` | 2 — `Equal` | correct |
| `Literal(7).cmp(Year4)` | 1 — `Less` | correct |

Two values that differ report `Equal`. A sort over such an enum believes it has
grouped equal keys; a binary search over it finds the wrong element; and neither
says anything. **A refusal is a bad afternoon. A silent `Equal` between two
different values is a wrong answer nobody goes looking for.**

The two halves are not even consistent with each other: the trait that would
say *these are different* will not compile, and the trait that ranks them says
they are the same.

## The isolation

It is the **payload** that does it, and the compile failure is **`Eq` alone**.
Section 4 of the transcript is generated from this template, one file per row,
so that eight near-identical files are not eight things to keep in step:

```
mod:iso;
#[derive($DERIVE)]
enum:Part = { $BODY };
func:main = int32(cstring[]:_~argv) { exit 0i32; };
func:failsafe = int32(Error:e) { … the seven standard arms … };
```

| `$DERIVE` | `$BODY` | `npkc` |
|---|---|---|
| `Eq` | `Literal(uint16); Year4;` | **exit 1**, `NITPICK-TYPE-034` |
| `Eq` | `Year4; Month2;` | exit 0 |
| `Ord`, `PartialOrd`, `Hash`, `Clone`, `ToString`, `Debug` | `Literal(uint16); Year4;` | exit 0 |

A plain struct with the same field types derives `Eq` fine, and the payload
enum with no derive compiles fine.

## Why it is untested territory rather than a regression

**No file anywhere in the compiler's tree derives any trait on an enum with a
payload.** Its derive tests cover `enum:Season`, `enum:Tag` and `enum:Level` —
all payload-less — and `struct:Point`, `struct:Key`, `struct:Box<T>`. Section 5
of the transcript is that search, and it returns nothing.

That also explains the asymmetry: the payload-less path is exercised, the
payload path was written and never run.

## What is being asked

- `#[derive(Eq)]` on a payload enum to emit an implementation that compiles —
  tag equality, then payload equality per variant;
- `#[derive(Ord)]` and `#[derive(PartialOrd)]` to **compare the payload** after
  the tag, rather than stopping at the tag;
- and, whichever way those go, a test in the compiler's own tree that derives
  on a payload enum, because the gap here is coverage.

`Hash` hashing the tag only is **not** part of the ask: a hash that collides is
correct, if weak. It is recorded because with `Eq` refused there is no route to
keying on one of these types at all, so the three answers have to be read
together.

## What it costs `ntime`

**One type, and nothing today.** `FmtPart.Literal(uint16)` is the only
payload-carrying variant in the entire specification set (`FORMAT_MODEL.md`
F-4), its payload owns nothing, and no rule requires `Eq` or `Ord` on it —
`TESTING.md`'s round trips compare formatted **strings** and parsed **values**,
never two `Layout`s.

So this is **raised, not blocking**, and the constraint to carry forward is the
second one rather than the first: a refusal cannot be ignored, and
`#[derive(Ord)] enum:FmtPart` would compile and be wrong. The cycle that builds
`src/fmt/` is where that matters, and O-N10 in
[`../../../../meta/OPEN_QUESTIONS.md`](../../../../meta/OPEN_QUESTIONS.md)
carries it.

**Nothing is being worked around.** `probe05_payload_enum.npk` derives the five
that are correct and pins `Eq`'s refusal in `probe05b_derive_eq_refused.npk`;
no hand-written `eq` has been added to stand in for the broken derive, because
there is no library code yet that needs one, and writing one now would bury the
defect exactly where it must not be buried.

## For cycle 0.0.2

None of these three files is a `program`-stage entry. One must not compile and
two exit non-zero on purpose. They need an exclusion with the reason next to it.
