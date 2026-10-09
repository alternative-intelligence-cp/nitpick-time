#!/usr/bin/env python3
"""0.3.2a -- EVERY slot this subcycle re-spells, undone ALONE, in a copy, and its file compiled as a root at both
pins: the claim that the pin requires each one, checked by enumerating the set rather than by sampling it.

    python3 -B slots.py <tree> <step>

A slot is one `fixed uint8[]` on a code line of a tracked `.npk` under `src/` or `tests/` -- the unchanged tree
holds none, so every one is this subcycle's. Step 1's are the parameters, locals and fields; step 2's are the five
return types (`= fixed uint8[](`), DEF-247's position, written after the pin moves. For each, the one occurrence
goes back to `uint8[]` in a copy of <tree> made once at `$A/slots/`, the file is compiled from its own directory by
each pin's `npkc` -- as the parse sweep roots it -- and put back; the copy is removed at the end. A line per slot,
`<file>:<line> <name>: at <old> ...; at <new> ...`, each diagnostic as `CODE L:C`, then the totals. Nothing here
writes into <tree>. `$WB`, `$A`, `$PIN` and `$OLD` come from `env.sh`.
"""
import os
import re
import shutil
import subprocess
import sys

WB, A, PIN, OLD = os.environ["WB"], os.environ["A"], os.environ["PIN"], os.environ["OLD"]
D = re.compile(r"^(NITPICK-[A-Z]+-[0-9]+) (\S+):([0-9]+):([0-9]+):", re.M)
SLOT = re.compile(r"fixed uint8\[\]")


def codes(pin, path):
    npkc = os.path.join(WB, ".internal", "toolchain", pin, "npkc")
    r = subprocess.run([npkc, os.path.basename(path), "-o", "/dev/null"], cwd=os.path.dirname(path),
                       capture_output=True, text=True, errors="replace")
    ds = D.findall(r.stdout + r.stderr)
    if not ds:
        return "compiles" if r.returncode == 0 else "exit %d" % r.returncode
    base = os.path.basename(path)
    return " ".join("%s %s%s:%s" % (c.replace("NITPICK-", ""), "" if os.path.basename(s) == base
                                    else os.path.basename(s) + ":", l, k) for c, s, l, k in ds)


def code_part(line):
    return "" if line.lstrip().startswith("//") else line.split("//", 1)[0]


def main(argv):
    if len(argv) != 3 or argv[2] not in ("1", "2"):
        print(__doc__)
        return 2
    tree, step = os.path.realpath(argv[1]), argv[2]
    fs = subprocess.run(["git", "-C", tree, "ls-files", "-co", "--exclude-standard", "-z"],
                        capture_output=True, text=True).stdout.split("\0")
    d = os.path.join(A, "slots")
    shutil.rmtree(d, ignore_errors=True)
    for f in fs:
        if f:
            os.makedirs(os.path.dirname(os.path.join(d, f)) or d, exist_ok=True)
            shutil.copy2(os.path.join(tree, f), os.path.join(d, f))
    seen = refused_new = 0
    for f in sorted(x for x in fs if x.endswith(".npk") and x.split("/")[0] in ("src", "tests")):
        p = os.path.join(d, f)
        with open(p, encoding="utf-8", newline="") as fh:
            lines = fh.read().split("\n")
        for i, line in enumerate(lines):
            code = code_part(line)
            for m in SLOT.finditer(code):
                is_ret = code[:m.start()].rstrip().endswith("=") and code[m.end():].startswith("(")
                if is_ret != (step == "2"):
                    continue
                seen += 1
                name = re.search(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=\s*$", code[:m.start()]) if is_ret else \
                    re.match(r":([A-Za-z_][A-Za-z0-9_]*)", code[m.end():])
                what = ("%s's return" % name.group(1)) if is_ret else (name.group(1) if name else "?")
                undone = list(lines)
                undone[i] = line[:m.start()] + "uint8[]" + line[m.end():]
                with open(p, "w", encoding="utf-8", newline="") as fh:
                    fh.write("\n".join(undone))
                old, new = codes(OLD, p), codes(PIN, p)
                if "TYPE-007" in new:
                    refused_new += 1
                print("%s:%d %s: at %s %s; at %s %s" % (f, i + 1, what, OLD, old, PIN, new))
                with open(p, "w", encoding="utf-8", newline="") as fh:
                    fh.write("\n".join(lines))
    shutil.rmtree(d, ignore_errors=True)
    print("%d slot(s) undone one at a time; %d of them NITPICK-TYPE-007 at %s" % (seen, refused_new, PIN))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
