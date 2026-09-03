# `ntime` specifications

This directory is the **authority on what `ntime` does**. Code that disagrees
with a document here is a defect in the code; a document that turns out to be
wrong is amended by a decision recorded in
[`../DECISIONS.md`](../DECISIONS.md), never by editing the text and moving on.

That discipline is borrowed, deliberately, from the compiler repository, where
the cycle notes record the same finding over and over: **the compiler and the
thing that describes it have to be diffed, because reading either alone never
reveals the gap.** A specification nothing is held to is decoration.

## Reading order

Read the first three before proposing anything. `TIME_MODEL.md` in particular
is the document that decides everything else: almost every bad idea in a date
library is a type distinction it declined to make.

| # | Document | What it settles |
|---|---|---|
| 1 | [`SAFETY.md`](SAFETY.md) | the constraints, the error budget, the purity rule — **and where each comes from** |
| 2 | [`TIME_MODEL.md`](TIME_MODEL.md) | the type set, the three scales, leap seconds — **the core** |
| 3 | [`BUILD.md`](BUILD.md) | how this is built and tested today, and the module and import conventions |
| 4 | [`CALENDAR.md`](CALENDAR.md) | the civil types, the proleptic Gregorian algorithms, the supported range |
| 5 | [`SPAN_MODEL.md`](SPAN_MODEL.md) | `Duration` and `Period`, and every arithmetic rule with worked examples |
| 6 | [`ZONE_MODEL.md`](ZONE_MODEL.md) | the compiled-in IANA database, offset lookup, and what happens at a DST edge |
| 7 | [`FORMAT_MODEL.md`](FORMAT_MODEL.md) | formatting and parsing, the typed layout, and why there is no format string |
| 8 | [`HOST.md`](HOST.md) | the one impure module: the clocks and the system-zone discovery |
| 9 | [`TESTING.md`](TESTING.md) | the harness, the exhaustive gates, the round trips, the fuzzer |
| 10 | [`VERIFICATION.md`](VERIFICATION.md) | the proof obligations this library carries into the compiler's cycle 1.5 |
| 11 | [`COMPAT.md`](COMPAT.md) | what is supported, the tzdb version policy, and what is deliberately absent |
| 12 | [`GLOSSARY.md`](GLOSSARY.md) | the words, used one way each |

## What is normative, and what is not

- A **rule** stated in these documents is normative. Rules read as statements of
  fact about the library ("an `Instant` has no epoch"), not as intentions.
- A **rationale** paragraph explains why, and carries no obligation of its own.
- A **decision reference** — `TM-nnn` — points at
  [`../DECISIONS.md`](../DECISIONS.md), which holds the argument, the
  alternatives considered, and the date. `D-nnn` points at the **compiler's**
  `meta/specs/DECISIONS.md`; those are language decisions and are not ours to
  amend.
- An **open item** is listed at the end of the document that owns it, and is
  mirrored in [`../OPEN_QUESTIONS.md`](../OPEN_QUESTIONS.md) with a
  recommendation. A question that lives only in a conversation evaporates.

## The language, in one paragraph, for a reader arriving from C

Nitpick has no exceptions and no unhandled errors: every function returns
`Result<T>` except `main` and `failsafe`. There is no garbage collector; the
default regime is static ownership with destruction at scope exit, owning values
are move-only, and borrows are second class — they pass down the call stack and
never up, never across a thread spawn, never across an `await`. Plain integer
overflow **traps**. There are no closures, and there is no format-specifier
language. `defer` runs on every normal exit path and **not** on a trap. Anything
uncaught routes through a mandatory `failsafe` handler, which is the last code
that runs in a process that has decided to stop. Read the compiler's
`meta/specs/` for the full statement; the pieces that bite hardest here are
enumerated in [`SAFETY.md`](SAFETY.md) §1.
