"""The self-check. `TESTING.md` V-14 and V-15. Step 1, and it is step 1 on purpose.

A SUITE THAT ONLY EVER AGREES WITH WHAT IT IS HANDED REPORTS GREEN WHILE
CHECKING NOTHING. Everything else in `harness/` is a check; this is the only
thing that demonstrates the checks can FAIL. Cycle 0.0.2 ended with an honest
list of what its green run did not prove, and the first line of it was *"not
that the runner can fail"* -- three instruments had been commissioned by hand
there, and three checks is not a runner.

  V-14: feed the harness wrong expectations and require it to report every one
        as a failure. Seven cases, and this repository's cycle README adds an
        eighth of its own -- and cycle 0.1.4b a ninth, a program whose managed
        memory disagrees with its header (TM-187).
  V-15: it runs FIRST in every full invocation, and its failure is fatal. A
        harness that has not proven it can fail has not proven anything, so a
        green suite underneath a red self-check is a state this ordering makes
        unreachable rather than merely discouraged.

HOW A CASE WORKS, AND WHY EVERY ONE CARRIES A CONTROL.

  Each case builds a small tree under `.internal/scratch/selfcheck/` (gitignored
  -- nothing here is ever committed), plants ONE fault in it, and runs THIS
  RUNNER against it with `--root`. The case passes when the run comes back RED
  and names the fault.

  AND WHEN THE CONTROL BESIDE IT CAME BACK GREEN. Every tree holds a correct
  twin of the faulted file, and the case asserts a `PASS` line for it in the
  same run. Without that, a red proves only that something went wrong -- it
  could be the scratch tree, the manifest, the toolchain -- and a self-check
  that is satisfied by a broken harness is worse than none. This is 0.0.2 §5.3's
  argument (*"a red that came from `--between` rather than from the
  non-determinism would prove nothing"*) applied to all eight.

  `--root` EXISTS FOR THIS AND FOR NOTHING ELSE. An inner run skips the
  self-check -- otherwise it would not terminate -- and says so, and prints that
  it concludes nothing about the library.

THE SPECIMENS ARE REAL WHERE A REAL ONE EXISTS.

  Case 3 -- a reported code no expectation names -- is not invented. It is
  `tests/probe/probe02d_wide_literal_refused.npk` as it stood before cycle
  0.0.2: the file whose own prose says the harness "expects BOTH" codes, whose
  machine-readable header named ONE, and which the harness's first run caught.
  The file that exists to state D-237's rule was the file that broke it, so its
  header is the specimen this case uses.

  Case 8 -- a program whose `failsafe` has been deleted -- is driven through an
  `npkc` WRAPPER that renames the `@npk_failsafe` define in the emitted IR, the
  technique cycle 0.0.2 used to commission the undefined-symbol scan. It has to
  be driven that way: at pin `0dfddac` a program with `main` and no `failsafe`
  is refused by `npkc` itself (`NITPICK-REACH-003`, the compiler's DEF-5,
  TM-112), so the source-level spelling of this fault no longer reaches the
  belt. The belt is kept and driven anyway, because `npkc` exit 0 is not
  well-formedness and this stage must not depend on which pin it runs against.
"""

import os
import shutil
import subprocess
import sys

import arms as arms_mod
import build as build_mod
import checks as checks_mod
import manifest as manifest_mod

HARNESS = os.path.dirname(os.path.abspath(__file__))

FAILSAFE = """
func:failsafe = int32(Error:e) {
    pick (e) {
        (HeapBadRequest) { exit 91i32; },
        (HeapOom)        { exit 92i32; },
        (Unreachable)    { exit 95i32; },
        (WildLeak)       { exit 96i32; },
        (StackExhausted) { exit 106i32; },
        (MachineFault)   { exit 107i32; },
        (*)              { exit 99i32; }
    }
    exit 9i32;
};
"""

# AND THE SAME HANDLER PLUS THE MODULE'S OWN IDENTITY. `(*)` COUNTS FOR NOTHING
# (D-179): a `failsafe` must NAME every identity that can reach it, and the two
# `?!` sites below put `EW` in the reachable set. The first draft of this file
# left the arm out and every writer program was refused
# `NITPICK-REACH-002` -- which is the language's rule working exactly as
# `SAFETY.md` S-1 describes it, met in the harness's own fixtures.
FAILSAFE_EW = """
func:failsafe = int32(Error:e) {
    pick (e) {
        (EW)             { exit 90i32; },
        (HeapBadRequest) { exit 91i32; },
        (HeapOom)        { exit 92i32; },
        (Unreachable)    { exit 95i32; },
        (WildLeak)       { exit 96i32; },
        (StackExhausted) { exit 106i32; },
        (MachineFault)   { exit 107i32; },
        (*)              { exit 99i32; }
    }
    exit 9i32;
};
"""

# A program that writes `text` to fd 1 and exits 0. `sys(1, 1, ptr, len)` is
# `write` -- the compiler's `lib/nio.npk` is off limits (B-10: not the
# compiler's `lib/`), so the syscall is spelled directly, exactly as this
# repository's own `probe03` and `probe08` spell `clock_gettime` and `readlink`.
WRITER = """mod:%(mod)s;

error:EW;

func:main = int32(cstring[]:_~argv) {
    cstring:s = to_cstring("%(text)s") ?! EW;
    int64:n = sys(1i64, 1i64, s.ptr, s.len) ?! EW;
    if (n != %(len)di64) { exit 3i32; }
    exit 0i32;
};
""" + FAILSAFE_EW

TRIVIAL = """mod:%(mod)s;

func:main = int32(cstring[]:_~argv) {
    exit %(code)si32;
};
""" + FAILSAFE

# The wide literal, measured at pin `0dfddac`: exactly two codes,
# `NITPICK-LEX-004` (the lexer refuses the token) and `NITPICK-PARSE-002` (the
# parser is then left with no expression where one was required). Cases 2 and 3
# are the two ways a header can disagree with that pair.
WIDE_LITERAL = """mod:%(mod)s;

func:main = int32(cstring[]:_~argv) {
    int128:x = 9223372036854775808i128;
    if (x > 0i128) { exit 1i32; }
    exit 0i32;
};
""" + FAILSAFE

MANIFEST = """# GENERATED by harness/selfcheck.py. Never committed.
[project]
name        = "selfcheck"
version     = "0.0.0"
description = "a scratch tree with one planted fault"
target      = "library"

[build]
entry     = "src/lib.npk"
output    = "build/libselfcheck"
opt-level = 0

[toolchain]
llvm          = "%(llvm)s"
triple        = "%(triple)s"
datalayout    = "%(datalayout)s"
llc-flags     = %(llc)s
llc-opt-flags = %(llcopt)s
opt-flags     = %(opt)s
lld-flags     = %(lld)s

[dependencies]
"""

TEST_ENTRY = """
[[test]]
name  = "%(name)s"
stage = "%(stage)s"
path  = "%(path)s"
"""

WRAPPER = '''#!/usr/bin/env python3
"""GENERATED by harness/selfcheck.py -- an `npkc` that DELETES the handler.

Runs the real compiler, then renames `@npk_failsafe`'s define in the emitted IR
so the program genuinely has no handler while `npkc` reports success. That is
the shape `npkc` exit 0 had before the compiler's DEF-5 (O-N11, TM-112), and it
is the only way left to drive `build_program`'s `require_failsafe` belt.
"""
import os
import subprocess
import sys

real = os.environ["NTIME_SELFCHECK_REAL_NPKC"]
st = subprocess.run([real] + sys.argv[1:]).returncode
out = None
argv = sys.argv[1:]
for i, a in enumerate(argv):
    if a == "-o" and i + 1 < len(argv):
        out = argv[i + 1]
if st == 0 and out and os.path.isfile(out):
    with open(out, "r", encoding="utf-8") as fh:
        text = fh.read()
    # THE NEW NAME REPLACES THE PREFIX, and that is not a stylistic choice. The
    # first attempt appended a suffix -- `@npk_failsafe_DELETED` -- and the
    # belt's `text.count("\\ndefine i32 @npk_failsafe")` still matched it, so
    # the fault was planted and the check sailed past. The self-check caught
    # its own fixture being ineffective, which is the shape it exists to catch
    # everywhere else.
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(text.replace("\\ndefine i32 @npk_failsafe",
                              "\\ndefine i32 @DELETED_BY_SELFCHECK_failsafe"))
sys.exit(st)
'''


# ---------------------------------------------------------------------------
# building a scratch tree
# ---------------------------------------------------------------------------

# Every layer `BUILD.md` B-17 names. A scratch tree carries all six because
# `check_layering` asserts the NODES as well as the edges from cycle 0.0.6
# (D1): a control missing one would be red for a reason that is not its plant.
LAYERS = ("core", "cal", "span", "zone", "fmt", "host")


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # `newline=""` (cycle 0.1.5): a planted lone CR is written as the one byte
    # it is, on every platform, because the reader it tests reads bytes.
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def make_tree(where, man, files, entries):
    """A minimal tree: the pinned manifest, an empty umbrella, and `files`.

    THE TOOLCHAIN VALUES ARE COPIED FROM THE REAL MANIFEST, never retyped. A
    scratch tree pinned to a different LLVM would make every inner run's red
    ambiguous -- and the pin is an assertion (D-204), so it has to be the same
    assertion here.
    """
    if os.path.isdir(where):
        shutil.rmtree(where)
    tc = man["toolchain"]

    def arr(xs):
        return "[" + ", ".join('"%s"' % x for x in xs) + "]"

    text = MANIFEST % {
        "llvm": tc["llvm"], "triple": tc["triple"],
        "datalayout": tc["datalayout"], "llc": arr(tc["llc-flags"]),
        "llcopt": arr(tc["llc-opt-flags"]), "opt": arr(tc["opt-flags"]),
        "lld": arr(tc["lld-flags"]),
    }
    for name, stage, path in entries:
        text += TEST_ENTRY % {"name": name, "stage": stage, "path": path}
    _write(os.path.join(where, "nitpick.toml"), text)
    _write(os.path.join(where, "src", "lib.npk"),
           "// GENERATED by selfcheck.py. The umbrella, re-exporting nothing.\n"
           "mod:lib;\n")
    # AND ONE MODULE PER LAYER B-17 NAMES. `check_layering` asserts the NODES
    # as well as the edges from cycle 0.0.6 (D1), so a scratch tree without
    # them is red for a reason that is not its plant -- which it was, on this
    # assertion's first run, in every one of the eight cases at once.
    for layer in LAYERS:
        _write(os.path.join(where, "src", layer, layer + ".npk"),
               "mod:%s;\n" % layer)
    # THE SCRATCH TREE IS A MINIATURE OF THIS REPOSITORY, NOT JUST OF ITS CODE.
    # The tree checks DIFF AGAINST DOCUMENTS -- `check_error_budget` parses
    # `SAFETY.md` §2's table rather than carrying a copy of it -- so a tree with
    # no `meta/` is a tree where that check cannot run, and a check that cannot
    # run is a failure. Without this, every inner run was red for a reason that
    # had nothing to do with its planted fault.
    _write(os.path.join(where, "meta", "specs", "SAFETY.md"), MINI_SAFETY)
    for rel, body in files:
        _write(os.path.join(where, rel), body)
    return where


