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
| `parse` | every source in the tree is readable by the real parser — the grammar is never quietly made partial. **A whole-tree stage, not a `[[test]]` entry**, and it asks `$NPKC` rather than the compiler's `tools/parse_check`: TM-123 has the measurement and the reason. Its value here is the **30 files of 78 that no other stage roots** <!-- [[sweep: npk_total=78]] --> |
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
| `check_layering` | `BUILD.md` §6's diagram against `src/` — its **edges** (every `use`) and its **nodes** (every layer the diagram names holds at least one module). The node half is D1's repair: cycle 0.0.1's acceptance claimed `run.py` "asserts the count is at least 7" and no such assertion was in the tree, so *"a directory whose placeholder was deleted rather than replaced is invisible to the sweep"* was live for four subcycles inside a ticked box |
| `check_no_owning_fields` | every value stored in a table or array declares no owning field. **It could not see a SINGLE-LINE struct until cycle 0.0.6 and both of this repository's structs are one** (TM-138), so neither type's real fields had ever been examined while the check reported `0 of 0`; the self-check now plants the same violation in both spellings |
| `check_int128_sites` | `int128` appears at exactly the three sites `SPAN_MODEL.md` §5 names, and nowhere else |
| `check_constants_named` | no bound outside `src/core/limits.npk`; no magic 86400, 146097, 719468 or 1000000000 outside the algorithm module that owns it |
| `check_no_format_string` | no function anywhere takes a pattern `string` and interprets it — `FORMAT_MODEL.md` F-5's rule, made checkable |
| `check_raw_index` | **no index through a bare pointer in `src/`, by FIELD or by BINDING.** `Vec<T>.items` and `Bytes`' buffer body are bare pointers, which the language does not bounds-check (TM-108, `SAFETY.md` S-17b), so the accessor pair is the only bound there is. It was two literal substrings until cycle 0.0.6 and was **evadable in one line** — bind the pointer to a local and index the local, which was built at `aaffb87`, ran, and read four elements past the live prefix while the check reported `0 sites` (TM-144). Every `wild T->:name` in a file is now watched. **The limit is stated: it is lexical and per-file**, so a bare pointer passed to another function and indexed there is still not covered; cycle 0.5 gets the widening |
| `check_expect_headers` | **the tree partitioned three ways, with the denominator printed** (TM-115): every `.npk` is under `src/` (judged by "it compiles"), or under `tests/` with an `expect-` marker of its own or a NAMED exemption, or it is unowned — and unowned is a failure. The exemption list is diffed in both directions, so an exemption naming a file that is gone fails too. **It says a marker is WELL-FORMED and nothing about whether it is TRUE**; that is `check_exemptions_live`'s and `run_defect_corpus`'s job, and the gap between the two readings was TM-141 |
| `check_exemptions_live` (TM-137) | **every exemption's recorded VERDICT, re-derived from the file on every run.** An exemption's reason is a claim about what the compiler does, and the compiler moves. The superseded mechanism checked only that the named file still existed: O-N17 landed, two files went from stopping at `llc` to running clean, the suite stayed green and nothing said a word |
| `run_defect_corpus` (TM-141) | **every `expect-` marker under `tests/probe/defect/`, asserted.** The `probe` entry is non-recursive by design, so the suite selected 0 of these 24 files and 21 committed expectations — the whole regression corpus for four discharged compiler defects — were evaluated by nothing. The inversion was sharp: the 3 files EXEMPT from having an expectation had their verdict re-derived every run, and the 21 that HAD one did not |
| `check_denominators` (TM-142) | **every number TAGGED `[[sweep: name=N]]` against what the tree measures.** The tree went from 50 `.npk` to 78 and eleven sites in six live files still carried the 0.0.3 figures. The harness PRINTS every denominator on every run (V-1b) and no document was diffed against the print. **The mechanism is narrower than "every number": it checks the tagged ones**, and an untagged number is not covered — which is why the marker is ugly enough to notice in review |
| `check_specs_current` | **reports** spec citations that no longer resolve — a renumbering is not a reason to stop a build — and **FAILS on a stale exemption** (TM-145). Those are different animals: a stale exemption is V-1c's both-directions rule, a failure everywhere else in this harness, and the one thing here a green run would otherwise hide. It matters at a cycle close, when archiving `meta/roadmap/<cycle>/` moves the paths two of its keys name. **There is no whole-file entry in its table, as a rule**: `checks.py` marks one excused as long as the file EXISTS, so its reason is never re-derived — TM-137's shape inside the mechanism written to prevent it |

