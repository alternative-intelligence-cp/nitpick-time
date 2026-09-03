# `src/host/` — the only impure module

Five functions, and nothing else in the library calls any of them (TM-018):
`host_now_utc`, `host_now_instant`, `host_now_boot`, `host_clock_res`,
`host_system_zone`.

Everything outside this directory is a pure function of its arguments, which
is what makes the library reproducible, testable without a double, and portable
by rewriting one module. `check_purity` fails the build if that stops being
true. Governed by `meta/specs/HOST.md`. Built in cycle 0.3.
