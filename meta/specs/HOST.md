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
pub func:host_system_zone    = SystemZone() never fails;
```

*(Cycle 0.3.0, TM-248: four of the five are in `src/host/host.npk` —
`host_system_zone` is cycle 0.3.2's — beside `HostClock`, the argument
`host_clock_res` takes, which no specification declared until then: `pub
enum:HostClock = { Realtime; Monotonic; Boottime; }`, `host`'s own, because
`span`'s `InstantClock` has no realtime clock and must not gain one. "Nothing
else" is no sixth PUBLIC function: the module also holds five private `fixed`
numbers — the two syscalls and H-4's three clock ids — and one private helper,
`timespec_ns`.)* *(Cycle 0.3.2, TM-256: the fifth is written, and `never
fails` — the block read `SystemZone();` — beside `SystemZone` and
`ZoneSource`, what it answers (H-12): a step that cannot read its source has
not answered, so nothing is left to fail but a trap. And beside the five, one
more private number, `readlink`'s 89, and four more helpers, the system zone's
three steps and its not-found answer.)*

**Rule H-2 (TM-018) — nothing else in the library calls any of them.** A function that
needs "now" takes it as a parameter (`SAFETY.md` S-9). `check_purity` enforces
the converse — that no syscall appears outside this module — and a second check
enforces this one: no module outside `src/host/` names a `host_` symbol except
`src/lib.npk`'s re-export.

*(Cycle 0.3.1: or any name `src/host/` makes public — `HostClock` since cycle
0.3.0 — read from its own declarations, TM-253; and a third reading holds
this rule from the library's emission, `check_call_edges`, which refuses a
call into `src/host/` from any function outside it, TM-250.)*

**Rule H-3 — this module has no state.** No cached clock, no memoised zone, no
lazy initialisation. Two calls to `host_now_utc()` are two syscalls, which is
what the caller asked for.

*(Cycle 0.3.0, TM-249: `tests/unit/host_clocks.npk` makes this observable —
each reading ADVANCES within a million reads, which a cached or computed
reading never does — forty runs a leg (`TESTING.md` V-11); and the module's IR
holds no global that is not `constant`. **Four mutants of the module no test
can see** are named in the unit's header, each held by reading instead: the
boot clock read through `CLOCK_MONOTONIC` under the `Boottime` tag — the two
differ by the time the machine has spent suspended, which a CI runner never
has; `Boottime`'s resolution asked of `CLOCK_REALTIME` — every clock's
resolution here is 1 ns; the forwarded errno's branch deleted; and
`timespec_ns`'s range check deleted — each of the last two needs a kernel that
breaks its contract. A green run is not evidence about these four.)*

*(Cycle 0.3.2, TM-257: and no memoised zone, observed —
`tests/unit/system_zone_etc.npk` asks `host_system_zone()` thirty times in
one process, `/etc` rewritten between each, and every answer is that
`/etc`'s.)*

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

*(Cycle 0.3.0, TM-248: the `CLOCK_MONOTONIC` row's "not used" holds for the
READINGS, by H-5, and `host_clock_res(HostClock.Monotonic)` hands id 1 to
**`clock_getres`, syscall 229**, which this rule did not name — the kernel's
own table (`../research/CURRENCY.md`), its behaviour measured at cycle 0.3.0's
planning: `{0 s, 1 ns}` for clocks 0, 1 and 7. Both numbers and the three ids
are private `fixed int64`s in `src/host/host.npk`, each with its source.)*

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
pub enum:InstantClock = { Monotonic; Boottime; };
pub struct:Instant = { sealed int64:ns; sealed InstantClock:clock; };
```

*(Amended at cycle 0.2.0, TM-215 and TM-216. The block read `pub
struct:Instant = { int64:ns; uint8:clock; };   // clock: 0 monotonic, 1
boottime` — and a `uint8` holds 254 values that are no clock (`SAFETY.md`
S-15c), so the tag is an enum; both fields are sealed, so `host` builds its
readings through `span`'s `instant_of`; and `instant_cmp` refuses two clocks as
`instant_since` does. `host` importing `span` is cycle 0.3's, with a
`BUILD.md` B-17 arrow it does not have yet.)* *(Cycle 0.3.0, TM-247: `host`
imports `span`, and B-17 draws the arrow.)*

