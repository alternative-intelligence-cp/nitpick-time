# The kernel's x86-64 syscall numbers for the clocks — research digest

**As of 2026-10-07.** Question: which numbers does the Linux kernel give
`clock_gettime` and `clock_getres` on x86-64 — and `readlink`, which cycle
0.3.2 needs — so that `src/host/host.npk` can name each number's source?

## Answer

`clock_gettime` is **228**, `clock_getres` is **229** and `readlink` is **89**,
each in the `common` ABI of the kernel's own table. The table is the ABI's
statement, and the kernel does not renumber a syscall on an architecture, so
the numbers do not move with a kernel release. 228 is also the number the
compiler's runtime calls at the pin (`npk_mono_now` in
`runtime/npkrt.ll` at `5fbaf4a`: `@npk_sys6(i64 228, i64 1, …)`). 229 is in
no file of the compiler's tree at the pin (`git grep -i clock_getres` prints
nothing), and 89 is in none of its runtime or `lib/`: the word `readlink`
appears there only as a shell command in its scripts.

## Evidence

- https://raw.githubusercontent.com/torvalds/linux/master/arch/x86/entry/syscalls/syscall_64.tbl
  — retrieved 2026-10-07 — the format line, *"# <number> <abi> <name> <entry
  point> [<compat entry point> [noreturn]]"*, and the rows:

  ```text
  89	common	readlink		sys_readlink
  228	common	clock_gettime		sys_clock_gettime
  229	common	clock_getres		sys_clock_getres
  ```

- The same table, fetched once on 2026-10-02 by cycle 0.2's close, which
  quoted rows 228 and 229 into `meta/roadmap/0.3/0.3.0.md` §1.3.

## What would change this

A different number for either clock call, which would make `host.npk`'s
constants wrong: it did not. And by behaviour, which the plan measures on both
legs at the pin: `sys(229, id, ptr)` answers 0 and writes `{0 s, 1 ns}` for the
clock ids 0, 1 and 7, and an errno in the `Result` for 99.

## Confidence and gaps

High: the primary source, quoted, on two dates five days apart, and 228
corroborated by the compiler's runtime. The table is read on `master`, not at a
tagged release; for a number the ABI never changes that is the same answer.
