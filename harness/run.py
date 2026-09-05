#!/usr/bin/env python3
"""ntime's build-and-test runner. Cycle 0.0.2.

THIS REPLACED THE 0.0.1 FLOOR; IT DID NOT GROW OUT OF IT. The floor was four
hardcoded checks with no manifest reader, no stage dispatch and no way to be
pointed at anything. Two things came across because they had earned it:
`check_expect_headers`, which states its denominator and partitions the tree so
nothing falls between buckets (TM-115), and the rule that every `npkc` exit 0 is
paired with the artefact it should have produced.

WHAT A GREEN RUN HERE IS, AND IS NOT.

  IT IS: the manifest read and schema-checked; the three tools held to the pin's
  exact patch release; the library emitted, optimised, assembled and scanned;
  the IR proved identical from two working directories; every tracked `.npk`
  owned by an expectation or a named exemption; and every test file held to its
  own header at -O0 and again under `opt -O2`.

  IT IS NOT evidence that the RUNNER can fail. `harness/selfcheck.py` is cycle
  0.0.3 (`TESTING.md` V-14/V-15), and until it exists the only things here that
  have been seen to go red on purpose are the three commissioned by hand at
  0.0.2 and recorded in `meta/roadmap/0.0/0.0.2.md`: the undefined-symbol scan,
  the toolchain pin, and `repro`.

  IT IS NOT a purity result. The undefined-symbol scan CANNOT SEE A SYSCALL --
  `npk_sys6` is the runtime's own and is in the allowlist by construction. See
  `harness/elf.py`. `check_purity` is a source-level check and it is 0.0.3's.

STAGE ORDER, and each line is a reason:

  1  manifest          nothing else can start; every path and flag comes from it
  2  toolchain         a wrong `llc` makes every later result meaningless
  3  tree sweep        cheap, and it is the check that finds files no test owns
  4  library           one build per run, and it is a check in its own right
  5  repro             before the suite, because it builds the library again
  6  suite             the `[[test]]` entries, in manifest order
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import build as build_mod                                        # noqa: E402
import elf                                                       # noqa: E402
import manifest as manifest_mod                                  # noqa: E402
import repro as repro_mod                                        # noqa: E402
import stages                                                    # noqa: E402
import toolchain                                                 # noqa: E402

# The repository root, derived from THIS FILE rather than from the working
# directory, so `python3 harness/run.py` and `python3 /abs/path/run.py` mean the
# same run. B-4 wants two builds from different working directories to agree; a
# runner that resolved its own tree by `os.getcwd()` could not honour that.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# THE EXEMPTION LIST IS THE DENOMINATOR'S OTHER HALF (TM-115, V-1c). A sweep
# reporting "no violations" and a sweep that opened nothing print the same line,
# so this check states how many files it opened, and every file it opened is
# either covered or named here with the reason it is not. The list is diffed in
# BOTH directions: a name here that no longer exists is itself a failure,
# because an exemption that outlives its file silently excuses the next file
# with that name.
EXPECT_EXEMPT = {
    "tests/probe/support/probe11_arms_lib.npk":
        "a library module probe 11 imports: no `main`, no `failsafe`, never "
        "run and never refused, so there is no exit code and no diagnostic to "
        "expect (tests/probe/README.md, 0.0.0 P-1)",
    "tests/probe/support/probe11_calc_lib.npk":
        "the same: a support module, imported by probe 11c to price its "
        "arithmetic",
    "tests/probe/support/probe11_silent_lib.npk":
        "the same: a support module that declares no error at all, the control "
        "for TM-107's per-module arm bill",
}

# The directories a `.npk` may not live in and be missed: none. This walk is
# over the whole tree deliberately, because the file that went uncovered for two
# days was under `tests/probe/defect/`, which every directory-scoped sweep
# written before it had left out.
WALK_SKIP = {".git", ".internal", "build", "__pycache__"}


class Report:
    """Verdict lines, the failure list, and the counts. One place, so the
    summary cannot disagree with what was printed."""

    def __init__(self, verdicts_path=None):
        self.failures = []
        self.units = 0
        self.passed = 0
        self.verdicts = []
        self.verdicts_path = verdicts_path

    def say(self, line):
        sys.stdout.write(line + "\n")
        sys.stdout.flush()

    def fail(self, what, detail):
        self.failures.append(what)
        self.say("  FAIL  %s" % what)
        for line in str(detail).rstrip().splitlines():
            self.say("        %s" % line)

    def unit(self, name, problems, note=""):
        """One test unit's verdict. `--verdicts` writes one line per unit."""
        self.units += 1
        if problems:
            self.failures.append(name)
            self.say("  FAIL  %s" % name)
            for p in problems:
                for line in str(p).rstrip().splitlines():
                    self.say("        %s" % line)
            self.verdicts.append("FAIL %s" % name)
        else:
            self.passed += 1
            self.say("  ok    %-46s %s" % (name, note))
            self.verdicts.append("PASS %s%s" % (name,
                                                (" " + note) if note else ""))

    def write_verdicts(self):
        if not self.verdicts_path:
            return
        with open(self.verdicts_path, "w", encoding="utf-8") as fh:
            for line in self.verdicts:
                fh.write(line + "\n")
        self.say("wrote %d verdict line(s) to %s"
                 % (len(self.verdicts), self.verdicts_path))


