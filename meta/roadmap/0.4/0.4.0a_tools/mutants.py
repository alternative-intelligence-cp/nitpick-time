#!/usr/bin/env python3
"""0.4.0a -- the named mutants of `mutants.tsv`: one change made in a copy of a tree -- a re-spelling undone, a view
held where the step ends it, a rule broken -- and the roots its row names compiled at BOTH pins, `npkc` alone, from
each root's directory, as the parse sweep does; and, where the row's last column says `legs`, each root that both
pins compile built and run at -O0 and through `opt -O2`, its exits printed, and with `heap` the runtime's own heap
line too. Each row says which compiler sees the change: one only the new pin refuses is a rule the new pin holds
and the old cannot; one both refuse, a rule both hold; one neither refuses is a change only a run can see, or none.

    python3 -B mutants.py <tree> <step>

<tree>'s tracked and untracked files (not the ignored) are copied to `$A/mut/<name>/` per row whose first column is
<step>; the row's text is replaced ONCE -- any other count is a STOP, printed, and nothing compiled -- and the copy
is removed at the end. TAB-separated; `\\n` in a text is a newline; the sixth column is the roots, space-separated,
and the seventh `-`, `legs` or `heap`. `$WB`, `$A`, `$PIN` and `$OLD` come from the environment (`env.sh`).
`0.3.2a_tools/vmut.py`, with the run added.
"""
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WB, A, PIN, OLD = os.environ["WB"], os.environ["A"], os.environ["PIN"], os.environ["OLD"]
D = re.compile(r"^(NITPICK-[A-Z]+-[0-9]+) (\S+):([0-9]+):([0-9]+):", re.M)
HEAP = re.compile(r"^heap: .*$", re.M)


def tc(pin, name):
    return os.path.join(WB, ".internal", "toolchain", pin, name)


def codes(pin, root):
    r = subprocess.run([tc(pin, "npkc"), os.path.basename(root), "-o", "/dev/null"], cwd=os.path.dirname(root),
                       capture_output=True, text=True, errors="replace")
    ds = D.findall(r.stdout + r.stderr)
    if not ds:
        return "compiles" if r.returncode == 0 else "exit %d" % r.returncode
    return " ".join("%s %s:%s:%s" % (c, os.path.basename(s), l, k) for c, s, l, k in ds)


def run_legs(pin, root, out, heap):
    """Both legs of `root` at `pin`: '<e0> / <e2>', and the heap lines when asked."""
    b = os.path.join(out, "%s.%s" % (pin, os.path.basename(root)[:-4]))
    d = os.path.dirname(root)
    if subprocess.run([tc(pin, "npkc"), os.path.basename(root), "-o", b + ".ll"], cwd=d,
                      capture_output=True).returncode:
        return "npkc refused"
    steps = [["llc", "-O0", "-filetype=obj", "-relocation-model=static", b + ".ll", "-o", b + ".o"],
             ["ld.lld", "-static", b + ".o", tc(pin, "npkrt.o"), "-o", b + ".x0"],
             ["opt", "-O2", "-S", b + ".ll", "-o", b + ".2.ll"],
             ["llc", "-O2", "-filetype=obj", "-relocation-model=static", b + ".2.ll", "-o", b + ".2.o"],
             ["ld.lld", "-static", b + ".2.o", tc(pin, "npkrt.o"), "-o", b + ".x2"]]
    for s in steps:
        if subprocess.run(s, capture_output=True).returncode:
            return "%s failed" % s[0]
    env = {"NTIME_HARNESS": "1"}
    if heap:
        env["NPK_HEAP_STATS"] = "1"
    res = []
    for x in (".x0", ".x2"):
        r = subprocess.run([b + x], cwd=d, env=env, capture_output=True, text=True, errors="replace")
        h = HEAP.findall(r.stderr) if heap else []
        res.append("%d%s" % (r.returncode, (" (" + h[0] + ")") if h else ""))
    return " / ".join(res)


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    tree, step = os.path.realpath(argv[1]), argv[2]
    rows = []
    for line in open(os.path.join(HERE, "mutants.tsv"), encoding="utf-8"):
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        st, name, path, old, new, roots, how = line.split("\t")
        if st == step:
            rows.append((name, path, old.replace("\\n", "\n"), new.replace("\\n", "\n"), roots.split(), how))
    files = subprocess.run(["git", "-C", tree, "ls-files", "-co", "--exclude-standard", "-z"],
                           capture_output=True, text=True).stdout.split("\0")
    for name, path, old, new, roots, how in rows:
        d = os.path.join(A, "mut", name)
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
        bins = os.path.join(d, ".internal", "mutbin")
        os.makedirs(bins, exist_ok=True)
        for r in roots:
            line = "%s: %s at %s: %s; at %s: %s" % (name, os.path.basename(r), OLD, codes(OLD, os.path.join(d, r)),
                                                    PIN, codes(PIN, os.path.join(d, r)))
            if how in ("legs", "heap"):
                line += " -- run: %s" % "; ".join("%s %s" % (pin, run_legs(pin, os.path.join(d, r), bins, how == "heap"))
                                                 for pin in (OLD, PIN))
            print(line)
        shutil.rmtree(d, ignore_errors=True)
    shutil.rmtree(os.path.join(A, "mut"), ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
