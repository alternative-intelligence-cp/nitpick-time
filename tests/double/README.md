# `tests/double/`

The test host — [`../../meta/specs/HOST.md`](../../meta/specs/HOST.md) H-9 …
H-11, as TM-261 reads them. `src/host/` is the one module of `ntime` a test
needs a double for, and the double lives here, never in `src/` (H-10).

One module, `host_double.npk`, imported by the tests that use it and run by
none: it has no `main`, so `../../harness/run.py`'s `EXPECT_EXEMPT` names it at
the verdict `none`, re-derived on every run (TM-137).

| Name | What it is |
|---|---|
| `HostReadings` | **the seam**: H-1's five readings as a trait — `now_utc`, `now_instant`, `now_boot`, `clock_res`, `system_zone` — each with H-1's result and `never fails` where H-1 says it, the receiver the one parameter added |
| `MachineHost`, `machine_host()` | the machine's `host` behind the seam: each method one call of `src/host/`'s |
| `FakeHost`, `fake_host()` | **the double**: readings a test sets, and nothing else — its fields `hidden`, its start the epoch, both instants at 0 ns, no zone, every clock's resolution 1 ns and nothing refused |
| `fake_set_utc`, `fake_set_instant`, `fake_advance` | H-9's three setters, each taking the double it sets |
| `fake_set_zone` | the fifth reading's setter, beside H-9's three |
| `fake_set_utc_raw` | the realtime as the kernel would hand it, unchecked: `timestamp_of` refuses it where it is read, by `YearRange` or `NanoRange`, as `host_now_utc` refuses the kernel's |
| `fake_set_res` | a clock's resolution |
| `fake_refuse_utc`, `fake_refuse_boot`, `fake_refuse_res` | a fallible reading refused with the identity the test hands it — an errno, forwarded verbatim as `host` forwards the kernel's (`SAFETY.md` S-5), or `ETimeValue` — until that reading is set again |
| `SteppedHost`, `stepped_host()`, `FakeStep`, `FakeTick` | **a reading that changes per call**: each reading answers what the `FakeHost` it points to answers, then a step runs on that double — `FakeTick` an advance per reading, or a `FakeStep` the test writes |

**The double is a value, and the substitution a type** (TM-261). A
clock-dependent function takes `<H: HostReadings>` and is instantiated with
`MachineHost` in a program and `FakeHost` in a test — at build time, statically.
The language keeps no state in a module (the compiler's D-211), and `npkc`
links no `host` object in `host`'s place (TM-117), so neither H-9's setters
without a handle nor a second `host` module could be built.

**What it cannot do**: test `host` (TM-249). It stands beside `host`, not in it.
What reaches a caller from `host` — every reading, every refusal and its
identity, a clock that moves between two readings — it answers when a test
tells it to ([`0.3.3.md`](../../meta/roadmap/0.3/0.3.3.md) §1.4b).

**What may import what**: this directory imports what `host` may (`BUILD.md`
B-17's row), and `host` itself, and `check_layering` holds it to that (TM-260).

Its tests (TM-262): [`../unit/double_readings.npk`](../unit/double_readings.npk),
the double alone; [`../unit/double_substitution.npk`](../unit/double_substitution.npk),
one generic function and both hosts, under `// stress: 40`; and
[`../golden/double_transcript.npk`](../golden/double_transcript.npk), a fixed
sequence and its fixed transcript, `double_transcript.txt`.