# ---------------------------------------------------------------------------
# 3. the tree sweep -- carried over from the 0.0.1 floor, with the strict reader
# ---------------------------------------------------------------------------

def all_npk():
    found = []
    for dirpath, dirs, names in os.walk(ROOT):
        dirs[:] = sorted(d for d in dirs if d not in WALK_SKIP)
        for n in sorted(names):
            if n.endswith(".npk"):
                found.append(os.path.relpath(os.path.join(dirpath, n), ROOT)
                             .replace(os.sep, "/"))
    return sorted(found)


def check_expect_headers(rep):
    """Every `.npk` in the tree is in exactly ONE of three buckets.

      src/       judged by "it compiles" -- check 4 emits the whole graph the
                 entry reaches, and a library module has no exit code and no
                 diagnostic to expect, so it carries no marker.
      tests/     judged by a marker in its own header (B-5), or named in
                 EXPECT_EXEMPT with the reason it cannot have one.
      elsewhere  nothing. A `.npk` outside both is a file no check owns.

    The counts are printed whether or not anything is wrong, and they are
    asserted to sum -- "swept, no violations" and "swept nothing" are the same
    line otherwise (TM-115, V-1b).

    THE READER IS `stages.read`, the same one the suite dispatches on. That is
    the point: the sweep and the dispatch cannot disagree about what a header
    says, and the sweep reaches files no `[[test]]` entry selects -- every file
    under `tests/probe/defect/`, which is all of them.
    """
    files = all_npk()
    in_src, in_tests, orphan = [], [], []
    for rel in files:
        (in_src if rel.startswith("src/")
         else in_tests if rel.startswith("tests/")
         else orphan).append(rel)

    covered, exempt, bad = [], [], []
    for rel in in_tests:
        if rel in EXPECT_EXEMPT:
            exempt.append(rel)
            continue
        try:
            stages.read(ROOT, rel)
            covered.append(rel)
        except stages.MarkerError as err:
            bad.append((rel, err))

    rep.say("[3/6] expect- header sweep -- %d .npk in the tree = %d src/ + %d "
            "tests/ + %d elsewhere" % (len(files), len(in_src), len(in_tests),
                                       len(orphan)))
    rep.say("      of the %d under tests/: %d with a valid header, %d exempt, "
            "%d rejected" % (len(in_tests), len(covered), len(exempt),
                             len(bad)))

    if not files:
        rep.fail("expect- sweep", "opened 0 .npk files; a sweep with an empty "
                                  "denominator reports green while checking "
                                  "nothing")
        return
    if not in_tests:
        rep.fail("expect- sweep", "found 0 .npk under tests/; the sweep's whole "
                                  "subject is missing, which is not the same "
                                  "as finding no violations in it")
        return
    if len(in_src) + len(in_tests) + len(orphan) != len(files):
        rep.fail("expect- sweep", "the buckets do not sum to the denominator")

    for rel in orphan:
        rep.fail("unowned .npk: %s" % rel,
                 "a .npk in neither src/ nor tests/ is judged by no check. Put "
                 "it under one, or give this sweep a bucket for it and say why.")
    for rel, err in bad:
        rep.fail("header: %s" % rel, err)
    for rel in sorted(EXPECT_EXEMPT):
        if rel not in set(files):
            rep.fail("stale exemption: %s" % rel,
                     "EXPECT_EXEMPT names a file that is not in the tree. An "
                     "exemption that outlives its file is how a later file "
                     "with the same name gets excused without anyone deciding "
                     "to excuse it (V-1c).")


