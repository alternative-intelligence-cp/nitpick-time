"""The self-check. `TESTING.md` V-14 and V-15. Step 1, and it is step 1 on purpose.

A SUITE THAT ONLY EVER AGREES WITH WHAT IT IS HANDED REPORTS GREEN WHILE
CHECKING NOTHING. Everything else in `harness/` is a check; this is the only
thing that demonstrates the checks can FAIL. Cycle 0.0.2 ended with an honest
list of what its green run did not prove, and the first line of it was *"not
that the runner can fail"* -- three instruments had been commissioned by hand
there, and three checks is not a runner.

  V-14: feed the harness wrong expectations and require it to report every one
        as a failure. Seven cases, and this repository's cycle README adds an
        eighth of its own.
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
    with open(path, "w", encoding="utf-8") as fh:
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
        "llvm": tc["llvm"], "llc": arr(tc["llc-flags"]),
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
    (checks_mod.check_constants_named,
     ("src/zone/zone.npk", "mod:zone;\nfunc:f = int64() never fails "
                           "{ pass 86400i64; };\n"),
     ("src/cal/cal.npk", "mod:cal;\nfunc:f = int64() never fails "
                         "{ pass 86400i64; };\n"),
     "belongs to module `cal`"),
    (checks_mod.check_constants_named,
     ("src/cal/cal.npk", "mod:cal;\nfixed int64:YEAR_MAX = 9999i64;\n"),
     ("src/core/limits.npk", "mod:limits;\nfixed int64:YEAR_MAX = 9999i64;\n"),
     "Every named bound lives in"),
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
    # A TYPE WITH A VALIDATING CONSTRUCTOR, BUILT BY STRUCT LITERAL INSTEAD
    # (C-8b, TM-148). The language cannot take the literal away -- measured at
    # pin `aaffb87`, a consumer's `CivilDate{ year: 32000i32, month: 99u8,
    # day: 99u8 }` compiles, links and runs at exit 0 -- so this check is what
    # keeps `src/` itself inside the guarantee everything downstream is
    # written against.
    (checks_mod.check_civil_literal,
     ("src/zone/zone.npk", "mod:zone;\nfunc:f = CivilDate() never fails "
                           "{ pass CivilDate{ year: 1i32 }; };\n"),
     # THE CLEAN CONTROL IS THE BANNED FORM IN A COMMENT, and it is not a
     # contrivance: `src/lib.npk`'s own header spells `CivilDate{ year:
     # 32000i32, ... }` out in prose to document this rule, so a grep-shaped
     # version of this check fails the repository on the paragraph arguing for
     # it. That is the failure `check_purity` met on its first run, and this
     # row is where the comment-blanking is asserted rather than assumed.
     ("src/zone/zone.npk", "mod:zone;\n// CivilDate{ year: 32000i32 } is named\n"
                           "// here in PROSE, and CivilTime{ hour: 99u8 } too.\n"),
     "builds a `CivilDate` by struct literal"),
    # THE OWNER IS EXEMPT, AND THE EXEMPTION IS PROVEN RATHER THAN ASSERTED.
    # `src/cal/cal.npk` is where both constructors live, so it writes the
    # literal on the line after the last range check -- if the owner were not
    # skipped, this check would fail the module it exists to protect.
    (checks_mod.check_civil_literal,
     ("src/span/span.npk", "mod:span;\nfunc:f = CivilTime() never fails "
                           "{ pass CivilTime{ hour: 1u8 }; };\n"),
     ("src/cal/cal.npk", "mod:cal;\nfunc:f = CivilTime() never fails "
                         "{ pass CivilTime{ hour: 1u8 }; };\n"),
     "builds a `CivilTime` by struct literal"),
    (checks_mod.check_no_owning_fields,
     ("src/zone/zone.npk",
      "mod:zone;\nstruct:Row = {\n    int64:id;\n    string:name;\n};\n"
      "pub fixed Row[2]:TABLE = [];\n"),
     ("src/zone/zone.npk",
      "mod:zone;\nstruct:Row = {\n    int64:id;\n    int64:name_off;\n};\n"
      "pub fixed Row[2]:TABLE = [];\n"),
     "owning field"),
    # THE SAME VIOLATION, WRITTEN ON ONE LINE -- which is the form BOTH of
    # this repository's own structs take (`vec.npk:111`, `bytes.npk:60`) and
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
]


# THE COUNTS THIS FILE PRINTS, DERIVED RATHER THAN TYPED (TM-142).
#
#   V14_CASES     what `TESTING.md` V-14 names -- seven, plus this repository's
#                 own eighth (a program whose `failsafe` has been deleted).
#   PLANTED_CASES what is actually planted: case 6 is PEND until cycle 0.5.
#   TREE_PLANTS   `PLANTED`'s rows, plus THREE that no row can express:
#                 `check_layering`'s node half (the fault is a file that is NOT
#                 there); the whole-tree walk's nested-repository pruning
#                 (the subject is the WALK, not a check -- TM-146); and
#                 `check_specs_current` (which reports and never fails, so it
#                 is driven separately). Every one has a control beside it,
#                 which is why the two numbers printed are equal.
V14_CASES = 8
PLANTED_CASES = 7
TREE_PLANTS = len(PLANTED) + 3


def part_b(rep, base):
    """Every tree check, seen RED on a planted violation and GREEN beside it."""
    problems = []
    for i, (fn, bad, good, needle) in enumerate(PLANTED):
        name = fn.__name__
        red = _mini_tree(os.path.join(base, "planted", "%s_%d_bad" % (name, i)),
                         [bad])
        res = fn(red)
        if not res.problems:
            problems.append(
                "%s did not fire on a planted violation in %s. A check that "
                "has never failed has never been shown to work.\n      the "
                "plant was:\n%s" % (name, bad[0],
                                    "\n".join("        " + l
                                              for l in bad[1].splitlines())))
        elif not any(needle in p for p in res.problems):
            problems.append(
                "%s fired on the plant in %s but never said %r, so it may have "
                "fired for a different reason.\n      it said: %s"
                % (name, bad[0], needle, res.problems[0].splitlines()[0]))

        green = _mini_tree(
            os.path.join(base, "planted", "%s_%d_good" % (name, i)), [good])
        res = fn(green)
        if res.problems:
            problems.append(
                "%s fired on the CLEAN control in %s, so its red above is not "
                "evidence about the plant.\n      it said: %s"
                % (name, good[0], res.problems[0]))

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
    _write(os.path.join(where, "meta", "DECISIONS.md"),
           "# Decisions\n\n### %s - a decision that exists\n" % ok_tm)
    _write(os.path.join(where, "meta", "specs", "SAFETY.md"),
           "# Safety\n\n**Rule %s.** A rule that exists.\n" % ok_s)
    _write(os.path.join(where, "CLAUDE.md"),
           "This cites %s, which resolves, and %s, which does not.\n"
           "It cites %s, which resolves, and %s, which does not.\n"
           % (ok_tm, bad_tm, ok_s, bad_s))
    res = checks_mod.check_specs_current(where)
    if res.problems:
        problems.append(
            "check_specs_current FAILED a run. It reports and never fails "
            "(TESTING.md §2): a renumbered citation is not a reason to stop a "
            "build.\n      it said: %s" % res.problems[0])
    got = " ".join(res.reports)
    for want in (bad_tm, bad_s):
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
# PART C -- the S-6 arm generator, calibrated on TM-107's own specimens
# ---------------------------------------------------------------------------

# Measured at pin `0dfddac` from `NITPICK-REACH-003`'s own identity list. Each
# row is one of TM-107's three constraints, and the arithmetic is written out
# because a number embedded in prose travels with the prose:
#
#   floor                                    = 4
#   silent_lib  = floor + 0 (declared, never raised)   = 4   <- constraint 1
#   arms_lib    = floor + 1 (one raised identity)      = 5
#   calc_lib    = floor + 4 (its own arithmetic)       = 8   <- constraint 2
#
# and 8 - 4 = 4 is `SAFETY.md` S-4b's measured "four extra arms" from a module
# that declares no error at all.
CALIBRATION = [
    ("tests/probe/support/probe11_silent_lib.npk", 4,
     {"Unreachable", "HeapOom", "HeapBadRequest", "WildLeak"},
     "constraint 1: it declares `pub error:EProbeSilent` and never raises it, "
     "so the identity arms NOTHING. An implementation counting DECLARATIONS "
     "would publish 5."),
    ("tests/probe/support/probe11_arms_lib.npk", 5,
     {"Unreachable", "HeapOom", "HeapBadRequest", "WildLeak",
      "probe11_arms_lib.EProbeZone"},
     "a `fail` SITE puts the identity in, and it arrives module-qualified."),
    ("tests/probe/support/probe11_calc_lib.npk", 8,
     {"Unreachable", "HeapOom", "HeapBadRequest", "WildLeak", "DivByZero",
      "DivOverflow", "IntOverflow", "OutOfBounds"},
     "constraint 2: it declares no error at all and still costs four extra "
     "arms, from its `/`, its `%`, its `+` and its one index."),
]


def part_c(rep, root, bld, base):
    """The generator against the compiler, on three modules with known bills."""
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
    real = {"Unreachable", "HeapOom", "HeapBadRequest", "WildLeak"}
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
# except `llc`/`ld`, which no spelling in this tree reaches at this pin.
VERDICT_SPECIMENS = [
    ("stops_at_npkc.npk", WIDE_LITERAL % {"mod": "stops_at_npkc"}, "npkc",
     "the frontend refuses it, so no `.ll` is written"),
    ("runs_clean.npk", TRIVIAL % {"mod": "runs_clean", "code": 0}, "run:0",
     "it builds all the way and the RUN is what is judged"),
    ("no_main_here.npk", "mod:no_main_here;\n\npub func:f = int64() never "
     "fails { pass 1i64; };\n", "none",
     "a module with no `main` is not a program, so the question does not "
     "arise -- this is the bucket the three `probe11` support modules are in"),
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

    problems = part_b(rep, base) + part_b_specs_current(rep, base)
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