**Rule H-7 — `host_now_utc` forwards the kernel's errno verbatim**
(`SAFETY.md` S-5), so it declares no error and costs no `failsafe` arm.
`clock_gettime(CLOCK_REALTIME, valid-ptr)` cannot fail on Linux, and the
impossible branch still returns the error rather than trapping, because "cannot
fail" is a claim and claims are checked — the compiler's own posture on the
same call (D-061).

*(Amended at cycle 0.1.5's second half, the cycle audit's C5: the last clause
gave the compiler the opposite posture, under the wrong decision. D-061
removes the `(!)` marker and prescribes `#unreachable()`, which TRAPS; the
compiler's posture on this call is its D-176 §3 — `mono_now` is `never fails`,
and the floor guards the impossible branch of `clock_gettime(CLOCK_MONOTONIC,
valid-ptr)` with that trap, read at `c970483`. Both treat "cannot fail" as a
claim to check. Returning the forwarded errno instead is `ntime`'s own choice,
S-5's: `host_now_utc` is fallible already, for H-8's range check, and a
forwarded errno costs no arm.)*

**Rule H-8 — the returned `Timestamp` is range-checked.** A `CLOCK_REALTIME`
reading from a machine whose clock is unset can be anything; if it is outside
`CALENDAR.md` §2's range the answer is `ETimeValue`/`YearRange`, not a
`Timestamp` that fails later somewhere less obvious.

