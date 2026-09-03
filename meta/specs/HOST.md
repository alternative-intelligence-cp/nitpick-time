# `src/host/` — the one impure module

Everything in `ntime` is a pure function of its arguments except what is in
this module (`SAFETY.md` §3). It is small on purpose, it is the only place a
syscall appears, and it is the only place a test needs a double.

---

## 1. The boundary

**Rule H-1.** `src/host/` contains exactly five public functions and nothing
else:

```nitpick
pub func:host_now_utc        = Timestamp();          // CLOCK_REALTIME
pub func:host_now_instant    = Instant() never fails;// mono_now()
pub func:host_now_boot       = Instant();            // CLOCK_BOOTTIME
pub func:host_clock_res      = Duration(HostClock:which);
pub func:host_system_zone    = SystemZone();
```

**Rule H-2 (TM-018) — nothing else in the library calls any of them.** A function that
needs "now" takes it as a parameter (`SAFETY.md` S-9). `check_purity` enforces
the converse — that no syscall appears outside this module — and a second check
enforces this one: no module outside `src/host/` names a `host_` symbol except
`src/lib.npk`'s re-export.

**Rule H-3 — this module has no state.** No cached clock, no memoised zone, no
lazy initialisation. Two calls to `host_now_utc()` are two syscalls, which is
what the caller asked for.

---

## 2. The clocks

**Rule H-4 — the syscall is `clock_gettime`, number 228 on x86-64**, taking a
clock id and a pointer to a `struct timespec`:

```
struct timespec { int64 tv_sec; int64 tv_nsec; }    // 16 bytes, align 8
```

laid out in a `buffer` and handed to `sys` as a pointer, the same shape the
sibling library uses for `ioctl` — and a cycle-0.0 probe asserts the 16 bytes
and the field offsets rather than trusting this paragraph.

| Constant | Value | Used by |
|---|---|---|
| `CLOCK_REALTIME` | 0 | `host_now_utc` |
| `CLOCK_MONOTONIC` | 1 | *(not used — see H-5)* |
| `CLOCK_BOOTTIME` | 7 | `host_now_boot` |

**Rule H-5 — `host_now_instant()` calls the floor's `mono_now()`, not
`clock_gettime`.** (There is no floor builtin for the *wall* clock, which is
why `host_now_utc` goes through `sys`; recorded as O-N2, with no ask.) The floor already provides `CLOCK_MONOTONIC` nanoseconds, it
is `never fails`, and it is the same clock the deadline substrate uses — so an
`Instant` from `ntime` and a deadline from the executor are on the same
timeline by construction rather than by coincidence. Reimplementing it here
would be a second reading of one clock through a second path.

**Rule H-6 (TM-010) — `CLOCK_MONOTONIC` and `CLOCK_BOOTTIME` both produce
`Instant`, and they are not interchangeable.** `BOOTTIME` includes suspend; `MONOTONIC`
does not, on Linux. An `Instant` records which clock produced it in a field, and
`instant_since` refuses a pair from different clocks with `ETimeValue` — the
same argument as M-3, one level down.

```nitpick
pub struct:Instant = { int64:ns; uint8:clock; };   // clock: 0 monotonic, 1 boottime
```

**Rule H-7 — `host_now_utc` forwards the kernel's errno verbatim**
(`SAFETY.md` S-5), so it declares no error and costs no `failsafe` arm.
`clock_gettime(CLOCK_REALTIME, valid-ptr)` cannot fail on Linux, and the
impossible branch still returns the error rather than trapping, because "cannot
fail" is a claim and claims are checked — the compiler's own posture on the
same call (D-061).

**Rule H-8 — the returned `Timestamp` is range-checked.** A `CLOCK_REALTIME`
reading from a machine whose clock is unset can be anything; if it is outside
`CALENDAR.md` §2's range the answer is `ETimeValue`/`YearRange`, not a
`Timestamp` that fails later somewhere less obvious.

---

## 3. The test double

