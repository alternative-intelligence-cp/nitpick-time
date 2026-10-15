#!/usr/bin/env python3
"""0.3.3 -- the sweep's positive control (the workbench `PLAYBOOK.md`, "a stale-claim sweep's patterns get a
positive control: the step's own hunks"): every hunk of steps 1 ... 4 read on its PARENT side -- its context and the
lines it removes, joined, comment markers, `*` and backticks stripped, as `sweep.py` joins a file -- and held to
`sweep_patterns.txt`, case-insensitive. A hunk no pattern matches is printed, with its file and first line, to be
named: the kind of sentence the sweep cannot see.

    python3 -B control.py <tools-dir>

A hunk of a file the patch creates has no parent side, and is counted apart.
"""
import os
import re
import sys

_MARK = re.compile(r"^\s*(?://+|#+|\*|>)?\s?")


def hunks(path):
    f, out, cur = None, [], None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("diff --git "):
            f, cur = None, None
        elif line.startswith("--- "):
            new_file = line == "--- /dev/null"
        elif line.startswith("+++ b/"):
            f = line[6:]
        elif line.startswith("@@ "):
            cur = {"file": f, "at": line, "parent": [], "new": new_file}
            out.append(cur)
        elif cur is not None and line[:1] in (" ", "-"):
            cur["parent"].append(line[1:])
    return out


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    t = argv[1]
    pats = [re.compile(l.rstrip("\n"), re.I) for l in open(os.path.join(t, "sweep_patterns.txt"), encoding="utf-8")
            if l.strip() and not l.startswith("#")]
    total = matched = created = 0
    misses = []
    for n in (1, 2, 3, 4):
        for h in hunks(os.path.join(t, "step%d.patch" % n)):
            if h["new"]:
                created += 1
                continue
            total += 1
            text = " ".join(_MARK.sub("", l).replace("*", "").replace("`", "") for l in h["parent"])
            if any(p.search(text) for p in pats):
                matched += 1
            else:
                misses.append("step%d %s %s" % (n, h["file"], h["at"].split("@@")[1].strip()))
    print("%d hunk(s) with a parent side: %d matched by a pattern, %d not; %d in files the patches create"
          % (total, matched, len(misses), created))
    for m in misses:
        print("  not matched: " + m)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
