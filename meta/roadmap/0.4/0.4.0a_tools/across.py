#!/usr/bin/env python3
"""0.4.0a -- emissions compared through the compiler's own normalisers, read at a named commit of the compiler with
`git show` and never run from its tree: `attrnorm.py` (landing 115's `null_pointer_is_valid` on every define),
`sitenorm.py` (landing 126's site table, and any edit that moves a site's line), `dropnorm.py` (landing 105's drop
flag tests) and `tidnorm.py` (a type id). ONE tree at two pins, or two trees at one pin -- never both at once (the
workbench `PLAYBOOK.md` §12: "Compare emissions across pins over ONE tree").

    python3 -B across.py <tree-a> <pin-a> <tree-b> <pin-b> <tools-commit> <scratch-dir>

Each `.npk` of <tree-a> is compiled as a root from its own directory by <pin-a>'s `npkc`, and the same path of
<tree-b> by <pin-b>'s; a file either side refuses is counted and not compared. Each pair is classed by the FIRST
normalisation after which the two texts are equal, applied cumulatively in this order: `identical`; `attr`
(attrnorm's strip); `attr+site` (and sitenorm's canon, its `--site-path-cap` mask on, the two sides' preludes mapped
line to line); `attr+site+drop` (and dropnorm's strip and renumbering); `attr+site+drop+tid` (and tidnorm's
renumbering); or `RESIDUE`, whose first differing lines are printed. A class past `attr+site` names its files.
`$WB` names the workbench (`env.sh`); `$NPK_TREE` the compiler's tree, read with `git show` only.
"""
import collections
import difflib
import importlib.util
import os
import re
import subprocess
import sys


def load_tools(npk_tree, commit, scratch):
    d = os.path.join(scratch, "normalisers")
    os.makedirs(d, exist_ok=True)
    out = {}
    for name in ("attrnorm", "sitenorm", "dropnorm", "tidnorm"):
        src = subprocess.run(["git", "-C", npk_tree, "show", "%s:meta/roadmap/1.6/tools/%s.py" % (commit, name)],
                             capture_output=True, text=True, check=True).stdout
        path = os.path.join(d, name + ".py")
        open(path, "w", encoding="utf-8").write(src)
        out[name] = (path, src)
    # attrnorm and tidnorm run their comparison at the top level and have no `__main__` guard: take each one's
    # pattern and `norm` by executing the module's text up to its argument parsing, which follows them.
    ns = {}
    for name in ("attrnorm", "tidnorm"):
        text = out[name][1]
        head = text[:text.index("args = sys.argv[1:]")]
        g = {"__name__": name}
        exec(compile(head, out[name][0], "exec"), g)
        ns[name] = g["norm"]
    mods = {}
    for name in ("sitenorm", "dropnorm"):
        spec = importlib.util.spec_from_file_location(name, out[name][0])
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        mods[name] = m
    return ns["attrnorm"], ns["tidnorm"], mods["sitenorm"], mods["dropnorm"]


