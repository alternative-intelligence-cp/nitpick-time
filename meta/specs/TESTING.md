# Testing

The instruments. The compiler project's recurring finding is that **the checks
that diff two lists found the holes and the tests did not**, and that a suite
which only ever agrees with what it is handed reports green while checking
nothing. This document is `ntime`'s answer to both.

`ntime` is unusually lucky: it is almost entirely pure arithmetic over a small
domain, so several of its properties can be checked **exhaustively** rather
than sampled. Where that is possible it is the gate, and §3 says where.

---

## 1. The stages

[`BUILD.md`](BUILD.md) §3 lists them; this is what each is *for*.

| Stage | Answers |
|---|---|
| `parse` | every source in the tree is readable by the real parser — the grammar is never quietly made partial. **A whole-tree stage, not a `[[test]]` entry**, and it asks `$NPKC` rather than the compiler's `tools/parse_check`: TM-123 has the measurement and the reason. Its value here is the **19 files of 50 that no other stage roots** |
| `compile` | **the public API is importable, and the program that imports it RUNS** — `tests/conformance/`, held to `kind = "positive"`, judged on the run's exit code. It is not `accept`: see `BUILD.md` B-4b and TM-114 for why "accepted in silence" is the shape a program with no `failsafe` walks through |
| `accept` | *(the stage exists upstream; this library does not use it — TM-114)* |
| `check` | every documented refusal actually refuses, with exactly its code |
| `program` | the library does what it says, judged by exit code, at -O0 and under `opt -O2`. **Membership is per file, on its own header** (`BUILD.md` B-4c, TM-119): `expect-error:` makes it a refusal member, `expect-exit:` a run member, and neither is a failure rather than a skip |
| `golden` | formatted output is exactly the bytes it is supposed to be |
| `sweep` | the exhaustive properties, run in full |

---

## 2. What the harness checks about the tree

Not tests. Checks that diff the library against the documents describing it,
run on every full invocation, in the compiler's tradition where every one of
them found something on its first run.

