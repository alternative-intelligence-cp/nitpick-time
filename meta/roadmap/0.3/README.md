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

**And one open question reaches it, blocking nothing: `meta/OPEN_QUESTIONS.md`
Q-7**, the author's — whether `instant_of`'s name should say it takes a raw
reading. `host_now_instant` and `host_now_boot` build their readings through
`instant_of` (0.3.0's checklist); under the recommended answer nothing here
changes, and under the other the rename lands first, by a decision of its own,
and 0.3.0's plan reads it. *(From cycle 0.2's close, `done/0.2/0.2.4.md`;
the question is the cycle audit's C2, TM-243.)* *(Answered 2026-10-02 by the
author, the workbench's question 21: **A, keep `instant_of`**. Nothing here
moves; `0.3.0.md`'s gate reads the answer before its step 2 builds on the
name, and its decision for the clocks records it and strikes Q-7.)*

**And one more since, blocking nothing: `meta/OPEN_QUESTIONS.md` O-X11**, ours
— raised by 0.3.0's verification on 2026-10-08: `check_int128_sites` reads
spellings, so a wide value no width is spelled for, a call's result, passes
it. It is dormant and older than this cycle, and 0.3.1's planner decides
whether a check that reads types rather than spellings is in scope, and when
(`0.3.0.md` §7). *(Decided at 0.3.1's planning, 2026-10-08: in scope, at
0.3.1 — `0.3.1.md`'s PD-96, a second reading of the library's emission
beside `check_int128_sites`, over the reader O-X9's scan is built on.)*

**And one more since, blocking nothing: `meta/OPEN_QUESTIONS.md` O-X12**, ours
— raised by 0.3.1's fix on 2026-10-08, and registered at 0.3.2's planning: a
generic function of `src/` that nobody instantiates is in no emission, so the
two readings of the emission read it not at all and `check_purity` reads its
spellings alone. Dormant, and older than 0.3.1. *(Decided at 0.3.2's
planning, 2026-10-08: every generic function `src/` declares instantiated in
an emission the two readings read — `0.3.2.md`'s PD-99, its first step.)*

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.3.0 | **The clocks** — `clock_gettime` through `sys`, the three readings — **[`0.3.0.md`](0.3.0.md)**, written at cycle 0.2's close, measured at `5fbaf4a`, and rehearsed from its blocks in its real position on 2026-10-07 and 2026-10-08 (its §8); it opens with the instrument the close handed on | a `Timestamp` from the machine, range-checked |
| 0.3.1 | **`check_purity` goes live** — the dormant check from 0.0.3, turned on — **[`0.3.1.md`](0.3.1.md)**: its ban list and `check_host_isolation`'s reviewed against the language at the pin and `src/host/`'s body, each seen to fail in a real module, and two readings of the library's emission beside the spelling checks, the calls (O-X9) and the wide values (O-X11) — planned at `5fbaf4a` and rehearsed from its blocks in its real position on 2026-10-08 (its §8) | the library's reproducibility claim, enforced |
| 0.3.2 | **The system zone** — the four-step discovery, and what it reports — **[`0.3.2.md`](0.3.2.md)**: `host_system_zone` answering the name each step finds and the mechanism that answered, the lookup the caller's at cycle 0.6, its tests in a user and mount namespace each unit makes with an `/etc` of its own; and first every generic function of `src/` read in an emission (O-X12) — planned at `5fbaf4a`, rehearsed from its blocks in its real position, and revised for its verifier's findings and rehearsed again, on 2026-10-08 (its §8) | a program can ask, and is told which mechanism answered |
| 0.3.2a | **The adoption of compiler `7e91730`** — landing 103, the libraries' one re-pin, by the author's word of 2026-10-08: every slot a string's bytes reach spelled `fixed uint8[]`, the read-only view, with the old compiler seeing no difference; then the pin's own moves — LLVM 20.1.8, the self-check's two-code case, five returns of the view, five headers' counts (the compiler's DEF-164 and DEF-165), and the adoption list below — **[`0.3.2a.md`](0.3.2a.md)**, planned and rehearsed in its real position at both pins on 2026-10-09 (its §8) | the tree green at `7e91730`, and CI pinned there |
| 0.3.3 | **The double** — the test host module, in `tests/` | every clock-dependent behaviour reproducible |
| 0.3.4 | **Close** | `done/0.3/`, `0.4.0.md` written |

## Checklist

### 0.3.0 — the clocks
*(Restated 2026-10-02, at cycle 0.2's close, to `0.3.0.md`'s drafted decisions, PD-91 … PD-94. The first item is new — the instrument the close handed on; the `sys.npk` item is struck for the shape PD-93 drafts; `HostClock`, `timespec_ns` and the arm bill are named; and the H-3 item says how a test sees it. The rest keep their words.)*
- [x] **FIRST, the instrument cycle 0.2's close handed on, in a commit of its own**: `check_int128_sites` reads a numeric literal's width suffix as it reads a type's name, so `(3i256 * 5i256) =>! int64` in a function `SPAN_MODEL.md` §5 does not mark is a finding; two plants, and `TESTING.md` §2's row restated (PD-91) *(found by 0.2.4a's verifier after the cycle audit; `done/0.2/0.2.4.md`)* — **done, TM-246**: both plants unseen by the check before it, its first control read as a stale mark, and both caught after; the tree 0 findings, the headline's count 15 with `bytes_put_int`'s `0i128`; its own commit green with 94 plants
- [ ] ~~`src/host/sys.npk` with the four syscall numbers, each carrying the header it came from as a comment~~ — restated by PD-93, the item below: two numbers this subcycle needs, kept in `host.npk`, and no header on this machine their source
- [x] the two syscall numbers — `clock_gettime` 228 and `clock_getres` 229 — and the clock ids 0, 1 and 7, as private `fixed int64`s in `src/host/host.npk`, each with its source in a comment: the compiler's runtime at the pin and the kernel's own table (PD-93) — TM-248, and `meta/research/CURRENCY.md`'s row
- [x] the 16-byte `timespec` laid out in a `buffer`, asserted by `#size_of` and by offsets (probe 03's shape) — `probe03` asserts both on every run, and the module's three readings are its shape, the reads in bounds by construction and said so at each (S-17b's fourth row)
- [x] `host_now_utc` (CLOCK_REALTIME 0), `host_now_boot` (CLOCK_BOOTTIME 7) — `host_now_boot`'s nanoseconds through a private `timespec_ns`, which refuses a reading an `int64` cannot hold before it multiplies (PD-93) — TM-248
- [x] `host_now_instant` calls the floor's `mono_now()`, **not** `clock_gettime` (H-5) — so an `ntime` `Instant` and an executor deadline are on the same timeline by construction — TM-248; its IR calls `mono_now` and no `npk_sys6`
- [x] `host_clock_res` over `clock_getres`, on `HostClock` — `{ Realtime; Monotonic; Boottime; }`, declared in `host`, which H-1 names and no specification declared (PD-93) — TM-248, H-1 and H-4 dated
- [x] **`BUILD.md` B-17 gains `host` → `span`, by decision, when `host` first imports it** (PD-92): `host_now_instant` and `host_now_boot` return `Instant`s, and both fields of an `Instant` are sealed, so `host` builds them through `span`'s public `instant_of` (TM-215, TM-216) — B-17 draws `host` → `zone`, `cal`, `core` today *(handed on by `done/0.2/0.2.0.md` §7)* — and `host_now_utc`'s `Timestamp` through `timestamp_of`, its fields sealed since cycle 0.2.1 (TM-219, TM-220) — TM-247; `check_layering`'s new plant, `host` importing `fmt`, red beside `host` importing `span`
- [x] errnos **forwarded verbatim** (H-7), so this module declares no error and costs no arm — asserted by `check_error_budget`; and its bill measured, 11 for `host` alone and 13 for the umbrella with its five names (PD-93) — `check_error_budget` silent; 11 by `arms.compute_bill` and by `NITPICK-REACH-003`, 13 the umbrella's, both tagged
- [x] the returned `Timestamp` range-checked (H-8): an unset machine clock is `ETimeValue`, not a value that fails somewhere less obvious — by `timestamp_of`, whose `YearRange` refusal is H-8's (TM-220) — and the unit's exit 10 is red when `host_now_utc` hands it a nanosecond field a second high
- [x] **no state in the module** (H-3): a test asserts two calls are two syscalls — each reading ADVANCES within a million reads, which a cached or computed one never does; the module's IR holds no global that is not `constant`; and the four mutants no test can see named (PD-94) — TM-249: ten of fourteen one-line mutants red at their exits on both legs, the four named in the unit's header and under H-3
- [x] `// stress: 40` on every clock test — `tests/unit/host_clocks.npk`, forty runs a leg on every full invocation

### 0.3.1 — `check_purity` goes live
*(Stale in its title, found at cycle 0.2.0's planning: `check_purity` has been live since cycle 0.0.3, TM-126. What this subcycle owes is the review of its ban list against a `src/` with a real `host/` — the last item below — and the two plants. `done/0.2/0.2.0.md` §7.)*
- [x] the dormant check from 0.0.3 turned on and green — live since cycle 0.0.3 (TM-126), and green over `src/host/`'s body: 0 findings over the eight files outside `src/host/` and `src/lib.npk`, at 0.3.1 as at 0.3.0
- [x] **seen to fail**: a deliberately planted `mono_now()` in `src/cal/` fails the build, by name — TM-252: a full run over a copy with `mono_now()` appended to `src/cal/cal.npk` is RED, `check_purity` naming the file, the line and `mono_now`, and `check_call_edges` the function and `npk_mono_now` (`0.3.1.md`'s record)
- [x] `check_host_isolation` likewise: a planted `host_now_utc()` call in `src/fmt/` fails — TM-253: the same run names `src/fmt/fmt.npk`'s `host_now_utc`, and `check_layering` its import of `host`
- [x] both checks' ban lists reviewed against what `src/` actually contains now, rather than what 0.0.3 guessed — and against what the language offers at the pin: the two items below

*(Four more, from 0.3.1's planning on 2026-10-08 — `0.3.1.md`: the two
questions handed on, which share one reader of the library's emission, and
the two ban lists' decisions. The four above keep their words.)*
- [x] **O-X9**: the call-edge scan — every call a function of `src/` outside `src/host/` makes, read from `npkc`'s emission of the umbrella and held to a reviewed allowlist (PD-95) — **TM-250**, `check_call_edges`: eight plants caught and eight controls silent; over the tree 0 findings, `src/host/` reaching `npk_mono_now` and `npk_sys6`, every non-generic function `src/` declares in the emission
- [x] **O-X11**: the wide values — every integer wider than `i64` in that emission held to §5's sites, spelled or not (PD-96) — **TM-251**, `check_wide_types`: three plants caught; over the tree exactly §5's three marked functions hold one
- [x] `check_purity`'s list: every builtin and every synchronous public prelude function at the pin that reaches past the program's own memory, matched as a call with an identifier boundary on its left (PD-97) — **TM-252**: forty-three names in seven classes; five plants red against the six names before it and caught after, and `reopen(` a finding before and none after *(corrected 2026-10-08 by the subcycle's verification, where the item said "every builtin and prelude function": the asynchronous prelude names that do and are not on the list — `text_read_line`, `text_write_str`, `text_write_line`, `ByteReader.seek` and `LineBufWriter.flush` — are callable only from an `async func`, which `check_call_edges` refuses in `src/` unless it is generic — and a generic one the arm bill refuses instead, its `await` or spawn arming `DeadlineExceeded`, which no consumer owes (the fix's verification, where this called it a hole); TM-252's dated note)*
- [x] `check_host_isolation`'s: every name `src/host/` makes public, `HostClock` among them, beside the `host_` prefix (PD-98) — **TM-253**: its plant unseen before and caught after

### 0.3.2 — the system zone
*(Restated at 0.3.2's planning, 2026-10-08, to `0.3.2.md`'s drafted
decisions, PD-99 … PD-102: `ZoneId` and the compiled table it indexes are
cycles 0.5's and 0.6's, so `SystemZone` holds the NAME each step finds, and
the lookup — a rule string's refusal with it — is the caller's, at 0.6
(PD-101); and a machine with none of the three is one the unit makes (PD-100).
The items keep their words; the first and third carry what PD-101 makes of
them.)*
- [x] `SystemZone` and `ZoneSource` as `HOST.md` §4 defines them — *as PD-101 amends §4: the name, where H-12 held a `ZoneId`, and `EtcTimezone`, where it named `TzDirLink`* — **TM-256**, H-12 amended; both re-exported, and read by `check_host_isolation` among `src/host/`'s public names
- [x] the four steps in order, stopping at the first that answers (H-13) — each a private function, `host_system_zone` `never fails`; `tests/unit/system_zone_etc.npk`'s exit 32 sees step 2 answer before step 3, and every `$TZ` unit sees step 1 answer before the machine's `/etc/localtime`
- [x] `$TZ` with a leading `:` stripped; **a POSIX rule string refused** with `ETimeZone`/`Unknown` (H-13.1), not parsed — *as PD-101 places it: reported as the text it is, never parsed, and refused by the lookup, cycle 0.6's `zone_by_name`* — `tests/unit/system_zone_tz.npk`, `_colon.npk`, `_colon_bare.npk`, `_path.npk` and `_empty.npk`, and `_raw.npk`'s two environments by `execve`; cycle 0.6's item noted
- [x] `/etc/localtime` read as a **symlink target**, never as bytes (H-14) — `readlink`, 89; exits 34 (a dangling link answers) and 38 (a regular file is passed by)
- [x] `readlink`'s four facts honoured (H-15): the length is the authority, the result is not NUL-terminated, `NTIME_PATH_MAX` bounds it, a truncated result is not-found — each kept where H-15's dated note says; a link of 4 095 bytes read whole (exit 40), and the two no test can see named: the kernel never makes a link that fills the buffer, and a zeroed buffer hides a NUL scan
- [x] `/etc/timezone` as step 3 — its first line; exits 31, 41 … 48 and 55 … 59
- [x] **not-found is `found: false`, not UTC** (H-13.4) — a test asserts it on a machine with none of the three — exit 30, an empty `/etc` in the unit's own namespace (TM-255)
- [x] the descriptor closed on every path (S-20) — an `OwnedFd`, closed by its drop; the lowest free descriptor held across all thirty calls

*(Four more, from 0.3.2's planning on 2026-10-08 — `0.3.2.md`: the question
0.3.1's fix raised and its verifier's nit, in a commit before the zone; the
instrument the zone's tests stand on, in a commit of its own; and the tests.
The eight above keep their words.)*
- [x] **O-X12**: every generic function `src/` declares instantiated in `tests/unit/generic_instances.npk`, its emission read by `check_call_edges` and `check_wide_types` beside the umbrella's, and a generic no instance holds a finding (PD-99) — **TM-254**: four plants caught and four controls silent, each unseen by the checks before it; over the tree `vec.npk`'s nine, at `int64`, reach the allocator, the error route and LLVM's arithmetic, every symbol in the allowlist
- [x] the 0.3.1 verifier's nit: `check_purity`'s docstring and TM-252's note say a truncation of descriptors is red "only where the `DecreasesViolated` and `LimitViolated` it arms are new" — it is *any of* them, `DecreasesViolated` alone in `src/core/vec.npk` — corrected by dated notes, not rewritten — the docstring in place, recording its words, and TM-252's note by a further dated sentence
- [x] a unit makes its own `/etc` — a user and a mount namespace and an empty `tmpfs`, by its own syscalls; `probe22` measures the shape and the kernel's longest link, and CI lifts Ubuntu 24.04's restriction on the namespace (PD-100) — **TM-255**: `probe22` exit 0 on both legs, here and in CI after the step that lifts the restriction; `TESTING.md` V-1m
- [x] the tests: one unit of thirty machines in a namespace of its own, the lowest free descriptor held across every call; five units of `$TZ`, and one that makes by `execve` the environments no harness line can; every exit seen red on a mutant of `host` but the belts, each named; every single-site mutant of the system zone's section run; and each no test can see named, with why (PD-102) — **TM-257**: seven units, forty runs a leg; of 293 single-site mutants, 28 stillborn, 237 red and 28 named; the mutants in `0.3.2.md`'s record

*(The fourth was restated at the plan's revision, 2026-10-08, after its
verifier measured what it claimed. It said "one unit of nineteen machines …;
three units of `$TZ`; every exit seen red on a mutant of `host`, and the
mutants no test can see named" — and a machine a unit can make saw mutants
the plan had named unseeable.)*

### 0.3.2a — the adoption of compiler `7e91730`
*(Written at 0.3.2a's planning, 2026-10-09 — `0.3.2a.md`, PD-105 and PD-106. It carries this README's list "The adoption, when the pin moves", below.)*
- [ ] the unchanged tree measured at both pins: `GREEN -- 143` at `5fbaf4a`; at `7e91730` refused at the toolchain check, and with its LLVM row moved red at the self-check and, past it, by landing 103's readers and five headers' counts, each enumerated
- [ ] every slot a string's bytes reach is `fixed uint8[]`, none written through, and `5fbaf4a` sees no difference — every file's codes and sites as before, `GREEN -- 143` there (PD-105)
- [ ] the pin moved: LLVM 20.1.8, the self-check's cases 2 and 3 on two codes, five returns of the view, the five headers, and the adoption list's six items each measured — `GREEN -- 143` at `7e91730` (PD-106)
- [ ] the readings of `npkc`'s output — `check_call_edges`, `check_wide_types`, and `check_purity` beside them — at both pins, what moves said and why
- [ ] CI pinned to `7e91730` — the commit, the emission's row and LLVM 20.1.8, and the full invocation's comment back above the harness — and its log read per job
- [ ] the prose, and the sweep read line by line

### 0.3.3 — the double
- [ ] the fake host module in `tests/`, **not** in `src/` (H-10)
- [ ] `fake_set_utc`, `fake_set_instant`, `fake_advance`
- [ ] the harness links whichever host object it is told to, and a test proves the substitution works
- [ ] a demonstration that a clock-dependent behaviour is reproducible: the same fake reading twice gives the same answer, and a fixed sequence gives a fixed transcript

## The adoption, when the pin moves

**Cycle 0.2 closed at compiler `5fbaf4a`, and the next re-pin is the
orchestrator's to place**, as an adoption subcycle of its own that measures the
unchanged tree at both pins before it changes anything, as 0.1.0b, 0.1.4c and
0.2.0a did. What it owes here, from cycle 0.2's close (`done/0.2/0.2.4.md`):

1. **The statement form of `#unreachable()`** — `if (r.is_error) {
   #unreachable(); }` before a read of `r.value` — re-measured at the new pin:
   at `5fbaf4a` it is `NITPICK-TAINT-001`, the compiler's defect the workbench
   registry holds and `meta/OPEN_QUESTIONS.md` restates (TM-245). If it
   compiles, a decision keeps `span`'s two `?| #unreachable()` or respells
   them, and strikes the question with its number.
2. **`timestamp_since`'s `int128` multiplication and `instant_since`'s `int128`
   subtraction** linked at both legs against `npkrt.o` alone, as
   `done/0.2/0.2.3.md` §7 and `done/0.2/0.2.4b.md` §1.7 measured them: at
   `5fbaf4a` each is inline — `llvm.smul.with.overflow.i128` and
   `llvm.ssub.with.overflow.i128` — and no libcall is called, `__muloti4`,
   which `npkrt.o` does not define, among them.
3. **The compiler's lexer re-read** whatever part E says (TM-202), and
   `harness/lexical.py` brought to it; part E's third half re-run against the
   literal reader `check_constants_named` uses (TM-231).
4. **`src/`'s `#wild_slice` sites** — nine in code, in `bytes.npk` and
   `vec.npk`, fourteen lines naming it with the comments, measured at cycle
   0.2's close — are the first to read at a pin that carries the compiler's
   D-341; cycle 0.2 added none.
5. **Each CI's pin bump**, and the emission row CI asserts (TM-212), in the
   adoption's own commit.
6. **The compiler's builtin table and prelude re-read against
   `check_purity`'s list** (TM-252) — `src/frontend/builtins.npk` and
   `src/prelude/prelude.npk` at the new pin: a name that reaches past the
   program's own memory joins the list *(read with TM-252's dated note of
   2026-10-08: the list holds every synchronous one, and the note names the
   asynchronous ones that are not on it)*, and a runtime symbol
   `check_call_edges` finds unreviewed joins `CALL_EDGE_ALLOW` or is refused,
   in the adoption's own commit (TM-250). And the emission's names —
   `npk.<module>.<name>` at `5fbaf4a` — read again: `check_call_edges` holds
   every non-generic function `src/` declares to it, so a re-pin that renames
   them is a red run.

*(Carried by 0.3.2a, the adoption of compiler `7e91730`, 2026-10-09 —
`0.3.2a.md` §1, TM-258 and TM-259 — each item measured at both pins. **1**
The statement form compiles at `7e91730`, the compiler's DEF-225, and runs on
both legs; `?|` is kept and O-N34 struck. **2** Both functions' `int128`
arithmetic is inline at both legs under each pin's LLVM, and no object names
a symbol `npkrt.o` does not define. **3** The lexer re-read: a float's scan and
a refused integer literal's token moved, and no span `lexical.py` finds; part
E is green at both pins, its third half too. **4 waits**: the compiler's D-341
is settled and not built at `7e91730`, so `src/`'s nine `#wild_slice` sites
read as they did — the re-pin that carries its build owes this item. **5** CI
is pinned to `7e91730`, its emission row notice 103's. **6** The builtin
table's fifty-seven names and the prelude's sixty-three public functions are
the same at both pins, the one row that moved `string_bytes`'s result, so
`check_purity`'s list stands; `check_call_edges` reaches no symbol outside its
allowlist, and the emission's names are `npk.<module>.<name>` as before.)*

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