def npk_files(tree):
    r = subprocess.run(["git", "-C", tree, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if r.returncode == 0 and os.path.realpath(r.stdout.strip()) == os.path.realpath(tree):
        return subprocess.run(["git", "-C", tree, "ls-files", "*.npk"], capture_output=True, text=True).stdout.split()
    out = []
    for d, dirs, names in os.walk(tree):
        dirs[:] = sorted(x for x in dirs if x not in (".git", ".internal", "build"))
        out += [os.path.relpath(os.path.join(d, n), tree) for n in names if n.endswith(".npk")]
    return sorted(out)


IDENT = re.compile(r"<([^:<>]+):(\d+)>")


def strip_map(a, b):
    """Line a -> line b for the lines difflib pairs as equal once each is stripped of its leading and trailing
    whitespace -- a block's lines, re-indented, are the same lines -- and a changed line maps to nothing."""
    la = [l.strip() for l in a.split("\n")]
    lb = [l.strip() for l in b.split("\n")]
    m = {}
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, la, lb, autojunk=False).get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                m[i1 + k + 1] = j1 + k + 1
    return m


def remap(m, srcmaps):
    """A site identity `<path:line>` of side a, read through the line map of a source the two trees hold apart."""
    path, line = m.group(1), int(m.group(2))
    for rel, mp in srcmaps.items():
        if rel == path or rel.endswith("/" + path) or path.endswith(rel):
            n = mp.get(line)
            return "<%s:%s>" % (path, n if n is not None else "changed-line-%d" % line)
    return m.group(0)


def emit(npkc, tree, rel, out):
    p = os.path.join(tree, rel)
    r = subprocess.run([npkc, os.path.basename(p), "-o", out], cwd=os.path.dirname(p),
                       capture_output=True, text=True, errors="replace")
    return r.returncode == 0 and os.path.exists(out)


def main(argv):
    if len(argv) != 7:
        print(__doc__)
        return 2
    tree_a, old, tree_b, new = os.path.realpath(argv[1]), argv[2], os.path.realpath(argv[3]), argv[4]
    commit, scratch = argv[5], os.path.realpath(argv[6])
    wb, npk_tree = os.environ["WB"], os.environ["NPK_TREE"]
    attr, tid, site, drop = load_tools(npk_tree, commit, scratch)
    preludes = {}
    for pin in (old, new):
        preludes[pin] = subprocess.run(["git", "-C", npk_tree, "show", "%s:src/prelude/prelude.npk" % pin],
                                       capture_output=True, text=True, check=True).stdout
    pmap = site.line_map(preludes[old], preludes[new])
    # TWO TREES: a site's identity is its source path and line, so a line an edit moves in a source both trees hold
    # moves every site below it. Each source that differs between the trees is mapped line to line, as sitenorm maps
    # the prelude, and side a's identities are read through that map; a line the edit changed maps to nothing.
    srcmaps = {}
    if tree_a != tree_b:
        for rel in npk_files(tree_a):
            pa, pb = os.path.join(tree_a, rel), os.path.join(tree_b, rel)
            if os.path.exists(pb):
                ta, tb = open(pa, errors="replace").read(), open(pb, errors="replace").read()
                if ta != tb:
                    srcmaps[rel] = strip_map(ta, tb)
    em = os.path.join(scratch, "emissions")
    os.makedirs(em, exist_ok=True)
    classes = collections.Counter()
    refused = {"a": [], "b": []}
    residue = []
    files = npk_files(tree_a)
    named = collections.defaultdict(list)
    for rel in files:
        key = rel.replace("/", "__")
        paths = {}
        for side, tree, pin in (("a", tree_a, old), ("b", tree_b, new)):
            o = os.path.join(em, "%s.%s.ll" % (key, side))
            if os.path.exists(o):
                os.remove(o)
            if emit(os.path.join(wb, ".internal", "toolchain", pin, "npkc"), tree, rel, o):
                paths[side] = o
            else:
                refused[side].append(rel)
        if len(paths) != 2:
            continue
        a, b = open(paths["a"], errors="replace").read(), open(paths["b"], errors="replace").read()
        if a == b:
            classes["identical"] += 1
            continue
        a, b = attr(a), attr(b)
        if a == b:
            classes["attr"] += 1
            continue
        ca, _na = site.canon(a, pmap, True, True)
        cb, _nb = site.canon(b, pmap, False, True)
        if srcmaps:
            ca = [IDENT.sub(lambda m: remap(m, srcmaps), l) for l in ca]
        if ca == cb:
            classes["attr+site"] += 1
            continue
        sa, _ta = drop.strip("\n".join(ca))
        sb, _tb = drop.strip("\n".join(cb))
        da, db = drop.canon("\n".join(sa)), drop.canon("\n".join(sb))
        if da == db:
            classes["attr+site+drop"] += 1
            named["attr+site+drop"].append(rel)
            continue
        ta, tb = tid("\n".join(da)).split("\n"), tid("\n".join(db)).split("\n")
        if ta == tb:
            classes["attr+site+drop+tid"] += 1
            named["attr+site+drop+tid"].append(rel)
            continue
        classes["RESIDUE"] += 1
        dl = [l for l in difflib.unified_diff(ta, tb, lineterm="", n=0) if l[:1] in "+-" and not l.startswith(("+++", "---"))]
        residue.append((rel, dl))
    both = sum(classes.values())
    print("%d .npk: %d compiled on both sides; refused on side a (%s at %s) alone %d, on side b (%s at %s) alone %d,"
          " on both %d" % (len(files), both, os.path.basename(tree_a), old, len(set(refused["a"]) - set(refused["b"])),
                           os.path.basename(tree_b), new, len(set(refused["b"]) - set(refused["a"])),
                           len(set(refused["a"]) & set(refused["b"]))))
    for r in sorted(set(refused["b"]) - set(refused["a"])):
        print("  refused on side b alone: %s" % r)
    for r in sorted(set(refused["a"]) - set(refused["b"])):
        print("  refused on side a alone: %s" % r)
    for k in ("identical", "attr", "attr+site", "attr+site+drop", "attr+site+drop+tid", "RESIDUE"):
        print("  %-20s %d%s" % (k, classes[k], (" -- " + " ".join(named[k])) if named.get(k) else ""))
    for rel, dl in residue:
        print("  RESIDUE %s: %d differing line(s)" % (rel, len(dl)))
        for l in dl[:6]:
            print("      " + l[:160])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
