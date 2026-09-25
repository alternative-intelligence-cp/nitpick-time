# Hinnant's `days_from_civil` / `civil_from_days` — research digest

**As of 2026-09-25.** Question: which published algorithms does TM-016 adopt,
at what revision, and what does their author state about their range and their
epoch shift — the facts `meta/roadmap/0.1/0.1.1.md` transcribes.

## Answer

Howard Hinnant's page *chrono-Compatible Low-Level Date Algorithms*, which dates
itself **2021-09-01**, gives `days_from_civil(y, m, d)` and
`civil_from_days(z)` as C++ templates over a signed `Int` with `unsigned`
intermediates. The constant 719 468 shifts serial day 0 from 0000-03-01 to
1970-01-01. With 64-bit arithmetic the author states overflow is out of reach
for any date; `ntime`'s range (±9999) is far inside it. `ntime` transcribes both
functions with `int64` in place of every `unsigned` (`CALENDAR.md` C-12), which
is the one deviation, and it is in the direction of totality: a field value the
`unsigned` form would wrap is an ordinary negative intermediate here.

## Evidence

- https://howardhinnant.github.io/date_algorithms.html — retrieved 2026-09-25 —
  the page's date line: *"2021-09-01"*.
- the same page, on the shift: *"This is a shift which aligns this algorithm with
  all known implementations of `std::chrono::system_clock`. It makes the serial
  date 0 be equivalent to 1970-01-01 instead of 0000-03-01."*
- the same page, on range: *"Using 32 bit arithmetic, overflow occurs
  approximately at +/- 5.8 million years. Using 64 bit arithmetic overflow occurs
  far beyond +/- the age of the universe."*
- the same page, `days_from_civil`'s first two lines of arithmetic:
  *"y -= m <= 2;"* and *"const Int era = (y >= 0 ? y : y-399) / 400;"* — the
  negative-year correction `meta/roadmap/0.1/0.1.0.md` §6 said this function
  still owes.
- the same page, `civil_from_days`' era line:
  *"const Int era = (z >= 0 ? z : z - 146096) / 146097;"*.

## What would change this

A revision of the page that changes either function's arithmetic, or a
published correction. Neither was found: the page's own date is its only
revision marker, and the functions are the ones `CALENDAR.md` C-10 already
quoted in shape. **The transcription is checked against the page line by line
at 0.1.1, not against this digest.**

## Confidence and gaps

High for the algorithms and their stated properties — one primary source, the
author's own page, read directly. Not security-sensitive. The page carries no
version beyond its date, so "pinned" means that date; re-checked at the
hardening cycle (0.8).
