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
  D-151, that **no `wild` allocation is live at exit** — a statement about
  coverage rather than a proof of cleanliness. **D-151 watches `wild` only**, so
  a probe that allocates nothing `wild` cannot trip it on any exit path, and a
  **managed** body is outside it entirely: probe 06's `Vec<string>` orphaned two
  million element bodies, retained 125 MiB and **exited 0** (TM-106). A probe
  over an owning container therefore asserts its memory too — a `ulimit -v` cap
  today, a `peak_live` bound from the compiler's `NPK_HEAP_STATS` after the
  1.5.1b re-pin. **Assert the cap, not a peak-RSS number:**
  `/usr/bin/time -f %M` reports `0 KiB` for these static binaries, including
  for `probe11d_floor_only.npk`, so it cannot tell a clean run from a small
  one. `probe06b`/`probe06c` are the committed pair.
  **Nine** probes here still carry the older one-line comment *"exit 0
  additionally asserts that nothing leaked"* — **01, 02, 02b, 03, 04, 04b, 05,
  07 and 08**. Each is locally harmless — none of those files allocates a
  managed container — and each is due the wording above; the rewording is
  deferred to **0.0.2**, when the harness picks this directory up and every
  probe is re-run anyway. **Take the list from the command, not from the probes
  you compiled:** `git grep -l 'additionally asserts that nothing leaked' --
  '*.npk'`. `probe04_big_fixed_table.npk` was missed once for exactly that
  reason — it is the one probe here that is never compiled (it is O-N4's 281 s /
  30.9 GiB case), so it drops out of any list built from what a session ran,
  while remaining a first-class probe row in the table below. `probe06` and
  `probe11` are correctly not among the nine: both were written with the `wild`
  wording already.
- **A probe that pins a fact the specification already states asserts the
  expected answer** (P-6) rather than printing what it found, so a change to
  that answer is a red run.
- **A file's `mod:` name equals its basename**, and no identifier may begin
  with a digit — hence `probeNN_topic.npk` and never `NN_topic.npk`.
- **A probe with a PRECONDITION states it in the header and exits a code no
  substantive assertion in that file uses** (TM-116, `TESTING.md` V-1d). Two
  probes here read `$TZ`. Run without it, `probe09b` used to exit **10** — its
  own *"the returned view is not the entry"*, which is the single question it
  exists to ask — so an unmet precondition and a real finding about the
  language were the same signal. Both files now use **30** for "the variable is
  absent" and **39** for "present and not `TZ=Europe/Kyiv`". Note the second:
  `TZ=Europe/Kiev`, the old IANA spelling, used to pass **both** probes at exit
  0, because every byte either one checks is equally true of `Kiev` and `Kyiv`.
- **Every `.npk` under `tests/` carries an `expect-` marker or is named as an
  exemption with its reason** (TM-115, `TESTING.md` V-1b/V-1c). The three
  modules in `support/` are the exemptions — no `main`, no `failsafe`, nothing
  to expect. `harness/run.py` sweeps this and **prints its denominator**,
  because the three `defect/missing_failsafe/` cases went two days with no
  marker at all and the silence looked exactly like a pass.

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
| `probe05_payload_enum.npk` | a payload enum in a `pick` and in a `Vec` | `FORMAT_MODEL.md` F-4, `SAFETY.md` S-3 |
| `probe05b_derive_eq_refused.npk` | *(must not compile)* `#[derive(Eq)]` on a payload enum | O-N10 |
| `probe06_generic_vec.npk` | a generic `Vec<T>` with `move`, at a scalar `T` and an owning one | TM-005, TM-106, `BUILD.md` B-12, `SAFETY.md` S-18b |
| `probe06b_element_leak.npk` | 2 000 000 × {init, push, free the block only} — what an orphaned element costs | TM-106, `SAFETY.md` S-18b — the leaking half |
| `probe06c_element_drop.npk` | the same, one line different: `free_names` first | the same — the remedy half. **Both exit 0**, which is the point |
| `probe07_negative_div.npk` | does signed `/` truncate toward zero and `%` take the dividend's sign? | TM-016, `CALENDAR.md`'s negative years |
| `probe08_readlink.npk` | `readlink` through `sys`, with the returned length as the authority | `HOST.md` H-13, H-14, H-15 |
| `probe09_environ_split.npk` | `environ()`, every entry as `KEY=VALUE`, and `TZ` split by prefix. **Needs `TZ=Europe/Kyiv` exported**; exits **30** if `TZ` is absent and **39** if it is present and wrong (TM-116) | `HOST.md`, TM-110 |
| `probe09b_environ_view_returned.npk` | a view of an environment entry, **returned**, and read after its frame died. **Needs `TZ=Europe/Kyiv` exported**, same two codes as its neighbour — **30** absent, **39** wrong (TM-116) | TM-110 — the pointer-shaped root, with a parameter confound |
| `probe10_view_edges.npk` | the five borrow edges, and §1 is the discriminator: an `alloc`'d block viewed and returned with **no parameter in the root chain** | TM-110, `SAFETY.md` S-22 |
| `probe10b_view_of_temporary_refused.npk` | *(must not compile)* a view of a **temporary**, returned | TM-110 — fires `NITPICK-BORROW-012` |
| `probe10c_view_of_move_param_refused.npk` | *(must not compile)* a view of a **`move` parameter**, returned | TM-110 — a `move` parameter is the callee's own |
| `probe11_failsafe_arms.npk` | the `failsafe` arm contract: an import that declares and raises one `error:` | TM-017, TM-107, `SAFETY.md` S-2/S-4/S-4b/S-4c/S-6 |
| `probe11b_arm_omitted_refused.npk` | *(must not compile)* the same, minus one arm | the same rules — the negative half TM-017 rests on |
| `probe11c_import_arm_cost.npk` | *(must not compile)* what an imported module's **arithmetic** costs a consumer | TM-107, `SAFETY.md` S-4b |
| `probe11d_floor_only.npk` | the **unconditional floor**: nothing imported, nothing computed | TM-107 — the control the other three are measured against |
| `probe11e_unused_import_refused.npk` | *(must not compile)* is the arm owed by the import, or by the call? | TM-107, `SAFETY.md` S-4c |
| `probe11f_declared_unraised.npk` | does a `pub error:` **declaration** cost an arm, or does the first `fail`? | TM-107, `SAFETY.md` S-6 |