**Rule V-1.** `check_purity` and `check_int128_sites` are the two that matter
most, because they guard the two claims this library makes that are easy to
break by accident and hard to notice: that it is reproducible, and that its
arithmetic does not silently overflow.

**Rule V-1a (TM-126) — a check runs from the cycle it can be written, and its
pending siblings are PRINTED.** The table above has **17** rows: **13 are live**
as of cycle 0.0.6 and **4 print on every run as `PEND`**, and `13 + 4 = 17`
closes. Several of the live ones run over a subject that is currently empty —
which is the right answer, and is what makes the check exist on the day the
first table type is written rather than be invented in the same week as the
thing it guards.

*(**The arithmetic did not close until cycle 0.0.6**, and that is C2. This rule
read "nine of the fourteen above are live", against a fourteen-row table with
four pending: `9 + 4 = 13`. The row that fell out of the count was
`check_expect_headers`, which `run.py` runs as step 4 rather than as a tree
check — and it is the same row V-14c was false about. A rule's own arithmetic
is the cheapest place to notice that a family has a member nobody is counting.
The 13 live are `checks.LIVE`'s 9 — including `check_denominators` — plus
`check_failsafe_arms`, `check_expect_headers`, `check_exemptions_live` and
`run_defect_corpus`, the last three of which `run.py` drives outside step 5
because they need a toolchain or a manifest.)*

The four pending each name **the cycle that turns it on and why it cannot run
today**, because a family whose gaps are invisible is a family nobody
completes:

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

**Rule V-1g (TM-141) — EVERY EXPECTATION IN THE TREE IS EVALUATED, and "in a
bucket" is not "evaluated".** V-1f is about a marker in the wrong place; this
is about a marker in the right place that nothing reads. `tests/probe/defect/`
holds 24 `.npk`: 3 are named in `EXPECT_EXEMPT` and have their verdict
re-derived every run, and the other **21 carried an `expect-exit:` or
`expect-error:` marker that no stage asserted** — the entire regression corpus
for O-N9, O-N10, O-N11 and TM-137. `check_expect_headers` checked the markers
were well-formed; the `probe` entry is non-recursive and selected none of them;
`run_parse` compares only the diagnostic's phase family. §1's description of the
coverage — *"under `tests/` with an `expect-` marker of its own or a NAMED
exemption"* — read as coverage and was, for those 21, membership in a bucket
nobody evaluated. **The arithmetic is printed on every run and asserted:
24 = 3 exempt + 21 asserted.**

**Rule V-1i (TM-146) — "every `.npk` in the tree" means THIS repository, and
what the walk prunes is PRINTED.** A directory holding a `.git` entry is a
separate repository and is not this tree; so is `.nitpick`, which is where CI
checks the pinned compiler out, because `actions/checkout` cannot place a
`path:` outside the workspace. Until cycle 0.0.6 every whole-tree sweep here
walked it — hundreds of *"unowned .npk"*, a denominator wrong by hundreds, and
the `parse` stage putting the compiler's own source in front of `npkc` one file
at a time. **The pruned list is printed beside the denominator**, because
*"78 files, 1 nested repository pruned"* and *"78 files"* are different
statements and only the first can be checked. **Found by CI's first run and by
nothing on the workbench**, which is the argument for pushing at a cycle's close
rather than at convenience.

**Rule V-1h (TM-142) — a derived number in a document is TAGGED or it is
history.** Eleven sites in six live files carried denominators from cycle 0.0.3
after the tree had grown from 50 `.npk` to 78 — `run.py`'s own docstring,
`stages.py` twice, `BUILD.md`, this document, `nitpick.toml` three times and
`OPEN_QUESTIONS.md`. Every one was reachable from the runner's own printed
output and nothing compared them. A number that describes the tree as it is now
carries `[[sweep: name=N]]` and `check_denominators` diffs it against the sweep;
a number inside a roadmap execution record is **history and is correctly
frozen**, and is not tagged. The distinction is tense: present tense is a claim,
past tense is a record.

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

