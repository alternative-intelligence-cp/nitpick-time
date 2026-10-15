#!/usr/bin/env python3
"""0.3.2a -- every tracked `.npk` of a tree compiled as a ROOT by a pin's `npkc`, from its own directory, as the
harness's parse sweep compiles it: what each reports, by code and site (`nitpick-regex`'s `0.2.1a_tools/census.py`).
Three verbs:

    python3 -B census.py run <pin> <tree> <out.tsv>        # compile, write, and print the summary
    python3 -B census.py compare <a.tsv> <b.tsv> [CODE...] # each file's codes and sites, a against b, CODEs left out of b
    python3 -B census.py sites <tsv> <CODE>                # a code's DISTINCT sites -- one per place, not per root

A site is `<path>:<line>:<col>` as `npkc` prints it, the path from the manifest's directory (the compiler's D-236), so
a site in `src/` reached from forty roots is forty lines of the TSV and ONE distinct site. The compiler side's lists
count per root; `sites` counts the places a re-spelling touches. `$WB` names the workbench whose toolchain directory
holds the pin (`env.sh` exports it). Nothing here writes into <tree>. A note's line -- `note NITPICK-...` -- is
the compiler's explanation and not a site, and is not read (B-7c).
"""
import collections
import os
import re
import subprocess
import sys

D = re.compile(r"^(NITPICK-[A-Z]+-[0-9]+) (\S+):([0-9]+):([0-9]+):", re.M)


def npk_files(tree):
    """The tree's tracked `.npk` files -- or, for a copy that is no work tree, every `.npk` in it."""
    r = subprocess.run(["git", "-C", tree, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if r.returncode == 0 and os.path.realpath(r.stdout.strip()) == os.path.realpath(tree):
        return subprocess.run(["git", "-C", tree, "ls-files", "*.npk"], capture_output=True, text=True).stdout.split()
    out = []
    for d, dirs, names in os.walk(tree):
        dirs[:] = sorted(x for x in dirs if x not in (".git", ".internal"))
        out += [os.path.relpath(os.path.join(d, n), tree) for n in names if n.endswith(".npk")]
    return sorted(out)


def run(pin, tree, out):
    npkc = os.path.join(os.environ["WB"], ".internal", "toolchain", pin, "npkc")
    fs = npk_files(tree)
    rows = []
    for f in fs:
        p = os.path.join(tree, f)
        r = subprocess.run([npkc, os.path.basename(p), "-o", "/dev/null"], cwd=os.path.dirname(p),
                           capture_output=True, text=True, errors="replace")
        ds = D.findall(r.stdout + r.stderr)
        rows += [(f, r.returncode, c, "%s:%s:%s" % (s, l, k)) for c, s, l, k in ds] or [(f, r.returncode, "-", "-")]
    with open(out, "w") as fh:
        for row in rows:
            fh.write("%s\t%d\t%s\t%s\n" % row)
    refused = sorted({f for f, e, c, s in rows if e != 0})
    codes = collections.Counter(c for f, e, c, s in rows if c != "-")
    print("%d file(s) at %s: %d compile, %d refused" % (len(fs), pin, len(fs) - len(refused), len(refused)))
    print("  reported, per root: " + (", ".join("%s x%d" % kv for kv in sorted(codes.items())) or "nothing"))


def load(p):
    d = collections.defaultdict(list)
    for line in open(p):
        f, e, c, s = line.rstrip("\n").split("\t")
        d[f].append((int(e), c, s))
    return d


def compare(a, b, leave):
    A, B = load(a), load(b)
    same, diff = 0, []
    for f in sorted(set(A) | set(B)):
        x = sorted((c, s) for e, c, s in A.get(f, []) if c != "-")
        y = sorted((c, s) for e, c, s in B.get(f, []) if c != "-" and c not in leave)
        hidden = any(c in leave for e, c, s in B.get(f, []))
        if x == y:
            same += 1
        else:
            diff.append((f, x, y, hidden))
    print("%d file(s) report the same codes at the same sites%s; %d differ"
          % (same, " (%s left out of the second)" % ", ".join(leave) if leave else "", len(diff)))
    for f, x, y, hidden in diff:
        print("  %s" % f)
        print("    first:  %s" % (" ".join("%s %s" % cs for cs in x) or "compiles"))
        print("    second: %s" % (" ".join("%s %s" % cs for cs in y)
                                  or ("nothing but what is left out" if hidden else "compiles")))


def sites(p, code):
    rows = [(f, s) for f, v in load(p).items() for e, c, s in v if c == code]
    roots = {f for f, s in rows}
    distinct = sorted({s for f, s in rows})
    files = collections.Counter(s.rsplit(":", 2)[0] for s in distinct)
    print("%s: %d root(s), %d per root, %d distinct site(s) in %d file(s)"
          % (code, len(roots), len(rows), len(distinct), len(files)))
    src = sorted(f for f in files if f.startswith("src/"))
    print("  in src/: %d site(s) in %d file(s) -- %s" % (sum(files[f] for f in src), len(src),
          ", ".join(s for s in distinct if s.startswith("src/"))))
    print("  roots in src/: %d, per root %d" % (len({f for f in roots if f.startswith("src/")}),
                                               sum(1 for f, s in rows if f.startswith("src/"))))


def main(argv):
    if len(argv) >= 5 and argv[1] == "run":
        run(argv[2], argv[3], argv[4])
    elif len(argv) >= 4 and argv[1] == "compare":
        compare(argv[2], argv[3], argv[4:])
    elif len(argv) == 4 and argv[1] == "sites":
        sites(argv[2], argv[3])
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