**Rule H-9 — `src/host/` is the only module that needs one**, which is the
whole reason the boundary is where it is. The double is a build-time
substitution rather than a runtime flag:

```nitpick
// tests only: a host module whose readings are supplied by the test
pub func:fake_set_utc     = NIL(Timestamp:t) never fails;
pub func:fake_set_instant = NIL(Instant:i) never fails;
pub func:fake_advance     = NIL(Duration:d) never fails;
```

**Rule H-10 — the double lives in `tests/`, not in `src/`.** A test harness
that links a different `host` module is the honest shape; a `#[cfg(test)]`
switch inside the shipped library is a second code path in the artifact, and
the ecosystem's closed-world link makes the substitution trivial anyway — the
harness links whichever `host` object it was told to.

**Rule H-11 — every other module is tested with no double at all**, because
every other module is pure. That is the payoff, and it is the reason to keep
this module as small as H-1 makes it.

---

## 4. The system zone

**Rule H-12 (TM-019) — there is no implicit local time** (`SAFETY.md` S-11).
`host_system_zone()` is a function a program calls on purpose, and it says what
it found:

```nitpick
pub struct:SystemZone = {
    ZoneId:zone;
    ZoneSource:source;
    bool:found;
};
pub enum:ZoneSource = { TzEnvironment; EtcLocaltime; TzDirLink; NotFound; };
```

**Rule H-13 — the discovery order**, and it stops at the first that answers:

1. **`$TZ`**, from `environ()`. A bare name (`Europe/London`) is looked up in
   the compiled table. A leading `:` is stripped, per POSIX. A POSIX *rule*
   string (`GMT0BST,M3.5.0/1,M10.5.0`) is **refused** — `ETimeZone`/`Unknown` —
   because parsing one at run time is the thing `ZONE_MODEL.md` Z-12 declined,
   and a program that sets `TZ` to a rule rather than a name is asking for
   something this library does not do.
2. **`/etc/localtime` as a symlink.** `readlink` it and take the tail after
   `zoneinfo/`. This is how essentially every Linux distribution records the
   choice, and it yields a *name* rather than requiring the file be parsed.
3. **`/etc/timezone`**, a one-line text file with the name. Debian's, and
   present on enough systems to be worth the four lines.
4. **Not found.** `found: false`, `source: NotFound`. Not an error and not a
   fallback to UTC: a program that needs local time and cannot find one should
   decide what to do, and a library that quietly substitutes UTC has made that
   decision badly on its behalf.

**Rule H-14 — the file that is never read is `/etc/localtime` itself.** Step 2
reads the *link target*, not the TZif content. If `/etc/localtime` is a regular
file rather than a symlink — which happens — step 2 does not answer and step 3
is tried. Reading its bytes is the post-1.0 opt-in of Z-3 and nothing here.

**Rule H-15 — `readlink` is syscall 89** (`readlinkat` is 267); the buffer is
`NTIME_PATH_MAX` (4096) bytes, the result is not NUL-terminated by the kernel
and the returned length is the authority, and a truncated result is treated as
not-found rather than as a shorter name. Every one of those four facts is a
place a careless implementation is wrong.

**Rule H-16 — the descriptor is closed on every path.** `SAFETY.md` S-20: the
module holds nothing across a call.

---

## 5. What is deliberately absent

- **Setting the clock.** `clock_settime` is a privileged operation with
  system-wide effect, and a date library is not where it belongs.
- **NTP status.** `adjtimex` reports whether the clock is synchronised and
  whether a leap second is pending. It is genuinely useful and it is a
  different library's job; recorded so the absence is a decision.
- **A caching layer.** H-3. A program that wants to read the clock once and
  pass it around can do exactly that, and then it knows it did.
- **Process and thread CPU clocks.** `CLOCK_PROCESS_CPUTIME_ID` measures work,
  not time; that is a profiler's concern.

---

## 6. Open items

*(None. Every item this document raised is settled in `../DECISIONS.md`.)*
