# ISO 8601-1 week dates — research digest

**As of 2026-09-25.** Question: what is the current edition of ISO 8601-1
(*Date and time — Representations for information interchange — Part 1: Basic
rules*), including any amendment in force, and what exactly does it define as
the first calendar week of a year and the year a week belongs to? Asked by the
stream-2 planner for `meta/roadmap/0.1/0.1.3.md`, which implements
`CALENDAR.md` C-14; filed by that planner, and cited by C-14 as
*"per `meta/research/iso-8601-week-date.md`, as of 2026-09-25"*.

## Answer

The edition in force is **ISO 8601-1:2019, first edition** (2019-02, 38 pages,
ISO/TC 154), with one amendment, **ISO 8601-1:2019/Amd 1:2022, "Technical
corrections"** (2022-10); no other amendment or corrigendum is listed. The 2019
edition has stood at stage 90.92, *"Standard to be revised"*, since
2024-10-31, and its replacement, **ISO/CD 8601-1**, closed its committee-draft
comment period on 2026-07-25 (stage 30.60) — not yet a DIS, and not public.

Clause **3.1.1.23** (*week calendar*) defines the first calendar week of a year
as **"the week including the first Thursday of that year"**, and the last as
the week immediately preceding the next year's first. **The readable 2019 text
never mentions 4 January**: "the week containing 4 January", and so "the
Monday on or before 4 January", are equivalent restatements — derived below —
and are to be cited as derived, not quoted. Amendment 1 replaces the NOTE in
4.2.2 to say the week calendar's year and the Gregorian year "are independent
units and do not necessarily align", with the example that **the first day of
2019 Week 1, a Monday, is 2018-12-31**; it does not change the rule. **The
weekday numbering Monday = 1 … Sunday = 7 could not be quoted from the 2019
text**: the clauses that state it (4.2.2 Table 2, 4.3.6, 5.2.4) lie past the
end of every freely readable copy.

## Evidence

The 2019 edition and Amd 1 texts are ISO's own pages (each carries "© ISO" and
the ISO reference number), read from free previews a standards distributor
hosts, because iso.org and the OBP both answered HTTP 403.

- https://cdn.standards.iteh.ai/samples/70907/5e8d00e639cf4f849462bd63062f4cd8/ISO-8601-1-2019.pdf
  — retrieved 2026-09-25; the preview ends at 3.1.2.1.
  - title page: "ISO 8601-1 First edition 2019-02 … Reference number ISO 8601-1:2019(E)"
  - foreword: "This first edition of ISO 8601-1, together with ISO 8601-2,
    cancels and replaces ISO 8601:2004, which has been technically revised."
    None of the listed main changes concerns week numbering.
  - 3.1.1.23 *week calendar*: "calendar (3.1.1.18) based on an unbounded series
    of contiguous calendar weeks (3.1.2.16) that uses the time scale unit
    (3.1.1.7) of calendar week as its basic unit to represent a calendar year
    (3.1.2.21), according to the rule that the first calendar week of a
    calendar year is the week including the first Thursday of that year, and
    that the last one is the week immediately preceding the first calendar
    week of the next calendar year"
  - Note 1 to entry: "This rule is based on the principle that a week belongs
    to the calendar year to which the majority of its calendar days (3.1.2.11)
    belong."
  - Note 2 to entry: "In the week calendar, calendar days of the first and last
    calendar week of a calendar year may belong to the previous and the next
    calendar year respectively in the Gregorian calendar (3.1.1.19)."
- https://cdn.standards.iteh.ai/samples/81801/f527872a9fe34281ae3a4af8e730f3f8/ISO-8601-1-2019-Amd-1-2022.pdf
  — retrieved 2026-09-25; ten pages, body pages 1–6, apparently the whole
  amendment.
  - title page: "First edition 2019-02 AMENDMENT 1 2022-10 … AMENDMENT 1:
    Technical corrections … Reference number ISO 8601-1:2019/Amd.1:2022(E)"
  - "4.2.2 Replace "NOTE" with the following: NOTE The calendar year used in
    the week calendar and the Gregorian calendar are independent units and do
    not necessarily align. … For instance, the first day of 2019 Week 1 (a
    Monday) in the week calendar is actually 2018-12-31 in the Gregorian
    calendar."
  - no other instruction touches the week rule.
- https://iss.rs/en/project/show/iso:proj:70907 — retrieved 2026-09-25 — the
  Institute for Standardization of Serbia, an ISO member body mirroring ISO's
  records: "Current stage: "90.92" "Standard to be revised" "Oct 31, 2024"";
  "Publication date: "Feb 25, 2019""; life cycle "PUBLISHED ISO
  8601-1:2019/Amd 1:2022", "PROJECT ISO/CD 8601-1".
- https://iss.rs/en/project/show/iso:proj:90784 — retrieved 2026-09-25 —
  "ISO/CD 8601-1 … 30.60 Close of voting/ comment period" "Jul 25, 2026".
- Context only, not a source for the current rule:
  https://www.rfc-editor.org/rfc/rfc3339.txt — Appendix A, an informational
  transcription of the 1988 edition: "date-wday = DIGIT ; 1-7 ; 1 is Monday, 7
  is Sunday".

**The derivation of the 4-January form.** Let 1 January fall on weekday `w`,
Monday = 1. The first Thursday is day `d = 1 + ((4 − w) mod 7)` of January,
`1 ≤ d ≤ 7`; its Monday-to-Sunday week runs from `d − 3` to `d + 3`, so it
always contains 4 January, and that week's Monday is the Monday on or before
4 January. Consecutive week-1 Mondays are 364 or 371 days apart, so a
week-calendar year has 52 or 53 weeks — also derived, since 4.3.4 was not
readable.

## What would change this

- **Week 1 defined other than by the first Thursday — did not trigger.**
  3.1.1.23 matches C-14 as written.
- **Weekdays numbered other than Monday = 1 … Sunday = 7 — unresolved.** Monday
  as the first day of week 1 is quoted (Amd 1's NOTE); the 1 … 7 numbering is
  quoted from no edition's own text, and every indirect source agrees with it.
- **An amendment changing the week-date rules — did not trigger.** Amd 1 was
  read in full.
- **The edition in force is not 2019 — did not trigger**, but ISO/CD 8601-1
  will replace both the 2019 edition and Amd 1: re-check when it reaches DIS or
  publishes, and at the latest at the hardening cycle (0.8).

## Confidence and gaps

- Edition, amendment and status: **high** — the documents' own title pages and
  a member body's mirror of ISO's records agree; iso.org's own catalogue page
  was never seen (403).
- The first-week rule and the year split: **high** — verbatim 2019 text, and
  Amd 1 read in full changes neither.
- Weeks start on Monday: **high**, resting on Amd 1's example.
- Monday = 1 … Sunday = 7: **medium, unverified against the 2019 text** — a
  licensed copy's 4.2.2 Table 2, 4.3.6 and 5.2.4 would settle it.
- No term "week-numbering year" was seen; "week-year" in `CALENDAR.md` C-14 is
  this library's own word (`GLOSSARY.md`).
- ISO/CD 8601-1's content: unknown, not public.
- Noticed, outside week dates, for later cycles: Amd 1 4.3.2 admits negative
  and more-than-four-digit years, which matters when formatting week-years
  outside 0000–9999 (cycle 0.4); Amd 1 5.3.2 re-admits "24:00:00" as the end of
  the day (`CALENDAR.md` C-9, `FORMAT_MODEL.md` F-20); ISO 8601-2 was not
  examined.
- Budget: 12 of 12 fetches used, and 9 searches.
