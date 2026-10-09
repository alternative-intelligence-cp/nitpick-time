#!/usr/bin/env python3
"""0.3.2a -- the runner's own judge of every refusal, at each named pin: for every tracked `.npk` whose header names
a code (`expect-error:`), read through <tree>'s OWN `harness/stages.py` and judged by its `refusal` -- B-7's sets,
D-332's count per code (B-7c, TM-210) and every `expect-error-at` -- with that pin's `npkc`. The judge runs `npkc`
alone, so no LLVM is involved.

    python3 -B refusals.py <tree> <pin> [<pin> ...]

Prints the denominator, then one line per file the judge fails at a pin -- the first line of each problem -- and
nothing for a file that passes. `$WB` names the workbench whose toolchain directory holds the pins (`env.sh`).
The port of `0.2.0a_tools/sitecount.py`, which counted D-332 alone: this asks the runner's whole question, so a
code named and not reported -- `probe02d`'s `NITPICK-PARSE-002` at `7e91730` -- is seen too.
"""
import os
import shutil
import subprocess
import sys
import tempfile


def files(tree):
    r = subprocess.run(["git", "-C", tree, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if r.returncode == 0 and os.path.realpath(r.stdout.strip()) == os.path.realpath(tree):
        out = subprocess.run(["git", "-C", tree, "grep", "-l", "-E", r"^// expect-error:", "--", "*.npk"],
                             capture_output=True, text=True).stdout.split()
        return sorted(out)
    out = []
    for d, dirs, names in os.walk(tree):
        dirs[:] = sorted(x for x in dirs if x not in (".git", ".internal", "build"))
        for n in names:
            if n.endswith(".npk"):
                p = os.path.join(d, n)
                with open(p, "rb") as fh:
                    if any(l.startswith(b"// expect-error:") for l in fh.read().split(b"\n")[:12]):
                        out.append(os.path.relpath(p, tree))
    return sorted(out)


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    tree, pins = os.path.realpath(argv[1]), argv[2:]
    sys.path.insert(0, os.path.join(tree, "harness"))
    import build
    import manifest
    import stages
    man = manifest.load(tree)
    fs = files(tree)
    print("%d file(s) name a code in `expect-error`" % len(fs))
    for pin in pins:
        tc = os.path.join(os.environ["WB"], ".internal", "toolchain", pin)
        out = tempfile.mkdtemp(prefix="refusals.", dir=os.environ.get("A"))
        bld = build.Build(tree, man, os.path.join(tc, "npkc"), os.path.join(tc, "npkrt.o"), out)
        bad = []
        for rel in fs:
            e = stages.read(tree, rel)
            if not e.is_refusal:
                continue
            probs = stages.refusal(bld, rel, e)
            if probs:
                bad.append("  %s at %s: %s" % (rel, pin, probs[0].split("\n")[0][:110]))
        shutil.rmtree(out, ignore_errors=True)
        print("at %s: %d pass, %d fail" % (pin, len(fs) - len(bad), len(bad)))
        for b in bad:
            print(b)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
