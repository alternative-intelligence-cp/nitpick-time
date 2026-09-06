#!/usr/bin/env python3
"""Which functions in an emitted `.ll` reach the allocator DIRECTLY.

WHY THIS EXISTS. `0.0.4.md` §6 requires `put_uint` to be allocation-free
"verified by READING THE EMITTED IR for a call to the allocator" -- and reading
it by eye once, in a session nobody can replay, is the shape this repository
keeps finding wrong. This makes the reading a command with an exit status.

IT IS NOT A HARNESS CHECK YET, and that is deliberate: a check belongs in
`harness/checks.py` with a planted-violation case in `selfcheck.py` proving it
can fail, and inventing one at the end of a subcycle is how an instrument
arrives untested on the day it is needed (0.0.2's own finding). This is a tool
the record cites and a later cycle promotes.

    $ python3 tools/ir_alloc_scan.py <file.ll> [name-substring ...]

Exit 0 and print one line per matching function. With substrings given, exit 1
if any named function calls an allocator directly -- so it can be asserted.
"""
import re
import sys

# The runtime's allocator entry points, read off a linked `.ll`'s own
# `declare` lines rather than guessed: npk_alloc and its family, plus malloc.
ALLOC = ("npk_alloc", "npk_aalloc", "npk_calloc", "npk_ralloc",
         "npk_alloc_managed", "npk_wildx_alloc", "npk_arena_alloc",
         "npk_buffer_new", "malloc")


def bodies(path):
    out, cur, buf = {}, None, []
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.rstrip("\n")
        m = re.match(r'define [^@]*@"?([A-Za-z0-9_.<>:$ ]+)"?\(', line)
        if m:
            cur, buf = m.group(1), []
            continue
        if cur is None:
            continue
        if line == "}":
            out[cur] = "\n".join(buf)
            cur = None
        else:
            buf.append(line)
    return out


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    fns = bodies(argv[1])
    wanted = argv[2:]
    # THE DENOMINATOR IS PRINTED. A scan that matched nothing and a scan that
    # found nothing print the same line otherwise, which is TM-115's rule.
    print("%d function bodies in %s" % (len(fns), argv[1]))
    bad = 0
    shown = 0
    for name in sorted(fns):
        if wanted and not any(w in name for w in wanted):
            continue
        shown += 1
        body = fns[name]
        hits = sorted({a for a in ALLOC if ('@' + a) in body})
        calls = sorted({c for c in re.findall(
            r'call [^@]*@"?([A-Za-z0-9_.<>:$]+)"?\(', body)})
        print("  %-44s allocator=%-28s calls=%d"
              % (name, ",".join(hits) or "NONE", len(calls)))
        if hits and wanted:
            bad += 1
    if wanted and shown == 0:
        print("NO FUNCTION MATCHED %r -- an empty denominator is not a pass"
              % (wanted,))
        return 2
    if bad:
        print("FAIL: %d named function(s) call an allocator directly" % bad)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
