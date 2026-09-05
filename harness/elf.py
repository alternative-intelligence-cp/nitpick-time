"""The ELF64 symbol table, read directly. P-13.

WHY NOT `llvm-readelf` OR `nm`. `BUILD.md` B-2 makes the undefined-symbol scan a
BUILD STEP -- the thing that makes "no C, ever" structural rather than a
convention. A rule that is law should not rest on a fourth tool outside the
`[toolchain]` pin, whose text output nothing checks and whose formatting is free
to change between releases. Python's `struct` reads an ELF64 symbol table in
about forty lines, so it does.

WHAT THE SCAN CAN AND CANNOT SEE -- READ THIS BEFORE CITING IT AS A GUARANTEE.

  It CAN see: a reference to any symbol the runtime does not define. That is
  exactly B-2's claim -- no libc, no compiler-rt, no C anywhere -- and it is
  the whole of it.

  It CANNOT see a SYSCALL. `npk_sys6` is the runtime's own generic syscall
  trampoline and is therefore IN the allowlist by construction, so a module
  that issues a raw syscall is indistinguishable, at the symbol level, from one
  that does not. This is not a defect in the scan; it is the boundary of what a
  symbol table can answer. It was measured in `nitpick-regex` (RX-120) as a
  symbol diff coming out EMPTY -- 29 undefined each way -- across exactly that
  change, and it reproduces here: an `ntime` program's undefined set is 29
  symbols and `npk_sys6` is one of them, whether or not anything calls it.
  PURITY IS A DIFFERENT CHECK: `check_purity` (`TESTING.md` §2, `SAFETY.md`
  S-10) is a SOURCE-level ban list over `src/` outside `src/host/`, and it is
  the only thing that answers "did this module touch the kernel". Do not read a
  green symbol scan as a purity result.

WHERE THE ALLOWLIST COMES FROM, AND WHY IT IS NOT WHAT THE PLAN SAID.

  P-14 and `BUILD.md` B-2 both say the allowlist is *"every `define` in
  `runtime/npkrt.ll` plus `main`"*. Measured at pin `0dfddac`, that set is
  WRONG IN BOTH DIRECTIONS -- see TM-118:

    166  `define`s in `runtime/npkrt.ll`
    111  global defined symbols in the `npkrt.o` we actually link
     56  in the .ll and NOT global in the .o -- `internal` linkage, so they
          become local symbols the linker will not resolve for anyone. An
          allowlist holding them EXCUSES a reference that then fails at link.
      2  global in the .o and NOT a `define` in the .ll -- `_start` and
          `npk_clone_raw`, which come from `module asm` blocks. An allowlist
          missing them FAILS a reference that would have linked.

  So the allowlist is derived from `$NPKRT`'s own symbol table: the artefact
  that is actually linked, named by the toolchain pin, and incapable of drifting
  from what the linker will accept. Both halves are derived -- what it provides
  and what it requires of the program -- because "plus `main`" was not enough
  either. See `runtime_allowlist` below.
"""

import struct

# Elf64 constants. Named rather than inlined because a bare 2 in a symbol-table
# reader is the kind of thing that is right until the day it is not.
ELFMAG = b"\x7fELF"
ELFCLASS64 = 2
ELFDATA2LSB = 1
SHT_SYMTAB = 2
SHN_UNDEF = 0
STB_LOCAL, STB_GLOBAL, STB_WEAK = 0, 1, 2

_EHDR = struct.Struct("<16sHHIQQQIHHHHHH")      # 64 bytes
_SHDR = struct.Struct("<IIQQQQIIQQ")            # 64 bytes
_SYM = struct.Struct("<IBBHQQ")                 # 24 bytes


class ElfError(Exception):
    """A file this reader will not guess about. Always names the file."""