def invoke(where, extra_env=None, args=()):
    """Run THIS runner against `where`. Returns `(status, output, verdicts)`."""
    verdicts_path = os.path.join(where, "verdicts.txt")
    env = dict(os.environ)
    env.update(extra_env or {})
    argv = [sys.executable, os.path.join(HARNESS, "run.py"),
            "--root", where, "--verdicts", verdicts_path] + list(args)
    # NO SHELL AND NO PIPELINE. `$?` after a pipeline is the last command's
    # status, and this function's whole job is to return a status that is the
    # runner's own.
    #
    # AND `env=env` IS PASSED, which it was not on the first draft. The
    # environment was built and dropped, so case 8 -- whose whole fault is
    # injected through `$NPKC` -- ran the CONTROL twice and reported that the
    # harness had not caught its planted fault. It was right: nothing had been
    # planted. A constructed environment that is never handed over is the same
    # defect TM-120 is about, arriving one level up.
    p = subprocess.run(argv, env=env, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    out = p.stdout.decode("utf-8", "replace")
    verdicts = []
    if os.path.isfile(verdicts_path):
        with open(verdicts_path, "r", encoding="utf-8") as fh:
            verdicts = fh.read().splitlines()
    return p.returncode, out, verdicts


# ---------------------------------------------------------------------------
# the assertion a case makes
# ---------------------------------------------------------------------------

class Case:
    """One V-14 case: the planted fault, the control beside it, and the verdict."""

    def __init__(self, num, title):
        self.num = num
        self.title = title
        self.problems = []

    def red(self, status, out):
        if status == 0:
            self.problems.append(
                "the inner run exited 0. THE HARNESS DID NOT NOTICE THE "
                "PLANTED FAULT, which is the only thing this case exists to "
                "find out.\n%s" % _indent(out))
        elif status != 1:
            self.problems.append(
                "the inner run exited %d; a red run is exit 1 (2 is a usage "
                "error, which means the case built a tree the runner would not "
                "accept).\n%s" % (status, _indent(out)))

    def fails(self, verdicts, rel):
        if not any(v.startswith("FAIL " + rel) for v in verdicts):
            self.problems.append(
                "no `FAIL %s` verdict. The faulted file was not reported as a "
                "failing unit.\n      verdicts: %s" % (rel, verdicts or "none"))

    def passes(self, verdicts, rel):
        """THE CONTROL. Without it a red proves only that SOMETHING broke."""
        if not any(v.startswith("PASS " + rel) for v in verdicts):
            self.problems.append(
                "no `PASS %s` verdict. The correct twin beside the fault did "
                "NOT come back green, so the red above is not evidence that "
                "the harness caught the planted fault -- it is evidence that "
                "something in the scratch tree is wrong.\n      verdicts: %s"
                % (rel, verdicts or "none"))

    def says(self, out, needle):
        if needle not in out:
            self.problems.append(
                "the run never said %r. A check that fails without naming what "
                "it caught is a check somebody debugs by bisection."
                % needle)

    def silent_about(self, out, needle):
        if needle in out:
            self.problems.append(
                "the run mentioned %r, and this case requires it not to."
                % needle)


def _indent(text):
    return "\n".join("      " + l for l in text.rstrip().splitlines()[-25:])


# ---------------------------------------------------------------------------
# PART A -- V-14's cases, each a full inner run of this runner
# ---------------------------------------------------------------------------

def case_1_wrong_exit(root, man, base):
    c = Case(1, "a `program` case whose `expect-exit` is wrong by one")
    where = make_tree(
        os.path.join(base, "case1"), man,
        [("tests/unit/good_exit.npk",
          "// expect-exit: 7\n" + TRIVIAL % {"mod": "good_exit", "code": "7"}),
         ("tests/unit/bad_exit.npk",
          "// expect-exit: 8\n" + TRIVIAL % {"mod": "bad_exit", "code": "7"})],
        [("unit", "program", "tests/unit")])
    st, out, v = invoke(where)
    c.red(st, out)
    c.fails(v, "tests/unit/bad_exit.npk")
    c.passes(v, "tests/unit/good_exit.npk")
    c.says(out, "exited 7; the header expects 8")
    return c


def case_2_missing_code(root, man, base):
    c = Case(2, "a `check` case expecting a code the compiler does not report")
    where = make_tree(
        os.path.join(base, "case2"), man,
        [("tests/rejection/good_codes.npk",
          "// expect-error: NITPICK-LEX-004\n"
          "// expect-error: NITPICK-PARSE-002\n"
          + WIDE_LITERAL % {"mod": "good_codes"}),
         ("tests/rejection/bad_codes.npk",
          "// expect-error: NITPICK-LEX-004\n"
          "// expect-error: NITPICK-PARSE-002\n"
          "// expect-error: NITPICK-TYPE-009\n"
          + WIDE_LITERAL % {"mod": "bad_codes"})],
        [("rejection", "check", "tests/rejection")])
    st, out, v = invoke(where)
    c.red(st, out)
    c.fails(v, "tests/rejection/bad_codes.npk")
    c.passes(v, "tests/rejection/good_codes.npk")
    c.says(out, "expected and not reported: NITPICK-TYPE-009")
    return c


def case_3_unexpected_code(root, man, base):
    c = Case(3, "a `check` case reporting a code no expectation names (D-237)")
    where = make_tree(
        os.path.join(base, "case3"), man,
        [("tests/rejection/good_codes.npk",
          "// expect-error: NITPICK-LEX-004\n"
          "// expect-error: NITPICK-PARSE-002\n"
          + WIDE_LITERAL % {"mod": "good_codes"}),
         # THE HISTORICAL SPECIMEN: `probe02d`'s header as it stood until cycle
         # 0.0.2 -- one `expect-error:` above a body that reports two codes.
         ("tests/rejection/bad_codes.npk",
          "// expect-error: NITPICK-LEX-004\n"
          + WIDE_LITERAL % {"mod": "bad_codes"})],
        [("rejection", "check", "tests/rejection")])
    st, out, v = invoke(where)
    c.red(st, out)
    c.fails(v, "tests/rejection/bad_codes.npk")
    c.passes(v, "tests/rejection/good_codes.npk")
    c.says(out, "reported and not expected: NITPICK-PARSE-002")
    c.says(out, "B-7: the set reported must EQUAL the set expected")
    return c


def case_4_golden_off_by_one_byte(root, man, base):
    c = Case(4, "a `golden` case whose bytes differ by one byte")
    where = make_tree(
        os.path.join(base, "case4"), man,
        [("tests/golden/good_bytes.npk",
          "// expect-exit: 0\n// expect-golden: good_bytes\n"
          + WRITER % {"mod": "good_bytes", "text": "hello\\n", "len": 6}),
         ("tests/golden/good_bytes.txt", "hello\n"),
         ("tests/golden/bad_bytes.npk",
          "// expect-exit: 0\n// expect-golden: bad_bytes\n"
          + WRITER % {"mod": "bad_bytes", "text": "hello\\n", "len": 6}),
         # ONE byte different: `hellp` for `hello`. Same length, so a check
         # comparing sizes would pass it.
         ("tests/golden/bad_bytes.txt", "hellp\n")],
        [("golden", "golden", "tests/golden")])
    st, out, v = invoke(where)
    c.red(st, out)
    c.fails(v, "tests/golden/bad_bytes.npk")
    c.passes(v, "tests/golden/good_bytes.npk")
    c.says(out, "first difference at byte 4")
    return c


def case_5_does_not_parse(root, man, base):
    c = Case(5, "a `parse` case that does not parse")
    where = make_tree(
        os.path.join(base, "case5"), man,
        # UNDER `src/`, WHERE NOTHING ELSE ROOTS IT. `src/lib.npk` re-exports
        # nothing, so the module graph does not reach these two and no
        # `[[test]]` entry selects them. The parse stage is the ONLY thing in
        # the harness that opens them -- which is the whole argument for the
        # stage covering the tree rather than a directory.
        [("src/cal/cal.npk", "mod:cal;\n"),
         ("src/zone/zone.npk",
          "mod:zone;\n\nfunc:main = int32(cstring[]:_~argv) {\n"
          "    this is not a program at all ((( ;\n};\n")],
        [("unit", "program", "tests/unit")])
    # The tree has no `tests/unit/`, so the entry itself is a second red. Drop
    # it: this case is about the parse stage and nothing else.
    _write(os.path.join(where, "tests", "unit", "ok.npk"),
           "// expect-exit: 0\n" + TRIVIAL % {"mod": "ok", "code": "0"})
    st, out, v = invoke(where)
    c.red(st, out)
    c.says(out, "FAIL  parse: src/zone/zone.npk")
    c.says(out, "the parser refused it")
    c.silent_about(out, "parse: src/cal/cal.npk")
    c.passes(v, "tests/unit/ok.npk")
    return c


def case_6_generator_off_by_one_line(root, man, base):
    """PENDING until cycle 0.5, and it prints as pending rather than passing."""
    return None


def case_7_sweep_silently_skipped(root, man, base):
    c = Case(7, "a `sweep` case that is silently skipped")
    where = make_tree(
        os.path.join(base, "case7"), man,
        [("tests/unit/sweep/good_sweep.npk",
          "// expect-exit: 0\n// sweep-count: 10\n"
          + WRITER % {"mod": "good_sweep", "text": "swept 10\\n", "len": 9}),
         # THE FAULT: a sweep that returns after three cases and exits 0. Its
         # exit code is indistinguishable from the one that did the work, which
         # is exactly why the evidence has to be a COUNT.
         ("tests/unit/sweep/bad_sweep.npk",
          "// expect-exit: 0\n// sweep-count: 10\n"
          + WRITER % {"mod": "bad_sweep", "text": "swept 3\\n", "len": 8})],
        [("sweep", "sweep", "tests/unit/sweep")])
    st, out, v = invoke(where)
    c.red(st, out)
    c.fails(v, "tests/unit/sweep/bad_sweep.npk")
    c.passes(v, "tests/unit/sweep/good_sweep.npk")
    c.says(out, "swept 3 of the 10 its header declares")
    c.says(out, "7 case(s) were NOT visited")

    # AND THE OTHER HALF OF THE SAME CASE: `--quick` skips the stage, and it
    # must say so THROUGH THE REPORT -- so the transcript and the summary agree
    # -- and must refuse to call the run plain GREEN.
    st2, out2, v2 = invoke(where, args=["--quick"])
    if st2 != 0:
        c.problems.append(
            "under `--quick` the same tree exited %d. The faulted sweep is the "
            "only fault in it, so skipping the stage must leave the run green "
            "-- otherwise the skip is not what made the difference.\n%s"
            % (st2, _indent(out2)))
    c.says(out2, "THE EXHAUSTIVE GATE DID NOT RUN")
    c.says(out2, "*** --quick: THIS RUN CONCLUDES NOTHING.")
    c.says(out2, "THIS CONCLUDES NOTHING")
    if not any(x.startswith("SKIP ") for x in v2):
        c.problems.append(
            "`--quick` wrote no `SKIP` line into the verdicts file. The skip "
            "must travel through the same `Report` object as every other "
            "verdict, or the summary and the transcript can disagree about "
            "what ran -- which is the failure `--verdicts` exists to make "
            "impossible.\n      verdicts: %s" % (v2 or "none"))
    if "GREEN --" in out2:
        c.problems.append(
            "a `--quick` run printed the unqualified `GREEN --` summary. B-9: "
            "nothing is concluded from a run that skipped the exhaustive gate.")
    return c


def case_8_failsafe_deleted(root, man, base, npkc):
    c = Case(8, "a program whose `failsafe` has been deleted")
    wrapper = os.path.join(base, "npkc_no_failsafe.py")
    _write(wrapper, WRAPPER)
    os.chmod(wrapper, 0o755)
    where = make_tree(
        os.path.join(base, "case8"), man,
        [("tests/unit/handler.npk",
          "// expect-exit: 0\n" + TRIVIAL % {"mod": "handler", "code": "0"})],
        [("unit", "program", "tests/unit")])

    # THE NEGATIVE: the same tree, compiled by an `npkc` that renames the
    # handler's define after emitting it.
    st, out, v = invoke(where, extra_env={
        "NPKC": wrapper, "NTIME_SELFCHECK_REAL_NPKC": npkc})
    c.red(st, out)
    c.fails(v, "tests/unit/handler.npk")
    c.says(out, "the emitted IR defines no @npk_failsafe")

    # THE POSITIVE, THROUGH THE IDENTICAL CODE PATH. The same tree and the same
    # runner with the real compiler must be green -- so the red above came from
    # the deleted handler and not from the mechanism that deleted it.
    st2, out2, v2 = invoke(where)
    if st2 != 0:
        c.problems.append(
            "the control run -- same tree, real `npkc` -- exited %d. The red "
            "above is then not evidence about the missing handler.\n%s"
            % (st2, _indent(out2)))
    if not any(x.startswith("PASS tests/unit/handler.npk") for x in v2):
        c.problems.append(
            "the control run did not pass `tests/unit/handler.npk`.\n"
            "      verdicts: %s" % (v2 or "none"))
    return c


def _target_case(c, root, man, base, name, fault):
    """A manifest-level fault, and its control through the identical code path:
    the same tree with the real manifest's rows must come back green, so the
    red came from the planted pin and not from the tree (V-14b). `fault` maps
    the generated manifest's text to the faulted one."""
    where = make_tree(
        os.path.join(base, name), man,
        [("tests/unit/fine.npk",
          "// expect-exit: 0\n" + TRIVIAL % {"mod": "fine", "code": "0"})],
        [("unit", "program", "tests/unit")])
    toml = os.path.join(where, "nitpick.toml")
    with open(toml, "r", encoding="utf-8") as fh:
        good = fh.read()
    bad = fault(good)
    if bad == good:
        c.problems.append("the fault changed nothing in the scratch manifest; "
                          "the case planted nothing")
        return None
    _write(toml, bad)
    st, out, v = invoke(where)
    c.red(st, out)
    _write(toml, good)
    st2, out2, v2 = invoke(where)
    if st2 != 0 or not any(x.startswith("PASS tests/unit/fine.npk")
                           for x in v2):
        c.problems.append(
            "the control run -- the same tree with the real manifest's pins -- "
            "exited %d or did not pass `tests/unit/fine.npk`. The red above is "
            "then not evidence about the pin.\n%s" % (st2, _indent(out2)))
    return out, v


def case_10_layout_pin_wrong(root, man, base):
    c = Case(10, "a manifest whose layout pin is not what the pinned opt derives")
    # One field of the layout dropped (TM-209, BUILD.md B-1a): the compiler's
    # `check_datalayout_pin`, ported -- a stated layout proves nothing about
    # itself, because `opt` keeps a wrong one as written and `llc` accepts one
    # in silence.
    got = _target_case(c, root, man, base, "case10",
                       lambda t: t.replace("-n8:16:32:64-S128", "-n8:16:32-S128"))
    if got:
        c.says(got[0], "but the pinned `opt` derives")
    return c


def case_11_other_target(root, man, base):
    c = Case(11, "a tree pinned consistently to another target")
    # `i686-unknown-linux-gnu` and the layout the pinned `opt` derives for it
    # (measured at cycle 0.2.0a's planning), so case 10's check PASSES and only
    # the header belt can see that every module this compiler emits states
    # x86-64 (TM-209): the compiler's `check_module_header`, ported.
    got = _target_case(
        c, root, man, base, "case11",
        lambda t: t.replace('"x86_64-unknown-linux-gnu"',
                            '"i686-unknown-linux-gnu"')
                   .replace('"e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-'
                            'i128:128-f80:128-n8:16:32:64-S128"',
                            '"e-m:e-p:32:32-p270:32:32-p271:32:32-p272:64:64-'
                            'i128:128-f64:32:64-f80:32-n8:16:32-S128"'))
    if got:
        c.fails(got[1], "tests/unit/fine.npk")
        c.says(got[0], "the module's header is not the pinned one")
        c.says(got[0], "i686-unknown-linux-gnu")
    return c


# TWO SITES OF ONE CODE, measured at cycle 0.2.0a's planning at `5fbaf4a` and at
# `c970483`: `NITPICK-TYPE-007` at 4:5 and at 5:5 -- two initialisers of the
# wrong type, each its own report. Cases 12 and 13 are the two ways a header
# can disagree with that COUNT while agreeing with its SET (TM-210).
TWO_SITES = """mod:%(mod)s;

func:main = int32(cstring[]:_~argv) {
    int32:a = true;
    int32:b = true;
    exit 0i32;
};
""" + FAILSAFE


def _sites_case(c, man, base, name, bad_lines, bad_name):
    good = "// expect-error: NITPICK-TYPE-007\n" * 2
    where = make_tree(
        os.path.join(base, name), man,
        [("tests/rejection/good_sites.npk",
          good + TWO_SITES % {"mod": "good_sites"}),
         ("tests/rejection/%s.npk" % bad_name,
          "// expect-error: NITPICK-TYPE-007\n" * bad_lines
          + TWO_SITES % {"mod": bad_name})],
        [("rejection", "check", "tests/rejection")])
    st, out, v = invoke(where)
    c.red(st, out)
    c.fails(v, "tests/rejection/%s.npk" % bad_name)
    c.passes(v, "tests/rejection/good_sites.npk")
    return out


def case_12_code_named_once(root, man, base):
    c = Case(12, "a `check` case naming a code once where it is reported at two sites")
    # Under B-7's set equality this PASSES -- the code is named and reported.
    # `probe15`, `probe11c`, `probe14` and `generic_owning_copy/case5` each
    # named their code once for two to four sites until cycle 0.2.0a (F24).
    c.says(_sites_case(c, man, base, "case12", 1, "one_line"),
           "and 1 `expect-error` line(s) name it")
    return c


def case_13_silent_site(root, man, base):
    c = Case(13, "a `check` case naming a code at three sites where it is reported at two")
    # The compiler's own `silent_site` self-check case (D-332), ported: a site
    # the compiler stopped reporting is invisible to a set, and to lines that
    # carry no position.
    c.says(_sites_case(c, man, base, "case13", 3, "three_lines"),
           "and 3 `expect-error` line(s) name it")
    return c


# CASE 9's SPECIMEN (cycle 0.1.4b, TM-187). HELD keeps one 4096-byte managed
# buffer live to its exit, so the runtime reports `allocated=4096
# peak_live=4096 count=1` -- measured at `c3bdae2` on both legs, and the
# arithmetic of the one line that allocates. With CLOSE_STDERR it closes fd 2
# before it exits, so the report has nowhere to go and the harness must call
# that no measurement, never a pass.
HELD = """mod:%(mod)s;

error:EW;

func:main = int32(cstring[]:_~argv) {
    buffer:held = buffer_new(4096i64);
    if (held.len != 4096i64) { exit 3i32; }
%(tail)s    exit 0i32;
};
""" + FAILSAFE_EW

CLOSE_STDERR = """    int64:r = sys(3i64, 2i64) ?! EW;
    if (r != 0i64) { exit 4i32; }
"""


def case_9_memory_disagrees(root, man, base):
    c = Case(9, "a program whose managed memory disagrees with its header")

    def held(mod, markers, tail=""):
        return ("// expect-exit: 0\n"
                + "".join("// %s\n" % m for m in markers)
                + HELD % {"mod": mod, "tail": tail})
    where = make_tree(
        os.path.join(base, "case9"), man,
        [
            # THE CONTROL: every field held at BOTH of its bounds, and the
            # belt at a cap the runtime starts under -- so each comparison is
            # shown inclusive, and the reds below are about the plants.
            ("tests/unit/heap_held.npk", held("heap_held", [
                "heap: allocated <= 4096", "heap: allocated >= 4096",
                "heap: peak_live <= 4096", "heap: peak_live >= 4096",
                "heap: count <= 1", "heap: count >= 1",
                "cap: 65536 KiB, exit 0"])),
            # A CEILING ONE BYTE UNDER THE MEASUREMENT.
            ("tests/unit/heap_over.npk", held("heap_over", [
                "heap: peak_live <= 4095"])),
            # A FLOOR ONE ALLOCATION OVER IT -- the other operator, another field.
            ("tests/unit/heap_under.npk", held("heap_under", [
                "heap: count >= 2"])),
            # NO LINE AT ALL: fd 2 closed before the exit that would print it.
            ("tests/unit/heap_silent.npk", held("heap_silent", [
                "heap: peak_live <= 8192"], CLOSE_STDERR)),
            # THE BELT'S EXIT WRONG: clean under the cap, and the header says
            # it takes HeapOom there.
            ("tests/unit/cap_exit.npk", held("cap_exit", [
                "cap: 65536 KiB, exit 92"])),
            # A CAP NOTHING STARTS UNDER -- 1 KiB, on any machine -- so the
            # floor program fails first and the unit must say so (TM-131).
            ("tests/unit/cap_machine.npk", held("cap_machine", [
                "cap: 1 KiB, exit 0"])),
        ],
        [("unit", "program", "tests/unit")])
    st, out, v = invoke(where)
    c.red(st, out)
    for stem in ("heap_over", "heap_under", "heap_silent", "cap_exit",
                 "cap_machine"):
        c.fails(v, "tests/unit/%s.npk" % stem)
    c.passes(v, "tests/unit/heap_held.npk")
    c.says(out, "peak_live is 4096; the header bounds it <= 4095")
    c.says(out, "count is 1; the header bounds it >= 2")
    c.says(out, "line on stderr and found 0")
    c.says(out, "exited 0; the header expects exit 92")
    c.says(out, "the cap measures the RUNTIME")
    c.says(out, "heap allocated=4096 peak_live=4096 count=1 on both legs, "
                "exit 0 under 65536 KiB on both legs")
    return c


# ---------------------------------------------------------------------------
# PART B -- the tree checks, each shown red on a planted violation
# ---------------------------------------------------------------------------

# A minimal `SAFETY.md` §2, because `check_error_budget` READS the document
# rather than a transcription of it -- so a scratch tree needs one to read.
MINI_SAFETY = """# Safety

## 2. The error budget

| Error | Raised when |
|---|---|
| `ETimeValue` | a value is not a representable, real time |
| `ETimeParse` | input text did not match the format asked for |
| `ETimeZone` | a zone name is not in the compiled table |

| Module | Declares |
|---|---|
| `ntime/cal.npk` | `ETimeValue` |
| `ntime/zone.npk` | `ETimeZone` |
| `ntime/fmt.npk` | `ETimeParse` |

## 3. Purity
"""


# THE SWEEP TAG, ASSEMBLED AT RUN TIME AND NEVER WRITTEN OUT HERE. A tag
# spelled out in this file would be a LIVE tag in the tree, and
# `check_denominators` would fail the real run on its own fixture -- which is
# how `check_specs_current` ended up with a whole-file exemption for this file
# that can never expire (the audit's B3). Building the marker from a format
# string leaves nothing here for the scanner to match, so the fixture needs no
# exemption at all. That is the shape to reach for first.
#
# It caught the first draft of THIS COMMENT, which spelled the tag out to
# explain why it must not be spelled out.
_TAG = "[[" + "sweep: %s=%d" + "]]"

# The `.npk` a `_mini_tree` holds: `src/lib.npk` plus one per layer. DERIVED,
# because a control whose expected number is typed by hand is the thing this
# check exists to catch, and a later session adding a seventh layer should get
# a green run and not a puzzle.
_MINI_NPK = 1 + len(LAYERS)


def _mini_tree(where, files, skip_layers=()):
    if os.path.isdir(where):
        shutil.rmtree(where)
    _write(os.path.join(where, "src", "lib.npk"), "mod:lib;\n")
    for layer in LAYERS:
        if layer in skip_layers:
            continue
        _write(os.path.join(where, "src", layer, layer + ".npk"),
               "mod:%s;\n" % layer)
    _write(os.path.join(where, "meta", "specs", "SAFETY.md"), MINI_SAFETY)
    for rel, body in files:
        _write(os.path.join(where, rel), body)
    return where


def _div_tree(expr):
    """`src/cal/cal.npk` for one of `check_literal_divisors`' rows: a function
    whose body divides as `expr`, beside a `use` PATH and a COMMENT that hold a
    `/` and a `%` each.

    The two are the shapes the real `cal.npk` has -- five `use
    "../core/limits.npk"` lines, and a header that explains C-11 in prose -- so
    a check that read strings or prose would fail the repository on its own
    imports and its own documentation (`check_purity`'s first-run lesson).
    Every control built here is therefore also the proof that it does not.
    Concatenated rather than `%`-formatted, because the fixture is full of `%`.
    """
    return ("mod:cal;\n"
            "use \"../core/limits.npk\".NTIME_DAY_MIN;\n"
            "// IN PROSE, NOT CODE: y / m, y % 0i64 and x /= m divide by nothing\n"
            "func:f = int64(int64:y, int64:m) never fails { pass "
            + expr + "; };\n")


# ---- CYCLE 0.2.3a: THE FAMILY'S THREE NEW MEMBERS ---------------------------
#
# `check_check_registry` (TM-201) reads four texts -- `TESTING.md` §2's two
# tables and `harness/checks.py`, `arms.py` and `run.py` -- so each of its rows
# below plants a STUB of each, never imported, and drifts ONE statement. The
# consistent family is four checks: `check_a` live in `LIVE`, `check_b` and
# `check_c` driven by `run.py` (one defined there, one in `arms.py`, called
# through `arms_mod`), and `check_p` pending at cycle 0.9.
def _family(rows=("check_a", "check_b", "check_c", "check_p"),
            doc_pending=(("check_p", "0.9"),), live=("check_a",),
            pending=(("check_p", "0.9"),), run_defs=("check_b",),
            run_calls=("check_b", "arms_mod.check_c")):
    """The four statements as a list of `(rel, text)` stubs."""
    doc = ("# Testing\n\n## 2. What the harness checks about the tree\n\n"
           "| Check | Diffs |\n|---|---|\n"
           + "".join("| `%s` | the stub's %s |\n" % (r, r) for r in rows)
           + "\n**Rule V-1a.** The pending ones:\n\n"
           "| Pending | Live from | Why not now |\n|---|---|---|\n"
           + "".join("| `%s` | %s | nothing to check |\n" % p for p in doc_pending)
           + "\n## 3. The next section\n")
    checks = ("".join("def %s(tree, **_):\n    return None\n\n\n" % n
                      for n in sorted(set(live) | {"check_a"}))
              + "LIVE = (\n" + "".join("    %s,\n" % n for n in live) + ")\n\n"
              + "PENDING = (\n"
              + "".join("    (%r, %r, \"nothing to check\"),\n" % p
                        for p in pending) + ")\n")
    run = ("".join("def %s(rep, root):\n    return None\n\n\n" % n
                   for n in run_defs)
           + "def run_tree_checks(rep, root):\n    return None\n\n\n"
           + "def main(argv):\n"
           + "".join("    %s(None, None)\n" % c for c in run_calls)
           + "    run_tree_checks(None, None)\n    return 0\n")
    arms = "def check_c(tree, **_):\n    return None\n"
    return [("meta/specs/TESTING.md", doc), ("harness/checks.py", checks),
            ("harness/run.py", run), ("harness/arms.py", arms)]


# A FUNCTION IN `src/fmt/`, the first code that could want a view back (cycle
# 0.4's parsers): `check_no_view_returns` (TM-204) is planted with each shape
# it reads as a view -- a `uint8[]`, a slice of anything else, a `cstring`, a
# struct holding a slice, and one handed back inside a `Vec` -- beside the same
# function returning what owns nothing: a `string`, a fixed array, a struct of
# integers, a `Vec<int64>`. A fixed `int64[4]` is a value, not a view, which
# is what the second row's control is for.
def _fmt(decl):
    return ("src/fmt/fmt.npk", "mod:fmt;\n" + decl + "\n")


# `check_int128_sites` (O-X6) reads `SPAN_MODEL.md` §5's `int128` column, so
# each row plants a stub of it beside `src/span/span.npk`. `_wide` is a
# function that computes in `int128`, the shape `probe02`'s `ns_add_checked`
# has; `_narrow` the same in `int64`.
def _span5(rows):
    return ("meta/specs/SPAN_MODEL.md",
            "# Spans\n\n## 5. Where the arithmetic can overflow\n\n"
            "| Site | Risk | Answer | `int128` |\n|---|---|---|---|\n"
            + "".join("| %s | the stub's | the stub's | %s |\n" % r for r in rows)
            + "\n## 6. Open items\n")


def _wide(name):
    return ("func:%s = int64(int64:a, int64:b) never fails {\n"
            "    int128:w = (a => int128) + (b => int128);\n"
            "    pass w =>! int64;\n};\n" % name)


def _narrow(name):
    return ("func:%s = int64(int64:a, int64:b) never fails {\n"
            "    pass a + b;\n};\n" % name)


# `check_constants_named` READS A LITERAL AS THE COMPILER'S LEXER DOES (cycle
# 0.2.3a, TM-231). Twelve rows plant one spelling the pinned compiler reads as
# 86 400 -- one of them as its negation -- in `span`, where the number is
# `core`'s, beside the SAME spelling one higher, so a check that fired on the
# shape rather than on the value fails its control. Two are the other way
# round, their GOOD column the point: `86400hexi64` is 549 888 and a string's
# text is no number, and the check before TM-231 fired on both. The last plants
# a token the lexer refuses, beside a hex literal it reads.
def _div(expr):
    return ("src/span/span.npk",
            "mod:span;\nfunc:f = int64(int64:s) never fails { pass s / %s; };\n"
            % expr)


def _loop(hi):
    return ("src/span/span.npk",
            "mod:span;\nfunc:f = int64(int64:s) never fails {\n"
            "    int64:last = 0i64;\n"
            "    for (int64:k in 0i64...%s) { last = k; }\n"
            "    pass last;\n};\n" % hi)


# Each row: the check, the file that violates it, the file that does not, and a
# fragment the finding must name. The CLEAN column is not decoration -- several
# of these checks are one predicate away from failing this repository's own
# documentation, and two of them would have on their first run: `mono_now()`
# appears in `src/host/host.npk`'s header and `host_now_utc` in
# `src/lib.npk`'s, both in PROSE. The clean column is where that is asserted.
PLANTED = [
    # A TAGGED DENOMINATOR THAT NO LONGER MATCHES THE TREE (TM-142). The
    # mini-tree holds two `.npk` -- `src/lib.npk` and the plant -- so the
    # control's `2` is derived and not chosen, and a change to `_mini_tree`
    # that added a file would redden this row rather than pass it.
    (checks_mod.check_denominators,
     ("src/cal/cal.npk",
      "mod:cal;\n// " + _TAG % ("npk_total", 999) + "\n"),
     ("src/cal/cal.npk",
      "mod:cal;\n// " + _TAG % ("npk_total", _MINI_NPK) + "\n"),
     "the tree says %d" % _MINI_NPK),
    # AND A TAG NAMING A DENOMINATOR NOTHING MEASURES, which is the other way
    # the marker can be wrong: a typo excused by nobody noticing.
    (checks_mod.check_denominators,
     ("src/cal/cal.npk",
      "mod:cal;\n// " + _TAG % ("npk_totl", _MINI_NPK) + "\n"),
     ("src/cal/cal.npk",
      "mod:cal;\n// " + _TAG % ("npk_total", _MINI_NPK) + "\n"),
     "which this sweep does not measure"),
    # AND A SWEEP'S DECLARED DOMAIN AGAINST A STATEMENT OF IT (cycle 0.1.2) --
    # TM-161's shape, a test and a document holding two values for one
    # quantity. The member declares 10 and the tag beside it says 11; one
    # file, so the row plants one file as every row does. The needle is the
    # MEASURED side, so a check that read the tag back as its own measurement
    # would not pass it.
    (checks_mod.check_denominators,
     ("tests/unit/sweep/tiny.npk",
      "// expect-exit: 0\n// sweep-count: 10\n// "
      + _TAG % ("domain_tiny", 11) + "\nmod:tiny;\n"),
     ("tests/unit/sweep/tiny.npk",
      "// expect-exit: 0\n// sweep-count: 10\n// "
      + _TAG % ("domain_tiny", 10) + "\nmod:tiny;\n"),
     "the tree says 10"),
    # AND AN ARM BILL A DOCUMENT WRITES (the close's second half, the audit's
    # C6; TM-205). The mini-tree's `cal` is `mod:cal;` alone and owes the
    # floor, so a tag one higher is stale -- the floor's size DERIVED from
    # `arms.FLOOR`, never typed, for `_MINI_NPK`'s reason.
    (checks_mod.check_denominators,
     ("src/cal/cal.npk",
      "mod:cal;\n// " + _TAG % ("arms_cal", len(arms_mod.FLOOR) + 1) + "\n"),
     ("src/cal/cal.npk",
      "mod:cal;\n// " + _TAG % ("arms_cal", len(arms_mod.FLOOR)) + "\n"),
     "the tree says %d" % len(arms_mod.FLOOR)),
    (checks_mod.check_purity,
     ("src/cal/cal.npk", "mod:cal;\nfunc:f = int64() never fails "
                         "{ pass mono_now(); };\n"),
     ("src/cal/cal.npk", "mod:cal;\n// mono_now() is named here in PROSE, and\n"
                         "// `sys(` and `environ(` are too.\n"),
     "calls `mono_now` outside `src/host/`"),
    (checks_mod.check_host_isolation,
     ("src/cal/cal.npk", "mod:cal;\nfunc:f = int64() never fails "
                         "{ pass host_now_utc(); };\n"),
     ("src/lib.npk", "mod:lib;\npub use \"./host/host.npk\".host_now_utc;\n"),
     "names `host_now_utc`"),
    (checks_mod.check_layering,
     ("src/cal/cal.npk", "mod:cal;\nuse \"../zone/zone.npk\".*;\n"),
     ("src/cal/cal.npk", "mod:cal;\nuse \"../core/core.npk\".*;\n"),
     "B-17's arrows point one way"),
    (checks_mod.check_layering,
     ("src/cal/cal.npk", "mod:cal;\nuse \"../host/host.npk\".*;\n"),
     ("src/cal/cal.npk", "mod:cal;\nuse \"../core/core.npk\".*;\n"),
     "NOTHING imports `host`"),
    (checks_mod.check_error_budget,
     ("src/cal/cal.npk", "mod:cal;\npub error:ETimeOops;\n"),
     ("src/cal/cal.npk", "mod:cal;\npub error:ETimeValue;\n"),
     "three is a ceiling"),
    # 86400 IS `core`'S ALONE SINCE CYCLE 0.2.2 (TM-223): the plant is the
    # conversion's own module spelling it, the slip the map now refuses, and
    # the control is the one copy, declared where `src/core/limits.npk`
    # declares it. (The plant was `zone`'s and the control `cal`'s, the owner
    # then, until cycle 0.2.2.)
    (checks_mod.check_constants_named,
     ("src/span/span.npk", "mod:span;\nfunc:f = int64(int64:s) never fails "
                           "{ pass s / 86400i64; };\n"),
     ("src/core/limits.npk",
      "mod:limits;\npub fixed int64:NTIME_SECS_PER_DAY = 86400i64;\n"),
     "belongs to module `core`"),
    # 1 000 000 000 IS `core`'S ALONE SINCE CYCLE 0.2.3a (TM-232): the plant is
    # the old owner spelling it -- digit-separated, the spelling the check
    # could not read until TM-231 -- and the control the one copy, declared
    # where `src/core/limits.npk` declares it.
    (checks_mod.check_constants_named,
     ("src/cal/cal.npk", "mod:cal;\nfunc:f = int64(int64:n) never fails "
                         "{ pass n / 1_000_000_000i64; };\n"),
     ("src/core/limits.npk",
      "mod:limits;\npub fixed int64:NTIME_NANOS_PER_SEC = 1_000_000_000i64;\n"),
     "1000000000 as `1_000_000_000i64`, which belongs to module `core`"),
    # A `core` NUMBER IN `core` BUT NOT IN `limits.npk` (cycle 0.2.4a, the
    # cycle audit's C3): the check let a copy stand anywhere in the module,
    # and S-16 says the one copy is the file's. The control is the one copy.
    (checks_mod.check_constants_named,
     ("src/core/bytes.npk", "mod:bytes;\nfunc:f = int64(int64:s) never fails "
                            "{ pass s / 86400i64; };\n"),
     ("src/core/limits.npk",
      "mod:limits;\npub fixed int64:NTIME_SECS_PER_DAY = 86400i64;\n"),
     "is spelled in `src/core/limits.npk` alone"),
    # A `cal` NUMBER IN `core`: Hinnant's era constant is `src/cal/`'s.
    (checks_mod.check_constants_named,
     ("src/core/vec.npk", "mod:vec;\nfunc:f = int64(int64:z) never fails "
                          "{ pass z / 146097i64; };\n"),
     ("src/cal/cal.npk", "mod:cal;\nfunc:f = int64(int64:z) never fails "
                         "{ pass z / 146097i64; };\n"),
     "is spelled in `src/cal/` alone"),
    # A BOUND SPELLED BY ITS VALUE (C8): `limits.npk` declares the range's last
    # second, and `span` divides by the number rather than by the name.
    # The control divides by the second before it, which is no bound.
    (checks_mod.check_constants_named,
     [("src/core/limits.npk",
       "mod:limits;\npub fixed int64:NTIME_SECS_MAX = 253402300799i64;\n"),
      _div("253402300799i64")],
     [("src/core/limits.npk",
       "mod:limits;\npub fixed int64:NTIME_SECS_MAX = 253402300799i64;\n"),
      _div("253402300798i64")],
     "the value of the bound `NTIME_SECS_MAX`"),
    # THE FOLDED MINIMUM IS ITS VALUE, NEVER ITS PARTS: -2^63 spelled in
    # `int128` is the bound; the `0` and the `1` the fold is written with are
    # not, and the control holds both.
    (checks_mod.check_constants_named,
     [("src/core/limits.npk", "mod:limits;\npub fixed int64:NTIME_DURATION_NS_MIN"
                              " = (0i64 - 9223372036854775807i64) - 1i64;\n"),
      _div("9223372036854775808i128")],
     [("src/core/limits.npk", "mod:limits;\npub fixed int64:NTIME_DURATION_NS_MIN"
                              " = (0i64 - 9223372036854775807i64) - 1i64;\n"),
      ("src/span/span.npk", "mod:span;\nfunc:f = int64(int64:s) never fails "
                            "{ pass (s - 0i64) + 1i64; };\n")],
     "the value of the bound `NTIME_DURATION_NS_MIN`"),
    # A SMALL BOUND IS READ BY REVIEW: the GOOD column is the point --
    # `NTIME_PARSE_MAX`'s 128 is in `nitpick-regex`'s `_SMALL` set (its
    # RX-062), and a 128 in `span` is structure as often as policy. And the
    # BAD column's 9999 is two bounds' value, `NTIME_YEAR_MIN` negated, so the
    # finding names both: a literal does not say which it meant.
    (checks_mod.check_constants_named,
     [("src/core/limits.npk",
       "mod:limits;\npub fixed int64:NTIME_YEAR_MIN = -9999i64;\n"
       "pub fixed int64:NTIME_YEAR_MAX = 9999i64;\n"),
      _div("9999i64")],
     [("src/core/limits.npk",
       "mod:limits;\npub fixed int64:NTIME_PARSE_MAX = 128i64;\n"),
      _div("128i64")],
     "the value of the bound `NTIME_YEAR_MIN` or `NTIME_YEAR_MAX`"),
    # A BOUND THE CHECK CANNOT EVALUATE is reported, never passed.
    (checks_mod.check_constants_named,
     ("src/core/limits.npk",
      "mod:limits;\npub fixed int64:NTIME_SECS_MAX = NTIME_SECS_MIN + 1i64;\n"),
     ("src/core/limits.npk",
      "mod:limits;\npub fixed int64:NTIME_SECS_MAX = 253402300799i64;\n"),
     "with an initializer this check cannot evaluate"),
    (checks_mod.check_constants_named,
     ("src/cal/cal.npk", "mod:cal;\nfixed int64:YEAR_MAX = 9999i64;\n"),
     ("src/core/limits.npk", "mod:limits;\nfixed int64:YEAR_MAX = 9999i64;\n"),
     "Every named bound lives in"),
    # C-11 (TM-163): EVERY DIVISOR IN `src/cal/` A POSITIVE INTEGER LITERAL.
    # Four rows, each a plant and a control that differ in ONE expression, and
    # every one of the eight files carries a `use` path and a comment holding a
    # `/` and a `%` -- see `_div_tree` -- so each silent control is also the
    # proof that the check reads neither a string nor prose.
    (checks_mod.check_literal_divisors,
     ("src/cal/cal.npk", _div_tree("y / m")),
     ("src/cal/cal.npk", _div_tree("y / 400i64")),
     "is not a nonzero literal"),
    (checks_mod.check_literal_divisors,
     ("src/cal/cal.npk", _div_tree("y % 0i64")),
     ("src/cal/cal.npk", _div_tree("y % 4i64")),
     "literal zero"),
    # `+%` IS NOT A DIVISION -- it is the wrapping add (the compiler's D-312).
    # The control's operand is the NON-literal `m`, so only a check that reads
    # `+%` as an addition stays silent on it, and the plant is the same text
    # with the `+` deleted. (`0.1.1.md` planned `y +% 1i64` as this control,
    # and a check that misread `+%` as a remainder would have passed that too:
    # it would have been dividing by the nonzero literal `1i64`.)
    (checks_mod.check_literal_divisors,
     ("src/cal/cal.npk", _div_tree("(y % m) / 4i64")),
     ("src/cal/cal.npk", _div_tree("(y +% m) / 4i64")),
     "is not a nonzero literal"),
    # A LITERAL IS NOT THE DIVISOR WHEN AN OPERATOR THAT BINDS TIGHTER THAN
    # `/` FOLLOWS IT: `y / 256i64 =>! uint8` divides by `256i64 =>! uint8`,
    # which is 0. Lexical, so the plant need not type-check, and does not.
    (checks_mod.check_literal_divisors,
     ("src/cal/cal.npk", _div_tree("y / 256i64 =>! uint8")),
     ("src/cal/cal.npk", _div_tree("y / 256i64")),
     "binds tighter than"),
    (checks_mod.check_raw_index,
     ("src/cal/cal.npk", "mod:cal;\nfunc:f = int64(Vec:v) never fails "
                         "{ pass v.items[0i64]; };\n"),
     ("src/core/vec.npk", "mod:vec;\nfunc:f = int64(Vec:v) never fails "
                          "{ pass v.items[0i64]; };\n"),
     "That is a BARE POINTER"),
    # THE EVASION, WHICH RAN AT `aaffb87` AND THE CHECK COULD NOT SEE (B1).
    # Bind the bare pointer to a local and index the local: the field names
    # `.items[` and `.ptr[` never appear, and the read is just as unguarded.
    # The control is the SAME binding NOT indexed -- because `wild T->` locals
    # are ordinary in `vec.npk` (`mem`, `fresh`) and a check that fired on the
    # binding rather than on the index would fail this repository's own code.
    (checks_mod.check_raw_index,
     ("src/core/vec.npk",
      "mod:vec;\nfunc:f = int64(Vec:v) never fails {\n"
      "    wild int64->:p = v.items;\n    pass p[4i64];\n};\n"),
     ("src/core/vec.npk",
      "mod:vec;\nfunc:f = int64(Vec:v) never fails {\n"
      "    wild int64->:p = v.items;\n"
      "    int64[]:s = #wild_slice<int64>(p, v.count);\n    pass s[4i64];\n};\n"),
     "which is bound as a BARE POINTER"),
    (checks_mod.check_no_owning_fields,
     ("src/zone/zone.npk",
      "mod:zone;\nstruct:Row = {\n    int64:id;\n    string:name;\n};\n"
      "pub fixed Row[2]:TABLE = [];\n"),
     ("src/zone/zone.npk",
      "mod:zone;\nstruct:Row = {\n    int64:id;\n    int64:name_off;\n};\n"
      "pub fixed Row[2]:TABLE = [];\n"),
     "owning field"),
    # THE SAME VIOLATION, WRITTEN ON ONE LINE -- which is the form BOTH of
    # this repository's own structs take (`vec.npk`'s `Vec`, `bytes.npk`'s
    # `Bytes` -- by name, since line numbers move) and
    # the form the check could not see until cycle 0.0.6 (TM-138). The row
    # above was the only plant for three cycles, so the check was red on the
    # fixture its author imagined and silent on the identical fault in the
    # spelling the tree actually uses. A fix without this row would repeat the
    # original error: it would be commissioned on one spelling again.
    (checks_mod.check_no_owning_fields,
     ("src/zone/zone.npk",
      "mod:zone;\nstruct:Row = { int64:id; string:name; };\n"
      "pub fixed Row[2]:TABLE = [];\n"),
     ("src/zone/zone.npk",
      "mod:zone;\nstruct:Row = { int64:id; int64:name_off; };\n"
      "pub fixed Row[2]:TABLE = [];\n"),
     "owning field"),
    # AN OWNING ELEMENT, NOT A FIELD (cycle 0.1.3b). Until then the check read
    # only struct fields, so a table whose ELEMENT is a `string` was invisible
    # to it -- the table `tests/probe/probe17c_fixed_string_copy_refused.npk`
    # declares, which the language lets exist, refuses to copy from, and --
    # until compiler `c970483`, which refuses it too (TYPE-084) -- did not
    # stop a move out of.
    (checks_mod.check_no_owning_fields,
     ("src/zone/zone.npk",
      "mod:zone;\npub fixed string[2]:NAMES = [\"a\", \"b\"];\n"),
     ("src/zone/zone.npk",
      "mod:zone;\npub fixed int64[2]:IDS = [1i64, 2i64];\n"),
     "owning element"),
    # AND AN OWNER TWO STRUCTS DOWN (cycle 0.1.3b): `Row` holds no `string`,
    # but its `Name` does, so a row copied out of the table would own one all
    # the same. The control's `Name` holds an offset instead -- and both
    # `Row`s carry a field NAMED `string_off`, which the check matched as an
    # owner until 0.1.3b (it looked for the substring), so a check that went
    # back to substrings would fire on the control. Multi-line, because the
    # nested case's other spelling is covered by the rows above.
    (checks_mod.check_no_owning_fields,
     ("src/zone/zone.npk",
      "mod:zone;\nstruct:Name = {\n    string:text;\n};\n"
      "struct:Row = {\n    int64:string_off;\n    Name:name;\n};\n"
      "pub fixed Row[2]:TABLE = [];\n"),
     ("src/zone/zone.npk",
      "mod:zone;\nstruct:Name = {\n    int64:off;\n};\n"
      "struct:Row = {\n    int64:string_off;\n    Name:name;\n};\n"
      "pub fixed Row[2]:TABLE = [];\n"),
     "owns through"),
    # ---- CYCLE 0.1.5: THE READER (TM-199). Each row below is a shape where
    # this harness's reading of source disagreed with the compiler's lexer at
    # `c970483` (`0.1.5.md` section 1.3). The BAD column is a violation the old
    # reader did not see; the GOOD column is the same shape made harmless, so a
    # check that fired on the shape rather than on the violation fails its
    # control -- and in two rows the GOOD column is the point, because the old
    # reader fired on it.
    #
    # A LONE CR IN A `//` COMMENT IS NOT A LINE END, so the `"` after it is
    # comment text -- where a text-mode read made it open a string that
    # blanked the division on the next line.
    (checks_mod.check_literal_divisors,
     ("src/cal/cal.npk",
      "mod:cal;\n// note\r\"\nfunc:f = int64(int64:y, int64:m) never fails "
      "{ pass y / m; };\n// \"\n"),
     ("src/cal/cal.npk",
      "mod:cal;\n// note\r\"\nfunc:f = int64(int64:y, int64:m) never fails "
      "{ pass y / 4i64; };\n// \"\n"),
     "is not a nonzero literal"),
    # A `//` INSIDE A `/* */` IS BLOCK-COMMENT TEXT, and the block ends at its
    # `*/` -- where the old scanner blanked the rest of the LINE from the `//`.
    (checks_mod.check_purity,
     ("src/cal/cal.npk", "mod:cal;\nfunc:f = int64() never fails "
                         "{ /* see // below */ pass mono_now(); };\n"),
     ("src/cal/cal.npk", "mod:cal;\nfunc:f = int64() never fails "
                         "{ /* see // below */ pass 0i64; };\n"),
     "calls `mono_now` outside `src/host/`"),
    (checks_mod.check_error_budget,
     ("src/cal/cal.npk", "mod:cal;\n/* a // note */ pub error:ETimeOops;\n"),
     ("src/cal/cal.npk", "mod:cal;\n/* a // note */ pub error:ETimeValue;\n"),
     "three is a ceiling"),
    # A CHARACTER LITERAL `'"'` IS ONE CHARACTER -- where both old scanners
    # opened a string at its `"` that ran to the end of the file.
    (checks_mod.check_literal_divisors,
     ("src/cal/cal.npk",
      "mod:cal;\nfunc:f = int64(int64:y, int64:m) never fails "
      "{ char8:q = '\"'; pass y / m; };\n"),
     ("src/cal/cal.npk",
      "mod:cal;\nfunc:f = int64(int64:y, int64:m) never fails "
      "{ char8:q = '\"'; pass y / 4i64; };\n"),
     "is not a nonzero literal"),
    # A TEMPLATE'S TEXT IS TEXT, a `//` in it included.
    (checks_mod.check_literal_divisors,
     ("src/cal/cal.npk",
      "mod:cal;\nfunc:f = int64(int64:y, int64:m) never fails "
      "{ string:t = `a//b`; pass y / m; };\n"),
     ("src/cal/cal.npk",
      "mod:cal;\nfunc:f = int64(int64:y, int64:m) never fails "
      "{ string:t = `a//b`; pass y / 4i64; };\n"),
     "is not a nonzero literal"),
    # AN IMPORT PATH IS ITS LITERAL'S DECODED VALUE: `..\x2fhost/host.npk` is
    # `../host/host.npk` to the compiler, and was a directory named
    # `..\x2fhost` inside `cal`'s own layer to the old walk.
    (checks_mod.check_layering,
     ("src/cal/cal.npk", "mod:cal;\nuse \"..\\x2fhost/host.npk\".*;\n"),
     ("src/cal/cal.npk", "mod:cal;\nuse \"..\\x2fcore/core.npk\".*;\n"),
     "NOTHING imports `host`"),
    # AND THE OTHER DIRECTION: a `use` after a lone CR in a `//` comment is
    # comment text, not an import. The GOOD column is the point of this row --
    # the old reader made it an import of `host` and fired on the control.
    (checks_mod.check_layering,
     ("src/cal/cal.npk", "mod:cal;\nuse \"../host/host.npk\".*;\n"),
     ("src/cal/cal.npk", "mod:cal;\n// note\ruse \"../host/host.npk\".*;\n"),
     "NOTHING imports `host`"),
    # THE UMBRELLA'S COUNT IS OF RE-EXPORTS THE COMPILER READS: a `pub use`
    # inside a `/* */` is none, and the old count took every LINE that began
    # with the words -- so it fired on this row's GOOD column too.
    (checks_mod.check_denominators,
     ("src/lib.npk",
      "mod:lib;\n// " + _TAG % ("lib_reexports", 2) + "\n"
      "pub use \"./cal/cal.npk\".f;\n/*\npub use \"./cal/cal.npk\".g;\n*/\n"),
     ("src/lib.npk",
      "mod:lib;\n// " + _TAG % ("lib_reexports", 1) + "\n"
      "pub use \"./cal/cal.npk\".f;\n/*\npub use \"./cal/cal.npk\".g;\n*/\n"),
     "the tree says 1"),
    # ---- CYCLE 0.1.5: TOKENS, NOT LINES (TM-200). Each row below is a shape
    # the compiler reads as a call, an index or a declaration at `c970483`
    # (`0.1.5.md` section 1.4) that a pattern matched against one line did not.
    (checks_mod.check_purity,
     ("src/cal/cal.npk", "mod:cal;\nfunc:f = int64() never fails "
                         "{ pass mono_now (); };\n"),
     ("src/cal/cal.npk", "mod:cal;\nfunc:f = int64() never fails "
                         "{ pass mono_nowhere (); };\n"),
     "calls `mono_now` outside `src/host/`"),
    (checks_mod.check_purity,
     ("src/cal/cal.npk", "mod:cal;\nfunc:f = int64() never fails "
                         "{ pass environ\n(); };\n"),
     ("src/cal/cal.npk", "mod:cal;\nfunc:f = int64() never fails "
                         "{ pass environs\n(); };\n"),
     "calls `environ` outside `src/host/`"),
    (checks_mod.check_raw_index,
     ("src/cal/cal.npk", "mod:cal;\nfunc:f = int64(Vec:v) never fails "
                         "{ pass v.items\n[0i64]; };\n"),
     ("src/core/vec.npk", "mod:vec;\nfunc:f = int64(Vec:v) never fails "
                          "{ pass v.items\n[0i64]; };\n"),
     "That is a BARE POINTER"),
    # AND THE LEXER'S WHITESPACE AFTER THE DOT (the close's second half, the
    # audit's C12): `.` and `items` are two tokens, so a line end between them
    # is an index to the compiler -- which the pattern had not allowed.
    (checks_mod.check_raw_index,
     ("src/cal/cal.npk", "mod:cal;\nfunc:f = int64(Vec:v) never fails "
                         "{ pass v.\n    items [0i64]; };\n"),
     ("src/core/vec.npk", "mod:vec;\nfunc:f = int64(Vec:v) never fails "
                          "{ pass v.\n    items [0i64]; };\n"),
     "That is a BARE POINTER"),
    (checks_mod.check_raw_index,
     ("src/core/vec.npk",
      "mod:vec;\nfunc:f = int64(Vec:v) never fails {\n"
      "    wild int64->\n    :p = v.items;\n    pass p\n    [4i64];\n};\n"),
     ("src/core/vec.npk",
      "mod:vec;\nfunc:f = int64(Vec:v) never fails {\n"
      "    wild int64->\n    :p = v.items;\n"
      "    int64[]:s = #wild_slice<int64>(p, v.count);\n"
      "    pass s\n    [4i64];\n};\n"),
     "which is bound as a BARE POINTER"),
    (checks_mod.check_error_budget,
     ("src/cal/cal.npk", "mod:cal;\nerror\n:ETimeOops;\n"),
     ("src/cal/cal.npk", "mod:cal;\nerror\n:ETimeValue;\n"),
     "three is a ceiling"),
    # A SECOND DECLARATION AFTER A `;`. The control's second declaration is not
    # an `error:` -- `cal.npk`'s own `ValueFault` follows its identity -- because
    # S-4 gives each module ONE identity, so no module can declare two budgeted
    # ones on a line; until the close's second half the control declared
    # `ETimeParse` in `cal`, which S-4 gives to `fmt`, and required silence
    # (the audit's C2; TM-203 makes that a violation, planted two rows down).
    (checks_mod.check_error_budget,
     ("src/cal/cal.npk",
      "mod:cal;\npub error:ETimeValue; pub error:ETimeOops;\n"),
     ("src/cal/cal.npk",
      "mod:cal;\npub error:ETimeValue; pub enum:ValueFault = { YearRange; };\n"),
     "three is a ceiling"),
    # ---- THE CLOSE'S SECOND HALF: THE COMPILER'S UNIT (TM-203). An identity is
    # its MODULE and its name -- `NITPICK-REACH-003` names `moda.ETimeValue` and
    # `modb.ETimeValue` as two arms, measured at `c970483` and `c3bdae2` -- and
    # the count was keyed by the bare name. A budgeted name in TWO modules: two
    # files planted, and the control holds each module to its own identity.
    (checks_mod.check_error_budget,
     [("src/cal/cal.npk", "mod:cal;\npub error:ETimeValue;\n"),
      ("src/zone/zone.npk", "mod:zone;\npub error:ETimeValue;\n")],
     [("src/cal/cal.npk", "mod:cal;\npub error:ETimeValue;\n"),
      ("src/zone/zone.npk", "mod:zone;\npub error:ETimeZone;\n")],
     "is declared in 2 modules"),
    # AND A BUDGETED NAME OUTSIDE THE MODULE S-4 NAMES FOR IT: `ETimeParse` is
    # `fmt`'s, so in `cal` it is `cal.ETimeParse`, an identity no table names.
    (checks_mod.check_error_budget,
     ("src/cal/cal.npk", "mod:cal;\npub error:ETimeParse;\n"),
     ("src/fmt/fmt.npk", "mod:fmt;\npub error:ETimeParse;\n"),
     "S-4's table names module `fmt`"),
    (checks_mod.check_constants_named,
     ("src/cal/cal.npk", "mod:cal;\nfixed\nint64:YEAR_MAX = 9999i64;\n"),
     ("src/core/limits.npk", "mod:limits;\nfixed\nint64:YEAR_MAX = 9999i64;\n"),
     "Every named bound lives in"),
    (checks_mod.check_no_owning_fields,
     ("src/zone/zone.npk",
      "mod:zone;\nstruct\n:Row = { int64:id; string:name; };\n"
      "pub fixed Row[2]:TABLE = [];\n"),
     ("src/zone/zone.npk",
      "mod:zone;\nstruct\n:Row = { int64:id; int64:name_off; };\n"
      "pub fixed Row[2]:TABLE = [];\n"),
     "owning field"),
    (checks_mod.check_no_owning_fields,
     ("src/zone/zone.npk",
      "mod:zone;\npub fixed string\n[2]:NAMES = [\"a\", \"b\"];\n"),
     ("src/zone/zone.npk",
      "mod:zone;\npub fixed int64\n[2]:IDS = [1i64, 2i64];\n"),
     "owning element"),
    # A ROW NOTHING DRIVES -- the document promising a check the run does not
    # keep.
    (checks_mod.check_check_registry,
     _family(rows=("check_a", "check_b", "check_c", "check_p", "check_d")),
     _family(), "nothing runs it"),
    # A LIVE CHECK WITH NO ROW -- `check_exemptions_live`'s shape for a whole
    # subcycle (V-14e).
    (checks_mod.check_check_registry,
     _family(live=("check_a", "check_e")), _family(),
     "is in `checks.LIVE` and §2's table has no row for it"),
    # A PENDING CHECK THE DOCUMENT TURNS ON AT ANOTHER CYCLE.
    (checks_mod.check_check_registry,
     _family(pending=(("check_p", "0.8"),)), _family(),
     "turns on at cycle 0.9 by V-1a's pending table and at cycle 0.8"),
    # A PENDING CHECK THE DOCUMENT CALLS LIVE.
    (checks_mod.check_check_registry,
     _family(doc_pending=()), _family(), "the document says it is live"),
    # A CHECK `run.py` DRIVES WITH NO ROW -- `check_expect_headers`' shape,
    # the row V-1a's count left out at cycle 0.0.6 (C2).
    (checks_mod.check_check_registry,
     _family(run_defs=("check_b", "check_f"),
             run_calls=("check_b", "arms_mod.check_c", "check_f")),
     _family(), "the checks `run.py` drives outside step 5 and §2's table has no row"),
    # ONE CHECK STATED TWICE -- live in `LIVE` and pending at once.
    (checks_mod.check_check_registry,
     _family(live=("check_a", "check_p")), _family(), "at once"),
    (checks_mod.check_no_view_returns,
     _fmt("pub func:f = uint8[](string:s) never fails { pass string_bytes(s); };"),
     _fmt("pub func:f = string(string:s) never fails { pass s; };"),
     "returns `uint8[]`"),
    (checks_mod.check_no_view_returns,
     _fmt("pub func:f = int64[](int64:n) never fails { pass n; };"),
     _fmt("pub func:f = int64[4](int64:n) never fails { pass n; };"),
     "`int64[]` is a slice"),
    (checks_mod.check_no_view_returns,
     _fmt("pub func:f = cstring(string:s) { pass to_cstring(s); };"),
     _fmt("pub func:f = int64(string:s) never fails { pass 0i64; };"),
     "a `cstring`"),
    (checks_mod.check_no_view_returns,
     _fmt("struct:Span = { uint8[]:text; int64:at; };\n"
          "pub func:f = Span(int64:n) never fails { pass n; };"),
     _fmt("struct:Span = { int64:text; int64:at; };\n"
          "pub func:f = Span(int64:n) never fails { pass n; };"),
     "`Span` holds one"),
    (checks_mod.check_no_view_returns,
     _fmt("pub func:f = Vec<uint8[]>(int64:n) never fails { pass n; };"),
     _fmt("pub func:f = Vec<int64>(int64:n) never fails { pass n; };"),
     "its type argument `uint8[]`"),
    # AN OPTIONAL OF A VIEW (cycle 0.2.4a, the cycle audit's C4): "the rest,
    # or none" -- the result cycle 0.4's parsers will want first -- each
    # beside the same optional of an integer, which owns nothing.
    (checks_mod.check_no_view_returns,
     _fmt("pub func:f = uint8[]?(uint8[]:src) never fails { pass NIL; };"),
     _fmt("pub func:f = int64?(uint8[]:src) never fails { pass NIL; };"),
     "an optional of a view (`uint8[]` is a slice)"),
    (checks_mod.check_no_view_returns,
     _fmt("pub func:f = cstring?(cstring:src) never fails { pass NIL; };"),
     _fmt("pub func:f = int64?(cstring:src) never fails { pass NIL; };"),
     "an optional of a view (a `cstring`)"),
    # AN `int128` WHERE §5 MARKS NO SITE -- the control is the same function,
    # marked.
    (checks_mod.check_int128_sites,
     [_span5((("`f`", "**yes**"),)),
      ("src/span/span.npk", "mod:span;\n" + _wide("g"))],
     [_span5((("`g`", "**yes**"),)),
      ("src/span/span.npk", "mod:span;\n" + _wide("g"))],
     "marks no `int128` site there"),
    # A MARK THAT OUTLIVED ITS REASON -- the function is there, the wide type
    # is not.
    (checks_mod.check_int128_sites,
     [_span5((("`g`", "**yes**"),)),
      ("src/span/span.npk", "mod:span;\n" + _narrow("g"))],
     [_span5((("`g`", "**yes**"),)),
      ("src/span/span.npk", "mod:span;\n" + _wide("g"))],
     "spells no `int128`"),
    # AN `int128` AT MODULE LEVEL. The control holds the same type in prose and
    # in a string -- blanked, so neither is one.
    (checks_mod.check_int128_sites,
     [_span5((("`g`", "**yes**"),)),
      ("src/span/span.npk", "mod:span;\nfixed int128:WIDE = 1i128;\n" + _wide("g"))],
     [_span5((("`g`", "**yes**"),)),
      ("src/span/span.npk", "mod:span;\n// int128 here is prose\n"
                            "fixed string:WIDE = \"int128\";\n" + _wide("g"))],
     "outside every function"),
    (checks_mod.check_int128_sites,
     [_span5((("`g`", "maybe"),)), ("src/span/span.npk", "mod:span;\n")],
     [_span5((("`g`", "no"),)), ("src/span/span.npk", "mod:span;\n")],
     "neither yes nor no"),
    (checks_mod.check_int128_sites,
     [_span5((("the nanosecond step", "**yes**"),)),
      ("src/span/span.npk", "mod:span;\n")],
     [_span5((("`g`'s nanosecond step", "**yes**"),)),
      ("src/span/span.npk", "mod:span;\n")],
     "names no function"),
    (checks_mod.check_int128_sites,
     [("meta/specs/SPAN_MODEL.md",
       "# Spans\n\n## 5. Where\n\n| Site | Risk | Answer |\n|---|---|---|\n"
       "| `g` | the stub's | the stub's |\n"),
      ("src/span/span.npk", "mod:span;\n")],
     [_span5((("`g`", "**yes**"),)), ("src/span/span.npk", "mod:span;\n")],
     "no table with an `int128` column"),
    # A WIDER TYPE WHERE §5 MARKS NO SITE (cycle 0.2.4a, the cycle audit's
    # D1): an `int256` and a `uint128` intermediate, each narrowed by a bare
    # `=>!`, beside the same function marked -- N-20's reason is every width
    # past 64 bits, and the check read `int128` alone.
    (checks_mod.check_int128_sites,
     [_span5((("`f`", "**yes**"),)),
      ("src/span/span.npk", "mod:span;\n" + _wide("g").replace("int128", "int256"))],
     [_span5((("`g`", "**yes**"),)),
      ("src/span/span.npk", "mod:span;\n" + _wide("g").replace("int128", "int256"))],
     "spells `int256` in `g`"),
    (checks_mod.check_int128_sites,
     [_span5((("`f`", "**yes**"),)),
      ("src/span/span.npk", "mod:span;\n" + _wide("g").replace("int128", "uint128"))],
     [_span5((("`g`", "**yes**"),)),
      ("src/span/span.npk", "mod:span;\n" + _wide("g").replace("int128", "uint128"))],
     "spells `uint128` in `g`"),
    # A WIDE LITERAL WHERE §5 MARKS NO SITE (cycle 0.3.0, TM-246): a
    # computation of literals alone widens with no type's name and narrows in
    # silence -- `(3i256 * 5i256) =>! int64` compiles and runs at the pin -- so
    # the check reads a literal's width as it reads a type's name. The first
    # row is the function unmarked beside the same function marked; the second
    # a wide literal at module level, beside the same constant in `int64`.
    (checks_mod.check_int128_sites,
     [_span5((("`f`", "**yes**"),)),
      ("src/span/span.npk", "mod:span;\nfunc:g = int64() never fails {\n"
                            "    pass (3i256 * 5i256) =>! int64;\n};\n")],
     [_span5((("`g`", "**yes**"),)),
      ("src/span/span.npk", "mod:span;\nfunc:g = int64() never fails {\n"
                            "    pass (3i256 * 5i256) =>! int64;\n};\n")],
     "spells `3i256` in `g`"),
    (checks_mod.check_int128_sites,
     [_span5((("`g`", "**yes**"),)),
      ("src/span/span.npk", "mod:span;\nfixed int64:K = 7u128 =>! int64;\n" + _wide("g"))],
     [_span5((("`g`", "**yes**"),)),
      ("src/span/span.npk", "mod:span;\nfixed int64:K = 7i64;\n" + _wide("g"))],
     "spells `7u128` outside every function"),
    # A DIGIT SEPARATOR -- the dispatch's measured case, `86_400i64`.
    (checks_mod.check_constants_named, _div("86_400i64"), _div("86_401i64"),
     "belongs to module `core`"),
    # TWO TOGETHER, which Python's own `int()` refuses -- so a reader that left
    # the separators to `int()` passes the row above and fails this one.
    (checks_mod.check_constants_named, _div("86__400i64"), _div("86__401i64"),
     "belongs to module `core`"),
    # A LEADING ZERO: decimal still, and no longer the digits `86400`.
    (checks_mod.check_constants_named, _div("086400i64"), _div("086401i64"),
     "belongs to module `core`"),
    (checks_mod.check_constants_named, _div("15180hexi64"), _div("15181hexi64"),
     "belongs to module `core`"),
    (checks_mod.check_constants_named, _div("10101000110000000bini64"),
     _div("10101000110000001bini64"), "belongs to module `core`"),
    (checks_mod.check_constants_named, _div("250600octi64"), _div("250601octi64"),
     "belongs to module `core`"),
    # THE BALANCED BASES: ternary's `T` is -1, nonary's `a` ... `d` -1 ... -4.
    (checks_mod.check_constants_named, _div("1111TTTT000ti64"),
     _div("1111TTTT001ti64"), "belongs to module `core`"),
    (checks_mod.check_constants_named, _div("142dc0ni64"), _div("142dc1ni64"),
     "belongs to module `core`"),
    # A NEGATIVE LITERAL, which only a balanced base spells: -86 400 is a copy.
    (checks_mod.check_constants_named, _div("0TTTT1111000ti64"),
     _div("0TTTT1111001ti64"), "belongs to module `core`"),
    # A WIDTH PAST `u64`, from the width table.
    (checks_mod.check_constants_named, _div("86400i128"), _div("86401i128"),
     "belongs to module `core`"),
    # A CHARACTER LITERAL: its value is its code point, and it widens.
    (checks_mod.check_constants_named, _div("('\\u{15180}' => int64)"),
     _div("('\\u{15181}' => int64)"), "belongs to module `core`"),
    # A BOUND AFTER `...` -- the old pattern's look-behind on `.` hid it.
    (checks_mod.check_constants_named, _loop("86400i64"), _loop("86401i64"),
     "belongs to module `core`"),
    # THE GOOD COLUMN IS THE POINT: 0x86400 is 549 888.
    (checks_mod.check_constants_named, _div("86400i64"), _div("86400hexi64"),
     "belongs to module `core`"),
    # THE GOOD COLUMN IS THE POINT: a string's text is no number.
    (checks_mod.check_constants_named, _div("86400i64"),
     ("src/span/span.npk", "mod:span;\nfunc:f = string() never fails { "
                           "pass \"86400\"; };\n"),
     "belongs to module `core`"),
    # A TOKEN THE LEXER REFUSES is reported, never passed -- `0x` is no prefix
    # here: `0x15180` is `NITPICK-LEX-003`, "digit is not valid for this base".
    (checks_mod.check_constants_named, _div("0x15180"), _div("0FFhex"),
     "a literal this check does not read"),
]


# S-22'S ONE EXEMPTION, RE-DERIVED (TM-204, TM-137) -- which no `PLANTED` row
# can express, because the exemption applies to this repository's tree and to
# no scratch tree unless it is handed one. Each plant falsifies one part of the
# reason S-22 gives -- the function gone, no view, no pointer to its
# container, no container, and S-22 silent about it -- beside a control where
# every part holds, as `bytes_view` holds them today.
_EXEMPT_VIEW = {"bytes_view": ("src/core/bytes.npk", "Bytes")}
_S22_TEXT = ("# Safety\n\n## 5. Resources\n\n**Rule S-22 -- a view is a "
             "parameter, never a return value.** One is named -- %s.\n\n"
             "## 6. What an application owes\n")
_BYTES = ("mod:bytes;\npub struct:%s = { hidden buffer:body; sealed int64:len; };\n"
          "pub func:%s = %s(%s:b) never fails {\n"
          "    pass #wild_slice<uint8>(b.body.ptr, b.len);\n};\n")
VIEW_EXEMPT_PLANTS = [
    ("the function gone",
     _BYTES % ("Bytes", "bytes_peek", "uint8[]", "Bytes->"), "`bytes_view`",
     "declares no function of that name"),
    ("no view returned",
     _BYTES % ("Bytes", "bytes_view", "int64", "Bytes->"), "`bytes_view`",
     "no longer returns a view"),
    ("no pointer to the container",
     _BYTES % ("Bytes", "bytes_view", "uint8[]", "Bytes"), "`bytes_view`",
     "takes no pointer to `Bytes`"),
    ("no container",
     _BYTES % ("Sink", "bytes_view", "uint8[]", "Bytes->"), "`bytes_view`",
     "declares no struct `Bytes`"),
    ("S-22 silent about it",
     _BYTES % ("Bytes", "bytes_view", "uint8[]", "Bytes->"), "`bytes_peek`",
     "no longer names `bytes_view`"),
]


def part_b_view_exempt(rep, base):
    """S-22's exemption, each part of its reason falsified alone."""
    problems = []
    good = _mini_tree(os.path.join(base, "planted", "view_exempt_good"), [
        ("src/core/bytes.npk",
         _BYTES % ("Bytes", "bytes_view", "uint8[]", "Bytes->")),
        ("meta/specs/SAFETY.md", _S22_TEXT % "`bytes_view`")])
    res = checks_mod.check_no_view_returns(good, exempt=_EXEMPT_VIEW)
    if res.problems:
        problems.append(
            "check_no_view_returns fired on an exemption whose every reason "
            "holds, so its reds below are not evidence.\n      it said: %s"
            % res.problems[0])
    for i, (what, bytes_text, named, needle) in enumerate(VIEW_EXEMPT_PLANTS):
        red = _mini_tree(os.path.join(base, "planted", "view_exempt_%d" % i), [
            ("src/core/bytes.npk", bytes_text),
            ("meta/specs/SAFETY.md", _S22_TEXT % named)])
        res = checks_mod.check_no_view_returns(red, exempt=_EXEMPT_VIEW)
        if not any(needle in p for p in res.problems):
            problems.append(
                "check_no_view_returns did not fail S-22's exemption with %s: "
                "an exemption whose reason no longer holds excuses the next "
                "view returned (TM-137).\n      it said: %s"
                % (what, res.problems[0] if res.problems else "nothing"))
    return problems


# THE COUNTS THIS FILE PRINTS, DERIVED RATHER THAN TYPED (TM-142).
#
#   V14_CASES     what `TESTING.md` V-14 names -- seven, plus this repository's
#                 own eighth (a program whose `failsafe` has been deleted) and,
#                 since cycle 0.1.4b, its ninth (a program whose managed memory
#                 disagrees with its header, TM-187) and, since cycle 0.2.0a,
#                 its tenth and eleventh (a layout pin `opt` does not derive,
#                 and a tree pinned consistently to another target -- the
#                 compiler's two target checks, ported, TM-209), and its
#                 twelfth and thirteenth (a code named once where it is
#                 reported at two sites, and named at three where it is
#                 reported at two -- the compiler's D-332, TM-210).
#   PLANTED_CASES what is actually planted: case 6 is PEND until cycle 0.5.
#   TREE_PLANTS   `PLANTED`'s rows, plus THREE that no row can express:
#                 `check_layering`'s node half (the fault is a file that is NOT
#                 there); the whole-tree walk's nested-repository pruning
#                 (the subject is the WALK, not a check -- TM-146); and
#                 `check_specs_current` (which reports and never fails, so it
#                 is driven separately). And since cycle 0.2.3a the FIVE
#                 plants of S-22's exemption (`part_b_view_exempt`,
#                 TM-228), each one part of its reason falsified, against
#                 a control where every part holds. Every one has a
#                 control beside it, which is why the two numbers printed
#                 are equal.
V14_CASES = 13
PLANTED_CASES = 12
TREE_PLANTS = len(PLANTED) + 3 + len(VIEW_EXEMPT_PLANTS)


def part_b(rep, base):
    """Every tree check, seen RED on a planted violation and GREEN beside it."""
    problems = []
    for i, (fn, bad, good, needle) in enumerate(PLANTED):
        name = fn.__name__
        # A row plants ONE file, or -- since the close's second half, whose
        # violation is two modules agreeing on a name (TM-203) -- a LIST.
        bads = bad if isinstance(bad, list) else [bad]
        goods = good if isinstance(good, list) else [good]
        red = _mini_tree(os.path.join(base, "planted", "%s_%d_bad" % (name, i)),
                         bads)
        res = fn(red)
        if not res.problems:
            problems.append(
                "%s did not fire on a planted violation in %s. A check that "
                "has never failed has never been shown to work.\n      the "
                "plant was:\n%s" % (name, ", ".join(r for r, _ in bads),
                                    "\n".join("        " + l
                                              for _, body in bads
                                              for l in body.splitlines())))
        elif not any(needle in p for p in res.problems):
            problems.append(
                "%s fired on the plant in %s but never said %r, so it may have "
                "fired for a different reason.\n      it said: %s"
                % (name, ", ".join(r for r, _ in bads), needle,
                   res.problems[0].splitlines()[0]))

        green = _mini_tree(
            os.path.join(base, "planted", "%s_%d_good" % (name, i)), goods)
        res = fn(green)
        if res.problems:
            problems.append(
                "%s fired on the CLEAN control in %s, so its red above is not "
                "evidence about the plant.\n      it said: %s"
                % (name, ", ".join(r for r, _ in goods), res.problems[0]))

    # THE NODE HALF OF check_layering, WHICH NO `PLANTED` ROW CAN EXPRESS: the
    # fault is a file that is NOT THERE, and every row above plants a file that
    # is. `0.0/README.md`'s cycle-0.0.1 acceptance claimed this was enforced
    # and it was not, for four subcycles, inside a ticked box (D1, TM-142).
    red = _mini_tree(os.path.join(base, "planted", "layer_missing"), [],
                     skip_layers=("zone",))
    res = checks_mod.check_layering(red)
    if not any("src/zone/" in p and "holds no `.npk`" in p
               for p in res.problems):
        problems.append(
            "check_layering did not fire on a DELETED layer placeholder. That "
            "is the exact failure the acceptance item named -- a directory "
            "whose placeholder was deleted rather than replaced is invisible "
            "to every sweep that counts files.\n      it said: %s"
            % (res.problems[0] if res.problems else "nothing"))
    green = _mini_tree(os.path.join(base, "planted", "layer_present"), [])
    res = checks_mod.check_layering(green)
    if res.problems:
        problems.append(
            "check_layering fired on a tree holding every layer, so its red "
            "above is not evidence about the missing one.\n      it said: %s"
            % res.problems[0])

    # A NESTED REPOSITORY IS NOT THIS TREE (TM-146), and no `PLANTED` row can
    # express this either: the subject is the WALK, not a check. Found by CI's
    # first run, which checks the pinned compiler out INSIDE the workspace at
    # `.nitpick` -- every whole-tree sweep then walked the entire compiler.
    # Both rules are driven: by name, and by shape (a directory holding `.git`).
    where = _mini_tree(os.path.join(base, "planted", "nested"), [])
    base_n = len(checks_mod.all_npk(where))
    _write(os.path.join(where, ".nitpick", "src", "vendored.npk"),
           "mod:vendored;\n")
    _write(os.path.join(where, "elsewhere", ".git", "HEAD"), "ref: x\n")
    _write(os.path.join(where, "elsewhere", "other.npk"), "mod:other;\n")
    seen = len(checks_mod.all_npk(where))
    pruned = checks_mod.nested_repos(where)
    if seen != base_n:
        problems.append(
            "the whole-tree walk counted %d `.npk` with two nested "
            "repositories present and %d without. A vendored checkout is not "
            "this tree, and CI puts one at `.nitpick` (TM-146)."
            % (seen, base_n))
    for want in (".nitpick", "elsewhere"):
        if want not in pruned:
            problems.append(
                "nested_repos did not name `%s`. The pruning must be REPORTED "
                "or it is a silent skip, which is the thing V-1b is about.\n"
                "      it named: %s" % (want, pruned or "nothing"))
    # AND THE CONTROL: an ordinary directory is not pruned.
    _write(os.path.join(where, "ordinary", "keep.npk"), "mod:keep;\n")
    if "ordinary" in checks_mod.nested_repos(where):
        problems.append(
            "nested_repos pruned an ORDINARY directory, so its pruning above "
            "is not evidence about a vendored checkout.")
    if len(checks_mod.all_npk(where)) != base_n + 1:
        problems.append(
            "the walk did not pick up a `.npk` in an ordinary directory, so "
            "the pruning is wider than a nested repository.")
    return problems


def part_b_specs_current(rep, base):
    """`check_specs_current` reports and never fails, so it is shown REPORTING."""
    problems = []
    where = os.path.join(base, "planted", "specs_current")
    if os.path.isdir(where):
        shutil.rmtree(where)
    # THE FIXTURE CITATIONS ARE ASSEMBLED, NEVER SPELLED OUT (the audit's B3).
    # A dangling citation spelled out in this file is a LIVE one in the tree,
    # which is why `CITATION_EXEMPT` carried a WHOLE-FILE exemption for this
    # file -- an exemption whose reason ("it contains deliberately dangling
    # citations") was never re-derived, only its file's existence, which is
    # TM-137's shape in the mechanism written to prevent it. Built from pieces,
    # the fixtures are invisible to the scanner and the exemption is gone, so
    # this file's own dozen REAL citations are checked like everybody else's.
    ok_tm, bad_tm = "TM-" + "100", "TM-" + "999"
    ok_s, bad_s = "S-" + "1", "S-" + "77"
    # AND TWO BEFORE A MULTI-BYTE CHARACTER (the close's second half, TM-206):
    # read one character per byte, an em dash's first byte and a curly
    # apostrophe's are latin-1 LETTERS, and a pattern ending in `\b` saw no
    # boundary after the citation -- so neither of these was reported.
    bad_dash, bad_quote = "TM-" + "998", "S-" + "78"
    _write(os.path.join(where, "meta", "DECISIONS.md"),
           "# Decisions\n\n### %s - a decision that exists\n" % ok_tm)
    _write(os.path.join(where, "meta", "specs", "SAFETY.md"),
           "# Safety\n\n**Rule %s.** A rule that exists.\n" % ok_s)
    _write(os.path.join(where, "CLAUDE.md"),
           "This cites %s, which resolves, and %s, which does not.\n"
           "It cites %s, which resolves, and %s, which does not.\n"
           "And %s—with a dash, and %s’s own tail, neither.\n"
           % (ok_tm, bad_tm, ok_s, bad_s, bad_dash, bad_quote))
    res = checks_mod.check_specs_current(where)
    if res.problems:
        problems.append(
            "check_specs_current FAILED a run. It reports and never fails "
            "(TESTING.md §2): a renumbered citation is not a reason to stop a "
            "build.\n      it said: %s" % res.problems[0])
    got = " ".join(res.reports)
    for want in (bad_tm, bad_s, bad_dash, bad_quote):
        if want not in got:
            problems.append(
                "check_specs_current did not report the planted dangling "
                "citation %s.\n      it reported: %s" % (want, got or "nothing"))
    for unwanted in (ok_tm, ok_s + " cited"):
        if unwanted in got:
            problems.append(
                "check_specs_current reported %s, which resolves. A check that "
                "cries wolf about live citations is a check people stop "
                "reading.\n      it reported: %s" % (unwanted, got))
    return problems


# ---------------------------------------------------------------------------
# PART C -- the S-6 arm generator, calibrated on TM-107's own specimens and,
# since cycle 0.2.0, TM-217's
# ---------------------------------------------------------------------------

# Measured at pin `c3bdae2` from `NITPICK-REACH-003`'s own identity list (cycle
# 0.1.0b; the fourth row at `5fbaf4a`, cycle 0.2.0). Each of the first three
# rows is one of TM-107's three constraints, and the arithmetic is
# written out because a number embedded in prose travels with the prose:
#
#   floor                                    = 6
#   silent_lib  = floor + 0 (declared, never raised)   = 6   <- constraint 1
#   arms_lib    = floor + 1 (one raised identity)      = 7
#   calc_lib    = floor + 4 (its own arithmetic)       = 10  <- constraint 2
#   relay_lib   = floor + 1 (arms_lib's, relayed)      = 7   <- since cycle 0.2.0
#
# and 10 - 6 = 4 is `SAFETY.md` S-4b's measured "four extra arms" from a module
# that declares no error at all. At pin `0dfddac`, where these rows were first
# measured, the floor was FOUR and the three bills were 4 / 5 / 8; `c3bdae2`'s
# floor adds `StackExhausted` and `MachineFault` to every row and changes
# nothing else, which is the constraint-2 difference holding across the pins.
# The fourth row is cycle 0.2.0's (TM-217): a module that RAISES an
# identity it imports, which the compiler names by its DECLARING module -- the
# generator named the raising one until then, and `span` raising `cal`'s
# `ETimeValue` would have published an arm that does not exist.
CALIBRATION = [
    ("tests/probe/support/probe11_silent_lib.npk", 6,
     {"Unreachable", "HeapOom", "HeapBadRequest", "WildLeak",
      "StackExhausted", "MachineFault"},
     "constraint 1: it declares `pub error:EProbeSilent` and never raises it, "
     "so the identity arms NOTHING. An implementation counting DECLARATIONS "
     "would publish 7."),
    ("tests/probe/support/probe11_arms_lib.npk", 7,
     {"Unreachable", "HeapOom", "HeapBadRequest", "WildLeak",
      "StackExhausted", "MachineFault", "probe11_arms_lib.EProbeZone"},
     "a `fail` SITE puts the identity in, and it arrives module-qualified."),
    ("tests/probe/support/probe11_calc_lib.npk", 10,
     {"Unreachable", "HeapOom", "HeapBadRequest", "WildLeak",
      "StackExhausted", "MachineFault", "DivByZero", "DivOverflow",
      "IntOverflow", "OutOfBounds"},
     "constraint 2: it declares no error at all and still costs four extra "
     "arms, from its `/`, its `%`, its `+` and its one index."),
    ("tests/probe/support/probe11_relay_lib.npk", 7,
     {"Unreachable", "HeapOom", "HeapBadRequest", "WildLeak",
      "StackExhausted", "MachineFault", "probe11_arms_lib.EProbeZone"},
     "an identity RAISED here and DECLARED in the module it imports is that "
     "module's -- the compiler qualifies by the declaration, not the site."),
]


def part_c(rep, root, bld, base):
    """The generator against the compiler, on four modules with known bills."""
    problems = []
    scratch = os.path.join(base, "arms")
    for rel, count, expected, why in CALIBRATION:
        if not os.path.isfile(os.path.join(root, rel)):
            problems.append("the calibration specimen %s is gone. It is what "
                            "makes `check_failsafe_arms` a measured check "
                            "rather than a written one." % rel)
            continue
        try:
            measured = arms_mod.measure_bill(bld, root, rel, scratch)
            computed, _meta = arms_mod.compute_bill(root, rel)
        except build_mod.BuildError as err:
            problems.append("%s: %s" % (rel, err.detail))
            continue
        # THE IDENTITY, WRITTEN OUT: the count, the set the compiler listed and
        # the set this file computed are three statements of one fact, so all
        # three are asserted rather than one being believed.
        if len(measured) != count:
            problems.append(
                "%s: the compiler now lists %d identities and this calibration "
                "expects %d -- %s. Re-measure before changing the number; the "
                "specimen exists to detect exactly this.\n      it listed: %s"
                % (rel, len(measured), count, why, ", ".join(sorted(measured))))
        if measured != expected:
            problems.append(
                "%s: the compiler's identity list is not the calibrated set.\n"
                "      short by: %s\n      extra:    %s"
                % (rel, ", ".join(sorted(expected - measured)) or "none",
                   ", ".join(sorted(measured - expected)) or "none"))
        if computed != measured:
            problems.append(
                "%s: the S-6 generator disagrees with NITPICK-REACH-003.\n"
                "      generator short by: %s\n      generator overstates: %s\n"
                "      %s"
                % (rel, ", ".join(sorted(measured - computed)) or "none",
                   ", ".join(sorted(computed - measured)) or "none", why))

    # AND THE GENERATOR SHOWN WRONG ON PURPOSE. `diff_bill`'s overstating branch
    # is the one nothing else can catch (TM-107 constraint 3: a superset of the
    # required arms COMPILES), so it is the branch that most needs driving.
    fake = set(arms_mod.FLOOR) | {"NotAnArm"}
    # The floor as the compiler lists it at pin `c3bdae2`, so `NotAnArm` stays
    # the ONLY overstatement this fixture plants (cycle 0.1.0b gave `FLOOR` its
    # two new names; without them here the fixture would plant three).
    real = {"Unreachable", "HeapOom", "HeapBadRequest", "WildLeak",
            "StackExhausted", "MachineFault"}
    if not (fake - real):
        problems.append("the overstatement fixture does not overstate.")
    return problems


# ---------------------------------------------------------------------------
# PART D -- the verdict mechanisms, which had never been shown to fail
# ---------------------------------------------------------------------------
#
# THE TWO INSTRUMENTS THAT FOUND THIS CYCLE'S TWO WORST FAULTS WERE IN NEITHER
# THE SPECIFICATION NOR THIS FILE (TM-141). `check_exemptions_live` is the
# mechanism 0.0.5 built to fix TM-137 -- an exemption whose reason had expired
# and a diff that checked only that the file still existed -- and it could only
# ever be pointed at `EXPECT_EXEMPT`, where every recorded verdict was correct
# by construction. So the check written because a check had never failed had
# itself never failed. `run_defect_corpus` (TM-141) arrived in the same state.
#
# Both now take their list as a parameter, and this part hands each one a
# planted fault and requires the red, then the same input unfaulted and
# requires silence -- V-14b applied to a stage rather than to a `[[test]]`
# member.

# A file `npkc` refuses outright, one that links and runs clean, and a module
# with no `main`. Between them they cover every branch of `run._verdict`
# except `llc`/`ld`, which no spelling in this tree reaches at this pin. And
# since cycle 0.1.5 a fourth: a `main` whose `func` and `:main` stand on two
# lines, which the compiler builds and the old substring test called `none`
# (TM-200).
VERDICT_SPECIMENS = [
    ("stops_at_npkc.npk", WIDE_LITERAL % {"mod": "stops_at_npkc"}, "npkc",
     "the frontend refuses it, so no `.ll` is written"),
    ("runs_clean.npk", TRIVIAL % {"mod": "runs_clean", "code": 0}, "run:0",
     "it builds all the way and the RUN is what is judged"),
    ("no_main_here.npk", "mod:no_main_here;\n\npub func:f = int64() never "
     "fails { pass 1i64; };\n", "none",
     "a module with no `main` is not a program, so the question does not "
     "arise -- this is the bucket the four `probe11` support modules are in"),
    ("main_split.npk", "mod:main_split;\n\nfunc\n:main = int32(cstring[]:_~argv) "
     "{\n    exit 0i32;\n};\n" + FAILSAFE, "run:0",
     "`func` and `:main` on two lines declare a `main` -- the compiler builds "
     "it, and a test for the substring `func:main` said `none` (TM-200)"),
]


class _Recorder:
    """A `Report`-shaped sink that records instead of printing.

    Not `run.Report`: `run` imports THIS module, so importing it at the top of
    this one would be a cycle. The three methods a stage actually calls are
    the three that are here, and `failures` is the only thing part D reads.
    """

    def __init__(self):
        self.failures = []
        self.lines = []

    def say(self, line):
        self.lines.append(line)

    def note(self, line):
        self.lines.append(line)

    def fail(self, what, detail):
        self.failures.append("%s -- %s" % (what, str(detail).splitlines()[0]))

    def unit(self, name, problems, note=""):
        if problems:
            self.failures.append("%s -- %s"
                                 % (name, str(problems[0]).splitlines()[0]))

    def skip(self, what, why):
        self.lines.append("SKIP %s" % what)

    def pend(self, what, why):
        self.lines.append("PEND %s" % what)


def part_d(rep, root, man, base, npkc, npkrt):
    """`_verdict`, `check_exemptions_live` and `run_defect_corpus`, driven red."""
    # `run` imports this module, so this import is deliberately here and not at
    # the top. By the time this function is called `run` is fully initialised.
    import run as run_mod

    problems = []
    where = _mini_tree(os.path.join(base, "verdicts"), [])
    for name, body, _want, _why in VERDICT_SPECIMENS:
        _write(os.path.join(where, "tests", "corpus", name), body)
    bld = build_mod.Build(where, man, npkc, npkrt,
                          os.path.join(where, "build"))
    out_dir = os.path.join(where, "build", "exempt")
    os.makedirs(out_dir, exist_ok=True)

    # 1. THE INSTRUMENT. `check_exemptions_live` is only as good as the verdict
    #    it re-derives, so the verdict is measured against three files whose
    #    stopping point is known before it is trusted about any of them.
    verdicts = {}
    for name, _body, want, why in VERDICT_SPECIMENS:
        rel = os.path.join("tests", "corpus", name)
        got = run_mod._verdict(bld, where, rel, out_dir)
        verdicts[rel] = got
        if got != want:
            problems.append(
                "run._verdict said %r for %s and the answer is %r -- %s. The "
                "exemption check is a comparison against this function, so a "
                "wrong verdict here is a wrong verdict everywhere."
                % (got, name, want, why))

    # 2. THE MECHANISM, RED. One recorded verdict moved, the rest correct.
    faulted = dict((rel, ("ld", "a verdict this file does not have"))
                   if rel.endswith("runs_clean.npk") else (rel, (v, "correct"))
                   for rel, v in verdicts.items())
    rec = _Recorder()
    run_mod.check_exemptions_live(rec, where, bld, faulted)
    if not rec.failures:
        problems.append(
            "check_exemptions_live did not fire on a MOVED verdict. That is "
            "the whole of TM-137: an exemption's reason is a claim about what "
            "the compiler does, the compiler moves, and until 0.0.5 nothing "
            "noticed. A mechanism that has never failed has never been shown "
            "to work.")
    elif not any("runs_clean" in f for f in rec.failures):
        problems.append(
            "check_exemptions_live fired but did not name `runs_clean.npk`, "
            "the file whose verdict was moved.\n      it said: %s"
            % rec.failures[0])

    # 3. AND SILENT ON THE SAME LIST UNMOVED (V-14b).
    clean = dict((rel, (v, "correct")) for rel, v in verdicts.items())
    rec = _Recorder()
    run_mod.check_exemptions_live(rec, where, bld, clean)
    if rec.failures:
        problems.append(
            "check_exemptions_live fired on the CLEAN control, so its red "
            "above is not evidence about the moved verdict.\n      it said: %s"
            % rec.failures[0])

    # 4. THE DEFECT CORPUS, RED -- an `expect-exit:` wrong by one, which is the
    #    exact state 21 committed files were in until cycle 0.0.6: a marker
    #    that no stage asserted.
    corpus = _mini_tree(os.path.join(base, "corpus"), [])
    marked = os.path.join(corpus, "tests", "defect", "wrong_exit.npk")
    body = TRIVIAL % {"mod": "wrong_exit", "code": "0"}
    _write(marked, "// expect-exit: 1\n" + body)
    cbld = build_mod.Build(corpus, man, npkc, npkrt,
                           os.path.join(corpus, "build"))
    rec = _Recorder()
    run_mod.run_defect_corpus(rec, corpus, cbld, os.path.join("tests", "defect"))
    if not rec.failures:
        problems.append(
            "run_defect_corpus accepted a file whose `expect-exit:` is wrong "
            "by one. Before cycle 0.0.6, 21 committed markers under "
            "tests/probe/defect/ were in exactly that state -- present, "
            "well-formed, and asserted by nothing (TM-141).")

    # 5. AND SILENT ON THE CORRECT TWIN.
    _write(marked, "// expect-exit: 0\n" + body)
    rec = _Recorder()
    run_mod.run_defect_corpus(rec, corpus, cbld, os.path.join("tests", "defect"))
    if rec.failures:
        problems.append(
            "run_defect_corpus fired on the CLEAN control, so its red above "
            "is not evidence about the wrong marker.\n      it said: %s"
            % rec.failures[0])

    # 6. `check_expect_headers`, WHICH WAS `TESTING.md` §2's ONE UNPLANTED ROW.
    #    Three faults, one per branch, each with the control beside it: a file
    #    under `tests/` with no marker (the state the three `missing_failsafe`
    #    cases were in for two days, TM-115); a `.npk` in neither `src/` nor
    #    `tests/`, which no check owns; and an exemption naming a file that is
    #    gone, which is V-1c's both-directions diff and could not be driven at
    #    all until the list became a parameter.
    hdr = _mini_tree(os.path.join(base, "headers"), [])
    good = TRIVIAL % {"mod": "marked", "code": "0"}
    _write(os.path.join(hdr, "tests", "unit", "marked.npk"),
           "// expect-exit: 0\n" + good)
    for label, plant, needle in (
            ("a tests/ file with no marker",
             ("tests/unit/unmarked.npk", TRIVIAL % {"mod": "unmarked",
                                                    "code": "0"}),
             "header: tests/unit/unmarked.npk"),
            ("a .npk owned by no bucket",
             ("elsewhere/stray.npk", TRIVIAL % {"mod": "stray", "code": "0"}),
             "unowned .npk: elsewhere/stray.npk")):
        rel, text = plant
        path = os.path.join(hdr, *rel.split("/"))
        _write(path, text)
        rec = _Recorder()
        run_mod.check_expect_headers(rec, hdr, {})
        if not any(needle in f for f in rec.failures):
            problems.append(
                "check_expect_headers did not fire on %s. It is `TESTING.md` "
                "§2's row 13 and was planted NOWHERE until cycle 0.0.6, which "
                "is what made V-14c's \"every check\" false.\n      it said: %s"
                % (label, "; ".join(rec.failures) or "nothing"))
        os.remove(path)
        rec = _Recorder()
        run_mod.check_expect_headers(rec, hdr, {})
        if rec.failures:
            problems.append(
                "check_expect_headers fired on the CLEAN control after %s was "
                "removed.\n      it said: %s" % (label, rec.failures[0]))

    rec = _Recorder()
    run_mod.check_expect_headers(rec, hdr, {"tests/unit/deleted.npk":
                                            ("run:0", "a file that is gone")})
    if not any("stale exemption" in f for f in rec.failures):
        problems.append(
            "check_expect_headers did not fire on an exemption naming a file "
            "that is gone. That is V-1c's second direction -- an exemption "
            "that outlives its file silently excuses the next file with that "
            "name -- and nothing had ever driven it.\n      it said: %s"
            % ("; ".join(rec.failures) or "nothing"))
    return problems


# ---------------------------------------------------------------------------
# PART E -- the reader, against the compiler's lexer (cycle 0.1.5, TM-199)
# ---------------------------------------------------------------------------
#
# `lexical.py` is read by every tree check, the import walk, the arm generator,
# the exemption verdict and the markers, so a regression in it weakens all of
# them at once and reddens none: this part is the red it would otherwise not
# have. Two halves, and they answer different questions.
#
# E1 ASKS THE READER, AGAINST WHAT THE COMPILER READS: `nitpick-regex`'s case
# 18, TEXT FOR TEXT -- its `_LEX_TEXT` and `_LEX_IMPORTS` below are that
# repository's at its `fb37391` -- one of each lexical form that repository
# found to matter, each hiding a `use` and a `/` beside the ones that are real
# code, written to a FILE and read back through `lexical.read`, because a lone
# CR is lost in the READ, before any scanning begins. Its expectations are the
# compiler's reading at `c970483`, measured there (`0.1.5.md` section 1.3).
#
# E2 ASKS THE COMPILER, AGAINST WHAT THE READER MIRRORS: the forms a RUN can
# observe that `_FORMS_EXIT` names, in one program the pinned `npkc` compiles
# and runs -- exit 0 when each form reads as `lexical.py` reads it, and a code
# naming the form when one does not -- read by the reader as well, which must
# see exactly the statements that ran. So a re-pin that moves the lexer ON ONE
# OF THOSE FORMS is a red run here rather than a reader quietly mirroring a
# compiler that is gone.
#
# AND ONLY ON THOSE (cycle 0.1.5's audit, C1; TM-202). Until the close's second
# half E2 held seven forms and said "every form a run can observe"; it had no
# block string, raw string, escaped quote, empty string or interpolation, and
# the one lexer move between the kept pins -- the block string's close, the
# compiler's DEF-98, `c3bdae2` to `c970483` -- passed it at both. Each of those
# is here now with its VALUE asserted, and the program is refused at `c3bdae2`
# (its block string, line 21), so that move is a red run. A form E2 does not
# hold -- a nested interpolation, an escape inside a block string, an escape
# in a character literal beyond `\'` -- is not asked, and that is why the
# adoption re-reads `src/frontend/lexer.npk` at every re-pin whatever part E
# says.
_LEX_TEXT = (
    'mod:lexcase;\n'                                        # 1
    'use "./real_a.npk".*;\n'                               # 2  an import
    'pub use "./real_b.npk".name;\n'                        # 3  a re-export
    '// use "./line_comment.npk".*; a / b\n'                # 4
    '/*\n'                                                  # 5
    'use "./block_comment.npk".*; a / b\n'                  # 6
    '*/\n'                                                  # 7
    'string:s = "use \\"./in_string.npk\\" a / b";\n'       # 8
    'string:r = r"use a / b"; use "./after_raw.npk".*;\n'   # 9  an import
    'string:k = """\n'                                      # 10
    'use "./block_string.npk".*; a / b\n'                   # 11
    '""";\n'                                                # 12
    "char8:q = '\"'; use \"./after_char.npk\".*;\n"         # 13 an import
    'string:t = `use "./template.npk" a / b &{ n / 2 }`;\n' # 14 one `/` is code
    'pub /* gap */ use /* gap */ "./gapped.npk".*;\n'       # 15 a re-export
    'int64:x = y.use;\n'                                    # 16 a field, not a keyword
    '// see\ruse "./after_cr.npk".*; a / b\n'               # 17 a lone CR is not a line end
    '// note\r/* a / b\n'                                   # 18 ...so this `/*` is comment text
    'use "./after_cr_comment.npk".*;\n'                     # 19 an import
    'use "..\\x2freal_c.npk".*;\n'                          # 20 an import, `../real_c.npk`
    'use ".\\u{2F}real_d.npk".*;\n'                         # 21 an import, `./real_d.npk`
    'use "./back\\\\slash.npk".*;\n'                         # 22 an import, one backslash
    'string:bs = """a""b use "./in_block.npk".*; """; use "./after_block.npk".*;\n'  # 23
)
_LEX_IMPORTS = [(2, "./real_a.npk", False), (3, "./real_b.npk", True),
                (9, "./after_raw.npk", False), (13, "./after_char.npk", False),
                (15, "./gapped.npk", True), (19, "./after_cr_comment.npk", False),
                (20, "../real_c.npk", False), (21, "./real_d.npk", False),
                (22, "./back\\slash.npk", False), (23, "./after_block.npk", False)]


# THE FORMS A RUN CAN OBSERVE. Each guarded assignment after a form runs
# exactly when the form reads as `lexical.py` reads it; line 6's does not run,
# because the lone CR before it is not a line end. And from line 21 each
# literal's VALUE is asserted too, by its length (TM-202): a lexer that read the
# form another way would give the program another string, or refuse it.
_FORMS_TEXT = (
    "mod:lexical_forms;\n"                                     # 1
    "use \".\\x2flexical\\u{5F}six.npk\".*;\n"               # 2  decoded: ./lexical_six.npk
    "func:seven = int32() never fails { pass 7i32; };\n"       # 3
    "func:main = int32(cstring[]:_~argv) {\n"                  # 4
    "    int32:a = 0i32;\n"                                    # 5
    "    // a lone CR is not a line end\r    a = 10i32;\n"     # 6  all of it comment
    "    if (a != 0i32) { exit 10i32; }\n"                     # 7
    "    /* x // y */ a = 1i32;\n"                             # 8  code after the block
    "    if (a != 1i32) { exit 11i32; }\n"                     # 9
    "    /* p /* q */ a = 2i32;\n"                             # 10 the block does not nest
    "    if (a != 2i32) { exit 12i32; }\n"                     # 11
    "    char8:q = '\"'; a = 3i32;\n"                          # 12 one character
    "    if (a != 3i32) { exit 13i32; }\n"                     # 13
    "    string:t = `x//y`; a = 4i32;\n"                       # 14 a template's text
    "    if (a != 4i32) { exit 14i32; }\n"                     # 15
    "    int32:b = raw seven ();\n"                            # 16 a call, spaced
    "    int32:c = raw seven\n"                                # 17
    "    ();\n"                                                # 18 a call across a line end
    "    if (b != c) { exit 15i32; }\n"                        # 19
    "    if ((raw six()) != 6i32) { exit 16i32; }\n"           # 20 the decoded import
    "    string:k = \"\"\"a\"\"b\"\"\"; a = 5i32;\n"           # 21 a block string: 4 bytes
    "    if (a != 5i32) { exit 17i32; }\n"                     # 22
    "    if (string_byte_length(k) != 4i64) { exit 17i32; }\n" # 23
    "    string:w = r\"a\\\"; a = 6i32;\n"                     # 24 a raw string: 2 bytes
    "    if (a != 6i32) { exit 18i32; }\n"                     # 25
    "    if (string_byte_length(w) != 2i64) { exit 18i32; }\n" # 26
    "    string:e = \"a\\\"b\"; a = 7i32;\n"                   # 27 an escaped quote: 3 bytes
    "    if (a != 7i32) { exit 19i32; }\n"                     # 28
    "    if (string_byte_length(e) != 3i64) { exit 19i32; }\n" # 29
    "    string:z = \"\"; a = 8i32;\n"                         # 30 the empty string
    "    if (a != 8i32) { exit 20i32; }\n"                     # 31
    "    if (string_byte_length(z) != 0i64) { exit 20i32; }\n" # 32
    "    string:u = `<&{ e }>`; a = 9i32;\n"                   # 33 an interpolation is code
    "    if (a != 9i32) { exit 21i32; }\n"                     # 34
    "    if (string_byte_length(u) != 5i64) { exit 21i32; }\n" # 35
    "    char8:s = '\\''; a = 20i32;\n"                        # 36 an escaped character
    "    if (a != 20i32) { exit 22i32; }\n"                    # 37
    "    exit 0i32;\n"                                         # 38
    "};\n") + FAILSAFE
_FORMS_SIX = ("mod:lexical_six;\n\n"
              "pub func:six = int32() never fails { pass 6i32; };\n")
_FORMS_EXIT = {
    10: "a lone CR ended a `//` comment",
    11: "a `//` inside a `/* */` ended the line",
    12: "a `/* */` nested",
    13: "the character literal `'\"'` hid the code after it",
    14: "a `//` in a template's text ended the line",
    15: "a call's `(` could not follow whitespace",
    16: "the escaped `use` path -- `\\x2f` and `\\u{5F}` -- was not decoded",
    17: "a block string did not close at its first unescaped three quotes "
        "(DEF-98), or its value is not the 4 bytes `a\"\"b`",
    18: "a raw string read `\\\"` as an escape, or its value is not the 2 "
        "bytes `a\\`",
    19: "an escaped quote ended its string, or its value is not the 3 bytes "
        "`a\"b`",
    20: "`\"\"` was not the empty string",
    21: "an interpolation's code was read as template text, or its value is "
        "not the 5 bytes `<a\"b>`",
    22: "the escaped character `'\\''` hid the code after it",
}
# The lines whose literal must be blanked WHOLE -- no quote, backtick or
# apostrophe survives the reader there -- and the statement after each, which
# must survive it. `33`'s interpolation is code and must survive too.
_FORMS_LITERALS = ((21, "a = 5i32"), (24, "a = 6i32"), (27, "a = 7i32"),
                   (30, "a = 8i32"), (33, "a = 9i32"), (36, "a = 20i32"))


# THE SPELLINGS OF A NUMBER `check_constants_named` READS (cycle 0.2.3a, TM-231),
# and part E's third half asks the pinned compiler about every one: line by
# line, each spelling against the plain decimal the compiler must read it as,
# so the program exits 0 only if it reads every one so -- and the reader,
# `checks.literals`, must read each spelling on its line as that decimal too.
# A re-pin that moves the numeric scan on one of them -- a base suffix, a
# width, the separator, the leading-digit rule -- is a red run. Its own
# `failsafe`, because the loop's counter can reach `IntOverflow`.
_NUM_FORMS = (
    ("86_400i64", 86400), ("86__400i64", 86400), ("86400_i64", 86400),
    ("086400i64", 86400), ("15180hexi64", 86400),
    ("10101000110000000bini64", 86400), ("250600octi64", 86400),
    ("1111TTTT000ti64", 86400), ("142dc0ni64", 86400),
    ("0TTTT1111000ti64", -86400), ("86400hexi64", 549888),
    ("(86400i128 =>! int64)", 86400), ("('\\u{15180}' => int64)", 86400),
    ("1_000_000_000i64", 1000000000), ("01000000000i64", 1000000000),
    ("3B9ACA00hexi64", 1000000000),
    ("111011100110101100101000000000bini64", 1000000000),
    ("7346545000octi64", 1000000000), ("10TT1T01T001T1010001ti64", 1000000000),
    ("3d21c1b101ni64", 1000000000), ("(1000000000i128 =>! int64)", 1000000000),
)
_NUM_FAILSAFE = """
func:failsafe = int32(Error:e) {
    pick (e) {
        (HeapBadRequest) { exit 91i32; },
        (HeapOom)        { exit 92i32; },
        (IntOverflow)    { exit 93i32; },
        (Unreachable)    { exit 95i32; },
        (WildLeak)       { exit 96i32; },
        (StackExhausted) { exit 106i32; },
        (MachineFault)   { exit 107i32; },
        (*)              { exit 99i32; }
    }
    exit 9i32;
};
"""


def _num_program():
    """`(text, lines)`: the program, and `[(line, token, value)]` -- the token
    on each line the reader must read as `value`."""
    head = ("mod:numeric_forms;\n"
            "func:main = int32(cstring[]:_~argv) {\n")
    body, lines = [], []
    for k, (expr, value) in enumerate(_NUM_FORMS):
        want = "%di64" % value if value >= 0 else "(0i64 - %di64)" % -value
        body.append("    if (%s != %s) { exit %di32; }\n" % (expr, want, 10 + k))
        tok = expr.strip("()").split(" ")[0]
        lines.append((3 + k, tok, value))
    k = len(_NUM_FORMS)
    body.append("    int64:last = 0i64;\n")
    body.append("    for (int64:s in 0i64...86400i64) { last = s; }\n")
    lines.append((3 + k + 1, "86400i64", 86400))
    body.append("    if (last != 86399i64) { exit %di32; }\n" % (10 + k))
    text = head + "".join(body) + "    exit 0i32;\n};\n" + _NUM_FAILSAFE
    return text, lines


_NUM_TEXT, _NUM_LINES = _num_program()


def part_e(rep, root, man, base, npkc, npkrt):
    """The reader against the compiler's lexer: E1 and E2 above -- and, since
    cycle 0.2.3a, E3: `check_constants_named`'s literal reader against the
    compiler's numeric scan (TM-231)."""
    import lexical
    # `run` imports this module; by the time this is called it is initialised.
    import run as run_mod

    problems = []
    where = os.path.join(base, "lexical")
    if os.path.isdir(where):
        shutil.rmtree(where)
    os.makedirs(where)

    # E1 -- the reader, on one text of every form, through a FILE.
    path = os.path.join(where, "lexcase.npk")
    with open(path, "wb") as fh:
        fh.write(_LEX_TEXT.encode("latin-1"))
    text = lexical.read(path)
    if text != _LEX_TEXT:
        problems.append("E1: the file read back is not the bytes written -- a "
                        "line end or a byte was translated on the way in.")
    got = lexical.imports(text)
    if got != _LEX_IMPORTS:
        problems.append("E1: the imports read are %r, and the compiler reads "
                        "%r." % (got, _LEX_IMPORTS))
    code = lexical.blank(text)
    if len(code) != len(_LEX_TEXT) or code.count("\n") != _LEX_TEXT.count("\n"):
        problems.append("E1: blanking moved a byte or a line.")
    lines = code.split("\n")
    for ln in (4, 6, 8, 9, 11, 17, 18):
        if "/" in lines[ln - 1]:
            problems.append("E1: line %d: a `/` inside a comment or a literal "
                            "survived the blanking." % ln)
    if lines[13].count("/") != 1:
        problems.append("E1: line 14: the template's text was read as code, "
                        "or its interpolation was not.")
    if "after_char" in lines[12] or "use" not in lines[12]:
        problems.append("E1: line 13: the `'\"'` literal hid the rest of the "
                        "line, or was not blanked.")
    if "use" not in lines[18]:
        problems.append("E1: line 19: the `/*` inside line 18's comment was "
                        "read as a block comment and hid the code after it.")

    # E2 -- the compiler, on the forms `_FORMS_EXIT` names (TM-202), and the
    # reader on the same file.
    _write(os.path.join(where, "lexical_forms.npk"), _FORMS_TEXT)
    _write(os.path.join(where, "lexical_six.npk"), _FORMS_SIX)
    text = lexical.read(os.path.join(where, "lexical_forms.npk"))
    got = lexical.imports(text)
    if got != [(2, "./lexical_six.npk", False)]:
        problems.append("E2: the reader's imports are %r, and the program "
                        "imports ./lexical_six.npk at line 2." % (got,))
    lines = lexical.blank(text).split("\n")
    if "10i32" in lines[5]:
        problems.append("E2: line 6: the reader read code after a lone CR in "
                        "a `//` comment.")
    for ln, stmt in ((8, "a = 1i32"), (10, "a = 2i32"), (12, "a = 3i32"),
                     (14, "a = 4i32"), (16, "seven ("), (17, "seven"),
                     (18, "();")) + _FORMS_LITERALS + ((33, "{ e }"),):
        if stmt not in lines[ln - 1]:
            problems.append("E2: line %d: the reader blanked `%s`, which the "
                            "compiler runs." % (ln, stmt))
    for ln, _stmt in _FORMS_LITERALS:
        if any(ch in lines[ln - 1] for ch in "\"'`"):
            problems.append("E2: line %d: a quote survived the reader, so part "
                            "of the literal was read as code." % ln)
    bld = build_mod.Build(where, man, npkc, npkrt, os.path.join(where, "build"))
    out_dir = os.path.join(where, "build", "forms")
    os.makedirs(out_dir, exist_ok=True)
    verdict = run_mod._verdict(bld, where, "lexical_forms.npk", out_dir)
    if verdict != "run:0":
        code_ = int(verdict[4:]) if verdict.startswith("run:") else None
        problems.append(
            "E2: the pinned compiler's verdict on the forms program is %s, not "
            "run:0 -- %s. THE COMPILER'S LEXER HAS MOVED FROM WHAT `lexical.py` "
            "MIRRORS: re-read `src/frontend/lexer.npk` at the new pin and bring "
            "the reader to it, in the adoption that moved the pin."
            % (verdict, _FORMS_EXIT.get(code_, "it did not build and run")))

    # E3 -- `check_constants_named`'s literal reader against the compiler's
    # numeric scan (cycle 0.2.3a, TM-231): the reader on every spelling's
    # line of one program, and the pinned compiler on the program, which
    # exits at the first spelling it reads as another number.
    _write(os.path.join(where, "numeric_forms.npk"), _NUM_TEXT)
    lines = lexical.read(os.path.join(where, "numeric_forms.npk")).split("\n")
    for ln, tok, value in _NUM_LINES:
        got = [v for _a, t, v in checks_mod.literals(lines[ln - 1]) if t == tok]
        if got != [value]:
            problems.append(
                "E3: line %d: the reader reads `%s` as %s, and the program "
                "asserts %d." % (ln, tok, got or "nothing", value))
    verdict = run_mod._verdict(bld, where, "numeric_forms.npk", out_dir)
    if verdict != "run:0":
        code_ = int(verdict[4:]) if verdict.startswith("run:") else None
        problems.append(
            "E3: the pinned compiler's verdict on the numeric program is %s, "
            "not run:0 -- %s. THE COMPILER'S NUMERIC SCAN HAS MOVED FROM WHAT "
            "`checks.literals` MIRRORS: re-read `src/frontend/numeric.npk`, "
            "`num_width.npk` and `lexer.npk` at the new pin and bring the "
            "reader to them, in the adoption that moved the pin."
            % (verdict, "its line %d, `%s`, was read as another number"
               % _NUM_LINES[code_ - 10][:2]
               if code_ is not None and 10 <= code_ < 10 + len(_NUM_LINES)
               else "it did not build and run"))
    return problems


# ---------------------------------------------------------------------------

def run(rep, root, steps):
    """The whole self-check. Returns True when the harness has proven it fails."""
    base = os.path.join(root, ".internal", "scratch", "selfcheck")
    os.makedirs(base, exist_ok=True)
    npkc, npkrt = os.environ.get("NPKC"), os.environ.get("NPKRT")

    rep.say("[1/%d] self-check -- %d of V-14's %d cases (case 6 is PEND), then "
            "%d tree-check violations," % (steps, PLANTED_CASES, V14_CASES,
                                           TREE_PLANTS))
    rep.say("      then the S-6 arm generator against NITPICK-REACH-003 on %d "
            "specimens (V-15)" % len(CALIBRATION))

    if not npkc or not os.path.isfile(npkc) or not npkrt \
            or not os.path.isfile(npkrt):
        rep.fail("self-check",
                 "$NPKC and $NPKRT must both be set and be files; got %r and "
                 "%r. A SELF-CHECK THAT COULD NOT RUN IS A FAILURE, NOT A "
                 "SKIP -- silence here is indistinguishable from a pass, and "
                 "V-15 makes everything below it depend on this having run."
                 % (npkc, npkrt))
        return False
    try:
        man = manifest_mod.load(root)
    except manifest_mod.ManifestError as err:
        rep.fail("self-check", "the manifest does not read, so no scratch tree "
                               "can inherit its pin:\n%s" % err)
        return False

    ok = True
    builders = [case_1_wrong_exit, case_2_missing_code, case_3_unexpected_code,
                case_4_golden_off_by_one_byte, case_5_does_not_parse,
                case_6_generator_off_by_one_line, case_7_sweep_silently_skipped]
    for i, fn in enumerate(builders, 1):
        if i == 6:
            rep.pend(
                "self-check case 6 (cycle 0.5)",
                "a generator whose output differs from the committed table by "
                "one line. `tools/gen_tzdb.py` does not exist and no table is "
                "committed, so there is nothing to perturb. THE MECHANISM IS "
                "ALREADY HERE AND ALREADY RED-TESTED: `repro.py --between` runs "
                "a generator between two builds and requires the IR unchanged, "
                "and cycle 0.0.2 §5.3 drove it red against a generator whose "
                "rows came out of an unsorted `set`, with the sorted twin green "
                "through the identical code path.")
            continue
        c = fn(root, man, base)
        ok = _report_case(rep, c) and ok
    ok = _report_case(rep, case_8_failsafe_deleted(root, man, base, npkc)) and ok
    ok = _report_case(rep, case_9_memory_disagrees(root, man, base)) and ok
    for fn in (case_10_layout_pin_wrong, case_11_other_target,      # TM-209
               case_12_code_named_once, case_13_silent_site):       # TM-210
        ok = _report_case(rep, fn(root, man, base)) and ok

    problems = (part_b(rep, base) + part_b_specs_current(rep, base)
                + part_b_view_exempt(rep, base))
    if problems:
        ok = False
        rep.fail("self-check: the tree checks", "%d of them did not behave"
                 % len(problems))
        for p in problems:
            rep.note("")
            for line in p.splitlines():
                rep.note(line)
    else:
        rep.say("  ok    %-46s %s"
                % ("the tree checks",
                   "%d planted violation(s) caught, %d clean control(s) silent"
                   % (TREE_PLANTS, TREE_PLANTS)))

    bld = build_mod.Build(root, man, npkc, npkrt, os.path.join(root, "build"))
    problems = part_c(rep, root, bld, base)
    if problems:
        ok = False
        rep.fail("self-check: the S-6 arm generator", "%d disagreement(s)"
                 % len(problems))
        for p in problems:
            rep.note("")
            for line in p.splitlines():
                rep.note(line)
    else:
        rep.say("  ok    %-46s %s"
                % ("the S-6 arm generator",
                   "%d specimen(s): computed == NITPICK-REACH-003's own list, "
                   "both directions" % len(CALIBRATION)))

    problems = part_d(rep, root, man, base, npkc, npkrt)
    if problems:
        ok = False
        rep.fail("self-check: the verdict mechanisms", "%d of them did not "
                 "behave" % len(problems))
        for p in problems:
            rep.note("")
            for line in p.splitlines():
                rep.note(line)
    else:
        rep.say("  ok    %-46s %s"
                % ("the verdict mechanisms",
                   "%d specimen(s) for `_verdict`; exemption, defect corpus "
                   "and header sweep each driven RED and silent on the "
                   "control" % len(VERDICT_SPECIMENS)))

    problems = part_e(rep, root, man, base, npkc, npkrt)
    if problems:
        ok = False
        rep.fail("self-check: the reader", "%d disagreement(s) with the "
                 "compiler's lexer" % len(problems))
        for p in problems:
            rep.note("")
            for line in p.splitlines():
                rep.note(line)
    else:
        rep.say("  ok    %-46s %s"
                % ("the reader (lexical.py)",
                   "E1: %d lines of every form read back, %d import(s) as the "
                   "compiler reads them; E2: the pinned compiler runs the %d "
                   "observable forms it names to 0; E3: it runs %d spellings "
                   "of a number to their values, and the literal reader reads "
                   "each the same"
                   % (_LEX_TEXT.count("\n"), len(_LEX_IMPORTS),
                      len(_FORMS_EXIT), len(_NUM_LINES))))
    return ok


def _report_case(rep, c):
    if c is None:
        return True
    name = "self-check case %d: %s" % (c.num, c.title)
    if c.problems:
        rep.fail(name, "the harness did NOT catch its planted fault")
        for p in c.problems:
            rep.note("")
            for line in p.splitlines():
                rep.note(line)
        return False
    rep.say("  ok    case %d  %s" % (c.num, c.title))
    rep.say("                the fault was caught, and the control beside it "
            "came back green")
    return True
