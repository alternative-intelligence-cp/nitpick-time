# `src/fmt/` — formatting and parsing

Named functions for RFC 3339, ISO 8601, RFC 5322 and HTTP-date, plus the
**typed layout** — a `Vec<FmtPart>`, never a string — that drives both
directions. There is no `strftime` and there will never be a
`layout_from_pattern` (TM-009, TM-023).

Every parser is a bounded, non-recursive scan over ASCII. Governed by
`meta/specs/FORMAT_MODEL.md`. Built in cycle 0.4, whose gate is a round-trip
fixed point with exactly two documented exceptions.
