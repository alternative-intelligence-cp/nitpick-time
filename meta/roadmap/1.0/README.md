# Cycle 1.0 — Release

**Documentation, the API freeze, the `failsafe` arm contract, and versioning.**

## Decisions in

TM-013 (versioning, and adding an error identity is a major version). Settled;
this cycle **publishes** it rather than deciding it.

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 1.0.0 | **The API freeze** — the public surface enumerated and reviewed name by name | `src/lib.npk` as the contract |
| 1.0.1 | **The `failsafe` contract** — the generated per-import arm list, published | a consumer knows exactly what importing costs |
| 1.0.2 | **The guide** — `docs/` | a person can build a program from the documentation alone |
| 1.0.3 | **Examples** — one per format, plus the two consumers | every example built and run by the harness |
| 1.0.4 | **Versioning** — TM-013 published where a consumer will read it | a stated policy |
| 1.0.5 | **Close** | `done/1.0/`, the post-1.0 map reviewed |

## Checklist

### 1.0.0 — the API freeze
- [ ] `src/lib.npk` lists every public name, one per line, grouped by module
- [ ] each reviewed: is it needed, is it named right, does it belong at this layer?
- [ ] anything not needed removed **now** — removing a public name after 1.0 is a major version
- [ ] a conformance test that imports the umbrella and touches every name, so a removal breaks a test rather than a user
- [ ] the four refusals confirmed to still be refusals, with rejection tests:
      `Instant ↔ Timestamp`, `Period + Timestamp`, `layout_from_pattern`, and a
      `failsafe` missing an arm

### 1.0.1 — the `failsafe` contract
- [ ] the per-import arm table (`COMPAT.md` §6) generated, not written (S-6)
- [ ] `check_failsafe_arms` proving the published table is what a program actually owes
- [ ] the budget of three stated as part of the contract, with TM-013's
      major-version rule beside it
- [ ] the one-arm case for `cal`-only consumers stated prominently — it is the
      library's best answer to "what does importing this cost me"

### 1.0.2 — the guide
- [ ] getting started: a working program in under thirty lines
- [ ] **the model, first and at length**: the three scales, why `Instant` and
      `Timestamp` do not convert, and why `Period` and `Duration` are different
      types. A reader who understands only this will use the library correctly
- [ ] every format, with examples generated **by the golden suite**, so the
      documentation cannot show output the library does not produce
- [ ] the calendar-arithmetic rules with `SPAN_MODEL.md` §3's worked examples,
      including the non-associativity — a user who meets it in production
      should find it documented, not discover it
- [ ] the tzdb version policy (`COMPAT.md` §3) and how to read
      `ntime_tzdb_version()`
- [ ] a page on what `ntime` deliberately does not do, and why: no leap
      seconds, no non-Gregorian calendars, no locale, no format strings, no
      system tzdb at 1.0

### 1.0.3 — examples
- [ ] one per format, minimal
- [ ] the two consumers from 0.7.4, tidied
- [ ] an example of the DST-edge resolution modes, because it is the API most
      likely to be used wrongly
- [ ] every example built **and run** by the harness, so a broken example is a
      red run

### 1.0.4 — versioning
- [ ] TM-013 written into `docs/` and the release notes
- [ ] **adding an error identity is a major version** stated prominently — the
      one thing about this ecosystem a consumer most needs to know
- [ ] **a tzdb bump is a minor version** stated beside it
- [ ] the current error identity count (three) published, so a consumer can see
      the budget rather than infer it

## Gate

A person who has not seen the code can build a working program from `docs/`
alone, and every example is green in the harness.

## After

The post-1.0 map in `ROADMAP.md`: the system tzdb reader (1.1, a major version
for its fourth error identity), `aarch64` (1.2), intervals and possibly
recurrence (1.3), the verified build (1.4), and the `nparse` dependency once
O-N1 closes (1.5).