Probes 09 and 10 were planned in `0.0.0.md` §4 and **held, not merely
unwritten**: they are the borrow-edge probes, and the author ruled O-N9
BLOCKING (Q-5), so they waited for the compiler's cycle 1.5.1b rather than
being written against a rule that was about to change. **The hold ended on
2026-09-04** and all five files are here. `defect/` carries the reproductions
of every defect the subcycle found — and `defect/missing_failsafe/` is now a
**regression suite** rather than a reproduction, since O-N11 is fixed.

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

### Why 05 has a `b`

Probe 05's plan asked for `#[derive(Eq, Debug)]` on the payload enum. `Debug`
is fine; **`Eq` does not compile**, and the diagnostic lands in `<derived-1>` —
a synthetic module the user cannot open. Worse, `#[derive(Ord)]` on the same
declaration *does* compile and its `cmp` ignores the payload. So 05 derives the
five that are correct, 05b pins the refusal with its exact diagnostic, and the
silent half — which is the dangerous one — is reproduced in
`defect/derive_payload_enum/`. That is **O-N10**, and it is why this subcycle
stopped for the third time.

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

### Why 11 is six files

Probe 11's plan asked for two programs: one whose `failsafe` names the arms
REACH-002 requires, and its twin omitting one. Those are `probe11` and
`probe11b`, and they answer the question that was asked — **a missing arm is a
compile error**, so TM-017's budget is a constraint and not a convention.

The other four exist because the two-file answer would have been *true and
misleading*. Writing them turned up a bigger fact than the one being checked:
the arm set is computed over **every module in the program graph**, so an import
charges a consumer for its **arithmetic** as well as its error identities.

- **11d** imports nothing and computes nothing. It compiles and runs with four
  arms, which pins the unconditional floor. It is the **control**: 11c's
  `failsafe` is 11d's, character for character.
- **11c** imports a module that divides, indexes and adds and declares **no
  error at all**, with 11d's `failsafe`. Refused, four times, for `DivByZero`,
  `DivOverflow`, `IntOverflow` and `OutOfBounds`. Those four arms are the
  import's, and `SAFETY.md` §2's table said nothing about them until TM-107.
- **11e** imports the raiser and never calls it. Still refused — the arm is
  owed by the **import**, not by the call.
- **11f** imports an identity that is **declared and never raised**. Compiles.
  So the charge is levied by a `fail`/`?!`/`!!!` **site**, and a generator that
  counts `error:` declarations would overstate every bill.

The whole family costs about 0.6 s. `probe11_arm_contract.txt` beside them holds
every command and every exit code verbatim, on the same principle as `04b`'s.

## `support/`

Modules that probes **import**. Not probes: no `main`, no `failsafe`, and
`tests/probe/*.npk` does not glob them. See
[`support/README.md`](support/README.md). Only probe 11 uses them, because it is
the only probe whose question is about importing.

## `defect/`

Not probes. Reproductions of compiler defects that cycle 0.0.0 found and that
this library must not work around — see
[`defect/README.md`](defect/README.md). Each is deleted only when its defect is
closed. The O-N4 reproduction there costs about **6 seconds and 580 MiB**;
`probe04_big_fixed_table.npk` costs 281 seconds and 30.9 GiB. The
`missing_failsafe/` reproduction costs a tenth of a second.
