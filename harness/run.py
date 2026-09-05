#!/usr/bin/env python3
"""ntime's build-and-test runner -- THE 0.0.1 FLOOR, NOT THE HARNESS.

READ THIS BEFORE TRUSTING A GREEN RUN FROM THIS FILE.

This is not `harness/run.py` as `meta/specs/TESTING.md` describes it. There is
no manifest reader, no module-graph walk, no stage dispatch, no `--only`, no
self-check. Those are cycles 0.0.2 and 0.0.3, and this file is REPLACED by
them, not extended into them.

WHY IT EXISTS AT ALL, AND WHY IT IS NOT AN `exit 0` STUB. Cycle 0.0.1's step 4
puts CI in place, and CI has to run something. The obvious something is a stub
that exits 0 -- and a suite that reports green while checking nothing is the
single failure this library's testing plan is built to prevent (`BUILD.md` B-8,
`TESTING.md` V-14, and the manifest's own comment about an entry naming an
empty directory). So this floor checks exactly what cycle 0.0.1 created, and
nothing else:

  1. the toolchain is present and pinned  -- $NPKC, $NPKRT, LLVM's exact patch
  2. every `.npk` under `src/` compiles   -- the `parse` floor; P-7's whole
                                             reason for placing a module in
                                             every directory
  3. the conformance consumer runs        -- all four steps, judged on the
                                             RUN's exit code
  4. every tracked `.npk` is covered      -- by an `expect-` header or by a
                                             NAMED exemption, with the
                                             denominator printed (TM-115)

AND THE THIRD ONE IS THE POINT. `npkc` exiting 0 does not mean a program is
well-formed: a root with `main` and no `failsafe` was accepted at exit 0 until
the compiler's DEF-5 landed (`meta/OPEN_QUESTIONS.md` O-N11, TM-112), and a
stage that stops at the `.ll` would have passed it. So step 3 emits, assembles,
links AND RUNS, and it is the run that is judged.

WHAT A GREEN RUN HERE IS NOT EVIDENCE OF. Not this library's behaviour -- there
is none yet; `src/` is six placeholders and an empty umbrella. Not that the
runner can FAIL: the self-check is 0.0.3, and until it exists nothing here has
been seen to go red on purpose.
"""

import os
import subprocess
import sys

# The repository root, derived from THIS FILE rather than from the working
# directory, so `python3 harness/run.py` and `python3 /abs/path/run.py` mean the
# same run. B-4 wants two builds from different working directories to agree;
# a runner that resolved its own tree by `os.getcwd()` could not honour that.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# `nitpick.toml` [toolchain] llvm. Exact patch release, because a patch release
# can change instruction selection (D-204: the toolchain is a build input).
LLVM_VERSION = "20.1.2"

# `nitpick.toml` [toolchain] llc-flags / lld-flags. Rule B-1: no tool ever runs
# at its own defaults -- `llc` defaults to -O2 and would optimise a build the
# manifest declined.
LLC_FLAGS = ["-O0", "-filetype=obj", "-relocation-model=static"]
LLD_FLAGS = ["-static"]

failures = []


