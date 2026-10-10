# `tests/probe/`

Small Nitpick programs that ask the **compiler** a question. Each one pins a
language fact that `meta/specs/` depends on, so that a change to that fact is a
red run here rather than a wrong date in cycle 0.6.

Probes 01 to 11 were written in cycle 0.0.0, governed by
[`../../meta/roadmap/done/0.0/0.0.0.md`](../../meta/roadmap/done/0.0/0.0.0.md), which
carries their verdict table; every later probe was added by the subcycle whose
question it answers, and its row below and its own header say which. Picked up
by the harness as ordinary `program`-stage entries from cycle 0.0.2.

## The rules

- **A probe is a program**, never a library file (0.0.0 P-1). It has its own
  `main` and `failsafe` and imports nothing from `src/`.
  *(Cycle 0.1.5's second half, the cycle audit's C9: the last clause has been
  false since cycle 0.1.0c, and no decision said so. P-1 was written for
  questions about the LANGUAGE, which a probe asks with no library in the
  way. From 0.1.0c the questions included the language's verdict on this
  library's own declarations — a consumer's struct literal of a sealed type,
  a read of a hidden field, a copy of a `Vec`, `Pod` for an owner — and the
  decisions that asked them put each probe here importing the module it
  asks about: TM-156, TM-157, TM-193, TM-194 and TM-195. **Eleven import from
  `src/`**, by `lexical.imports` at that close: `probe15`, `probe16`,
  `probe16b` … `probe16i` and `probe19`. **The rule is now:** a probe asks the
  compiler one question; one about the language imports nothing from `src/`,
  and one about the language's verdict on the library imports the module it
  asks about and nothing more. Either way it is a program, with its own `main`
  and `failsafe`.)*
- **A probe is never deleted** (P-5). The verdicts are a regression suite; a
  probe that has served its purpose has not stopped being evidence.
- **Every probe exits 0 on success** and a distinct positive code per assertion
  it fails, so a failure names itself. `exit 0` additionally asserts, through
  D-151, that **no `wild` allocation is live at exit** — a statement about
  coverage rather than a proof of cleanliness. **D-151 watches `wild` only**, so
  a probe that allocates nothing `wild` cannot trip it on any exit path, and a
  **managed** body is outside it entirely: probe 06's `Vec<string>` orphaned two
  million element bodies, retained 125 MiB and **exited 0** (TM-106). A probe
  over an owning container therefore asserts its memory too — **since cycle
  0.1.4b by a `heap:` marker on the runtime's own `NPK_HEAP_STATS` count and a
  `cap:` marker under a 64 MiB address space** (`../../meta/specs/TESTING.md`
  V-17), where this said *"a `ulimit -v` cap today, a `peak_live` bound from
  the compiler's `NPK_HEAP_STATS` after the 1.5.1b re-pin"* and neither was
  run by the harness. `probe06b`/`probe06c` and `probe12`/`probe12b` carry
  both. **What follows was the rule until then — assert the cap, not a
  peak-RSS number:**
  `/usr/bin/time -f %M` reports `0 KiB` for these static binaries, including
  for `probe11d_floor_only.npk`, so it cannot tell a clean run from a small
  one. `probe06b`/`probe06c` are the committed pair.
  **Nine probes here carried the older one-line comment** *"exit 0 additionally
  asserts that nothing leaked"* — **01, 02, 02b, 03, 04, 04b, 05, 07 and 08** —
  and **all nine were reworded at 0.0.2**, when the harness picked this
  directory up and every probe was re-run anyway. Each was locally harmless:
  none of those files allocates a managed container. **The list came from the
  command and not from the probes anybody compiled:**
  `git grep -l 'additionally asserts that nothing leaked' -- '*.npk'`, nine
  files out of fifty tracked. `probe04_big_fixed_table.npk` had been missed once
  for exactly that reason — it was the one probe here that was never compiled
  by hand (O-N4's 281 s / 30.9 GiB case at `950bb1d`; since the compiler's
  1.5.1b fixed O-N4 it runs in the suite in under two seconds — a dated note of
  cycle 0.1.5), so it drops out of any list built
  from what a session ran, while remaining a first-class probe row in the table
  below. `probe06` and `probe11` were **confirmed by reading** to be correctly
  outside the nine: both were written with the `wild` wording already. **A wider
  sweep found a tenth line the exact one could not** — `git grep -n 'nothing
  leaked' -- '*.npk'` gives ten lines across the same nine files, the extra
  being a differently worded copy in `probe02_int128.npk`'s header prose. Both
  patterns now match **0**.
