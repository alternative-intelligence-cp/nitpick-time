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
decides if it is ever reopened.

## Why printer-first

The sibling library writes its screen oracle before its renderer, so the
renderer is developed against a checker that already works. The same shape
applies: a formatter is testable against committed goldens on its own, and once
it works it becomes the generator for the parser's corpus. The reverse order
means writing a parser with nothing to feed it.

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.4.0 | **The layout type** — `FmtPart`, `Layout`, `layout_validate` | a layout is a value the type checker sees |
| 0.4.1 | **The printer** — `format_with`, and the named emitters | goldens for every format |
| 0.4.2 | **The parser** — `parse_with`, the named parsers, `Parsed`, `ParseError` | every format read back |
| 0.4.3 | **The round trip** — the generated corpus and the fixed-point gate | the cycle's gate |
| 0.4.4 | **The standards corpus** — RFC 3339's, RFC 9110's and ISO 8601's own examples | agreement with the documents |
| 0.4.5 | **Close** | `done/0.4/`, `0.5.0.md` written |

## Checklist

### 0.4.0 — the layout type
- [ ] `FmtPart` with every variant in `FORMAT_MODEL.md` §3, and `Layout` holding a `Vec<FmtPart>` and its own text pool
- [ ] `layout_new`, `layout_push`, `layout_lit`
- [ ] `layout_validate` (F-7): two adjacent variable-width numeric parts with no literal between them is refused **at construction**, and `NanosAuto` is refused in a parsing layout
- [ ] **`check_no_format_string` goes live** — no function anywhere takes a pattern `string` and interprets it (TM-023's guard)
- [ ] a rejection test proving there is no `layout_from_pattern`, so the absence is checked rather than merely true today

### 0.4.1 — the printer
- [ ] `format_with(value, layout, sink)` writing into a caller-supplied `Bytes` (F-10)
- [ ] the named emitters: RFC 3339 (Z and offset forms), ISO date/time/datetime/week-date/ordinal-date, RFC 5322, HTTP-date, Unix seconds, ISO 8601 duration
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
