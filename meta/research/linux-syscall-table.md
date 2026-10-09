# The kernel's x86-64 syscall numbers for the clocks — research digest

**As of 2026-10-07.** Question: which numbers does the Linux kernel give
`clock_gettime` and `clock_getres` on x86-64 — and `readlink`, which cycle
0.3.2 needs — so that `src/host/host.npk` can name each number's source?

**And as of 2026-10-08** (cycle 0.3.2's planning): the numbers its tests call
to make an `/etc` of their own (`TESTING.md` V-1m), and the two flags
`unshare` takes — read again from the same table, and from the kernel's
`include/uapi/linux/sched.h`:

```text
83	common	mkdir			sys_mkdir
84	common	rmdir			sys_rmdir
87	common	unlink			sys_unlink
88	common	symlink			sys_symlink
89	common	readlink		sys_readlink
102	common	getuid			sys_getuid
104	common	getgid			sys_getgid
165	common	mount			sys_mount
272	common	unshare			sys_unshare
```

```text
#define CLONE_NEWNS	0x00020000	/* New mount namespace group */
#define CLONE_NEWUSER		0x10000000	/* New user namespace */
```

— https://raw.githubusercontent.com/torvalds/linux/master/arch/x86/entry/syscalls/syscall_64.tbl
and https://raw.githubusercontent.com/torvalds/linux/master/include/uapi/linux/sched.h,
each retrieved 2026-10-08, on `master`. 89 is the day before's, unchanged.

**And for cycle 0.3.2's third step, as revised the same day**: the numbers
the system zone's units use beyond those — `mknod` and `alarm`, by which the
namespace unit makes a FIFO and bounds the open it must not block on;
`execve`, by which the raw unit makes its two environments; and the constants
they pass, `MS_RDONLY` and `MS_REMOUNT` for the read-only remount and
`S_IFIFO` for the FIFO's mode — read by a research request from the same table
and from the kernel's `include/uapi/linux/mount.h` and
`include/uapi/linux/stat.h`. `execve`'s row is in the `64` ABI, not
`common`; the x32 ABI's is a row of its own, 520:

```text
37	common	alarm			sys_alarm
59	64	execve			sys_execve
133	common	mknod			sys_mknod
520	x32	execve			compat_sys_execve
```

```text
#define MS_RDONLY	 1	/* Mount read-only */
#define MS_REMOUNT	32	/* Alter flags of a mounted FS */
```

```text
#define S_IFIFO  0010000
```

— https://raw.githubusercontent.com/torvalds/linux/master/arch/x86/entry/syscalls/syscall_64.tbl,
https://raw.githubusercontent.com/torvalds/linux/master/include/uapi/linux/mount.h
and https://raw.githubusercontent.com/torvalds/linux/master/include/uapi/linux/stat.h,
each retrieved 2026-10-08, on `master`. `S_IFIFO` is octal, 4096 in decimal
as the unit writes it; `stat.h` defines it under `#if defined(__KERNEL__) ||
!defined(__GLIBC__) || (__GLIBC__ < 2)`, which decides whether a C program
built against the GNU C library sees the kernel's definition, and not the
value.

**And the four constants this library and this plan's programs declare that
had no row** — `src/host/host.npk`'s three clock ids, declared since cycle
0.3.0, sourced there to `HOST.md` H-4 and measured apart by `probe03`; and
`probe22`'s `PATH_MAX`, whose 4 096 its exits 34 and 35 measure — read by a
second research request from the kernel's `include/uapi/linux/time.h` and
`include/uapi/linux/limits.h`. Each define stands outside any conditional but
its file's include guard, and `PATH_MAX` counts the NUL, so the longest path
a buffer of it holds is 4 095 bytes:

```text
#define CLOCK_REALTIME			0
#define CLOCK_MONOTONIC			1
#define CLOCK_BOOTTIME			7
```

```text
#define PATH_MAX        4096	/* # chars in a path name including nul */
```

— https://raw.githubusercontent.com/torvalds/linux/master/include/uapi/linux/time.h
and https://raw.githubusercontent.com/torvalds/linux/master/include/uapi/linux/limits.h,
each retrieved 2026-10-08, on `master`, whose last change to `time.h` is
`9094c72c3d81bf2416b7c79d12c8494ab8fbac20` (2025-06-19) and to `limits.h`
`54d50897d544c874562253e2a8f70dfcad22afe8` (2019-03-08), by the repository's
API the same day.

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
