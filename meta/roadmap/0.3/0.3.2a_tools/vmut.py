#!/usr/bin/env python3
"""0.3.2a -- the view mutants of `vmutants.tsv`: one rule of the read-only view broken, in a copy of a tree, and the
roots its row names compiled at BOTH pins -- `npkc` alone, from each root's directory, as the parse sweep does. Each
row says which compiler sees the change: a mutant only the new pin refuses is a rule the new pin holds and the old
cannot -- a write through a `fixed` slice (the compiler's DEF-230) and a `fixed` parameter reassigned (DEF-248) --
and one both refuse is a rule both hold. A re-spelling undone is `slots.py`'s, every one.

    python3 -B vmut.py <tree> <step>

<tree>'s tracked and untracked files (not the ignored) are copied to `$A/vmut/<name>/` per row whose first column is
<step>; the row's text is replaced ONCE -- any other count is a STOP, printed, and nothing compiled -- and the copy is
removed at the end. TAB-separated; `\\n` in a text is a newline; the last column is the roots, space-separated.
`$WB`, `$A`, `$PIN` and `$OLD` come from the environment (`env.sh`). `nitpick-regex`'s `0.2.1a_tools/vmut.py`.
"""
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WB, A, PIN, OLD = os.environ["WB"], os.environ["A"], os.environ["PIN"], os.environ["OLD"]
D = re.compile(r"^(NITPICK-[A-Z]+-[0-9]+) (\S+):([0-9]+):([0-9]+):", re.M)


def codes(pin, root):
    npkc = os.path.join(WB, ".internal", "toolchain", pin, "npkc")
    r = subprocess.run([npkc, os.path.basename(root), "-o", "/dev/null"], cwd=os.path.dirname(root),
                       capture_output=True, text=True, errors="replace")
    ds = D.findall(r.stdout + r.stderr)
    if not ds:
        return "compiles" if r.returncode == 0 else "exit %d" % r.returncode
    return " ".join("%s %s:%s:%s" % (c, os.path.basename(s), l, k) for c, s, l, k in ds)


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    tree, step = os.path.realpath(argv[1]), argv[2]
    rows = []
    for line in open(os.path.join(HERE, "vmutants.tsv"), encoding="utf-8"):
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        st, name, path, old, new, roots = line.split("\t")
        if st == step:
            rows.append((name, path, old.replace("\\n", "\n"), new.replace("\\n", "\n"), roots.split()))
    files = subprocess.run(["git", "-C", tree, "ls-files", "-co", "--exclude-standard", "-z"],
                           capture_output=True, text=True).stdout.split("\0")
    for name, path, old, new, roots in rows:
        d = os.path.join(A, "vmut", name)
        shutil.rmtree(d, ignore_errors=True)
        for f in files:
            if f:
                os.makedirs(os.path.dirname(os.path.join(d, f)) or d, exist_ok=True)
                shutil.copy2(os.path.join(tree, f), os.path.join(d, f))
        p = os.path.join(d, path)
        s = open(p, encoding="utf-8").read()
        if s.count(old) != 1:
            print("%s: STOP: %d occurrence(s) of %r in %s" % (name, s.count(old), old[:60], path))
            shutil.rmtree(d, ignore_errors=True)
            continue
        open(p, "w", encoding="utf-8").write(s.replace(old, new))
        for r in roots:
            print("%s: %s at %s: %s; at %s: %s" % (name, os.path.basename(r), OLD, codes(OLD, os.path.join(d, r)),
                                                  PIN, codes(PIN, os.path.join(d, r))))
        shutil.rmtree(d, ignore_errors=True)
    shutil.rmtree(os.path.join(A, "vmut"), ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