def say(line):
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def run(argv, cwd=None):
    """Run argv with NO shell and NO pipeline, and return (status, output).

    Deliberately not `subprocess.check_output(...)` through a pipe: capturing a
    status through a pipeline is how a measurement session here once recorded
    thirty programs as `exit=0` when two of them had refused and written
    nothing. The status returned below is the process's own.
    """
    p = subprocess.run(argv, cwd=cwd or ROOT, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def fail(what, detail):
    failures.append(what)
    say("  FAIL  %s" % what)
    for line in detail.rstrip().splitlines():
        say("        %s" % line)


# ---------------------------------------------------------------------------
# 1. the toolchain
# ---------------------------------------------------------------------------

def check_toolchain():
    say("[1/4] toolchain")
    npkc = os.environ.get("NPKC")
    npkrt = os.environ.get("NPKRT")
    if not npkc or not os.path.isfile(npkc):
        fail("$NPKC", "not set, or not a file: %r" % npkc)
        return None, None
    if not npkrt or not os.path.isfile(npkrt):
        fail("$NPKRT", "not set, or not a file: %r" % npkrt)
        return None, None

    st, out = run(["llvm-config", "--version"])
    have = out.strip()
    if st != 0:
        fail("llvm-config", out)
    elif have != LLVM_VERSION:
        # An assertion, not a report. The whole reason the manifest names three
        # digits is that a different patch release fails HERE rather than
        # silently producing different code.
        fail("LLVM version",
             "have %s; nitpick.toml pins %s exactly" % (have, LLVM_VERSION))
    else:
        say("  ok    llvm-config --version == %s" % have)
        say("  ok    NPKC   %s" % npkc)
        say("  ok    NPKRT  %s" % npkrt)
    return npkc, npkrt


# ---------------------------------------------------------------------------
# 2. every .npk under src/ compiles
# ---------------------------------------------------------------------------

def sources():
    found = []
    for dirpath, _dirs, names in os.walk(os.path.join(ROOT, "src")):
        for n in sorted(names):
            if n.endswith(".npk"):
                found.append(os.path.relpath(os.path.join(dirpath, n), ROOT))
    return sorted(found)


def check_sources(npkc, out_dir):
    """The `parse` floor.

    THE DENOMINATOR IS PRINTED. A sweep that matches nothing and a sweep that
    ran over nothing print the same thing unless the count is stated, so the
    count is stated -- and it is asserted against a floor, because `src/` is
    known to hold an umbrella plus one placeholder per directory (P-7).
    """
    files = sources()
    say("[2/4] src/ compiles -- %d file(s)" % len(files))
    if len(files) < 7:
        fail("src/ inventory",
             "found %d .npk under src/; expected at least 7 (lib.npk plus one "
             "placeholder per directory, 0.0.1 P-7). A directory whose module "
             "was deleted rather than replaced is invisible to this sweep, "
             "which is the reason the floor is asserted." % len(files))
        return
    for rel in files:
        ll = os.path.join(out_dir, os.path.basename(rel)[:-4] + ".ll")
        st, out = run([npkc, rel, "-o", ll])
        if st != 0:
            fail(rel, out)
        elif not os.path.isfile(ll):
            # `npkc` exit 0 paired with the artefact it should have produced.
            # A status that disagrees with an artefact is the tell.
            fail(rel, "npkc exited 0 and wrote no .ll")
        else:
            say("  ok    %-32s %8d B of IR" % (rel, os.path.getsize(ll)))


# ---------------------------------------------------------------------------
# 3. the conformance consumer, all four steps
# ---------------------------------------------------------------------------

def check_conformance(npkc, npkrt, out_dir):
    rel = os.path.join("tests", "conformance", "import.npk")
    say("[3/4] %s -- emit, assemble, link, RUN" % rel)
    if not os.path.isfile(os.path.join(ROOT, rel)):
        fail(rel, "missing")
        return
    ll = os.path.join(out_dir, "import.ll")
    obj = os.path.join(out_dir, "import.o")
    exe = os.path.join(out_dir, "import")

    st, out = run([npkc, rel, "-o", ll])
    if st != 0 or not os.path.isfile(ll):
        fail(rel + " (npkc)", out or "exit 0 and no .ll")
        return
    # O-N11 / TM-112: the cheap guard against a program with no handler. It is
    # redundant now that `npkc` refuses one -- and it is kept, because it is
    # what catches the NEXT stage that stops at the `.ll`.
    with open(ll, "r", encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    if text.count("\ndefine i32 @npk_failsafe") < 1:
        fail(rel + " (failsafe)", "the emitted IR defines no @npk_failsafe")
        return

    st, out = run(["llc"] + LLC_FLAGS + [ll, "-o", obj])
    if st != 0:
        fail(rel + " (llc)", out)
        return
    st, out = run(["ld.lld"] + LLD_FLAGS + [obj, npkrt, "-o", exe])
    if st != 0:
        fail(rel + " (ld.lld)", out)
        return
    st, out = run([exe])
    if st != 0:
        fail(rel + " (run)", "exit %d; the file's header expects 0\n%s" % (st, out))
        return
    say("  ok    ran and exited 0")


# ---------------------------------------------------------------------------
# 4. every tracked .npk is covered by an expectation, or is exempt WITH A REASON
# ---------------------------------------------------------------------------

# THE EXEMPTION LIST IS THE DENOMINATOR'S OTHER HALF (TM-115). A sweep that
# reports "no violations" and a sweep that opened nothing print the same line,
# so this check states how many files it opened, and every file it opened is
# either covered or named here with the reason it is not. A name here that no
# longer exists is itself a failure -- that is the second list, and "every hole
# was found by a check that diffs two lists, and none by a test".
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
# over the whole tree deliberately, because the file that went uncovered for
# two days was under `tests/probe/defect/`, which every directory-scoped sweep
# written so far had left out.
WALK_SKIP = {".git", ".internal", "build", "__pycache__"}


def all_npk():
    found = []
    for dirpath, dirs, names in os.walk(ROOT):
        dirs[:] = sorted(d for d in dirs if d not in WALK_SKIP)
        for n in sorted(names):
            if n.endswith(".npk"):
                found.append(os.path.relpath(os.path.join(dirpath, n), ROOT))
    return sorted(found)


def has_expect_header(rel):
    """An `expect-` marker anywhere in the file's leading comment block.

    Read from the top and stop at the first line that is not a comment and not
    blank: a marker below `mod:` is not a header, and B-5 puts expectations in
    the header.
    """
    with open(os.path.join(ROOT, rel), "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            s = line.strip()
            if s.startswith("// expect-"):
                return True
            if s and not s.startswith("//"):
                return False
    return False


def check_expect_headers():
    """Every `.npk` in the tree is in exactly ONE of three buckets.

    THE TREE IS PARTITIONED, AND THE PARTITION IS ASSERTED. Three buckets and
    nothing between them:

      src/        judged by check 2 -- "it compiles". That IS its expectation,
                  and it is not spelled with a marker because a library module
                  has no exit code and no diagnostic to expect.
      tests/      judged by a marker in its own header (B-5), or named in
                  EXPECT_EXEMPT with the reason it cannot have one.
      elsewhere   nothing. A `.npk` outside both is a file no check owns, which
                  is the state the three `missing_failsafe` cases were in.

    The counts are printed whether or not anything is wrong, and they are
    asserted to sum -- because "swept, no violations" and "swept nothing" are
    the same line otherwise.
    """
    files = all_npk()
    in_src, in_tests, orphan = [], [], []
    for rel in files:
        key = rel.replace(os.sep, "/")
        if key.startswith("src/"):
            in_src.append(key)
        elif key.startswith("tests/"):
            in_tests.append(key)
        else:
            orphan.append(key)

    covered, exempt, uncovered = [], [], []
    for key in in_tests:
        if key in EXPECT_EXEMPT:
            exempt.append(key)
        elif has_expect_header(key):
            covered.append(key)
        else:
            uncovered.append(key)

    # THE DENOMINATOR, ALWAYS PRINTED, EVEN WHEN NOTHING IS WRONG.
    say("[4/4] expect- header sweep -- %d .npk in the tree = %d src/ + %d "
        "tests/ + %d elsewhere" % (len(files), len(in_src), len(in_tests),
                                   len(orphan)))
    say("      of the %d under tests/: %d with a header, %d exempt, %d "
        "uncovered" % (len(in_tests), len(covered), len(exempt),
                       len(uncovered)))

    if not files:
        fail("expect- sweep", "opened 0 .npk files; a sweep with an empty "
                              "denominator reports green while checking nothing")
        return
    if not in_tests:
        fail("expect- sweep", "found 0 .npk under tests/; the sweep's whole "
                              "subject is missing, which is not the same as "
                              "finding no violations in it")
        return

    for rel in orphan:
        fail("unowned .npk: %s" % rel,
             "a .npk in neither src/ nor tests/ is judged by no check. Put it "
             "under one, or give this sweep a bucket for it and say why.")

    for rel in uncovered:
        fail("no expect- header: %s" % rel,
             "every .npk under tests/ carries an expectation, or is named in "
             "harness/run.py's EXPECT_EXEMPT with the reason it cannot. A "
             "defect reproduction's expectation goes stale the day its defect "
             "is fixed, and this sweep is the check -- so a file outside it is "
             "the one the check most needed to see (TM-115).")

    stale = [k for k in sorted(EXPECT_EXEMPT) if k not in set(files)]
    for rel in stale:
        fail("stale exemption: %s" % rel,
             "EXPECT_EXEMPT names a file that is not in the tree. An exemption "
             "that outlives its file is how a later file with the same name "
             "gets excused without anyone deciding to excuse it.")


def main():
    say("ntime -- the 0.0.1 FLOOR. This is NOT the harness (cycle 0.0.2 is).")
    say("It checks the toolchain, that src/ compiles, and that the conformance")
    say("consumer RUNS. It checks nothing about this library's behaviour,")
    say("because there is none yet, and it has never been seen to fail on")
    say("purpose -- the self-check is cycle 0.0.3 (TESTING.md V-14).")
    say("")

    out_dir = os.path.join(ROOT, "build")
    os.makedirs(out_dir, exist_ok=True)

    npkc, npkrt = check_toolchain()
    if npkc and npkrt:
        check_sources(npkc, out_dir)
        check_conformance(npkc, npkrt, out_dir)
    check_expect_headers()

    say("")
    if failures:
        say("FLOOR RED -- %d failure(s): %s" % (len(failures), ", ".join(failures)))
        return 1
    say("FLOOR GREEN -- and read the header above for what that does not mean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
