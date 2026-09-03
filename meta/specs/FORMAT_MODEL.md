# Formatting and parsing

How a time becomes text and back. The shape of this is decided by a language
decision rather than by taste, and the decision is worth reading before the
API: **there is no format-specifier language in this ecosystem, and `strftime`
is not merely absent but against the grain.**

---

## 1. Why there is no `%Y-%m-%d`

D-053 removed `printf`, `scanf` and every relative from the language. Its
reasoning transfers to `strftime` exactly:

> A format string fuses three things into one literal. `"%-8.2f"` is at once
> the output text, the layout instruction, and a type assertion about an
> argument sitting elsewhere in the call. Every format defect found while
> porting `libn` is that fusion coming apart.

D-053 went further and explicitly **rejected adding format specifiers to
string interpolation** (`&{x:>8.2}`) — "it would reintroduce a second
mini-language, with its own grammar, its own diagnostics, and its own
conformance surface … purely to save characters."

**Rule F-1 (TM-009).** `ntime` offers no format string, no `strftime`, no
`strptime`, and no function that takes a pattern as text and interprets it at
run time. A reader arriving from C or Python will look for one; §2 and §3 are
what they get instead, and this section is why.

---

## 2. Named functions for the named formats

**Rule F-2.** Every format with a standard gets a named function, in both
directions. These cover essentially all real use and none of them needs a
pattern:

| Format | Emit | Parse |
|---|---|---|
| RFC 3339 (`2026-09-03T14:05:00.123Z`) | `to_rfc3339`, `to_rfc3339_offset` | `parse_rfc3339` |
| ISO 8601 date (`2026-09-03`) | `to_iso_date` | `parse_iso_date` |
| ISO 8601 time (`14:05:00.123`) | `to_iso_time` | `parse_iso_time` |
| ISO 8601 datetime | `to_iso_datetime` | `parse_iso_datetime` |
| ISO 8601 week date (`2026-W36-4`) | `to_iso_week_date` | `parse_iso_week_date` |
| ISO 8601 ordinal date (`2026-246`) | `to_iso_ordinal_date` | `parse_iso_ordinal_date` |
| RFC 5322 email (`Wed, 03 Sep 2026 14:05:00 +0000`) | `to_rfc5322` | `parse_rfc5322` |
| HTTP-date / IMF-fixdate (RFC 9110) | `to_http_date` | `parse_http_date` |
| Unix seconds | `to_unix_secs` | `from_unix_secs` |
| ISO 8601 duration (`P1Y2M3DT4H5M6S`) | `period_to_iso` | `period_parse_iso` |

**Rule F-3 — each emitter is total over the values its format can express, and
refuses the rest.** RFC 3339 has no spelling for a negative year or a year
above 9999, so `to_rfc3339` on one returns `ETimeValue`/`YearRange` rather than
inventing `-0001-...`. `to_iso_date` accepts the expanded form
(`+012026-09-03`) when the caller asks for it with `to_iso_date_expanded`,
because ISO 8601 says that form requires agreement between the parties and a
function name is where that agreement is recorded.

---

## 3. The typed layout, for everything else

**Rule F-4.** A custom layout is a **value**, not a string:

```nitpick
pub enum:FmtPart = {
    Literal(uint16);        // index into the layout's own text pool
    Year4; YearExpanded; YearShort2;
    Month2; MonthName; MonthAbbr;
    Day2; DaySpace2;
    Hour24_2; Hour12_2; AmPm;
    Minute2; Second2;
    Nanos3; Nanos6; Nanos9; NanosAuto;
    WeekdayName; WeekdayAbbr; WeekdayIsoNum;
    DayOfYear3; IsoWeekYear4; IsoWeek2;
    OffsetColon; OffsetCompact; OffsetOrZ;
    ZoneAbbr; ZoneName;
    UnixSecs;
};

pub struct:Layout = { Vec<FmtPart>:parts; Bytes:pool; };
```

Built in code:

```nitpick
Layout:l = layout_new();
drop layout_push(@l, FmtPart.Year4);
drop layout_lit(@l, "-");
drop layout_push(@l, FmtPart.Month2);
```

**Rule F-5 (TM-023) — this is not a mini-language, and the distinction is
exact.**
`FmtPart` is an enum the type checker sees; a bad layout is a bad program, not
a bad string. There is **no** `layout_from_pattern("%Y-%m-%d")` and there never
will be — that function is the mini-language, and adding it later would
reintroduce everything F-1 removed.

**Rule F-6 — one layout drives both directions.** `format_with(dt, layout)`
and `parse_with(text, layout)` read the same value, so a format and its parser
cannot drift. This is the round-trip gate's foundation (`TESTING.md` §4).