*(Cycle 0.2.1, TM-219 and TM-220: `Timestamp`'s fields are sealed, so
`host_now_utc` builds its reading through `span`'s `timestamp_of`, whose
refusal of a `secs` outside the range is this rule's `YearRange` — the `host`
→ `span` arrow cycle 0.3's README owes for `Instant` already.)* *(Drawn at
cycle 0.3.0, TM-247: `host_now_utc`'s reading is `timestamp_of`'s.)*

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
    string:name;
    ZoneSource:source;
    bool:found;
};
pub enum:ZoneSource = { TzEnvironment; EtcLocaltime; EtcTimezone; NotFound; };
```

*(Amended at cycle 0.3.2, TM-256. The block read `ZoneId:zone;` and named
the third variant `TzDirLink`. `ZoneId`, and the compiled table it indexes,
are cycles 0.5's and 0.6's — this cycle is gated on 0.2 alone — so what the
discovery answers is the zone's NAME as the mechanism gave it, and a program
turns it into a zone with the lookup, `zone_by_name` (cycle 0.6), whose
`ETimeZone`/`Unknown` refuses a name the table lacks. `host` looks nothing up,
imports nothing from `zone`, and raises nothing: a program that reads a clock
owes no zone arm (TM-017's decomposition). And `TzDirLink` named no mechanism
H-13 has — step 3 reads a one-line text file, through no link and no `TZDIR` —
so the variant is `EtcTimezone`, beside `EtcLocaltime`. `found` is false only
with `NotFound`, and `name` is then empty.)*

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

*(Cycle 0.3.2, TM-256 — each step made exact, and the lookup placed. **Step 1**
reads the first entry of `environ()` that begins `TZ=`, in place; one leading
`:` is stripped — POSIX leaves what follows it to the implementation, and the
GNU C library strips it too (`../research/tz-environment.md`) — and the rest is
the name, verbatim, the empty value included: a set `TZ` answers, because the
GNU C library reads an empty one as UTC, and moving on to `/etc/localtime`
would answer a question the environment did not ask. A rule string is reported
as the text it is, never parsed; "**refused** — `ETimeZone`/`Unknown`" is the
lookup's, at cycle 0.6, as a name no table holds, and not this step's — the
author's decision, his answer to the workbench's question 26, 2026-10-08.
**Step 2**'s name is the tail after the LAST `zoneinfo/` that begins the
target or follows a `/`; none, or an empty tail, and the step does not
answer. **Step 3**'s name is the bytes before the file's first newline, every
other byte as the file holds it; an empty first line, an empty file, or a
read that fills its buffer of `NTIME_PATH_MAX` bytes, and the step does not
answer. And **in every step an error is that step's not answering**: nothing
is forwarded, so `host_system_zone` is `never fails` (H-1).)*

*(Cycle 0.3.2, TM-257: step 1 asserted — five units set `TZ`, a rule string,
a name behind a `:`, a `:` alone, a path and the empty value; one makes by
`execve` an environment whose first entry is `TZ`, a second after it, and
one whose entries of no, one and two bytes come before its `TZ=`; and the
namespace unit's environment holds seven names that begin like `TZ=` and are
not it.)*

**Rule H-14 — the file that is never read is `/etc/localtime` itself.** Step 2
reads the *link target*, not the TZif content. If `/etc/localtime` is a regular
file rather than a symlink — which happens — step 2 does not answer and step 3
is tried. Reading its bytes is the post-1.0 opt-in of Z-3 and nothing here.

*(Cycle 0.3.2, TM-257: asserted — a regular file at `/etc/localtime` holding
a zone's name is passed by for step 3, and a dangling link answers with its
target's tail, each in `tests/unit/system_zone_etc.npk`.)*

**Rule H-15 — `readlink` is syscall 89** (`readlinkat` is 267); the buffer is
`NTIME_PATH_MAX` (4096) bytes, the result is not NUL-terminated by the kernel
and the returned length is the authority, and a truncated result is treated as
not-found rather than as a shorter name. Every one of those four facts is a
place a careless implementation is wrong.

*(Cycle 0.3.2, TM-256 and TM-257 — where each is kept. The length is the
authority: the view of the target is built from `n`, the syscall's answer, and
nothing scans for a NUL — `tests/unit/system_zone_etc.npk` reads a link of
4 095 bytes whole. The buffer is `NTIME_PATH_MAX`, `src/core/limits.npk`'s. A
truncated result does not answer: `n >= NTIME_PATH_MAX` passes it by. **Two of
the four are held by reading, not by a test**: the kernel refuses a link
target of 4 096 bytes and holds one of 4 095 (`tests/probe/probe22_private_etc.npk`),
so no link it made fills the buffer — the refusal deleted or weakened is
unseen, and so are step 2's buffer and `readlink`'s cap a byte off, which
differ only on such a link; and a scan for the first NUL in place of `n` stops
where `n` does, because the buffer is born zeroed — unseen too. A green run is
not evidence about these.)*

**Rule H-16 — the descriptor is closed on every path.** `SAFETY.md` S-20: the
module holds nothing across a call.

*(Cycle 0.3.2, TM-256: by construction. The descriptor is `/etc/timezone`'s,
step 3's — `readlink` opens none — and it is an `OwnedFd` the moment `open`
returns it, so its drop closes it on every path out; the close's verdict is not
observed, which for a descriptor opened read-only carries nothing the answer
could use. Opened `O_NONBLOCK`, so a FIFO there never blocks the open
(`SAFETY.md` S-21), and `O_CLOEXEC`, so it never outlives the call into an
`exec`. TM-257: the lowest free descriptor is the same after every call as
before it, through each path step 3 takes. **`O_NONBLOCK` is seen**: a FIFO
nothing writes, at `/etc/timezone`, under the unit's own alarm of five seconds
— without the flag the open blocks, and `SIGALRM` ends the process, red; and
opened read-only, the step answers from a read-only `/etc`. **`O_CLOEXEC` is
held by reading**: the descriptor lives only inside the call, so only an
`exec` during it — another thread's — could see it. And so is step 3's buffer
a byte short of its read: the byte a read of 4 096 bytes writes past it lands
in the allocator's rounding, short of its guard, measured.)*

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