**SEVEN OF THE EIGHT ARE PLANTED, AND THE RUNNER SAYS SEVEN.** Case 6 is
`PEND` until cycle 0.5, so *"this runner has been shown able to fail eight
ways"* — printed on every run, and repeated in `run.py`'s header, `CLAUDE.md`,
`harness/README.md` and the CI workflow — was an overstatement for three
cycles (C3). `0.0/README.md`'s Gate said **seven** and was the only place that
had it right. The number is now derived from `selfcheck.PLANTED_CASES` rather
than typed, in every one of those places that still states it.

**Rule V-14b — every case carries a CONTROL, in the same run.** Each case's
scratch tree holds a correct twin of the faulted file, and the case asserts a
`PASS` for it beside the `FAIL`. Without that, a red proves only that
*something* went wrong — the tree, the manifest, the toolchain — and a
self-check satisfied by a broken harness is worse than none. It is 0.0.2 §5.3's
own argument (*a red that came from the mechanism rather than from the fault
would prove nothing*) made a rule.

**Rule V-14c (TM-126, amended by TM-141) — every LIVE check in §2 is
commissioned, and the exceptions are named here rather than left to be
discovered.** The tree checks are pure functions of a directory, so the
self-check plants one violation per check and requires each to find it, then
runs it over a clean control and requires silence. This costs milliseconds and
no compilation, and it is what makes *"written"* and *"working"* different
words. **A check that has never failed has never been shown to work**, and
"written but not run" is the weakest state an instrument can be in — weaker
than absent, because absence is visible.

**This rule said "every check in §2" and was FALSE when it said it (A5).**
`check_expect_headers` was in §2's table and planted nowhere — the row TM-115
was written to create. `check_exemptions_live`, the mechanism 0.0.5 built to fix
TM-137, was in neither §2 nor the self-check. So of the two instruments that
found cycle 0.0's two worst faults, one was undocumented and neither had ever
been driven. Cycle 0.0.6 made the sentence true rather than softening it:

| Commissioned by | What it drives |
|---|---|
| `selfcheck.PLANTED` | the 9 tree checks of `checks.LIVE`, one planted violation and one clean control each |
| `selfcheck.part_b` directly | `check_layering`'s **node** half — the fault is a file that is NOT there, which no `PLANTED` row can express |
| `selfcheck.part_b_specs_current` | `check_specs_current`, which reports and never fails, so it is shown REPORTING |
| `selfcheck.part_c` (`CALIBRATION`) | `check_failsafe_arms`, against `NITPICK-REACH-003`'s own identity list on three modules with known bills |
| `selfcheck.part_d` | `run._verdict` on three specimens; `check_exemptions_live` on a MOVED verdict; `run_defect_corpus` on an `expect-exit:` wrong by one; `check_expect_headers` on all three of its branches |

**The four `PEND` rows are the named exception**, and they are exempt for the
reason each states: there is nothing in the tree for them to be red about.

**And the parameters exist for this and for nothing else.** `EXPECT_EXEMPT`,
the defect directory and the exemption list are arguments rather than module
constants, because a check that can only be pointed at a corpus where
everything already passes cannot be shown to fail. The instrument that was
built because a check had never failed had itself never failed.

**Rule V-14d — the S-6 arm generator is commissioned against the compiler.**
`check_failsafe_arms` computes an arm bill from source and diffs it against the
identity list `NITPICK-REACH-003` itself prints. The self-check runs that diff
over three modules whose bills TM-107 measured — `probe11_silent_lib` (declares
an identity and never raises it: **4**, the floor), `probe11_arms_lib` (raises
one: **5**) and `probe11_calc_lib` (declares none and costs **8**, the floor
plus its own arithmetic). Those three are TM-107's three constraints, one each,
and the numbers are re-measured on every run rather than remembered.

**Rule V-14e (TM-141) — the specification's list and the harness's list are
one list, or they are two lists that drift.** §2's table, `checks.LIVE`,
`checks.PENDING` and the checks `run.py` drives outside step 5 are four
statements of one family and **nothing diffs them** (D4). They agree today —
re-read row by row at cycle 0.0.6 — and the cost of them disagreeing is
exactly A5: a row can go missing from the count (C2) and a mechanism can exist
with no row (`check_exemptions_live` for a whole subcycle) and the run stays
green either way. **A `check_check_registry` is cycle 0.1's**, deferred and not
declined: it needs `TESTING.md` §2 to have a machine-readable shape, which is a
change to this document's form rather than to its content, and this cycle's
close was not the place to make one. Until then V-1a's arithmetic is the
belt — it is what caught the missing row.

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
