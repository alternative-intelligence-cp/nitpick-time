#!/usr/bin/env python3
"""0.3.2 -- the system zone's mutants against its seven units (the plan's §1.9).

    python3 -B enumerate.py all   <REPO> <WORK> [-j N]   # every single-site mutant, `mutate.py`'s
    python3 -B enumerate.py table <REPO> <WORK> [-j N]   # `mutants.tsv`'s step-3 rows, the named shapes

Each mutant is built in a copy of `src/` under <WORK>, `src/host/host.npk`
changed, beside copies of the units; EVERY unit is built at -O0 and under
`opt -O2`, as `run.py` builds a unit, and run with the environment the
harness gives it -- `NTIME_HARNESS=1` and its `// env:` lines, nothing
inherited -- under a sixty-second limit. A signal is printed as Python
reports it, as the harness's runner does: `-14` is `SIGALRM`.

A mutant is STILLBORN when the compiler refuses its text, RED when a unit
exits other than 0 on a leg, UNSEEN when every unit exits 0 on both.

`all` prints the counts; for each unit, every exit some mutant reaches; and
every UNSEEN mutant, its id, operator and change, and the line after it.
`table` prints, for each row, what every unit exits on both legs.

Needs `NPKC`, `NPKRT` and the pinned LLVM first on `PATH` -- `env.sh`.
"""
import concurrent.futures
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mutate  # noqa: E402

UNITS = ["system_zone_etc", "system_zone_tz", "system_zone_tz_colon",
         "system_zone_tz_colon_bare", "system_zone_tz_path",
         "system_zone_tz_empty", "system_zone_tz_raw"]
HOST = os.path.join("src", "host", "host.npk")


def short(u):
    return u[len("system_zone_"):]


def env_of(path):
    env = {"NTIME_HARNESS": "1"}
    for line in open(path, encoding="utf-8"):
        if line.startswith("// env: "):
            k, _, v = line[len("// env: "):].rstrip("\n").partition("=")
            env[k.strip()] = v
    return env


def build_and_run(d, unit):
    """`("ok", "r0/r2")` or `("refused", code)`."""
    npkc, rt = os.environ["NPKC"], os.environ["NPKRT"]
    o = os.path.join(d, unit)
    u = os.path.join(d, "tests", "unit")
    p = subprocess.run([npkc, unit + ".npk", "-o", o + ".ll"], cwd=u,
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
    env = env_of(os.path.join(u, unit + ".npk"))
    rs = []
    for x in (o + ".x0", o + ".x2"):
        try:
            rs.append(str(subprocess.run([x], cwd=u, env=env, stdout=subprocess.DEVNULL,
                                         stderr=subprocess.DEVNULL, timeout=60).returncode))
        except subprocess.TimeoutExpired:
            rs.append("timeout")
    return ("ok", "/".join(rs))


def run_mutant(repo, work, name, text):
    """Build and run every unit over `text` as `src/host/host.npk`:
    `("stillborn <code>", [])` or `("red" | "unseen", [(unit, "r0/r2")])`."""
    d = os.path.join(work, "m", name)
    shutil.rmtree(d, ignore_errors=True)
    shutil.copytree(os.path.join(repo, "src"), os.path.join(d, "src"))
    os.makedirs(os.path.join(d, "tests", "unit"))
    for u in UNITS:
        shutil.copy(os.path.join(repo, "tests", "unit", u + ".npk"),
                    os.path.join(d, "tests", "unit"))
    with open(os.path.join(d, HOST), "w", encoding="utf-8") as fh:
        fh.write(text)
    verdict, seen = "unseen", []
    for u in UNITS:
        kind, r = build_and_run(d, u)
        if kind == "refused":
            verdict, seen = "stillborn %s" % r, []
            break
        seen.append((short(u), r))
        if r != "0/0":
            verdict = "red"
    shutil.rmtree(d, ignore_errors=True)
    return verdict, seen


def jobs_of(argv):
    return int(argv[argv.index("-j") + 1]) if "-j" in argv else 8


def check_units(repo):
    for u in UNITS:
        if not os.path.isfile(os.path.join(repo, "tests", "unit", u + ".npk")):
            raise SystemExit("STOP: no tests/unit/%s.npk" % u)


def cmd_all(repo, work, jobs):
    lines, muts = mutate.mutants(os.path.join(repo, HOST))

    def one(m):
        mid, op, old, new, edits = m
        ml = mutate.apply(lines, edits)
        verdict, seen = run_mutant(repo, work, mid, "\n".join(ml))
        i = edits[0][0]
        return mid, op, old, new, verdict, seen, ml[i][:mutate.code_end(ml[i])].strip()

    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as ex:
        results = list(ex.map(one, muts))
    with open(os.path.join(work, "all.tsv"), "w", encoding="utf-8") as fh:
        for r in results:
            fh.write("\t".join([r[0], r[1], r[2], r[3], r[4],
                                "; ".join("%s %s" % s for s in r[5])]) + "\n")
    still = [r for r in results if r[4].startswith("stillborn")]
    red = [r for r in results if r[4] == "red"]
    unseen = [r for r in results if r[4] == "unseen"]
    print("%d single-site mutant(s) of the section: %d stillborn, %d red, %d unseen"
          % (len(results), len(still), len(red), len(unseen)))
    exits = {short(u): set() for u in UNITS}
    for r in red:
        for u, legs in r[5]:
            exits[u].update(x for x in legs.split("/") if x != "0")
    order = lambda x: (0, int(x)) if x.lstrip("-").isdigit() else (1, x)
    for u in UNITS:
        print("exits reached in %s: %s" % (short(u), " ".join(sorted(exits[short(u)], key=order)) or "none"))
    for r in unseen:
        print("unseen %s %s [%s] -> [%s]: %s" % (r[0], r[1], r[2], r[3], r[6]))


def cmd_table(repo, work, jobs):
    host = open(os.path.join(repo, HOST), encoding="utf-8").read()
    rows = []
    tsv = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mutants.tsv")
    for line in open(tsv, encoding="utf-8"):
        f = line.rstrip("\n").split("\t")
        if len(f) == 4 and f[0] == "3":
            rows.append((f[1], f[2].replace("\\n", "\n"), f[3].replace("\\n", "\n")))

    def one(row):
        name, old, new = row
        if host.count(old) != 1:
            return name, "STOP: %d occurrence(s) of the row's text" % host.count(old)
        verdict, seen = run_mutant(repo, work, name, host.replace(old, new))
        if verdict.startswith("stillborn"):
            return name, verdict
        return name, " ".join("%s %s" % s for s in seen)

    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as ex:
        for name, line in ex.map(one, rows):
            print("%s: %s" % (name, line))


def main(argv):
    if len(argv) < 4 or argv[1] not in ("all", "table"):
        print(__doc__)
        return 2
    repo, work = os.path.abspath(argv[2]), os.path.abspath(argv[3])
    check_units(repo)
    os.makedirs(work, exist_ok=True)
    (cmd_all if argv[1] == "all" else cmd_table)(repo, work, jobs_of(argv))
    shutil.rmtree(os.path.join(work, "m"), ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
