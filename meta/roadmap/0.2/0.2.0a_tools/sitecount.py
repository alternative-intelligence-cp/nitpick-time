#!/usr/bin/env python3
"""0.2.0a -- the compiler's D-332 over this tree, before our runner holds it: for every
tracked `.npk` whose header carries `expect-error`, compile it with each named kept
compiler and compare, per code, the number of reported SITES with the number of
`expect-error` lines naming it.

    python3 -B sitecount.py "$REPO" <pin> [<pin> ...]

Reads through the harness's own reader and diagnostic pattern (`harness/stages.py`'s
`read` and `_DIAG`), so it counts what the runner will count. Prints the denominator,
then one line per file whose count differs at any pin -- a file that agrees
everywhere is in the total. `nitpick-regex`'s `0.1.0b_tools/sitecount.py`, ported.
"""
import collections
import os
import subprocess
import sys


def main(argv):
    root, pins = os.path.realpath(argv[1]), argv[2:]
    wb = os.path.dirname(root)
    sys.path.insert(0, os.path.join(root, "harness"))
    import stages
    files = subprocess.run(["git", "-C", root, "grep", "-l", "-E", r"^// expect-error:",
                            "--", "*.npk"], capture_output=True, text=True).stdout.split()
    differ = []
    for rel in sorted(files):
        e = stages.read(root, rel)
        named = collections.Counter(e.errors)
        p = os.path.join(root, rel)
        for pin in pins:
            cc = os.path.join(wb, ".internal", "toolchain", pin, "npkc")
            r = subprocess.run([cc, os.path.basename(p), "-o", "/dev/null"],
                               cwd=os.path.dirname(p), capture_output=True, text=True)
            sites = {}
            for line in (r.stdout + r.stderr).splitlines():
                m = stages._DIAG.match(line)
                if m:
                    sites.setdefault(m.group(1), []).append(f"{m.group(3)}:{m.group(4)}")
            for code in sorted(named):
                got = sites.get(code, [])
                if got and len(got) != named[code]:
                    differ.append(f"{rel} at {pin}: {code} named x{named[code]}, reported "
                                  f"x{len(got)} at {' '.join(got)}")
    print(f"{len(files)} file(s) carry `expect-error`; {len(differ)} count(s) differ")
    for d in differ:
        print("    " + d)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
