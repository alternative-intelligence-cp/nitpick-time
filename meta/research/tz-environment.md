# What `TZ` holds, set empty or behind a `:` — research digest

**As of 2026-10-08.** Question: what does POSIX say of a `TZ` that begins
with `:`, and of one set to the empty string — and what does the reference C
library do with each — so that `HOST.md` H-13's first step can say what it
strips and whether an empty `TZ` answers?

## Answer

POSIX (Issue 8, IEEE Std 1003.1-2024, the base definitions' §8.3) makes a `TZ`
whose first character is `:` an implementation-defined form — the characters
after the `:` are the implementation's to read — and its entry for `TZ` says
nothing of a value set and empty. The GNU C library's `tzset_internal` strips
one leading `:` and reads what follows, and reads an empty `TZ` as UTC
("Universal"); an unset `TZ` is the site's default, `/etc/localtime`. So a C
program on the machine reads `TZ=` as UTC, and `TZ=:Europe/London` as
`Europe/London`.

## Evidence

- https://pubs.opengroup.org/onlinepubs/9799919799/basedefs/V1_chap08.html —
  retrieved 2026-10-08 — §8.3, the `TZ` entry, its first format: "the
  characters following the <colon> are handled in an implementation-defined
  manner." The page names The Open Group Base Specifications Issue 8, IEEE Std
  1003.1-2024. The entry does not say what a null `TZ` means.
- https://raw.githubusercontent.com/bminor/glibc/master/time/tzset.c — the GNU
  C library's source, its `master`, through the GitHub mirror of
  sourceware.org's repository (which answered a bot check) — retrieved
  2026-10-08 — `tzset_internal`:

  ```c
    tz = getenv ("TZ");
  ```
  ```c
    if (tz && *tz == '\0')
      /* User specified the empty string; use UTC explicitly.  */
      tz = "Universal";

    /* A leading colon means "implementation defined syntax".
       We ignore the colon and always use the same algorithm:
       try a data file, and if none exists parse the 1003.1 syntax.  */
    if (tz && *tz == ':')
      ++tz;
  ```
  ```c
    if (tz == NULL)
      /* No user specification; use the site-wide default.  */
      tz = TZDEFAULT;
  ```

## What would change this

A C library that read an empty `TZ` as unset — tried `/etc/localtime` — would
weaken the reason H-13.1 lets an empty `TZ` answer, which is that a silent fall
to the machine's zone would disagree with the C programs on the same machine.
It did not, for the reference implementation. And POSIX defining the `:` form
would bind H-13.1's reading of what follows it; it leaves it to the
implementation.

## Confidence and gaps

High for POSIX's wording and for glibc's behaviour, each quoted from its own
text. glibc is read on `master` through a mirror, not at a release tag; the
lines are old and the behaviour long-standing. Other C libraries were not
read, so the plan's claims name glibc alone.
