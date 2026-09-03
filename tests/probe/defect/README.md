# A compiler defect, reproduced

**`npkc`'s compile time and memory are quadratic in the size of a single
declaration.** Found by cycle 0.0.0's probe 04 on 2026-09-03, against the
pinned toolchain (compiler commit `950bb1d`, LLVM 20.1.2).

Nothing in this directory is a workaround and nothing in it is a probe. It is
the reproduction the ecosystem's rule requires: *never work around a compiler
defect — record it, stop, and raise it.* When the defect is closed,
`big_fixed_array_cost.npk` becomes the regression case that proves it and this
file records what the numbers used to be.

---

## What blocks this library

TM-007 compiles the whole IANA time-zone database into the binary as `fixed`
module state, and `ZONE_MODEL.md` §3 measures it at **26 838 transition rows**
across 447 zones. Probe 04 built a table that size and it compiles — in **281
seconds**, using **30.9 GiB of resident memory**.

That is not a size the library can ship against:

- a machine with 16 GiB cannot build `ntime` at all;
- CI runners are smaller than that, and cycle 0.0.1's checklist puts
  `harness/run.py` on every push;
- every *consumer* pays it too, because the table is in the library it imports.

There is no honest way around it inside `ntime`. Shrinking the table, splitting
it across modules, or encoding it as a byte blob decoded at first use would each
buy the number back — and each is a workaround for a compiler bug, buried in
library code, that would outlive the bug. So the work stopped here.

---

## The measurements

Every row below was checked for `npkc` **exit 0**. That matters: the first pass
at this measurement recorded several "fast" configurations that were in fact
compile *failures* stopping early, and drew the wrong conclusion from them. A
timing that is not paired with an exit code is not a measurement.

Each cell is `npkc` wall time and peak resident memory, from

```
/usr/bin/time -f "%e s  %M KiB" "$NPKC" <file>.npk -o /tmp/out.ll
```

### Axis 1 — elements in one module-level `fixed` array

The shape TM-007 needs. Rows are `{ int64; int32 }`, as `ZoneTransition` is.

| rows | wall | peak RSS | vs. previous |
|---:|---:|---:|---|
| 0 | 0.10 s | 23 MiB | — |
| 500 | 0.19 s | 31 MiB | — |
| 1 000 | 0.41 s | 54 MiB | ×2.2 time, ×1.7 memory |
| 2 000 | 1.19 s | 140 MiB | ×2.9, ×2.6 |
| 4 000 | 4.19 s | 473 MiB | ×3.5, ×3.4 |
| 8 000 | 15.83 s | 1.73 GiB | ×3.8, ×3.8 |
| **30 000** | **281.35 s** | **30.9 GiB** | — |

A ratio approaching 4 per doubling in both columns is quadratic growth. The
30 000-row figure is `probe04_big_fixed_table.npk` itself.

Two controls, both at 4 000 rows and both exit 0:

| variant | wall | peak RSS | what it says |
|---|---:|---:|---|
| `main` reads the table | 4.19 s | 473 MiB | — |
| `main` never reads it | 4.36 s | 496 MiB | the cost is in the **declaration**, not any use |
| a plain `int64[4000]` instead | 1.41 s | 161 MiB | not struct-specific; it tracks the count of scalar constants |

And the cost is not "many constants" — **4 000 separate module-level
`fixed int64` bindings** cost 0.61 s and 58 MiB. It is the size of **one**
declaration that hurts.

### Axis 2 — statements in one function body

No module-level data at all; `main` is `acc = acc + k;` repeated.

| statements | wall | peak RSS |
|---:|---:|---:|
| 1 000 | 0.87 s | 134 MiB |
| 2 000 | 2.27 s | 375 MiB |
| 4 000 | 7.03 s | 1.27 GiB |

Quadratic in both, and worse per element than an array initialiser.

### Axis 3 — bytes in one string literal

One `fixed string:BLOB = "abab…";`, nothing else.

| literal bytes | wall | peak RSS |
|---:|---:|---:|
| 60 000 | 5.24 s | 25 MiB |
| 120 000 | 22.72 s | 27 MiB |
| 240 000 | 78.11 s | 32 MiB |
| 480 000 | 308.12 s | 41 MiB |