- **A probe that pins a fact the specification already states asserts the
  expected answer** (P-6) rather than printing what it found, so a change to
  that answer is a red run.
- **A file's `mod:` name equals its basename**, and no identifier may begin
  with a digit — hence `probeNN_topic.npk` and never `NN_topic.npk`.
- **A probe with a PRECONDITION states it in the header, as a MARKER the runner
  honours, and exits a code no substantive assertion in that file uses**
  (TM-116 and TM-120, `TESTING.md` V-1d/V-1e). Two probes here read `$TZ` and
  both carry `// env: TZ=Europe/Kyiv`. **The harness constructs each program's
  environment** from a declared base plus that file's markers and passes nothing
  of its own through, so these two give the same verdict on a developer's shell
  as in CI. The base is deliberately **non-empty** (`NTIME_HARNESS=1`): under a
  genuinely empty environment `probe09_environ_split` exits **10**, one of its
  own substantive codes, which is TM-116's defect arriving through the runner
  instead of the file. Two Run without it, `probe09b` used to exit **10** — its
  own *"the returned view is not the entry"*, which is the single question it
  exists to ask — so an unmet precondition and a real finding about the
  language were the same signal. Both files now use **30** for "the variable is
  absent" and **39** for "present and not `TZ=Europe/Kyiv`". Note the second:
  `TZ=Europe/Kiev`, the old IANA spelling, used to pass **both** probes at exit
  0, because every byte either one checks is equally true of `Kiev` and `Kyiv`.
