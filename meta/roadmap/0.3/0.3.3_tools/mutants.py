#!/usr/bin/env python3
"""0.3.3 -- the double's mutants against its three tests (the plan's §1.9).

    python3 -B mutants.py all   <REPO> <WORK> [-j N]   # every single-site mutant, `mutate.py`'s
    python3 -B mutants.py table <REPO> <WORK> [-j N]   # `named.tsv`'s rows, each aimed at an exit

Every mutant `mutate.py` generates from `<REPO>/tests/double/host_double.npk`
is built in a copy under <WORK> -- `src/`, the double changed, and its three
tests -- and EVERY test is built at -O0 and under `opt -O2`, as `run.py` builds
a member, and run with the environment the harness gives it, `NTIME_HARNESS=1`,
nothing inherited, under a sixty-second limit, once a leg. A `golden` member's
stdout is held to its `.txt` beside it, byte for byte, on each leg, as the
`golden` stage holds it.

A mutant is STILLBORN when the compiler refuses its text, RED when a test exits
other than 0 on a leg or a golden differs, UNSEEN when every test passes on
both. `all` prints the counts; for each test, every exit some mutant reaches
(`g` a golden that differs); and every UNSEEN mutant, its id, operator and
change. `table` prints each row, the exit it is aimed at, and what each test
exits on both legs.
Needs `NPKC`, `NPKRT` and the pinned LLVM on `PATH` -- `env.sh`.
"""
import concurrent.futures
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mutate  # noqa: E402

DOUBLE = os.path.join("tests", "double", "host_double.npk")
TESTS = [("unit", "double_readings", None), ("unit", "double_substitution", None),
         ("golden", "double_transcript", "double_transcript.txt")]