# ---------------------------------------------------------------------------
# 4. the library
# ---------------------------------------------------------------------------

def build_library(rep, bld):
    """One build per run, both legs, scanned. It is a check, not an input.

    `npkc` has no separate-compilation mode (TM-117), so nothing links against
    this object -- every program re-emits the whole graph it reaches. What this
    step asserts is that the library's entry point emits, survives `opt -O2`,
    assembles at both optimisation levels, and needs no symbol the runtime does
    not define.
    """
    entry = bld.manifest["build"]["entry"]
    reached = build_mod.reachable_sources(os.path.join(ROOT, entry))
    rep.say("[4/6] library -- %s, reaching %d source(s) by `use`"
            % (entry, len(reached)))
    ll = os.path.join(bld.out_dir, "ntime.ll")
    try:
        bld.emit(entry, ll)
        rep.say("  ok    npkc            %9d B of IR" % os.path.getsize(ll))
        obj = os.path.join(bld.out_dir, "ntime.o")
        bld.assemble(ll, obj)
        bld.scan(obj)
        rep.say("  ok    llc + scan      %9d B object, 0 forbidden symbols of "
                "%d undefined" % (os.path.getsize(obj), len(elf.undefined(obj))))
        opt_ll = os.path.join(bld.out_dir, "ntime.opt.ll")
        bld.optimise(ll, opt_ll)
        opt_obj = os.path.join(bld.out_dir, "ntime.opt.o")
        bld.assemble(opt_ll, opt_obj, optimised=True)
        bld.scan(opt_obj)
        rep.say("  ok    opt -O2 + scan  %9d B object (B-3: the scan is "
                "repeated on the optimised object)" % os.path.getsize(opt_obj))
        return True
    except build_mod.BuildError as err:
        rep.fail("library build (%s)" % err.step, err.detail)
        return False


# ---------------------------------------------------------------------------
# 6. the suite
# ---------------------------------------------------------------------------

def select(entry):
    """The files a `[[test]]` entry selects: `<path>/*.npk`, non-recursive.

    NOT recursive, and the omission is load-bearing (the manifest says so at
    length): a plain glob over `tests/probe/` is exactly the twenty-six probe
    programs and excludes `support/` -- three library modules with no `main` --
    and `defect/`, whose files are reproductions rather than tests of this
    library. The schema has no `recursive` key, so writing one is refused by
    name rather than silently ignored.
    """
    d = os.path.join(ROOT, entry["path"])
    if not os.path.isdir(d):
        return None
    return sorted(
        os.path.join(entry["path"], n).replace(os.sep, "/")
        for n in os.listdir(d) if n.endswith(".npk"))


def run_entry(rep, bld, entry, only):
    name, stage, path = entry["name"], entry["stage"], entry["path"]
    files = select(entry)
    if files is None:
        rep.fail("[[test]] %s" % name,
                 "path `%s` is not a directory" % path)
        return
    if not files:
        # The manifest's own comment: an entry naming a directory with nothing
        # in it is a suite that reports green while checking nothing.
        rep.fail("[[test]] %s" % name,
                 "`%s/*.npk` matched 0 files. An entry naming an empty "
                 "directory is a suite that reports green while checking "
                 "nothing (B-8)." % path)
        return

    chosen = [f for f in files if only is None or only in f]
    refusals = 0
    runs = 0
    for rel in chosen:
        try:
            e = stages.read(ROOT, rel)
        except stages.MarkerError as err:
            rep.unit(rel, [str(err)])
            continue
        if e.is_refusal:
            refusals += 1
            problems = stages.refusal(bld, rel, e)
            rep.unit(rel, problems,
                     "refused %s" % ", ".join(sorted(set(e.errors))))
        else:
            runs += 1
            t0 = time.time()
            problems = stages.program(bld, rel, e)
            note = "exit %d, both legs, %.1f s" % (e.exit, time.time() - t0)
            if e.stress > 1:
                note += ", stress %d" % e.stress
            if e.env:
                note += ", env %s" % " ".join(sorted(e.env))
            rep.unit(rel, problems, note)

    rep.say("      %s: %d of %d file(s) -- %d run, %d refusal%s"
            % (name, len(chosen), len(files), runs, refusals,
               "" if only is None else "  [FILTERED by --only]"))


