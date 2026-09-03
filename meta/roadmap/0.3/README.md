# Cycle 0.3 — The host boundary

**`src/host/`: the clocks, the system-zone discovery, and the test double.**
Five functions, and the check that nothing else in the library is impure.

## Why here, and why it is small

Because it is the only impure module (TM-018), and everything above it is
testable without it. Putting it early gets the syscall shapes verified while
the library is small; keeping it to five functions is what makes the purity
claim worth making.

## Decisions in

TM-008 (Linux x86-64), TM-018 (purity), TM-019 (no implicit local time). All
settled.

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.3.0 | **The clocks** — `clock_gettime` through `sys`, the three readings | a `Timestamp` from the machine, range-checked |
| 0.3.1 | **`check_purity` goes live** — the dormant check from 0.0.3, turned on | the library's reproducibility claim, enforced |
| 0.3.2 | **The system zone** — the four-step discovery, and what it reports | a program can ask, and is told which mechanism answered |
| 0.3.3 | **The double** — the test host module, in `tests/` | every clock-dependent behaviour reproducible |
| 0.3.4 | **Close** | `done/0.3/`, `0.4.0.md` written |

## Checklist

### 0.3.0 — the clocks
- [ ] `src/host/sys.npk` with the four syscall numbers, each carrying the header it came from as a comment
- [ ] the 16-byte `timespec` laid out in a `buffer`, asserted by `#size_of` and by offsets (probe 03's shape)
- [ ] `host_now_utc` (CLOCK_REALTIME 0), `host_now_boot` (CLOCK_BOOTTIME 7)
- [ ] `host_now_instant` calls the floor's `mono_now()`, **not** `clock_gettime` (H-5) — so an `ntime` `Instant` and an executor deadline are on the same timeline by construction
- [ ] `host_clock_res` over `clock_getres`
- [ ] errnos **forwarded verbatim** (H-7), so this module declares no error and costs no arm — asserted by `check_error_budget`
- [ ] the returned `Timestamp` range-checked (H-8): an unset machine clock is `ETimeValue`, not a value that fails somewhere less obvious
- [ ] **no state in the module** (H-3): a test asserts two calls are two syscalls
- [ ] `// stress: 40` on every clock test

### 0.3.1 — `check_purity` goes live
- [ ] the dormant check from 0.0.3 turned on and green
- [ ] **seen to fail**: a deliberately planted `mono_now()` in `src/cal/` fails the build, by name
- [ ] `check_host_isolation` likewise: a planted `host_now_utc()` call in `src/fmt/` fails
- [ ] both checks' ban lists reviewed against what `src/` actually contains now, rather than what 0.0.3 guessed

### 0.3.2 — the system zone
- [ ] `SystemZone` and `ZoneSource` as `HOST.md` §4 defines them
- [ ] the four steps in order, stopping at the first that answers (H-13)
- [ ] `$TZ` with a leading `:` stripped; **a POSIX rule string refused** with `ETimeZone`/`Unknown` (H-13.1), not parsed
- [ ] `/etc/localtime` read as a **symlink target**, never as bytes (H-14)
- [ ] `readlink`'s four facts honoured (H-15): the length is the authority, the result is not NUL-terminated, `NTIME_PATH_MAX` bounds it, a truncated result is not-found
- [ ] `/etc/timezone` as step 3
- [ ] **not-found is `found: false`, not UTC** (H-13.4) — a test asserts it on a machine with none of the three
- [ ] the descriptor closed on every path (S-20)

### 0.3.3 — the double
- [ ] the fake host module in `tests/`, **not** in `src/` (H-10)
- [ ] `fake_set_utc`, `fake_set_instant`, `fake_advance`
- [ ] the harness links whichever host object it is told to, and a test proves the substitution works
- [ ] a demonstration that a clock-dependent behaviour is reproducible: the same fake reading twice gives the same answer, and a fixed sequence gives a fixed transcript

## Gate

`check_purity` green **and seen to fail**, and every clock test green under
`// stress: 40`.

## Watch for

- **This module is the only place `ntime` can be non-deterministic**, so it is
  the only place a `stress` run can find something. Forty runs is not
  ceremony here.
- **`fd` is a type, not a name**, and this is the module that wants it.
- **The system-zone discovery is where a careless implementation is wrong four
  ways at once** — H-15 names all four, and each is a test.
- **Resist adding a sixth function.** Every addition to this module is a
  subtraction from the purity claim, and the claim is what makes the other
  cycles testable.