def build_and_run(d, sub, name, golden):
    """`("ok", "r0/r2")` or `("refused", why)`; a golden that differs reads `g`."""
    npkc, rt = os.environ["NPKC"], os.environ["NPKRT"]
    u = os.path.join(d, "tests", sub)
    o = os.path.join(d, "out", name)
    os.makedirs(os.path.dirname(o), exist_ok=True)
    p = subprocess.run([npkc, name + ".npk", "-o", o + ".ll"], cwd=u,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if p.returncode != 0 or not os.path.isfile(o + ".ll"):
        m = re.search(rb"^(NITPICK-[A-Z]+-\d+)", p.stdout, re.M)
        return ("refused", m.group(1).decode() if m else "npkc exit %d" % p.returncode)
    steps = [["llc", "-O0", "-filetype=obj", "-relocation-model=static", o + ".ll", "-o", o + ".o"],
             ["ld.lld", "-static", o + ".o", rt, "-o", o + ".x0"],
             ["opt", "-O2", "-S", o + ".ll", "-o", o + ".2.ll"],
             ["llc", "-O2", "-filetype=obj", "-relocation-model=static", o + ".2.ll", "-o", o + ".2.o"],
             ["ld.lld", "-static", o + ".2.o", rt, "-o", o + ".x2"]]
    for s in steps:
        if subprocess.run(s, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0:
            return ("refused", "%s refused the emission" % s[0])
    want = open(os.path.join(u, golden), "rb").read() if golden else None
    rs = []
    for x in (o + ".x0", o + ".x2"):
        try:
            r = subprocess.run([x], cwd=u, env={"NTIME_HARNESS": "1"}, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, timeout=60)
            code = str(r.returncode)
            if want is not None and code == "0" and r.stdout != want:
                code = "g"
            rs.append(code)
        except subprocess.TimeoutExpired:
            rs.append("timeout")
    return ("ok", "/".join(rs))


def copy_tree(repo, d):
    if os.path.isdir(d):
        shutil.rmtree(d)
    shutil.copytree(os.path.join(repo, "src"), os.path.join(d, "src"))
    os.makedirs(os.path.join(d, "tests", "unit"))
    os.makedirs(os.path.join(d, "tests", "golden"))
    shutil.copytree(os.path.join(repo, "tests", "double"), os.path.join(d, "tests", "double"))
    for sub, name, golden in TESTS:
        shutil.copy(os.path.join(repo, "tests", sub, name + ".npk"), os.path.join(d, "tests", sub))
        if golden:
            shutil.copy(os.path.join(repo, "tests", sub, golden), os.path.join(d, "tests", sub))


def one(args):
    repo, work, mid, lines, edits = args
    d = os.path.join(work, mid)
    copy_tree(repo, d)
    with open(os.path.join(d, DOUBLE), "w", encoding="utf-8") as fh:
        fh.write("\n".join(mutate.apply(lines, edits)))
    res = [build_and_run(d, sub, name, golden) for sub, name, golden in TESTS]
    shutil.rmtree(d)
    return mid, res


def named_rows():
    rows = []
    for line in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "named.tsv"),
                     encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        name, aim, old, new = line.rstrip("\n").split("\t")
        rows.append((name, aim, old.replace("\\n", "\n"), new.replace("\\n", "\n")))
    return rows


def one_named(args):
    repo, work, name, text = args
    d = os.path.join(work, name)
    copy_tree(repo, d)
    with open(os.path.join(d, DOUBLE), "w", encoding="utf-8") as fh:
        fh.write(text)
    res = [build_and_run(d, sub, n, golden) for sub, n, golden in TESTS]
    shutil.rmtree(d)
    return name, res


def main(argv):
    if len(argv) < 4 or argv[1] not in ("all", "table"):
        print(__doc__)
        return 2
    mode, repo, work = argv[1], os.path.realpath(argv[2]), os.path.realpath(argv[3])
    jobs = int(argv[argv.index("-j") + 1]) if "-j" in argv else 4
    os.makedirs(work, exist_ok=True)
    lines, muts = mutate.mutants(os.path.join(repo, DOUBLE))
    base = one((repo, work, "unchanged", lines, []))[1]
    print("unchanged: " + "  ".join("%s %s" % (n, r[1]) for (_, n, _), r in zip(TESTS, base)))
    if any(r != ("ok", "0/0") for r in base):
        print("STOP: the unchanged double is not green on its three tests")
        return 1
    if mode == "table":
        src = "\n".join(lines)
        jobs_in = []
        for name, aim, old, new in named_rows():
            if src.count(old) != 1:
                print("STOP %s: its text is in the double %d time(s), not once" % (name, src.count(old)))
                return 1
            jobs_in.append((repo, work, name, src.replace(old, new)))
        with concurrent.futures.ThreadPoolExecutor(jobs) as ex:
            results = dict(ex.map(one_named, jobs_in))
        for name, aim, old, new in named_rows():
            print("%-34s aimed at %-16s %s" % (name, aim, "  ".join(
                "%s %s" % (n.replace("double_", ""), r[1]) for (_, n, _), r in zip(TESTS, results[name]))))
        return 0
    with concurrent.futures.ThreadPoolExecutor(jobs) as ex:
        results = dict(ex.map(one, [(repo, work, m[0], lines, m[4]) for m in muts]))
    still, red, unseen, exits = [], [], [], {n: set() for _, n, _ in TESTS}
    for mid, op, old, new, _ in muts:
        res = results[mid]
        if any(r[0] == "refused" for r in res):
            still.append(mid)
            continue
        hit = False
        for (_, n, _), r in zip(TESTS, res):
            for e in r[1].split("/"):
                if e != "0":
                    exits[n].add(e)
                    hit = True
        (red if hit else unseen).append((mid, op, old, new))
    print("%d mutant(s): %d stillborn, %d red, %d unseen" % (len(muts), len(still), len(red), len(unseen)))
    for _, n, _ in TESTS:
        print("  %s reached: %s" % (n, " ".join(sorted(exits[n], key=lambda x: (len(x), x))) or "nothing"))
    for mid, op, old, new in unseen:
        print("  unseen %-7s %-5s %s -> %s" % (mid, op, old[:60], new[:60] or "(deleted)"))
    if "--all" in argv:
        for mid, op, old, new, _ in muts:
            res = results[mid]
            print("  %-7s %-5s %-40s %s" % (mid, op, (old[:20] + " -> " + (new[:16] or "(del)")),
                                          "  ".join(r[1] for r in res)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