Quadratic in **time**, with memory flat — so this is a second, separate
pathology from the other two rather than the same one seen through a lexer.
It matters here because `ZONE_MODEL.md` Z-7's fourth table is a **name pool**,
which is exactly a large string constant.

---

## Reproducing it

The committed file is the 4 000-row point, chosen so that a reader sees the
defect in four seconds rather than five minutes:

```
"$NPKC" tests/probe/defect/big_fixed_array_cost.npk -o /tmp/p.ll
```

The curves are regenerated with the recipes below, which are what produced the
tables above.

```python
# axis 1 — N rows of a fixed array of { int64; int32 }
E = -2208988800
rows = ",\n".join("    R{ a: %di64, b: %di32 }" % (E + i*604800 + (i % 97)*3600, i % 13)
                  for i in range(N))
decl = "struct:R = { int64:a; int32:b; };\nfixed R[%d]:T = [\n%s\n];\n" % (N, rows)

# axis 2 — N statements in one body
body = "\n".join("    acc = acc + %di64;" % (i % 7) for i in range(N))

# axis 3 — N bytes in one string literal
decl = 'fixed string:BLOB = "%s";\n' % ("ab" * (N // 2))
```

Each is wrapped in a program with a `main` and a `failsafe`. **The `failsafe`
must name every reachable error and must still carry `(*)`** — `Error` has more
values than a `pick` can list, so omitting the wildcard is `NITPICK-PICK-003`,
and omitting a reachable identity is `NITPICK-REACH-002`. A file that trips
either compiles fast because it stops early, which is the trap the first pass at
this measurement fell into.

---

## What is being asked

Nothing in the language changes. The ask is on `npkc`'s implementation:

- the array-initialiser and function-body paths made linear, or near enough that
  30 000 rows costs seconds and hundreds of megabytes rather than minutes and
  tens of gigabytes;
- the string-literal path made linear in time.

Recorded as **O-N4** in [`../../../meta/OPEN_QUESTIONS.md`](../../../meta/OPEN_QUESTIONS.md),
with what `ntime` does in the meantime.

---

## A second defect, met by accident

Not committed as files, because it needs two source files with *deliberately*
wrong names and the harness would trip over them from 0.0.2. Six lines
reproduce it, so they are here instead.

**`npkc` accepts a root file whose `mod:` name differs from its basename when a
sibling carries that basename, silently compiles the sibling too, merges both
into one module, and emits IR with two `define i32 @main` — exiting 0.** The
LLVM it wrote is invalid and `llc` refuses it. Found while staging probe 04
under the wrong filename, which is how a compile that should have taken one
second appeared to take three hundred.

In one directory, with `ARMS` standing for a `failsafe` `pick` naming
`HeapBadRequest`, `HeapOom`, `IntOverflow`, `OutOfBounds`, `Unreachable`,
`WildLeak` and `(*)`:

```
alpha.npk:   mod:alpha;
             func:main = int32(cstring[]:_~argv) { exit 1i32; };
             func:failsafe = int32(Error:e) { ARMS exit 9i32; };

beta.npk:    mod:alpha;                          // <-- does not match `beta`
             func:main = int32(cstring[]:_~argv) { exit 2i32; };
             func:failsafe = int32(Error:e) { ARMS exit 9i32; };
```

```
$ "$NPKC" beta.npk -o b.ll ; echo $?
0
$ grep -c '^define i32 @main' b.ll
2
$ llc -O0 -filetype=obj -relocation-model=static b.ll -o b.o
llc: error: b.ll:10928:12: error: invalid redefinition of function 'main'
```

**Delete `alpha.npk` and the diagnostic is exemplary**, which is why this is a
narrow bug rather than a missing check:

```
NITPICK-RESOLVE-005 beta.npk:1:1: cannot find module `alpha`: neither
<dir>/alpha.npk nor <dir>/alpha/mod.npk; if this line is the file's own header,
note that this file is `beta.npk` and a file's module name must match its
basename
```

So the resolver knows the rule and says so well; it just does not apply it when
the name it was given happens to resolve to a different file. **It costs `ntime`
nothing** — the house rule is already `mod:` = basename — so it is raised
alongside O-N4 rather than blocking anything, and nothing in this library is
shaped around it.
