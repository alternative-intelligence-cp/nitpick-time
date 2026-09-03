# Cycle 0.8 — Hardening

**The fuzz sweep, the stress sweep, the verification reconciliation, and the
audit.** Everything the plan deferred to "before release", collected.

## Decisions in

TM-030 (no recursion), and `specs/VERIFICATION.md` in full.

**Open questions to settle:** O-X4 — whether the formatters need a scratch
buffer, decided here against the benchmark rather than in advance.

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.8.0 | **The fuzz sweep** — every parser, to exhaustion | a hundred million inputs clean |
| 0.8.1 | **The stress sweep** — `// stress: 40` on everything that reads a clock | forty runs, the same answer |
| 0.8.2 | **Benchmarks** — the six, with committed baselines and the regression gate | numbers, and O-X4 decided |
| 0.8.3 | **The verification reconciliation** — the obligation list against the code | an obligation list that is true |
| 0.8.4 | **The audit** — every specification rule against its implementation | a findings list, and the specs corrected |
| 0.8.5 | **Close** | `done/0.8/`, `1.0.0.md` written |

## Checklist

### 0.8.0 — fuzz
- [ ] `tools/fuzz_parse.py` over every named parser and `parse_with` with generated layouts
- [ ] random bytes, and structured mutations of the 0.4 corpus: truncations, byte flips, digit runs, extreme offsets, embedded NULs, non-ASCII
- [ ] the four invariants (V-9): never traps; always terminates; `consumed` never exceeds the input length; **anything that parses round-trips**
- [ ] a hundred million inputs clean
- [ ] every input that found something committed permanently under `tests/fixtures/fuzz/`
- [ ] the ISO 8601 duration parser fuzzed too — it has the most structure and therefore the most states

### 0.8.1 — stress
- [ ] `// stress: 40` on every test in `src/host/`'s suite
- [ ] a red under stress is a **stop sign, never a retry** — the compiler's R5, and its reason is that every timing-shaped defect it found looked like flakiness first

### 0.8.2 — benchmarks
- [ ] `harness/bench.py` writing to `meta/bench/<date>.txt`
- [ ] the six: civil ↔ timestamp; zone lookup at a transition; zone lookup far from one; RFC 3339 format; RFC 3339 parse; `Period` addition across a DST boundary
- [ ] each reports wall time **and** allocation count — the second is machine-independent and is the number that matters for a formatter
- [ ] the committed baseline and the 20% regression gate on the same machine (V-12)
- [ ] **O-X4 decided against the measurement**: if the `string`-returning formatters' allocation is material, the answer is documentation pointing at the `Bytes` form, not hidden state

### 0.8.3 — the verification reconciliation
- [ ] `specs/VERIFICATION.md`'s obligation list read against the code, entry by entry
- [ ] every obligation the code generates that the list does not name, added
- [ ] every obligation the list names that the code does not generate, removed or scheduled
- [ ] the contracts written as comments (P-1) checked to be syntactically what they will be, by pasting one into a scratch file and confirming the compiler's rung refuses it **by name** rather than parsing it as something else
- [ ] the property tests standing in for each, present and green
- [ ] the whole list handed forward as `meta/OBLIGATIONS.md`, ready for the compiler's verified build (P-11)

### 0.8.4 — the audit
- [ ] every specification document read against the code that implements it
- [ ] every numbered rule either implemented, refused with a reason, or struck by a decision
- [ ] the tree checks' coverage reviewed: **is there a document nothing diffs against?**
- [ ] `check_specs_current`'s backlog drained
- [ ] the `failsafe` arm table (`COMPAT.md` §6) regenerated and checked against real programs

## Gate

Every tree check green, the obligation list true, and a hundred million fuzz
inputs clean.

## Watch for

- **The audit is the cycle's most valuable part and the easiest to shorten.**
  The compiler's cycle 0.6 found every one of its holes this way and none of
  them by a test.
- **A specification rule with no implementation and no refusal** is the failure
  this cycle exists to find — the dormant-rule pattern, which the compiler
  found three times.
- **The fuzzer's round-trip invariant is the strong one.** A crash-only fuzzer
  finds traps; "anything that parses must round-trip" finds *wrong answers*,
  which is the defect class that survives to a release.