def _sections(blob, path):
    if len(blob) < _EHDR.size or blob[:4] != ELFMAG:
        raise ElfError("%s: not an ELF file" % path)
    if blob[4] != ELFCLASS64:
        raise ElfError("%s: not ELF64 (e_ident[EI_CLASS] = %d)"
                       % (path, blob[4]))
    if blob[5] != ELFDATA2LSB:
        raise ElfError("%s: not little-endian (e_ident[EI_DATA] = %d)"
                       % (path, blob[5]))
    (_, _, _, _, _, _, e_shoff, _, _, _, _,
     e_shentsize, e_shnum, _) = _EHDR.unpack_from(blob, 0)
    if e_shentsize != _SHDR.size:
        raise ElfError("%s: e_shentsize is %d, not %d"
                       % (path, e_shentsize, _SHDR.size))
    if e_shnum == 0:
        # The extended form puts the real count in section 0. Refused rather
        # than guessed: nothing this harness links is anywhere near 65 280
        # sections, so meeting one means something is wrong upstream.
        raise ElfError("%s: e_shnum is 0 (the extended section count). This "
                       "reader does not handle it, and a %s-sized object "
                       "should never need it." % (path, len(blob)))
    out = []
    for i in range(e_shnum):
        off = e_shoff + i * e_shentsize
        if off + _SHDR.size > len(blob):
            raise ElfError("%s: section header %d runs past the end of the "
                           "file" % (path, i))
        out.append(_SHDR.unpack_from(blob, off))
    return out


def _cstr(blob, base, offset):
    end = blob.index(b"\0", base + offset)
    return blob[base + offset:end].decode("utf-8", "replace")


def symbols(path):
    """Yield `(name, bind, shndx)` for every named symbol in `.symtab`.

    An object with no `.symtab` raises rather than returning nothing: "no
    symbol table" and "no symbols" are the same empty answer otherwise, and
    telling them apart is the entire lesson of TM-115.
    """
    with open(path, "rb") as fh:
        blob = fh.read()
    shdrs = _sections(blob, path)
    found = False
    out = []
    for (_, sh_type, _, _, sh_offset, sh_size, sh_link, _, _,
         sh_entsize) in shdrs:
        if sh_type != SHT_SYMTAB:
            continue
        found = True
        if sh_entsize != _SYM.size:
            raise ElfError("%s: .symtab sh_entsize is %d, not %d"
                           % (path, sh_entsize, _SYM.size))
        if sh_link >= len(shdrs):
            raise ElfError("%s: .symtab sh_link is %d, out of range"
                           % (path, sh_link))
        strtab_off = shdrs[sh_link][4]
        for i in range(sh_size // sh_entsize):
            st_name, st_info, _, st_shndx, _, _ = _SYM.unpack_from(
                blob, sh_offset + i * sh_entsize)
            if st_name == 0:
                continue
            out.append((_cstr(blob, strtab_off, st_name),
                        st_info >> 4, st_shndx))
    if not found:
        raise ElfError("%s: no .symtab. A stripped object cannot be scanned, "
                       "and a scan that silently passed one would be the "
                       "green-while-checking-nothing failure B-8 exists for."
                       % path)
    return out


def undefined(path):
    """The set of symbols this object needs somebody else to define."""
    return {name for name, _bind, shndx in symbols(path) if shndx == SHN_UNDEF}


def defined_globals(path):
    """The set of symbols this object offers to the link.

    GLOBAL and WEAK only: a LOCAL symbol resolves nobody else's reference, so
    including one would make the allowlist excuse a link that then fails.
    """
    return {name for name, bind, shndx in symbols(path)
            if shndx != SHN_UNDEF and bind in (STB_GLOBAL, STB_WEAK)}


def runtime_allowlist(npkrt_path):
    """P-14, corrected by TM-118: derived from `$NPKRT`, never written.

    Two halves, and both are derived:

      what the runtime PROVIDES -- its global defined symbols, 111 at the pin.
      what the runtime REQUIRES of the program -- its own undefined symbols,
        which are exactly `main` and `npk_failsafe`. P-14 said "plus `main`",
        and `main` alone is not enough: `src/lib.npk`'s object legitimately
        references `@npk_failsafe`, because `npkc` emits the prelude's trap
        paths into every root and the handler is the PROGRAM's to supply. The
        first run of this scan failed the library build on it. Deriving the
        second half from `undefined(npkrt)` rather than writing `{"main",
        "npk_failsafe"}` means the pair cannot go stale either.

    A written list goes stale the first time the floor gains a symbol, and the
    floor gained two (`_start`, `npk_clone_raw`) between what the `.ll` shows
    and what the object provides.
    """
    return defined_globals(npkrt_path) | undefined(npkrt_path)


def scan(obj_path, allowlist):
    """The B-2 build step. Returns the sorted forbidden symbols; `[]` is a pass.

    The caller decides what a non-empty result means; in this harness it fails
    the BUILD (B-2), which is why the result is a list and not a printed line.
    """
    return sorted(undefined(obj_path) - allowlist)
