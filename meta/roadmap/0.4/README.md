# Cycle 0.4 — Formatting and parsing

**`src/fmt/`: the named formats, the typed layout, and the round-trip gate.**
Written printer-first, because for a parser the printer is the oracle.

## Decisions in

TM-009 (no format-specifier language), TM-023 (the layout is a typed value),
TM-024 (no locale), TM-025 (strict by default, leniency by name), TM-029 (`:60`
and `24:00:00` fold, and there are exactly two exceptions), TM-030 (no
recursion). All settled.

**Open questions to settle:** O-X4 — whether the `string`-returning formatters
keep a scratch buffer. Recommendation on file: no, and the benchmark at 0.8
decides if it is ever reopened. *(Dated at cycle 0.3's close:
`meta/OPEN_QUESTIONS.md` says O-X4 is open by design until cycle 0.8's
benchmark, so it blocks nothing here — until then the formatters follow its
recommendation, F-10's caller-supplied `Bytes` and no scratch buffer.)*

**And two questions this cycle's planning settles**, found at cycle 0.3's
close by reading this README against the documents it names
(`meta/roadmap/done/0.3/0.3.4.md` §1.8), neither blocking 0.4.0's start:

1. **Where `check_no_format_string` goes live.** 0.4.0's item below says at
   0.4.0. The check's `PENDING` entry in `harness/checks.py`, and `TESTING.md`
   §2's row, say what it needs is the layout interpreter F-5 is written
   against, to tell a function that interprets a pattern `string` from one
   that copies it — and at 0.4.0 one copy is `layout_lit`'s own, which F-4's
   example hands `"-"`, beside `bytes_extend_str`'s since cycle 0.0.4.
   0.4.0's plan decides, by a decision with its alternatives.
2. **Whose the ISO 8601 duration is.** 0.4.1's item below names it among the
   emitters, and `FORMAT_MODEL.md` F-2 lists `period_to_iso` and
   `period_parse_iso`; but `Period` is cycle 0.7's (`../ROADMAP.md`), and
   cycle 0.7's README holds both functions at its 0.7.0. Recommendation:
   0.7's, with the type it formats — 0.4.1's plan restates its item.

**Currency** — the standards this cycle rests on are rows of
`meta/research/CURRENCY.md` since cycle 0.3's close, each with the date it
was checked and its digest: RFC 3339, RFC 5322, RFC 9110's HTTP-date and
ISO 8601-1's date and time representations. A row unchecked for six months
is stale, and a cycle whose rows are unchecked is not ready to start.

## Why printer-first

The sibling library writes its screen oracle before its renderer, so the
renderer is developed against a checker that already works. The same shape
applies: a formatter is testable against committed goldens on its own, and once
it works it becomes the generator for the parser's corpus. The reverse order
means writing a parser with nothing to feed it.

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.4.0a | **The adoption of compiler `2e1cb4a`** — landing 140, the libraries' one re-pin, by the author's word of 2026-10-22, two pins on from cycle 0.3's `7e91730` (landings 104 … 140): each view landing 128 ties to its owner in a block of its own, `probe19` asking the `Copy` judgement of `Bytes`, and `bytes_view`'s answer the read-only view — at the old pin first, which sees no difference; then the pin's own moves — part E's refused numeral, a held view and an orphan impl each a refusal asserted, TM-171's `fixed Weekday[7]` table weighed again and declined, the adoption list below each measured — and CI pinned, its LLVM asset's digest checked before it is unpacked — **[`0.4.0a.md`](0.4.0a.md)**, planned and rehearsed 2026-10-22 at both pins; it runs before 0.4.0 | the tree green at `2e1cb4a` |
| 0.4.0 | **The layout type** — `FmtPart`, `Layout`, `layout_validate` — **[`0.4.0.md`](0.4.0.md)**, written at cycle 0.3's close at `7e91730` (its §8 says whether it was rehearsed); its §1 is re-measured at `2e1cb4a` over 0.4.0a's tree before it is dispatched, by the list in `0.4.0a.md` §7 | a layout is a value the type checker sees |
| 0.4.1 | **The printer** — `format_with`, and the named emitters | goldens for every format |
| 0.4.2 | **The parser** — `parse_with`, the named parsers, `Parsed`, `ParseError` | every format read back |
| 0.4.3 | **The round trip** — the generated corpus and the fixed-point gate | the cycle's gate |
| 0.4.4 | **The standards corpus** — RFC 3339's, RFC 9110's and ISO 8601's own examples | agreement with the documents |
| 0.4.5 | **Close** | `done/0.4/`, `0.5.0.md` written |

## Checklist

### 0.4.0a — the adoption of compiler `2e1cb4a`
*(Written at 0.4.0a's planning, 2026-10-22 — `0.4.0a.md`, PD-201 … PD-203. It carries this README's list "The adoption, when the pin moves", below, and the three items the workbench's board holds for it: landing 128's freeze, 124's orphan rule and 123's enum constant.)*
- [x] the unchanged tree measured at both pins — every `.npk` a root, the full run, and the emissions compared through the compiler's normalisers — blocks 0a and 0b — `SAME`, worker 1: at `7e91730` `RED -- 144 unit(s) of 146`, the namespace pair alone (this shell refuses a user namespace), and at `2e1cb4a` red at the self-check, past it (`--root`) `RED -- 137 unit(s) of 146`; the 163 files 118 that compile and 45 refused at both pins, their emissions 116 `attr+site`, 2 with drops and no residue
- [x] the freeze met at the old pin, which sees no difference: `bytes_reserve`'s two views in a block, `bytes_view_lifetime`'s each in a block of its own, and `probe19` on `Bytes` (PD-201) — **TM-263**, `3a71a04`: at `7e91730` 162 of 163 files report the codes and sites they did and `probe19` the same code a line on, every emission the same but the re-spelled unit's; the named mutants compile at `7e91730` and are `NITPICK-BORROW-015` at `2e1cb4a`; `RED -- 144 unit(s) of 146` there, the namespace pair alone
- [x] `bytes_view`'s result the read-only view, with every slot that binds it, at the old pin; `src/`'s nine `#wild_slice` sites each measured where they stand (PD-202) — **TM-264**, `6a6c848`: each of the seven locals plain again is `NITPICK-TYPE-007` at both pins and a write through the answer `NITPICK-TYPE-086` at both; `RED -- 144 unit(s) of 146` at `7e91730`, the namespace pair alone
- [x] the pin moved: part E's refused numeral, a held view and an orphan impl each a refusal asserted, the lexer re-read, the reserved words, and the adoption list's six items each measured (PD-203) — **TM-265**, `8ad4917`: every file at `2e1cb4a` reports what the unchanged tree did at `7e91730` but `probe19`'s line and the two new probes (162 of 165 the same); all 47 refusals pass the runner's own judge there, the two new probes failing it at `7e91730`, and `probe10d`'s control reads 170 on both legs; part E's third half runs 21 spellings; `RED -- 146 unit(s) of 148`, the namespace pair alone
- [x] TM-171's `fixed Weekday[7]` table, spellable at `2e1cb4a`, weighed again and declined, in a dated note (PD-203) — **TM-265**, `8ad4917`: the note under TM-171 in `meta/DECISIONS.md` — `weekday` read from such a table compiles and passes every test that reads a weekday, and it stays declined on the decision's other grounds, `weekday_index`'s belt running first on every path
- [x] CI pinned to `2e1cb4a`, its LLVM asset's digest pinned and checked before it is unpacked, and its log read per job — `f1210b3` (TM-265): the install step exits 1 on a fake asset with the pin's digest and 0 with its own, the emission step 1 on a fake ladder and 0 on its own row; run 39792933155 at `a11f3b3`, job 119873202477 (`build`, success): `compiler HEAD == 2e1cb4a…` clean, `downloaded 2021269412 B` and `…/LLVM-20.1.8-Linux-X64.tar.xz: OK`, `llvm-config --version == 20.1.8`, `npkc.ll` 32569732 B / `0073060250f0…` equal to the pin's row, the namespace step `1` then `0`, `12 of V-14's 13 cases`, and `GREEN -- 148 unit(s), 0 failures; 4 pending`
- [x] the prose, and the sweep read line by line — `a11f3b3`; block 6's 368 and 211 saved lines, 464 distinct, each in its class of `0.4.0a.md`'s §3b table and none an omission, the control's 26 misses all appends

### 0.4.0 — the layout type
*(Restated 2026-10-15, at cycle 0.3's close, to `0.4.0.md`'s drafted decisions, PD-149 … PD-154. The instrument's item moves first, in a commit of its own, and says where and what it reads — the first question above, which PD-149 answers; `Layout`'s fields, its pool and its release are named; construction never fails, as F-4's `drop` requires; and `layout_validate` is F-7's answer, a predicate. The rest keep their words.)*
- [ ] **FIRST, `check_no_format_string` goes live, in a commit of its own** — no function anywhere takes a pattern `string` and interprets it (TM-023's guard): every text parameter of a function in `src/` outside `src/host/` is copied or measured and nothing else, `bytes_extend`, the copier, excused by name and its reason re-derived; four plants seen red first (PD-149) *(where it goes live was the first question above, from cycle 0.3's close)*
- [ ] `FmtPart` with every variant in `FORMAT_MODEL.md` §3 — thirty, `Literal(uint16)` the one payload, claiming `Copy` beside its declaration — and `Layout` holding a `Vec<FmtPart>` and its own text pool, every field `hidden`, and a third, `refused` (PD-150); a `Literal` holds the byte offset of a length-prefixed entry of the pool, and `NTIME_PARSE_MAX` bounds both the parts and a literal's bytes (PD-151)
- [ ] `layout_new`, `layout_push`, `layout_lit` — each `never fails`, as F-4's `drop` requires, a step a layout cannot take recorded in `refused` (PD-152) — and `layout_free`, which releases the parts (PD-154)
- [ ] `layout_validate` (F-7): two adjacent variable-width numeric parts with no literal between them is refused **at construction**, and `NanosAuto` is refused in a parsing layout — *as PD-153 reads F-7: `bool(Layout:l) never fails`, its false the refusal, and `YearExpanded`, `NanosAuto` and `UnixSecs` the variable-width numeric parts*
- [ ] a rejection test proving there is no `layout_from_pattern`, so the absence is checked rather than merely true today — *`probe23c`, refused `NITPICK-RESOLVE-002` by name, beside `probe23` and `probe23b`, a layout copied and its field read*

### 0.4.1 — the printer
- [ ] `format_with(value, layout, sink)` writing into a caller-supplied `Bytes` (F-10)
- [ ] the named emitters: RFC 3339 (Z and offset forms), ISO date/time/datetime/week-date/ordinal-date, RFC 5322, HTTP-date, Unix seconds, ISO 8601 duration *(the duration's place is 0.4.1's plan's to restate — the second question above, from cycle 0.3's close)*
- [ ] **each emitter refuses what its format cannot express** (F-3): `to_rfc3339` on a negative year is `ETimeValue`/`YearRange`, not an invented spelling
- [ ] `to_iso_date_expanded` as the separate, named opt-in for expanded years
- [ ] `NanosAuto` emits the shortest round-tripping form; `Nanos3/6/9` **truncate, never round** (F-12) — rounding during display would print a different instant
- [ ] no emitter allocates per field (F-11), verified by reading the IR for allocator calls
- [ ] a golden per format at: both range extremes, the epoch, a leap day, zero nanos, maximal nanos, and a negative offset

### 0.4.2 — the parser
- [ ] `parse_with(src, layout)` and the named parsers
- [ ] `Parsed` with `has_offset`, `folded_leap`, `folded_hour24` and `consumed` (F-13)
- [ ] `ParseError { at, expected }` and `ParseExpect` (F-15); `parse_error_text` is **the library's only prose** and lives in one place
- [ ] **strict by default; `_lenient` as a separate name** (F-14), with each accepted departure listed in the lenient function's documentation comment
- [ ] `_prefix` variants where trailing input is allowed (F-18)
- [ ] **bounded and non-recursive** (F-16): `NTIME_PARSE_MAX`, a straight-line scan, and a `prove`-shaped comment that the cursor strictly increases
- [ ] ASCII only (F-17): a non-ASCII byte is a parse error at its offset, and there is no Unicode dependency anywhere in the module
- [ ] `:60` folds to `:59` and `24:00:00` folds to the next day, each setting its flag (TM-029)

### 0.4.3 — the round trip — THE GATE
- [ ] `tools/gen_fmt_corpus.py` emitting the corpus of `FORMAT_MODEL.md` F-19's shape: both extremes, the epoch, every month, leap and common Februaries, zero and maximal nanos, every offset in ±18:00 at 15-minute granularity
- [ ] `parse_with(format_with(v, l), l) == v` for every value × every layout
- [ ] **the exception list is a committed file with exactly two entries**, and a test asserts it has exactly two (TM-029) — a third arriving is a red run, not a quiet edit
- [ ] the parse-first direction too, `format(parse(t)) == t`, where the exceptions are the two folds

### 0.4.4 — the standards corpus
- [ ] RFC 3339's own examples, committed verbatim as `(text, expected)` pairs
- [ ] RFC 9110's HTTP-date examples, including the two obsolete formats that must **parse but never emit**
- [ ] RFC 5322's examples, including obsolete two-digit years
- [ ] ISO 8601's week-date and ordinal-date examples
- [ ] each fixture's header naming the document and section it came from

## What cycle 0.3 hands on

*(From cycle 0.3's close, `meta/roadmap/done/0.3/0.3.4.md` — each the hand-on
of the cycle 0.3 plan it names, read again at the close.)*

- **The `golden` stage has a member and an entry** (`nitpick.toml`'s
  `golden` entry over `tests/golden/`, TM-262): a format's golden is a test
  whose `// expect-golden:` header names a `.txt` beside it, held byte for
  byte on both legs and between them. **And the `.txt` is derived by an
  oracle, never copied from the run** — `tests/golden/double_transcript.txt`
  is Python's `datetime`'s, through
  `meta/roadmap/done/0.3/0.3.3_tools/oracle.py` (`0.3.3.md` §7).
- **A parser takes `fixed uint8[]`**, the read-only view a string's bytes are
  since compiler `7e91730` (TM-258; `SAFETY.md` S-22's note, and
  `FORMAT_MODEL.md` F-16's). **`bytes_view`'s result is a question of its
  own**: a plain `uint8[]` today (`src/core/bytes.npk`), and a read-only one
  would refuse a consumer's write into the sink's `hidden` body. The
  compiler's D-341, `buffer`'s checked indexing, names `bytes.npk` its
  consumer and is not built — the list below — and the re-pin that carries
  its build is where both are decided (`0.3.2a.md` §7). *(Decided at that
  re-pin, cycle 0.4.0a, TM-264: `bytes_view` returns the read-only view,
  `fixed uint8[]`, and `src/`'s nine `#wild_slice` sites stand where they
  are, each measured — `0.4.0a.md` §1.)*
- **`fmt`'s functions are read in the library's emission the day they are
  written.** `check_call_edges` holds every call a function of `src/` outside
  `src/host/` makes to its reviewed allowlist, and names a non-generic
  function `src/` declares that the umbrella's emission does not define
  (TM-250); a generic one is instantiated in
  `tests/unit/generic_instances.npk`, or it is a finding (TM-254). And F-11's
  *"verified by reading the IR for allocator calls"* (0.4.1's item) can be a
  check over the same reader, `checks.read_emission` and `_reach`, where
  `tools/ir_alloc_scan.py` reads the IR its own way and is a tool
  (`0.3.1.md` §7).
- **`fmt` reads no clock**, so no test of it carries `// stress: 40`: a clock
  test is a test of a `src/host/` function (`TESTING.md` V-11, TM-262).
- **`check_no_view_returns` names a `fixed uint8[]` result `fixeduint8[]`** in
  its message — its `functions()` removes a result type's whitespace — and
  reads it as the view it is: a message, not a verdict (`0.3.2a.md` §7, and
  `0.3.3.md` §7 again). A parser's result is the likeliest to meet that check
  first (TM-239), so the subcycle that does fixes the message.

## The adoption, when the pin moves

**Cycle 0.3 closed at compiler `7e91730`**, its landing 103, and the next
re-pin is the orchestrator's to place, as an adoption subcycle of its own
that measures the unchanged tree at both pins before it changes anything and
re-spells at the old pin first — the shape of 0.1.0b, 0.1.4c, 0.2.0a and
0.3.2a. At the close the compiler's `main` was `e50eaf4`, its landing 111;
landings 104 … 111 are announced, and none is pinned. What a re-pin owes here,
from the list cycle 0.3's README carried (`meta/roadmap/done/0.3/README.md`),
each item measured by 0.3.2a at `7e91730` and owed again at every pin:

1. **`src/`'s `#wild_slice` sites, at a pin that builds the compiler's
   D-341** — nine in code, five in `src/core/bytes.npk` and four in
   `src/core/vec.npk` — and `bytes_view`'s result decided there (above).
   D-341 is settled and not built at `7e91730`, and none of landings 104 …
   111 names it: at `e50eaf4` the compiler's record holds `buffer`'s indexing
   as a plan (its `meta/roadmap/OPEN_DECISIONS.md`).
2. **`timestamp_since`'s `int128` multiplication and `instant_since`'s
   `int128` subtraction** linked at both legs against `npkrt.o` alone —
   inline at `7e91730`, no libcall (TM-259).
3. **The compiler's lexer re-read** whatever part E says (TM-202), and
   `harness/lexical.py` brought to it; part E's third half re-run against the
   literal reader `check_constants_named` uses (TM-231).
4. **The builtin table and the prelude re-read against `check_purity`'s
   list** (TM-252); a runtime symbol `check_call_edges` finds unreviewed
   joining `CALL_EDGE_ALLOW` or refused (TM-250); and the emission's names
   read again.
5. **The instances' unit compiles at the new pin** (TM-254), and CI's
   namespace step is read again with the runner image (TM-255).
6. **Each CI's pin bump**, and the emission row CI asserts (TM-212), in the
   adoption's own commit.

*(Carried by 0.4.0a, the adoption of compiler `2e1cb4a`, 2026-10-22 —
`0.4.0a.md` §1, TM-263 … TM-265 — each item measured at both pins. **1** D-341
is built at `2e1cb4a`: `bytes_reserve`'s two views take a block that ends before
its overwrite (TM-263), `bytes_view` answers the read-only view, and the nine
sites stand, each measured — `vec.npk`'s four over a `wild` pointer, which the
belt roots at the pointee, `bytes_push`'s and `bytes_extend`'s written through
into the view and `len`, and `bytes_view`'s travelling up to its caller
(TM-264). **2** Both functions' `int128` arithmetic is inline at both pins, and
no object names a symbol `npkrt.o` does not define. **3** The lexer re-read: a
numeral whose digit run ends in `_` is refused (DEF-190), so part E's third
half drops `86400_i64`; no span `lexical.py` finds moved (TM-265). **4** The
builtin table's fifty-seven names and the prelude's sixty-three public
functions are the same at both pins, the prelude unchanged and the one row that
moved `#wild_slice`'s views, so `check_purity`'s list stands;
`check_call_edges` reaches the same seventeen runtime symbols from every
function, and the emission's names and type ids are as before. **5** The
instances' unit compiles at `2e1cb4a`; CI's namespace step is read at the push.
**6** CI is pinned to `2e1cb4a`, its emission row notice 140's, in a commit of
its own after the adoption's three; and the LLVM asset it installs is held to
its digest before it is unpacked. The next re-pin owes the list again, from
0.4.0a's rows of the landings past `2e1cb4a`, §1.)*

## Gate

The round-trip fixed point over the generated corpus, with exactly two
documented exceptions and a test that counts them.

## Watch for

- **The temptation to add `layout_from_pattern` will be strong**, because it is
  four lines and everybody knows the syntax. It is TM-023's exact prohibition,
  `check_no_format_string` exists to catch it, and the reason is in
  `FORMAT_MODEL.md` §1 rather than in anybody's memory.
- **Truncation, not rounding, on fractional seconds** (F-12). Rounding
  `.9999` up to `1.000` while printing changes which second is displayed.
- **The two folds are the only non-injective inputs**, and they are the reason
  the round-trip test needs an exception list at all. Keep the list at two.
- **`in` is a keyword** and a parser wants it for its input constantly; `src` is
  the reserved spelling.
- **S-22's "a view is a parameter, never a return value" is a BELT, not the
  language's constraint** (TM-109, corrected and superseded by **TM-110**).
  This is the cycle that meets it: every parser here takes a `uint8[]` — a
  `fixed uint8[]`, the read-only view a string's bytes are, since compiler
  `7e91730`: `SAFETY.md` S-22's note, cycle 0.3.2a, TM-258.

  **DEF-3 HAS LANDED and the rule was MEASURED on 2026-09-04** at pin
  `94874ce`, so plan against this table and not against the prediction that
  stood here until then:

  | Shape, returned out of its frame | Measured | Evidence |
  |---|---|---|
  | a view of a **local** | refused `NITPICK-BORROW-001` | `defect/view_escape/case3`–`case5` |
  | a view of a **temporary** | refused **`NITPICK-BORROW-012`** | `probe10b` |
  | a view of a **`move` parameter** | refused `NITPICK-BORROW-001` | `probe10c` |
  | a view rooted at a plain **parameter** | **legal** | `probe10` §2, §3 |
  | a view rooted at a **pointer-shaped binding** | **legal** | `probe10` §1, `probe09b` |

  **The rule keys on the ROOT'S SHAPE, not on parameterhood** — that is
  TM-110's correction to TM-109, and it matters here because it widens what a
  helper may legally do. So if a helper in this cycle genuinely wants to return
  a view of its own parameter, or of a `wild` block it allocated, that is a
  request to loosen S-22 **by decision**, not a compiler limit to design around.

  ~~DEF-3 adds no new code, so there is no new diagnostic to wait for.~~
  **FALSE, corrected 2026-09-04:** DEF-3 adds `NITPICK-BORROW-012`, and this
  cycle's `check_codes_tested` gains it. A view of a temporary —
  `string_bytes(string_concat(a, b))` — is the shape that fires it, and it was
  doubly wrong before D-246 landed, because the intermediate also leaked;
  binding it fixes both and is still the right habit.
- **`FORMAT_MODEL.md` F-10's `string`-returning wrapper cannot be spelled the
  obvious way** — measured at compiler `c3bdae2`, cycle 0.1.4b's planning. A
  function that fills a LOCAL `Bytes` and ends `pass raw bytes_take(@sink);` is
  refused `NITPICK-BORROW-001` (D-004 rule 2): the borrow tracker takes the
  call's answer for a borrow of `sink`, whatever the callee does — refused
  with `bytes_take` a copy, and with the answer bound to a local first. **A
  take that CONSUMES the sink** — `string(move Bytes:b)`, copying out before
  `b` dies — compiles, and the wrapper built on it is correct on both legs.
  So the wrapper wants a consuming take, a public name this cycle chooses with
  a caller in hand (TM-013), or a re-measurement at the pin it plans against.
  And every `string` it hands back is a copy (`SAFETY.md` S-18f).
- **`Layout`'s `Vec<FmtPart>` needs `FmtPart: Copy`, and a `Layout` is
  move-only** (cycle 0.1.3c; `SAFETY.md` S-18g, S-18h — `Pod` until cycle
  0.2.0a, TM-211). `vec_at` takes `T: Copy`, and `FmtPart` — a payload enum
  whose payload owns nothing — claims it in one line beside its declaration,
  `impl:FmtPart:Copy = { };`: measured, a four-variant
  payload enum does, and reads back twice through `vec_at`
  (`tests/unit/vec_at_pod.npk`). *(Since cycle 0.2.0b the TYPE asks it too —
  `Vec<T: Copy>`, TM-214 — so without it `Layout`'s `Vec<FmtPart>` field is
  `NITPICK-TYPE-017` where it is declared, and every enum `FmtPart` holds
  claims it as well.)* A struct holding a `Vec` is move-only by
  containment, so a `Layout` is moved or lent, never copied; a formatter that
  takes one by loan reads its parts as `vec_at(l.parts, i)` — which compiles for
  a lent struct's field and for another module's `sealed` field alike — where
  `@l.parts` of a lent `Layout` is `NITPICK-TYPE-085` and of a sealed field
  from outside `NITPICK-TYPE-079` (measured at cycle 0.1.3c's planning). And
  every `Bytes` reader takes `Bytes->` — `bytes_len`, `bytes_view`,
  `bytes_take`, `bytes_capacity` — so a function holding a LENT `Bytes` cannot
  call them (`@` of a lent owner, `TYPE-085`); a sink a formatter writes is
  passed by pointer anyway, and a read-only one is this cycle's to shape, with
  a caller in hand (TM-013).
- **`Bytes` and `Vec<T>` are indexed WITHOUT a bounds check** (TM-108, S-17b).
  *(Since compiler `2e1cb4a` a `buffer` has checked indexing and ranging —
  `b[i]` and `b[lo...hi]`, the compiler's D-341 — and `bytes.npk`'s accessors
  keep their slices, each held to its owner by that decision's belt, TM-264; a
  formatter goes through them, as below.)*
  Every formatter in this cycle writes into a `Bytes`, and `Layout` holds a
  `Vec<FmtPart>`; both are bare pointers to the emitter, so an out-of-range
  index is a wrong byte rather than a trap. Go through the accessors, which is
  where the only bound is, and never write `.ptr[` or `.items[` here.
