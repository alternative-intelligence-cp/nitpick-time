# `src/host/` — the only impure module

Five functions, and nothing else in the library calls any of them (TM-018):
`host_now_utc`, `host_now_instant`, `host_now_boot`, `host_clock_res`,
`host_system_zone` — four of them since cycle 0.3.0, the clocks, beside
`HostClock`, the argument `host_clock_res` takes (TM-247 … TM-249);
`host_system_zone` is cycle 0.3.2's.

Everything outside this directory is a pure function of its arguments, which
is what makes the library reproducible, testable without a double, and portable
by rewriting one module. `check_purity` fails the build if that stops being
true. Governed by `meta/specs/HOST.md`. Built in cycle 0.3: the clocks at
0.3.0, the system zone at 0.3.2. *(It said "Built in cycle 0.3." until the
clocks were.)*
