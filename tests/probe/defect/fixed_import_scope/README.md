# `fixed_import_scope` — an imported `fixed` binding's type resolved in the importer's scope (O-N23); at compiler `c970483` it resolves at home

## Landed — cycle 0.1.4c, compiler `c970483`

**The fix this reproduction was raised to ask for is in the compiler.** Its
DEF-105, the compiler's 1.6.0 step 3h, resolves a `fixed` binding's declared
type in the module that declares it — which its D-137 already said of every
other annotation of a declaration. The reproduction was raised at cycle
0.1.4's planning as a script, `importscope.py` in `meta/roadmap/0.1/0.1.4.md`
§3, and **is committed here only now, where its fix has landed** (TM-192):
every case carries the marker its fixed verdict is, and the verdicts at the
pins that had the defect are each case's control.

| File | through `c3bdae2` — the control | at `c970483` — the marker |
|---|---|---|
| `case1_table_only.npk` | refused `NITPICK-TYPE-001` at `rows.npk`'s own line — the LOUD form | **run 0** |
| `case2_same_name.npk` | **run 10** — the table takes this module's `Row`, its fields swapped: the SILENT form | **run 0** |
| `case3_wider_same_name.npk` | **run 10** — this module's `Row` 8 bytes wider: a 24-byte stride over 16-byte rows | **run 0** |
| `case4_type_imported.npk` | run 0 — the control: the type imported by name | run 0 |
| `case5_type_imported_same_name.npk` | refused `NITPICK-RESOLVE-001` | refused `NITPICK-RESOLVE-001` — two declarations of one name, at every pin |
| `case6_scalar_same_name.npk` | **run 10** — a `fixed` SCALAR does the same | **run 0** |
| `case7_function_only.npk` | run 0 — a signature resolves at home | run 0 |

`rows.npk` is the module every case imports — a struct, a table of it, a
scalar of it and a function returning it — and is not a program: it is in
`harness/run.py`'s `EXPECT_EXEMPT` at `none`, re-derived on every run
(TM-137). **Every verdict is on both legs**, -O0 and `opt -O2`, and every case
exits 10 on a wrong read, so a case that compiles and reads the wrong row is
red. Each case's `failsafe` names exactly what `NITPICK-REACH-002` asks at
`c970483`, where the script's named two identities more. `TRANSCRIPT.txt` has all seven at every pin the workbench keeps, both
legs, generated from these files by `meta/roadmap/0.1/0.1.4c.md`'s
`transcript.py`: the same seven verdicts at the six pins from `950bb1d` to
`c3bdae2`, so the defect was not a regression, and the fixed ones at
`c970483`, where the IR indexes `ROWS` by `rows.Row` in every case that reads
it.

## What it held here, and holds no longer

`tests/unit/sweep/every_oracle_date.npk`, the first cross-module import of a
user-typed `fixed` table here, imports its row type by name beside the table
(TM-181) — case 4's spelling, which made a same-named struct there a case-5
refusal rather than a case-2 misread. At `c970483` nothing depends on it:
case 2's form reads correctly. The import stays, a belt (TM-192). **Cycle
0.5's zone tables** — generated `fixed` tables the lookup module imports —
were the designed-in exposure, and `meta/roadmap/0.5/README.md`'s "Watch for"
said to read the pin again before writing that module; it now says what was
read.

## The record, as raised

`meta/roadmap/0.1/0.1.4.md` §3 is the finding in full, measured at every pin
this repository then kept. In one paragraph: the compiler's D-137 resolves
every annotation of a declaration in its home scope, *"never in the scope of
whatever module happens to be asking"*, and names the danger itself — *"under
a name collision it would not have erred at all: it would have silently bound
the caller's same-named type."* A `fixed` binding's declared type was not
among the annotations it listed, and that collision is what happened: case 3's
IR indexed `@"npk.rows.ROWS"`, a `[2 x %"npk.rows.Row"]` of 32 bytes, as
`[2 x %"npk.case3_wider_same_name.Row"]` — a 24-byte stride over 16-byte rows,
so row 1 lay partly past the table's end.