**Rule F-7 — a layout is checked once, when it is built.** `layout_validate`
answers whether the parts can parse unambiguously — two adjacent variable-width
numeric parts with no literal between them cannot, and `NanosAuto` cannot
appear in a parsing layout. A layout that fails validation is refused at
construction rather than at every use.

---

## 4. Locale

**Rule F-8 (TM-024) — `ntime` has no locale, and month and weekday names are
English.**
`MonthName` yields `January`; `WeekdayAbbr` yields `Mon`.

*Reasoning:* localisation is a data problem the size of the tzdb with no
canonical source, it varies by more than language (calendars, numerals,
ordering), and getting it half-right is worse than not having it. A program
that needs localised names supplies its own table and formats the numeric parts
with `ntime`.

**Rule F-9 — the names that appear in the standard formats are not locale.**
RFC 5322 and HTTP-date mandate English abbreviations; those are protocol
constants and are emitted as such.

---

## 5. Emission

**Rule F-10 — every emitter writes into a caller-supplied `Bytes`**, and the
`string`-returning form is a thin wrapper over it. Formatting a million rows
should allocate once, not a million times — the compiler measured exactly the
opposite shape as quadratic in `npkg`'s first full run.

**Rule F-11 — no emitter allocates per field.** Numbers are written by an
allocation-free decimal writer into a stack array and appended, the same
`put_uint` that `src/core/bytes.npk` provides.

**Rule F-12 — fractional seconds:** `NanosAuto` emits the shortest
representation that round-trips — nothing when `nanos == 0`, otherwise 3, 6 or
9 digits, choosing the shortest that loses nothing. `Nanos3`/`6`/`9` emit
exactly that many, truncating rather than rounding, because rounding a
timestamp during *display* would make the printed value a different instant.

---

## 6. Parsing

**Rule F-13 — every parser returns a `Parsed` record, not a bare value:**

```nitpick
pub struct:Parsed = {
    CivilDateTime:civil;
    bool:has_offset;   int32:offset_secs;
    bool:folded_leap;      // input said :60          (M-13)
    bool:folded_hour24;    // input said 24:00:00     (C-9)
    int64:consumed;        // bytes consumed
};
```

The two `folded_` flags are `SAFETY.md` S-3's detail-field rule: they are
distinctions the *caller* may care about and a `failsafe` does not, so they ride
on the value instead of becoming errors.

**Rule F-14 (TM-025) — strictness is the default and leniency is named.**
`parse_rfc3339` requires exactly RFC 3339. `parse_rfc3339_lenient` accepts the
common departures — a space instead of `T`, a missing `Z`, lowercase `t`/`z` —
and each departure it accepts is listed in its documentation comment. There is
no leniency *flag*; there are two functions, and which one was called is
visible at the call site.

**Rule F-15 — a parse failure names the byte offset and what was expected:**

```nitpick
pub struct:ParseError = { int64:at; ParseExpect:expected; };
pub enum:ParseExpect = { Digit; Separator; TimeDesignator; OffsetSign;
                         MonthName; WeekdayName; Literal; EndOfInput; Extra; };
```

`ETimeParse` is the identity; this is the detail. A message is built from it by
`parse_error_text`, which is the library's only prose and lives in one place.

**Rule F-16 (TM-030) — parsing is bounded and non-recursive.** Every parser is a
straight-line scan over a `uint8[]` with a stated maximum input length
(`NTIME_PARSE_MAX`, 128 bytes — no time text is longer). There is no recursion,
so there is no depth to blow, which is the playbook's adversarial-input rule
satisfied by construction rather than by a limit.

**Rule F-17 — parsers consume UTF-8 bytes and never decode.** Every character
in every format this library parses is ASCII. A non-ASCII byte is a parse
error at its offset. No Unicode tables, no width question, no dependency on the
sibling library's text layer.

**Rule F-18 — trailing input is an error unless the caller asked otherwise.**
`parse_rfc3339` requires end-of-input; `parse_rfc3339_prefix` returns
`consumed` and lets the caller continue. Two functions again, for F-14's
reason.

---

## 7. The round trip

**Rule F-19 — the gate is a fixed point** (`TESTING.md` §4):

> For every value in the generated corpus and every layout in the suite,
> `parse_with(format_with(v, l), l)` equals `v`, exactly.

**Rule F-20 (TM-029) — the two documented exceptions**, and there are exactly
two:

1. `:60` folds to `:59` (M-13), so a *parse-first* round trip
   (`format(parse(t)) == t`) is not the identity for that input.
2. `24:00:00` folds to the next day's `00:00:00` (C-9), likewise.

Both are flagged on the `Parsed` record, both are named here, and the round-trip
test carries them as an explicit exception list rather than as a mysterious
skip. An exception nobody wrote down is a test that was weakened quietly.

---

## 8. Open items

*(None. Every item this document raised is settled in `../DECISIONS.md`.)*
