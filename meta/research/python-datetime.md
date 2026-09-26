# Python's `datetime` — research digest

**As of 2026-09-25.** Question: what does Python's `datetime` documentation
state about each call the civil cross-oracle's corpus reads — its year range,
its calendar, `toordinal()`, `isoweekday()`, `isocalendar()` and
`timetuple().tm_yday` — and do those statements support reading them as an
independent oracle for `CALENDAR.md`'s proleptic Gregorian calendar over years
1 … 9999?

## Answer

Yes. The documentation states that a `date` assumes *"the current Gregorian
calendar always was, and always will be, in effect"* — the proleptic Gregorian
calendar of `CALENDAR.md` C-1 — for years `MINYEAR` = 1 to `MAXYEAR` = 9999;
that `toordinal()` is the proleptic Gregorian ordinal with 1 January of year 1
as 1; that `isoweekday()` is Monday = 1 … Sunday = 7; that `isocalendar()`
returns the ISO year, week and weekday, week 1 being *"the first (Gregorian)
calendar week of a year containing a Thursday"*; and that `timetuple()`'s
`tm_yday` is `d.toordinal() − date(d.year, 1, 1).toordinal() + 1`, the day of
the year counted from 1. The page read is the **3.14.7** documentation; the
interpreter the corpus is generated with is **3.12.3**
(`/usr/bin/python3` and the workbench's virtual environment both report it),
and none of these statements is marked as changed between them.

## Evidence

- https://docs.python.org/3/library/datetime.html — retrieved 2026-09-25 —
  *"The smallest year number allowed in a `date` or `datetime` object.
  `MINYEAR` is 1."* and *"The largest year number allowed in a `date` or
  `datetime` object. `MAXYEAR` is 9999."*
- the same page — *"An idealized naive date, assuming the current Gregorian
  calendar always was, and always will be, in effect."*
- the same page, `date.toordinal()` — *"Return the proleptic Gregorian ordinal
  of the date, where January 1 of year 1 has ordinal 1."*
- the same page, `date.isoweekday()` — *"Return the day of the week as an
  integer, where Monday is 1 and Sunday is 7."*
- the same page, `date.isocalendar()` — *"Return a named tuple object with
  three components: `year`, `week` and `weekday`."* and *"The first week of an
  ISO year is the first (Gregorian) calendar week of a year containing a
  Thursday. This is called week number 1, and the ISO year of that Thursday is
  the same as its Gregorian year."*
- the same page, `date.timetuple()` — *"where `yday = d.toordinal() -
  date(d.year, 1, 1).toordinal() + 1` is the day number within the current
  year starting with 1 for January 1st."*
- the page's title — *"datetime — Basic date and time types — Python 3.14.7
  documentation"*.

## What would change this

A statement that `date` follows a Julian/Gregorian cutover, a range other than
1 … 9999, or an ISO week rule other than the first-Thursday rule would make
the corpus the wrong oracle for C-1, C-4 and C-14. **None did.** And
`tm_yday` being defined by `toordinal()` means fields 4 and 9 of the corpus's
fold come from one Python computation — which costs nothing here, since the
member computes `date_to_days` and `day_of_year` separately and must match
both.

## Confidence and gaps

High for every statement above: each is quoted from the primary source. The
gap is the version: the documentation read is 3.14.7's and the interpreter is
3.12.3. It is closed by measurement rather than by reading: the generator
asserts `MINYEAR` and `MAXYEAR` when it runs, and cycle 0.1.4's second
derivation — a count that reads no `datetime` — agrees with the corpus on
every one of its 3 652 059 days (`meta/roadmap/0.1/0.1.4.md` §4).