| Check | Diffs |
|---|---|
| `check_purity` | `src/` outside `src/host/` against a ban list — `sys(`, `mono_now`, `environ`, `read_file`, `open`, `write`. **`SAFETY.md` S-10, and the most important check in the suite.** It is also the **only** one that answers the question: the build's undefined-symbol scan cannot see a syscall, because `npk_sys6` is the runtime's own and is in its allowlist by construction (`BUILD.md` B-2c, TM-118, `nitpick-regex`'s RX-120) |
| `check_host_isolation` | no module outside `src/host/` and `src/lib.npk` names a `host_` symbol |
| `check_tables_regenerate` | the committed zone tables against a fresh generator run, byte for byte |
| `check_table_invariants` | every transition slice sorted and strictly increasing; every type index in range; every name-pool offset in range; the zone-name index lexicographically sorted |
| `check_error_budget` | the count and names of public `error:` declarations against `SAFETY.md` §2's table |
| `check_failsafe_arms` | the generated per-module arm list against programs that import each module and compile their `failsafe` |
| `check_layering` | every `use` edge against `BUILD.md` §6's diagram |
| `check_no_owning_fields` | every value stored in a table or array declares no owning field |
| `check_int128_sites` | `int128` appears at exactly the three sites `SPAN_MODEL.md` §5 names, and nowhere else |
| `check_constants_named` | no bound outside `src/core/limits.npk`; no magic 86400, 146097, 719468 or 1000000000 outside the algorithm module that owns it |
| `check_no_format_string` | no function anywhere takes a pattern `string` and interprets it — `FORMAT_MODEL.md` F-5's rule, made checkable |
| `check_raw_index` | no `.items[` outside `src/core/vec.npk` and no `.ptr[` outside `src/core/bytes.npk`. `Vec<T>.items` and `Bytes`' buffer body are **bare pointers**, which the language does not bounds-check (TM-108, `SAFETY.md` S-17b), so the accessor pair is the only bound there is |
| `check_expect_headers` | **the tree partitioned three ways, with the denominator printed** (TM-115): every `.npk` is under `src/` (judged by "it compiles"), or under `tests/` with an `expect-` marker of its own or a NAMED exemption, or it is unowned — and unowned is a failure. The exemption list is diffed in both directions, so an exemption naming a file that is gone fails too |
| `check_specs_current` | **reports, does not fail**: spec citations that no longer resolve |

**Rule V-1.** `check_purity` and `check_int128_sites` are the two that matter
most, because they guard the two claims this library makes that are easy to
break by accident and hard to notice: that it is reproducible, and that its
arithmetic does not silently overflow.

**Rule V-1a (TM-126) — a check runs from the cycle it can be written, and its
pending siblings are PRINTED.** Nine of the fourteen above are live as of cycle
0.0.3, several over a subject that is currently empty — which is the right
answer, and is what makes the check exist on the day the first table type is
written rather than be invented in the same week as the thing it guards. The
other four print on every run as `PEND`, each naming **the cycle that turns it
on and why it cannot run today**, because a family whose gaps are invisible is a
family nobody completes:

| Pending | Live from | Why not now |
|---|---|---|
| `check_int128_sites` | 0.2 | `SPAN_MODEL.md` N-20 says three sites and §5's table marks one (O-X6). A rule invented to make a count come out right is worse than an acknowledged gap |
| `check_no_format_string` | 0.4 | there is no function in `src/` yet, so there is no signature to read |
| `check_tables_regenerate` | 0.5 | the mechanism exists and has been red (`repro.py --between`); what is missing is a generator and a committed table |
| `check_table_invariants` | 0.5 | sorted, in range, indices valid — of tables that do not exist |

**Rule V-1b (TM-115) — every sweep states its denominator, green or red.** A
sweep that matched nothing and a sweep that opened nothing print the same line,
so the count of files opened is part of the result and not part of the
debugging. This is not a style rule: it is how the three
`tests/probe/defect/missing_failsafe/` cases went two days with **no `expect-`
marker at all** — the sweep that would have caught them could not see them, and
its silence was indistinguishable from a pass. A check whose subject is empty
(`0` files under `tests/`) fails rather than passes.

**Rule V-1c (TM-115) — an exemption is NAMED, carries its reason, and is diffed
in both directions.** A pattern exemption silently excuses whatever is later
placed under it. A named one that outlives its file silently excuses the next
file with that name. Both directions are checked.

**Rule V-1d (TM-116) — a test with a precondition states it in its header and
exits a code no substantive assertion in that file uses.** `probe09b` needed
`TZ=Europe/Kyiv` and, run without it, exited **10** — its own "the returned
view is not the entry", which is the one question it exists to ask. An unmet
precondition that arrives as a verdict is worse than a failure, because it is
believed. `probe09` and `probe09b` now share **30** (the variable is absent)
and **39** (present and wrong).

**Rule V-1e (TM-120) — a precondition the runner can HONOUR, and an environment
it constructs.** V-1d gives an unmet precondition a name; it does not stop the
run being red. The `// env: NAME=VALUE` marker (`BUILD.md` B-5c) states the
precondition where the test is, and the harness builds each program's
environment from a **declared base plus that file's markers and nothing else**.
Inheriting would make every `environ()`-reading test's verdict a property of
whoever ran it. **The base is deliberately non-empty**: under an empty
environment `probe09_environ_split` exits 10, a substantive code, so an empty
base would recreate V-1d's defect at the runner instead of the file.

**Rule V-1f (TM-121) — an expectation that does nothing is worse than none.**
The marker block is contiguous from line 1 and a marker-shaped line below it
**fails** rather than being ignored. The case that matters is not the prose
already in this tree; it is the `// stress: 40` somebody adds mid-file next
year, believing it took effect.

---

## 3. The exhaustive gates

**Rule V-2 (TM-026) — where a property can be checked over its whole domain, it
is, and that is the gate.** Sampling is what you do when you cannot enumerate.

| Gate | Domain | Size | Cycle |
|---|---|---|---|
| civil ↔ day-number round trip, both directions | every day in `[−9999-01-01, +9999-12-31]` | 7 304 485 × 2 | 0.1 |
| `date_to_days` strictly increasing | the same sweep | — | 0.1 |
| weekday advances by one mod seven | the same sweep | — | 0.1 |
| month lengths match the leap rule | every (year, month) in range | 239 976 | 0.1 |
| ISO week/ordinal round trip | the same sweep | — | 0.1 |
| `Timestamp` ↔ civil round trip | every second would be too many; every **day boundary**, plus every second of 512 randomly chosen days | 7.3 M + 44 M | 0.2 |
| zone transition sweep | every transition in the table, ±1 second | ~27 000 × 4 | 0.6 |
| format/parse round trip | the generated corpus × every layout | ~10⁶ | 0.4 |

**Rule V-3 — the civil sweep is the strongest statement this library makes.**
It is self-evident (a round trip is obviously the right property), it needs no
external corpus to trust, and it covers the negative years that no external
oracle reaches. It runs in seconds. Nothing else in the plan is as cheap for
as much certainty.

---

## 4. The round trips

**Rule V-4 — the general shape**: *if the library produces a representation,
write the reverse and check the fixed point.* `ntime` has three, and each has
a documented exception list rather than a mysterious skip:

1. **civil ↔ days** — no exceptions (V-2).
2. **`Timestamp` ↔ `CivilDateTime`** — no exceptions, by M-11's leap-second
   position: the mapping is a bijection by construction.
3. **format ↔ parse** — **exactly two exceptions**, both named in
   `FORMAT_MODEL.md` F-20: `:60` folds to `:59`, and `24:00:00` folds to the
   next day. The exception list is a committed file with two entries, and a
   test asserts the list has exactly two entries — so a third arriving is a
   red run and not a quiet edit.

**Rule V-5 — the format corpus is generated, not written.** Cycle 0.4 emits
values spanning: both range extremes, the epoch, every month, both leap and
common Februaries, every DST transition in a representative zone set, zero and
maximal nanoseconds, and every offset in ±18:00 at 15-minute granularity.

---

## 5. The cross-oracles

Three, each trusting something external, each **separate from the gates**
because a gate should not depend on somebody else's library being right.

**Rule V-6 — the civil cross-oracle.** A Python generator emits a few hundred
thousand `(y, m, d, day_number, weekday, iso_week, day_of_year)` rows from
`datetime`, committed under `tests/fixtures/civil/`. It covers years 1 … 9999
only, because that is Python's range; the negative half has V-2's
self-consistency and nothing else, which is stated rather than glossed.

**Rule V-7 — the zone cross-oracle.** A Python generator emits, from the
**same pinned tzdata release** via `zoneinfo`, `(zone, utc_second, offset,
abbr, is_dst)` rows covering every transition and a sampling between them,
committed under `tests/fixtures/zone/`. This is the check that the *generator*
read the database correctly — which the transition sweep cannot see, because
that only checks the table against itself.

**Rule V-8 — the format cross-oracle.** RFC 3339's own examples, the HTTP-date
examples from RFC 9110, and the ISO 8601 examples, committed verbatim as
`(text, expected)` pairs. Small, external, and exactly the cases the standards
authors thought were worth writing down.

---

## 6. Fuzzing

**Rule V-9 (TM-030).** The parsers are the only place `ntime` touches bytes it
did not produce, so they are the only place that needs a fuzzer — and they need one
badly, because a date string is a thing programs receive from the network.

`tools/fuzz_parse.py` drives every parser with random bytes and structured
mutations of the corpus. The invariants:

- **never traps** — no arithmetic overflow, no out-of-range index;
- **always terminates** — every parser is a bounded straight-line scan
  (`FORMAT_MODEL.md` F-16), so this is provable and the fuzzer confirms it;
- **`consumed` never exceeds the input length**;
- **a success is round-trippable** — anything that parses, formats and
  re-parses to the same value.

That last one is the strong invariant, and it is the one that finds the bugs a
crash-only fuzzer misses.

**Rule V-10 — anything the fuzzer found is committed as a permanent case**, in
`tests/fixtures/fuzz/`, forever.

---

## 7. Stress

**Rule V-11 — `// stress: 40` on everything that reads a clock.** `src/host/`'s
five functions are the only place `ntime` can behave differently on two runs,
so they are the only place that needs it — but they need it, because "the clock
went backwards between two calls" is exactly the shape of defect that hides
behind a single green run.

---

## 8. Performance

**Rule V-12.** `harness/bench.py` writes a line per benchmark into
`meta/bench/<date>.txt` and the harness fails on a regression worse than 20%
against the committed baseline on the same machine. The benchmarks: civil ↔
timestamp conversion, zone offset lookup at a transition and far from one,
RFC 3339 format and parse, and `Period` addition across a DST boundary.

**Rule V-13.** A benchmark is not a test and never gates on absolute numbers.

---

## 9. The harness is tested

**Rule V-14 — the self-check.** `harness/selfcheck.py` feeds the harness wrong
expectations and requires it to report every one as a failure:

1. a `program` case whose `expect-exit` is wrong by one;
2. a `check` case expecting a code the compiler does not report;
3. a `check` case reporting a code no expectation names (D-237's rule);
4. a `golden` case whose bytes differ by one byte;
5. a `parse` case that does not parse;
6. a generator whose output differs from the committed table by one line
   — **pending until cycle 0.5**, and it prints as pending rather than passing.
   The *mechanism* already exists and has already been red: `repro.py --between`
   runs a generator between two builds and requires the IR unchanged, driven red
   at 0.0.2 against a generator whose rows came out of an unsorted `set`;
7. a `sweep` case that is silently skipped — the harness must notice it did not
   run;
8. **a program whose `failsafe` has been deleted** — this repository's own
   addition, because `npkc` exit 0 is not well-formedness (B-4b, TM-112) and
   V-14's seven do not cover it.

**Rule V-14b — every case carries a CONTROL, in the same run.** Each case's
scratch tree holds a correct twin of the faulted file, and the case asserts a
`PASS` for it beside the `FAIL`. Without that, a red proves only that
*something* went wrong — the tree, the manifest, the toolchain — and a
self-check satisfied by a broken harness is worse than none. It is 0.0.2 §5.3's
own argument (*a red that came from the mechanism rather than from the fault
would prove nothing*) made a rule.

**Rule V-14c (TM-126) — every check in §2 is commissioned the same way.** The
tree checks are pure functions of a directory, so the self-check plants one
violation per check and requires each to find it, then runs it over a clean
control and requires silence. This costs milliseconds and no compilation, and it
is what makes *"written"* and *"working"* different words. **A check that has
never failed has never been shown to work**, and "written but not run" is the
weakest state an instrument can be in — weaker than absent, because absence is
visible.

**Rule V-14d — the S-6 arm generator is commissioned against the compiler.**
`check_failsafe_arms` computes an arm bill from source and diffs it against the
identity list `NITPICK-REACH-003` itself prints. The self-check runs that diff
over three modules whose bills TM-107 measured — `probe11_silent_lib` (declares
an identity and never raises it: **4**, the floor), `probe11_arms_lib` (raises
one: **5**) and `probe11_calc_lib` (declares none and costs **8**, the floor
plus its own arithmetic). Those three are TM-107's three constraints, one each,
and the numbers are re-measured on every run rather than remembered.

**Rule V-15.** The self-check runs **first** in every full invocation, and its
failure is **fatal** — nothing below it runs. A harness that has not proven it
can fail has not proven anything, so a green suite underneath a red self-check
is a state this ordering makes unreachable rather than merely discouraged. A
self-check that *could not run* — no `$NPKC`, no manifest — is a **failure and
not a skip**, because silence there is indistinguishable from a pass.

**Rule V-16 (TM-122) — a sweep declares its domain and PRINTS what it visited.**
A `sweep` member carries `// sweep-count: N` and writes exactly one line
`swept <N>` to stdout; the harness requires the two to be equal. **An exhaustive
loop that returns after one iteration exits 0 exactly like one that ran to the
end** — no exit code distinguishes them, and neither does wall time on a sweep
that takes seconds. Nothing outside the program can tell the difference, so the
program is made to testify. A `sweep` member with no `sweep-count` is a failure,
and a `sweep-count` on a member of any other stage is a failure too, because
there it is an expectation that does nothing (V-1f).