# ---------------------------------------------------------------------------

def main(argv):
    only, verdicts_path = None, None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--only" and i + 1 < len(argv):
            only, i = argv[i + 1], i + 2
        elif a.startswith("--only="):
            only, i = a.split("=", 1)[1], i + 1
        elif a == "--verdicts" and i + 1 < len(argv):
            verdicts_path, i = argv[i + 1], i + 2
        elif a.startswith("--verdicts="):
            verdicts_path, i = a.split("=", 1)[1], i + 1
        else:
            sys.stderr.write("run.py: unknown argument %r\n"
                             "usage: run.py [--only SUBSTRING] "
                             "[--verdicts PATH]\n" % a)
            return 2
        continue

    rep = Report(verdicts_path)
    t0 = time.time()
    rep.say("ntime harness -- cycle 0.0.2. The self-check is 0.0.3, so nothing")
    rep.say("here has been proved able to fail except by hand (V-14, V-15).")
    if only is not None:
        rep.say("")
        rep.say("*** --only %r: THIS RUN CONCLUDES NOTHING. A filtered run is "
                "for iterating; ***" % only)
        rep.say("*** nothing is committed on the strength of one.               "
                "             ***")
    rep.say("")

    # 1. the manifest
    try:
        man = manifest_mod.load(ROOT)
    except manifest_mod.ManifestError as err:
        rep.say("[1/6] manifest")
        rep.fail("nitpick.toml", err)
        rep.say("")
        rep.say("RED -- the manifest is where every path and flag comes from "
                "(P-12); nothing runs without it.")
        return 1
    rep.say("[1/6] manifest -- %s %s, entry %s, %d [[test]] entr%s"
            % (man["project"]["name"], man["project"]["version"],
               man["build"]["entry"], len(man["test"]),
               "y" if len(man["test"]) == 1 else "ies"))

    # 2. the toolchain
    rep.say("[2/6] toolchain -- nitpick.toml pins LLVM %s exactly"
            % man["toolchain"]["llvm"])
    npkc, npkrt = os.environ.get("NPKC"), os.environ.get("NPKRT")
    ok_env = True
    for var, val in (("NPKC", npkc), ("NPKRT", npkrt)):
        if not val or not os.path.isfile(val):
            rep.fail("$%s" % var, "not set, or not a file: %r" % val)
            ok_env = False
    try:
        for tool, version, banner in toolchain.check(man):
            rep.say("  ok    %-8s %-8s %s" % (tool, version, banner))
    except toolchain.ToolchainError as err:
        rep.fail("toolchain", err)
        ok_env = False

    # 3. the tree sweep -- runs even when the toolchain is wrong, because it
    #    needs no toolchain and its finding is worth having either way.
    check_expect_headers(rep)

    if not ok_env:
        rep.say("")
        rep.say("RED -- the toolchain is a build input (D-204). Nothing was "
                "built.")
        rep.write_verdicts()
        return 1

    bld = build_mod.Build(ROOT, man, npkc, npkrt, os.path.join(ROOT, "build"))
    rep.say("      allowlist: %d symbol(s), derived from %s (TM-118)"
            % (len(bld.allowlist), os.path.basename(npkrt)))

    if build_library(rep, bld):
        # 5. repro
        roots = [man["build"]["entry"]]
        rep.say("[5/6] repro -- %d root(s), each built twice from two working "
                "directories (B-4)" % len(roots))
        for p in repro_mod.check(bld, roots, say=rep.say):
            rep.fail("repro", p)

    # 6. the suite
    rep.say("[6/6] suite")
    for entry in man["test"]:
        run_entry(rep, bld, entry, only)

    rep.say("")
    rep.write_verdicts()
    elapsed = time.time() - t0
    if rep.failures:
        rep.say("RED -- %d unit(s) of %d passed; %d failure(s) in %.1f s: %s"
                % (rep.passed, rep.units, len(rep.failures), elapsed,
                   ", ".join(rep.failures)))
        return 1
    if only is not None:
        rep.say("GREEN under --only %r in %.1f s -- %d of the suite's units "
                "ran." % (only, elapsed, rep.units))
        rep.say("*** THIS CONCLUDES NOTHING. --only iterates; it never "
                "concludes. ***")
        return 0
    rep.say("GREEN -- %d unit(s), 0 failures, %.1f s. Read this file's header "
            "for what that does not mean." % (rep.units, elapsed))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
