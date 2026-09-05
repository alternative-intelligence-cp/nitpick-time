# `harness/` — the build and test runner

Python, because `npkg` cannot build a library yet
(`../meta/specs/BUILD.md` §1) and zero-dependency governs the artifact, not the
workbench. It retires into `npkg` the way `bootstrap/harness/` does in the
compiler repository, with both running side by side and a parity check first.

## What `run.py` is TODAY — a floor, not the harness

Written at cycle **0.0.1** and **replaced**, not extended, by 0.0.2 and 0.0.3.
There is no manifest reader, no module-graph walk, no stage dispatch, no
`--only`, and **no self-check**.

It exists in this shape for one reason: 0.0.1 puts CI in place, CI has to run
something, and the obvious something is a stub that exits 0 — which is a suite
reporting green while checking nothing, the single failure `TESTING.md` is
built to prevent. So it checks exactly what cycle 0.0.1 created:

```
$ NPKC=… NPKRT=… python3 harness/run.py
[1/4] toolchain                 $NPKC, $NPKRT, llvm-config == 20.1.2 exactly
[2/4] src/ compiles             every .npk under src/, each paired with its .ll
[3/4] tests/conformance/…       emit, assemble, link, RUN — the run is judged
[4/4] expect- header sweep      the tree partitioned, the denominator printed
```

**Read step 3 as the important one.** `npkc` exit 0 is not well-formedness
(O-N11, TM-112), so the consumer is run rather than compiled, and every `npkc`
exit 0 elsewhere is paired with the artefact it should have produced.

**Read step 4 as the one that was missing.** It states how many files it opened,
green or red, and it partitions every `.npk` into `src/` (judged by "it
compiles"), `tests/` (judged by a marker of its own or a named exemption), or
**unowned — which is a failure** (TM-115, `TESTING.md` V-1b/V-1c).

## What a green run does NOT mean

- **Not that the library works.** There is none yet; `src/` is placeholders.
- **Not that this runner can fail.** `TESTING.md` V-14's self-check is cycle
  0.0.3. Until it exists, a green run here is an *unfalsified* claim, not a
  tested one.

**It was commissioned by hand at 0.0.1 against seven planted failures** —
`$NPKC` unset; an unparseable `src/` module; the consumer's `failsafe` deleted;
a `src/` directory's placeholder deleted; an `expect-` header removed; a stale
exemption; a `.npk` in neither bucket — and it went red on each and green again
after. **That transcript is in `../meta/roadmap/0.0/0.0.1.md`'s execution
record with the exit codes**, and it is weaker than V-14, which is the point of
saying so here.