- **Every `.npk` under `tests/` carries an `expect-` marker or is named as an
  exemption with its reason** (TM-115, `TESTING.md` V-1b/V-1c). The four
  modules in `support/` (three until cycle 0.2.0's relay specimen) are the
  exemptions — no `main`, no `failsafe`, nothing to expect. `harness/run.py`
  sweeps this and **prints its denominator**,
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
| `probe05b_derive_eq_refused.npk` | `#[derive(Eq)]` on a payload enum — refused at `950bb1d`, and since O-N10's fix a POSITIVE regression case: it compiles and answers correctly *(this row said "must not compile" until cycle 0.1.5)* | O-N10, TM-111 |
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
| `probe12_set_overwrite_leak.npk` | 2 000 000 overwrites of one occupied `Vec<string>` slot — is `0.0.4.md`'s list of the entries that discard an element complete? (No: an overwrite discards one.) | TM-132, `SAFETY.md` S-18b — the leaking half, held by `heap:` and `cap:` (V-17) |
| `probe12b_set_overwrite_drop.npk` | the same overwrites with the old element moved out into a scope that ends first — the remedy's cost | the same — the remedy half, `heap:` bounded |
| `probe13_vec_bounds_guard.npk` | an accessor that indexes a `#wild_slice` laid over the live count — does the compiler's own bounds guard come back? | TM-129, `SAFETY.md` S-17b, S-17c |
| `probe13b_vec_index_past_end.npk` | the same accessor one PAST THE END — exits `94`, `OutOfBounds` | the same — the negative twin |
| `probe13c_vec_index_negative.npk` | the same accessor at a NEGATIVE index — exits `94` | the same — `0 <= i`, the half a hand-written `i < count` misses |
| `probe13d_vec_bare_pointer_unchecked.npk` | the control: the same out-of-range read through the BARE pointer returns a planted sentinel and does not trap | TM-108 — written at `int64` since cycle 0.1.4c, TM-190 |
| `probe14_error_payload_refused.npk` | *(must not compile)* can an `error:` identity carry a payload? | TM-147, `SAFETY.md` S-3, `CALENDAR.md` C-5b — `NITPICK-PARSE-001` |
| `probe15_civil_literal_bypass.npk` | *(must not compile)* may a consumer build an unreal `CivilDate` by struct literal? | TM-157, `CALENDAR.md` C-8c — `NITPICK-TYPE-079` since cycle 0.1.0c |
| `probe16_vec_count_write_refused.npk` | *(must not compile)* may a consumer assign a `Vec`'s `count`? | TM-156, `SAFETY.md` S-17b — `NITPICK-TYPE-079` |
| `probe16b_vec_items_read_refused.npk` | *(must not compile)* may a consumer index a `Vec`'s `items` directly? | TM-156 — `NITPICK-TYPE-080` |
| `probe16c_bytes_len_write_refused.npk` | *(must not compile)* may a consumer assign a `Bytes`' `len`? | TM-156 — `NITPICK-TYPE-079` |
| `probe16d_civil_field_write_refused.npk` | *(must not compile)* may a consumer assign month 13 to a real `CivilDate`? | TM-157, `CALENDAR.md` C-8c — `NITPICK-TYPE-079` |
| `probe16e_sealed_reads.npk` | the positive twin: every sealed field still READS from outside, and `bytes_capacity` reads the hidden body's capacity | TM-156, TM-157, TM-195 |
| `probe17_fixed_owning_reads.npk` | may `fixed` storage hold a `string` — as an element, a row's field, a scalar — and be read without moving it? | `SAFETY.md` S-19b — the positive twin |
| `probe17b_fixed_row_copy_refused.npk` | *(must not compile)* a row whose element owns, copied out by value — the accessor's read | S-19b — `NITPICK-TYPE-046` |
| `probe17c_fixed_string_copy_refused.npk` | *(must not compile)* an element of a `fixed string[2]`, copied out | S-19b — `NITPICK-TYPE-046` |
| `probe16f_vec_copy_refused.npk` | *(must not compile)* a `Vec` copied into a second binding | S-18g — `NITPICK-TYPE-046` |
| `probe16g_vec_assign_refused.npk` | *(must not compile)* one `Vec` assigned over another | S-18g — `NITPICK-TYPE-046` |
| `probe16h_vec_holder_copy_refused.npk` | *(must not compile)* a struct holding a `Vec`, copied | S-18g — `NITPICK-TYPE-046` |
| `probe16i_bytes_body_write_refused.npk` | *(must not compile)* a write through `Bytes.body`'s pointer | S-17b — `NITPICK-TYPE-080` |
| `probe18_zero_length_owner.npk` | does a `string[0]` field cost nothing, move, drop, and leave an `int64[0]` twin copyable? | S-18g — the language fact under `Vec`'s marker |
| `probe18b_zero_length_owner_copy_refused.npk` | *(must not compile)* a struct whose one owning field is `string[0]`, copied | S-18g — `NITPICK-TYPE-046` |
| `probe19_pod_owner_refused.npk` | *(must not compile)* `Copy` claimed for `string` — until cycle 0.2.0a, `Pod` implemented as its trait declared it, `TYPE-047` (TM-211) | S-18h — `NITPICK-TYPE-087` |
| `probe20_instant_literal_refused.npk` | *(must not compile)* an `Instant` built by a consumer's struct literal | `TIME_MODEL.md` M-2, TM-215 — `NITPICK-TYPE-079`, twice: one report per sealed field *(once since compiler `7e91730`, naming both: its DEF-165, TM-259)* |
| `probe20b_instant_conversion_refused.npk` | *(must not compile)* `instant_to_timestamp` called | M-3, TM-010 — `NITPICK-RESOLVE-002` |
| `probe20c_instant_as_timestamp_refused.npk` | *(must not compile)* an `Instant` handed to `Timestamp`'s `cmp` | M-3, TM-221 — `NITPICK-TYPE-007` |
| `probe20d_timestamp_as_instant_refused.npk` | *(must not compile)* a `Timestamp` handed to `instant_since` | M-3, TM-221 — `NITPICK-TYPE-007` |
| `probe20e_instant_cast_to_timestamp_refused.npk` | *(must not compile)* `a =>! Timestamp` — the unchecked cast | M-3, TM-221 — `NITPICK-TYPE-032` |
| `probe20f_timestamp_cast_to_instant_refused.npk` | *(must not compile)* `t =>! Instant` — the unchecked cast | M-3, TM-221 — `NITPICK-TYPE-032` |
| `probe20g_construction_from_numbers.npk` | a consumer builds an `Instant` from a `Timestamp`'s numbers through `instant_of`, and a `Timestamp` back through `timestamp_of`, with no `wild` and no `=>!` — the construction M-3 does not refuse | M-3, TM-216, TM-243 — the positive twin of `probe20b` … `probe20f` |
| `probe21_timestamp_literal_refused.npk` | *(must not compile)* a denormalised `Timestamp` built by a consumer's struct literal | M-7, TM-219 — `NITPICK-TYPE-079`, twice: one report per sealed field *(once since compiler `7e91730`, naming both: its DEF-165, TM-259)* |
| `probe21b_timestamp_field_write_refused.npk` | *(must not compile)* a consumer's write to a `Timestamp`'s `nanos` | M-7, TM-219 — `NITPICK-TYPE-079` |
| `probe22_private_etc.npk` *(cycle 0.3.2)* | a program enters a user and a mount namespace of its own, mounts an empty `tmpfs` over `/etc`, and makes a link there that reads back whole and a file whose bytes read back; the kernel refuses a link target of 4 096 bytes and holds one of 4 095 | `TESTING.md` V-1m, `HOST.md` H-15, TM-255 — the shape `tests/unit/system_zone_etc.npk` stands on; 20 … 24 the machine's refusal (V-1d) |

*(Cycle 0.1.3b: the three `probe17` rows are new. **Probes 12 to 16 — cycles
0.0.4 to 0.1.0c — are not in this table**, and the heading above says "What is
here": found at 0.1.3b's planning, and owed to cycle 0.1's close. Each of those
files says in its own header what it asks.)*

*(Cycle 0.1.3c: the seven rows after `probe17c` are new — four more of the
`probe16` family, which assert the library's own access and move rules, and
three language probes — written with the port that makes `Vec` move-only and
bounds `vec_at` by `Pod` (TM-193 … TM-195). The rest of 12 to 16e is still the
close's.)*

*(Cycle 0.1.5, the close: the thirteen rows for probes 12 to 16e are in the
table, each taken from its own header, so "What is here" is every file in this
directory.)*

*(Cycle 0.2.0: the two `probe20` rows are new — `Instant`'s refusals, each a
probe that imports the module it asks about (TM-218).)*

*(Cycle 0.2.1: the six rows after `probe20b` are new — M-3's refusal at the
type, both directions and through the unchecked cast, and `Timestamp`'s seal,
one refusal per probe, each importing `span` and nothing more (TM-221).)*

*(Cycle 0.2.4b: the `probe20g` row is new — the path M-3 does not refuse, a
construction from numbers in writing, compiled and run so the restated rule is
checked (TM-243; the cycle audit's C2).)*

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
stopped for the third time. *(Fixed at pin `94874ce`, TM-111: both derives
compile and read every payload field, and 05b — the name kept, a record of what
it asked — is a positive regression case since. This paragraph is cycle
0.0.0's.)*

### Why 04 has a `b`

O-N4 made `probe04_big_fixed_table.npk` cost **281 seconds and 30.9 GiB** at
compiler `950bb1d`, so it was not runnable in CI and not re-runnable by a reader.
*(The compiler's 1.5.1b fixed O-N4, struck here at cycle 0.0.6: at `c970483`
the probe runs in under two seconds on both legs, a member of the suite like
any other. What follows is why `04b` exists, and it is still the reason.)* Its
two questions
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
  `failsafe` is 11d's, character for character. *(Six arms since compiler
  `c3bdae2`, whose floor gained `StackExhausted` and `MachineFault` — TM-155;
  the two files still share their `failsafe`, and the four arms 11c is refused
  for are still the import's.)*
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
the only probe whose question is about importing. *(And since cycle 0.2.0 one
no probe imports: `probe11_relay_lib.npk`, the self-check's fourth arm-bill
specimen, which only its part C compiles — TM-217.)*

## `defect/`

Not probes. Reproductions of compiler defects this library found — cycle
0.0.0 first, cycles 0.1.3b and 0.1.4 since — and must not work around: see
[`defect/README.md`](defect/README.md). **When a defect is fixed its
reproduction is not deleted: it becomes the regression test that proves the
fix, with its old verdicts as the control** (TM-154, TM-189). *(Until cycle
0.1.5 this said "Each is deleted only when its defect is closed", which
TM-154 reversed at cycle 0.1.0b; and it quoted O-N4's reproduction at about 6
seconds and 580 MiB and probe 04 at 281 seconds and 30.9 GiB — `950bb1d`'s
numbers, before the compiler's 1.5.1b fixed it. At `c970483` each takes under
two seconds.)*
