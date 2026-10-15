#!/usr/bin/env python3
"""0.3.2a, a planning measurement no block runs -- the MINIMAL re-spelling, found by the compiler: from a tree, compile
every `.npk` as a root at a pin; for each `NITPICK-TYPE-007` "expected `uint8[]`, found `fixed uint8[]`" site, re-spell
the ONE slot the site names -- a local `uint8[]:x = ...` on that line, else the parameter of the function called at
that column, else a field of the struct a literal at that column builds -- and repeat until no such site is left.
`nitpick-regex`'s `0.2.1a_tools/minfix.py`, run here unchanged.

    git clone -q --shared --branch main "$REPO" "$A/minfix" && python3 -B minfix.py "$A/minfix" "$WB/.internal/toolchain/7e91730/npkc"

IT WRITES THE TREE IT IS GIVEN -- a throwaway clone, never the checkout. It prints each round's count of sites and,
at the end, every slot it re-spelled. At planning, over the unchanged tree: three rounds -- 32 sites, then 14, then
6 -- and 32 slots re-spelled; the six sites left are five `pass string_bytes(...)` out of a function whose result is
a plain `uint8[]`, which no slot holds, and `view_escape/case4`'s field, a struct on one line, which this tool's field
reader does not parse. With those six and the six slots their re-spelling then requires, the set is step 1's 39 and
step 2's five (`0.3.2a.md` §1.5), and `slots.py` holds each one to its `NITPICK-TYPE-007`. About two minutes.
"""
import os, re, subprocess, sys

tree, npkc = sys.argv[1], sys.argv[2]
D = re.compile(r"^NITPICK-TYPE-007 (\S+):([0-9]+):([0-9]+): expected `uint8\[\]`, found `fixed uint8\[\]`", re.M)
fs = subprocess.run(["git", "-C", tree, "ls-files", "*.npk"], capture_output=True, text=True).stdout.split()
fixed = []


def sites():
    out = set()
    for f in fs:
        p = os.path.join(tree, f)
        r = subprocess.run([npkc, os.path.basename(p), "-o", "/dev/null"], cwd=os.path.dirname(p),
                           capture_output=True, text=True, errors="replace")
        for path, l, c in D.findall(r.stdout + r.stderr):
            out.add((path, int(l), int(c)))
    return out


def lines(path):
    return open(os.path.join(tree, path), encoding="utf-8").read().split("\n")


def save(path, ls):
    open(os.path.join(tree, path), "w", encoding="utf-8").write("\n".join(ls))


def fix_line(path, ln):
    ls = lines(path)
    new = re.sub(r"(?<!fixed )\buint8\[\]:", "fixed uint8[]:", ls[ln - 1], count=1)
    if new == ls[ln - 1]:
        return False
    ls[ln - 1] = new
    save(path, ls)
    fixed.append("%s:%d local" % (path, ln))
    return True


def fix_param(name, argi, where):
    for f in fs:
        ls = lines(f)
        for i, l in enumerate(ls):
            m = re.match(r"^\s*(?:pub\s+)?(?:async\s+)?func:%s\s*=\s*[^(]*\((.*)\)\s*(never fails)?\s*\{" % re.escape(name), l)
            if not m:
                continue
            params = [p.strip() for p in m.group(1).split(",")]
            if argi < len(params) and re.match(r"^uint8\[\]:", params[argi]):
                params[argi] = "fixed " + params[argi]
                s, e = m.span(1)
                ls[i] = l[:s] + ", ".join(params) + l[e:]
                save(f, ls)
                fixed.append("%s:%d parameter %d of %s (called at %s)" % (f, i + 1, argi, name, where))
                return True
    return False


def fix_field(path, ln, col):
    sm = re.match(r"([A-Z][A-Za-z0-9_]*)\s*\{", lines(path)[ln - 1][col - 1:])
    if not sm:
        return False
    for f in fs:
        ls = lines(f)
        for i, x in enumerate(ls):
            if re.match(r"^\s*(pub\s+)?struct:%s\s*=" % re.escape(sm.group(1)), x):
                j = i + 1
                while j < len(ls) and not ls[j].strip().startswith("}"):
                    if re.match(r"^\s*(sealed |hidden )?uint8\[\]:", ls[j]):
                        ls[j] = re.sub(r"(?<!fixed )\buint8\[\]:", "fixed uint8[]:", ls[j], count=1)
                        save(f, ls)
                        fixed.append("%s:%d field of %s" % (f, j + 1, sm.group(1)))
                        return True
                    j += 1
    return False


def callee(l, col):
    depth, i, argi = 0, col - 2, 0
    while i >= 0:
        ch = l[i]
        if ch == ")":
            depth += 1
        elif ch == "(":
            if depth == 0:
                m = re.search(r"([A-Za-z_][A-Za-z0-9_]*)\s*$", l[:i])
                return (m.group(1) if m else None), argi
            depth -= 1
        elif ch == "," and depth == 0:
            argi += 1
        i -= 1
    return None, 0


rnd = 0
while True:
    rnd += 1
    ss = sorted(sites())
    print("round %d: %d site(s)" % (rnd, len(ss)))
    if not ss or rnd > 30:
        break
    progress = False
    for path, ln, col in ss:
        l = lines(path)[ln - 1]
        if re.match(r"^\s*uint8\[\]:\w+\s*=", l):
            progress |= fix_line(path, ln)
            continue
        name, argi = callee(l, col)
        if name and fix_param(name, argi, "%s:%d" % (path, ln)):
            progress = True
            continue
        if fix_field(path, ln, col):
            progress = True
            continue
        print("  no slot at %s:%d:%d (this round, or none at all): %s" % (path, ln, col, l.strip()[:100]))
    if not progress:
        break
print("re-spelled %d slot(s)" % len(fixed))
for x in fixed:
    print("  " + x)
