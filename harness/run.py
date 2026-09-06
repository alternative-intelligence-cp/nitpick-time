#!/usr/bin/env python3
"""ntime's build-and-test runner. Cycle 0.0.3.

WHAT A GREEN RUN HERE IS, AND IS NOT.

  IT IS: the self-check green FIRST (V-15), so the runner has been shown able
  to fail SEVEN ways before it is believed about anything -- V-14 names eight
  and case 6 is `PEND` until cycle 0.5, which is a number this file claimed
  wrong for three cycles (TM-142); the manifest read
  and schema-checked; the three tools held to the pin's exact patch release;
  every `.npk` in the tree put in front of the real parser; the tree diffed
  against the documents that describe it by eight checks, each of which has
  itself been seen red on a planted violation; the library emitted, optimised,
  assembled and scanned; the IR proved identical from two working directories;
  and every test file held to its own header at -O0 and again under `opt -O2`.

  IT IS NOT a purity result from the SYMBOL SCAN. The undefined-symbol scan
  CANNOT SEE A SYSCALL -- `npk_sys6` is the runtime's own and is in the
  allowlist by construction (`elf.py`, B-2c, TM-118, RX-120). `check_purity` is
  a SOURCE-level check and is the only thing that answers that question.

  IT IS NOT evidence that the WHOLE library works. `src/core/` is real code
  since cycle 0.0.4 -- `Vec<T>`, `Bytes` and thirteen named bounds -- and the
  suite is evidence about it. The other five `src/` directories are still
  placeholders, so nothing here dates anything. AND IT IS NOT A MEMORY RESULT
  FOR THE MANAGED HALF: D-151's exit-0 trap counts `wild` allocations and a
  `buffer` is managed (TM-106), so a green run says nothing about `Bytes`
  (S-18b, S-18e).

  IT IS NOT a `--quick` or `--only` run. Both say so twice, at the top and at
  the bottom, and both refuse to print the word GREEN on its own.

STAGE ORDER, and each line is a reason:

  1  self-check   V-15: a harness that has not proven it can fail has not
                  proven anything, so this is FIRST and its failure is fatal
  2  manifest     nothing else can start; every path and flag comes from it
  3  toolchain    a wrong `llc` makes every later result meaningless
  4  tree sweep   cheap, and it is the check that finds files no test owns
  5  tree checks  the documents diffed against the tree, before anything builds
  6  parse        every `.npk` in front of the real parser, each exactly once
  7  library      one build per run, and it is a check in its own right
  8  repro        before the suite, because it builds the library again
  9  suite        the `[[test]]` entries, in manifest order
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import arms as arms_mod                                          # noqa: E402
import build as build_mod                                        # noqa: E402
import checks as checks_mod                                      # noqa: E402
import elf                                                       # noqa: E402
import manifest as manifest_mod                                  # noqa: E402
import repro as repro_mod                                        # noqa: E402
import stages                                                    # noqa: E402
import toolchain                                                 # noqa: E402

# The repository root, derived from THIS FILE rather than from the working
# directory, so `python3 harness/run.py` and `python3 /abs/path/run.py` mean the
# same run. B-4 wants two builds from different working directories to agree; a
# runner that resolved its own tree by `os.getcwd()` could not honour that.
# `--root` overrides it, and ONLY the self-check uses that.
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# THE EXEMPTION LIST IS THE DENOMINATOR'S OTHER HALF (TM-115, V-1c). A sweep
# reporting "no violations" and a sweep that opened nothing print the same line,
# so this check states how many files it opened, and every file it opened is
# either covered or named here with the reason it is not. The list is diffed in
# BOTH directions: a name here that no longer exists is itself a failure,
# because an exemption that outlives its file silently excuses the next file
# with that name.
#
# EVERY ENTRY CARRIES THE VERDICT IT WAS WRITTEN AGAINST, AND THAT IS TM-137.
# The first column is where the file STOPS -- `npkc`, `llc`, `ld`, `run:<code>`
# or `none` for a file no program roots -- and `check_exemptions_live` below
# re-derives it on every full run. Until 0.0.5 the both-directions diff checked
# only that the named file still EXISTED, and this list's own text claimed the
# entry "fails the both-directions diff" on the day its defect landed. It did
# not: O-N17 landed at pin `aaffb87`, `case1` and `case5` went from `llc` to
# `run:0`, the suite stayed GREEN, and nothing anywhere said so. An exemption
# whose reason has expired is exactly the shape this repository keeps finding
# -- a check whose NAME describes the property while its MECHANISM covers
# something narrower -- and it was in the mechanism written to prevent it.
EXPECT_EXEMPT = {
    "tests/probe/support/probe11_arms_lib.npk": ("none",
        "a library module probe 11 imports: no `main`, no `failsafe`, never "
        "run and never refused, so there is no exit code and no diagnostic to "
        "expect (tests/probe/README.md, 0.0.0 P-1)"),
    "tests/probe/support/probe11_calc_lib.npk": ("none",
        "the same: a support module, imported by probe 11c to price its "
        "arithmetic"),
    "tests/probe/support/probe11_silent_lib.npk": ("none",
        "the same: a support module that declares no error at all, the control "
        "for TM-107's per-module arm bill"),
    # O-N17's two reproductions ARE NOT HERE ANY MORE, and their absence is
    # the mechanism working. They were exempt because `npkc` accepted them at
    # exit 0 and `llc` then refused the IR, so neither `expect-error:` nor
    # `expect-exit:` was true of them. O-N17 landed at pin `aaffb87`: both now
    # link and run, both carry `// expect-exit: 0`, and both are ordinary
    # members of the `probe` stage. TM-137.
    "tests/probe/defect/fixed_array_len/case1_local_array_len.npk": ("npkc",
        "O-N18, a SECOND compiler defect, found at 0.0.4 (the compiler's "
        "DEF-22, FIXED in its 1.5.2e which is AHEAD of our pin): `.len` on a "
        "fixed-size "
        "array `T[N]` is accepted by the frontend and cannot be lowered "
        "(`NITPICK-EMIT-002`). `expect-error:` would be spellable here -- "
        "`npkc` DOES refuse it -- and is WRONG ANYWAY: EMIT-002's own text "
        "says the program is correct and the compiler is at fault, so "
        "asserting the refusal would turn the bug into a committed "
        "expectation and go RED on the day it is fixed. The controls (a slice "
        "`.len`, and the same array indexed without `.len`) are in that "
        "directory's README"),
    "tests/probe/defect/generic_owning_copy/case1_generic_bare_copy.npk":
        ("run:0",
        "O-N19, a THIRD compiler defect, found at 0.0.5, ACCEPTED as a "
        "soundness hole in the checker: `NITPICK-TYPE-046` is not "
        "enforced inside a GENERIC function body, so `T:answer = s[i]` at an "
        "owning `T` compiles, links and runs -- and the identical statement "
        "with `string` written out is refused (`case2`). No marker is right: "
        "`expect-error:` is false, because nothing refuses it; and "
        "`expect-exit: 0` would commit the repository to a program whose "
        "whole point is that exiting 0 is WRONG, and would go red on the day "
        "the check lands. The recorded verdict above is what makes that "
        "landing visible instead: `run:0` becomes `npkc` and this entry "
        "fails. TM-136"),
    "tests/probe/defect/generic_owning_copy/case4_use_after_free.npk":
        ("run:170",
        "the same defect's CONSEQUENCE: two owners of one body, the first "
        "dropped, the second read -- exit 170 is the allocator's 0xAA poison "
        "(D-183), which is the evidence that the copy was real. `expect-exit: "
        "170` is spellable and is declined for `case1`'s reason: it would "
        "make a use-after-free a committed expectation of this suite. The "
        "recorded verdict carries it instead, and `run:170` becomes `npkc` "
        "when the check lands. TM-136"),
}

# The directories a `.npk` may not live in and be missed: none. This walk is
# over the whole tree deliberately, because the file that went uncovered for two
# days was under `tests/probe/defect/`, which every directory-scoped sweep
# written before it had left out.
# The skip list now lives in `checks.py` beside the walk that uses it; this
# name is kept because the module's own prose cites it.
WALK_SKIP = checks_mod.WALK_SKIP

STEPS = 9


class Report:
    """Verdict lines, the failure list, and the counts. One place, so the
    summary cannot disagree with what was printed.

    EVERYTHING GOES THROUGH THIS OBJECT, INCLUDING THE SKIPS. A `--quick` run
    that announced its skipped sweeps by writing to stdout directly would let
    the transcript and the summary disagree about what ran, which is precisely
    the failure `--verdicts` was built to make impossible.
    """

    def __init__(self, verdicts_path=None):
        self.failures = []
        self.units = 0
        self.passed = 0
        self.skipped = []
        self.pending = []
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

    def note(self, line):
        self.say("        %s" % line)

    def skip(self, what, why):
        """A stage or unit deliberately not run. LOUD, and counted (P-19)."""
        self.skipped.append(what)
        self.say("  SKIP  %s" % what)
        for line in str(why).rstrip().splitlines():
            self.say("        %s" % line)
        self.verdicts.append("SKIP %s" % what)

    def pend(self, what, why):
        """A case that is not written yet. PRINTS AS PENDING, NEVER AS A PASS."""
        self.pending.append(what)
        self.say("  PEND  %s" % what)
        for line in str(why).rstrip().splitlines():
            self.say("        %s" % line)
        self.verdicts.append("PEND %s" % what)

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
# 4. the tree sweep
# ---------------------------------------------------------------------------

def all_npk(root):
    """ONE walk, and it lives in `checks.py` so `check_denominators` and this
    runner cannot disagree about what "every `.npk` in the tree" means."""
    return checks_mod.all_npk(root)


def exemptions_for(root):
    """`EXPECT_EXEMPT` names files in THIS repository, so it applies to THIS one.

    An inner run (`--root`, the self-check's scratch trees) gets an empty list
    and is told the number. That is not a loophole in V-1c: the rule is that an
    exemption is NAMED and diffed in both directions, and a list naming three
    files of another tree would fail the second half of it in every inner run
    -- which is what it did on this stage's first run, three times per case.
    """
    return EXPECT_EXEMPT if os.path.abspath(root) == HERE else {}


def check_expect_headers(rep, root, exempt_list=None):
    """Every `.npk` in the tree is in exactly ONE of three buckets.

      src/       judged by "it compiles" -- check 7 emits the whole graph the
                 entry reaches, and check 6 parses every file individually. A
                 library module has no exit code and no diagnostic to expect,
                 so it carries no marker.
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

    `exempt_list` IS A PARAMETER BECAUSE THIS ROW WAS PLANTED NOWHERE (TM-141).
    It is `TESTING.md` §2's row 13 and V-14c claimed "every check in §2 is
    commissioned the same way"; this was the row that made the claim false, and
    the row it was false about is the one TM-115 was written to create. Its
    stale-exemption branch -- V-1c's both-directions diff -- cannot be driven
    at all without handing it a list, which is why it never was.
    """
    files = all_npk(root)
    if exempt_list is None:
        exempt_list = exemptions_for(root)
    in_src, in_tests, orphan = [], [], []
    for rel in files:
        (in_src if rel.startswith("src/")
         else in_tests if rel.startswith("tests/")
         else orphan).append(rel)

    covered, exempt, bad = [], [], []
    for rel in in_tests:
        if rel in exempt_list:
            exempt.append(rel)
            continue
        try:
            stages.read(root, rel)
            covered.append(rel)
        except stages.MarkerError as err:
            bad.append((rel, err))

    rep.say("[4/%d] expect- header sweep -- %d .npk in the tree = %d src/ + %d "
            "tests/ + %d elsewhere" % (STEPS, len(files), len(in_src),
                                       len(in_tests), len(orphan)))
    rep.say("      of the %d under tests/: %d with a valid header, %d exempt of "
            "%d named, %d rejected" % (len(in_tests), len(covered), len(exempt),
                                       len(exempt_list), len(bad)))

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
    if len(covered) + len(exempt) + len(bad) != len(in_tests):
        rep.fail("expect- sweep", "the tests/ buckets do not sum to %d"
                 % len(in_tests))

    for rel in orphan:
        rep.fail("unowned .npk: %s" % rel,
                 "a .npk in neither src/ nor tests/ is judged by no check. Put "
                 "it under one, or give this sweep a bucket for it and say why.")
    for rel, err in bad:
        rep.fail("header: %s" % rel, err)
    for rel in sorted(exempt_list):
        if rel not in set(files):
            rep.fail("stale exemption: %s" % rel,
                     "EXPECT_EXEMPT names a file that is not in the tree. An "
                     "exemption that outlives its file is how a later file "
                     "with the same name gets excused without anyone deciding "
                     "to excuse it (V-1c).")


def _verdict(bld, root, rel, out_dir):
    """Where does this file STOP?  `npkc`, `llc`, `ld`, `run:<code>`, or
    `none` when nothing roots it.  Every status is taken from the call that
    produced it and paired with the artefact it should have written.
    """
    src = os.path.join(root, rel)
    with open(src, "r", encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    # A module with no `main` is not a program: `npkc` has no root to compile
    # and the question does not arise.  This is the `none` bucket, and it is
    # the support modules.
    if "func:main" not in text:
        return "none"
    stem = os.path.splitext(os.path.basename(rel))[0]
    ll = os.path.join(out_dir, stem + ".exempt.ll")
    obj = os.path.join(out_dir, stem + ".exempt.o")
    exe = os.path.join(out_dir, stem + ".exempt")
    for path in (ll, obj, exe):
        if os.path.exists(path):
            os.remove(path)
    st, _out = bld.emit_expecting_refusal(src, ll)
    if st != 0 or not os.path.isfile(ll):
        return "npkc"
    try:
        bld.assemble(ll, obj)
    except build_mod.BuildError:
        return "llc"
    if not os.path.isfile(obj):
        return "llc"
    try:
        bld.link([obj], exe)
    except build_mod.BuildError:
        return "ld"
    if not os.path.isfile(exe):
        return "ld"
    st, _out = build_mod.run([exe])
    return "run:%d" % st


def check_exemptions_live(rep, root, bld, exempt_list=None):
    """AN EXEMPTION'S REASON EXPIRES, AND NOTHING USED TO NOTICE.  TM-137.

    Every entry in `EXPECT_EXEMPT` records the verdict it was written against.
    This re-derives that verdict from the file itself, on every full run, and
    fails when it has changed -- because the reason an exemption exists is a
    claim about what the compiler does, and the compiler moves.

    THE CASE THAT MADE THIS NECESSARY IS THE ONE THE LIST ITSELF DESCRIBED.
    O-N17's two entries said, in the list, that on the day the defect landed
    the entry would "fail the both-directions diff until somebody deletes it".
    The diff checked only that the named file still EXISTED.  O-N17 landed;
    both files went from stopping at `llc` to running clean; the suite was
    green; nothing said a word.  A rule that asks a later reader to remember
    is not a mechanism, and this is the mechanism.

    `exempt_list` IS A PARAMETER SO THAT THIS CAN BE COMMISSIONED (TM-141).
    Until cycle 0.0.6 it read `EXPECT_EXEMPT` directly and could therefore only
    ever be run against a tree where every recorded verdict was correct -- so
    the mechanism written to catch a check that had never failed had itself
    never failed.  `selfcheck.py` part D hands it a list with one verdict moved
    and requires the red, and the same list unmoved and requires silence.
    """
    if exempt_list is None:
        exempt_list = exemptions_for(root)
    out_dir = os.path.join(root, "build", "exempt")
    os.makedirs(out_dir, exist_ok=True)
    checked, moved = 0, 0
    for rel in sorted(exempt_list):
        if rel not in set(all_npk(root)):
            continue                      # already failed as a stale exemption
        recorded = exempt_list[rel][0]
        got = _verdict(bld, root, rel, out_dir)
        checked += 1
        if got != recorded:
            moved += 1
            rep.fail("expired exemption: %s" % rel,
                     "the entry records that this file stops at `%s`; it now "
                     "stops at `%s`. An exemption is a claim about what the "
                     "compiler does, and that claim has changed. Either the "
                     "defect it stands on has landed -- in which case give "
                     "the file its `expect-` marker and delete this entry -- "
                     "or it has changed shape and the entry must say how "
                     "(TM-137)." % (recorded, got))
    rep.say("      exemption verdicts: %d of %d re-derived, %d moved"
            % (checked, len(exempt_list), moved))


DEFECT_DIR = "tests/probe/defect"


def run_defect_corpus(rep, root, bld, subdir=None):
    """THE REGRESSION CORPUS FOR EVERY DISCHARGED COMPILER DEFECT, ASSERTED.

    TM-141.  THE INVERSION THIS FIXES IS SHARP.  `tests/probe/defect/` holds
    24 `.npk`.  Three are EXEMPT from carrying an expectation, and those three
    had their verdict re-derived on every run since 0.0.5 (TM-137).  The other
    21 CARRY one -- `expect-exit: 121` for O-N10, `expect-error:
    NITPICK-BORROW-001` for O-N9, `expect-error: NITPICK-REACH-003` for O-N11,
    `expect-exit: 0` for the TM-137 fix -- and until cycle 0.0.6 NOTHING
    ASSERTED ANY OF THEM.  `nitpick.toml`'s `probe` entry is deliberately
    non-recursive, so the suite selected 0 of these 24; `check_expect_headers`
    checks only that a marker is WELL-FORMED; and `run_parse` compares only
    the diagnostic's phase family, never the code.

    So the files exempt from having an expectation were checked and the files
    that had one were not.  `TESTING.md` §1 described the coverage as "under
    `tests/` with an `expect-` marker of its own or a NAMED exemption", which
    reads as coverage and was, for 21 files, membership in a bucket nobody
    evaluated.

    WHY HERE AND NOT AS A `[[test]]` ENTRY.  The manifest selects by DIRECTORY
    with a non-recursive glob (`<path>/*.npk`), and this corpus is six
    subdirectories deep-ish; a recursive entry over `tests/probe/` would also
    sweep `support/`, which must never be run.  One entry per subdirectory
    would put the coverage rule in six places that can drift apart.  This walks
    the directory, so a NEW subdirectory is covered the day it is created --
    which is the property that failed here.

    THE ARITHMETIC IS PRINTED AND ASSERTED: 24 = 3 exempt + 21 asserted.  A
    corpus that grew a file nobody judged would change the sum.

    `subdir` IS A PARAMETER FOR THE SAME REASON `check_exemptions_live` takes
    one: a stage that can only be pointed at a corpus where everything already
    passes cannot be shown to fail.  `selfcheck.py` part D points it at a
    scratch corpus holding one file whose `expect-exit:` is wrong by one.
    """
    if subdir is not None:
        return _defect_corpus(rep, root, bld, subdir, {})
    if os.path.abspath(root) != HERE:
        # An inner tree -- a self-check scratch root -- has no defect corpus,
        # for the reason `exemptions_for` gives about `EXPECT_EXEMPT`: this
        # corpus names files in THIS repository, so it applies to this one.
        # Saying so with a number is the difference between "nothing to judge"
        # and "judged nothing".
        rep.say("      defect corpus: not this tree (--root), 0 file(s)")
        return
    return _defect_corpus(rep, root, bld, DEFECT_DIR, exemptions_for(root))


def _defect_corpus(rep, root, bld, subdir, exempt_list):
    base = os.path.join(root, subdir)
    if not os.path.isdir(base):
        rep.fail("defect corpus", "%s is not a directory. The regression "
                 "corpus for every discharged compiler defect lives there "
                 "(TM-141)." % subdir)
        return
    files = sorted(rel for rel in all_npk(root)
                   if rel.startswith(subdir + os.sep))
    exempt_here = [rel for rel in files if rel in exempt_list]
    judged = [rel for rel in files if rel not in exempt_list]
    refusals, runs, bad_header = 0, 0, 0
    for rel in judged:
        try:
            e = stages.read(root, rel)
        except stages.MarkerError as err:
            bad_header += 1
            rep.unit(rel, [str(err)])
            continue
        if e.is_refusal:
            refusals += 1
            rep.unit(rel, stages.refusal(bld, rel, e),
                     "refused %s" % ", ".join(sorted(set(e.errors))))
        else:
            runs += 1
            t0 = time.time()
            rep.unit(rel, stages.program(bld, rel, e),
                     "exit %d, both legs, %.1f s" % (e.exit, time.time() - t0))
    rep.say("      defect corpus: %d file(s) = %d exempt (verdict re-derived "
            "above) + %d asserted (%d run, %d refusal, %d unowned)"
            % (len(files), len(exempt_here), len(judged), runs, refusals,
               bad_header))
    if len(exempt_here) + len(judged) != len(files):
        rep.fail("defect corpus", "the buckets do not sum to %d" % len(files))


# ---------------------------------------------------------------------------
# 5. the tree checks
# ---------------------------------------------------------------------------

def run_tree_checks(rep, root, bld, extra=None):
    """`TESTING.md` §2's family. Every one runs on every full invocation (P-20).

    A CHECK WITH NOTHING TO CHECK RUNS ANYWAY AND SAYS SO WITH A NUMBER. That
    is not politeness: `check_no_owning_fields` over an empty set is the right
    answer, and running it today is what makes it exist -- already written,
    already commissioned -- on the day the first table type is written, rather
    than being invented in the same week as the thing it guards.
    """
    live = list(checks_mod.LIVE)
    rep.say("[5/%d] tree checks -- %d live, %d pending"
            % (STEPS, len(live) + 1, len(checks_mod.PENDING)))
    for fn in live:
        # `extra` carries the two denominators that need the manifest. Every
        # check takes `**_`, so the ones that do not want it never see it.
        res = fn(root, extra=extra)
        if res.problems:
            rep.fail(res.name, res.headline)
            for p in res.problems:
                rep.note("")
                for line in str(p).rstrip().splitlines():
                    rep.note(line)
        else:
            rep.say("  ok    %-24s %s" % (res.name, res.headline))
        for r in res.reports:
            rep.note("report: %s" % r)

    # check_failsafe_arms needs the compiler: it diffs its generated table
    # against what NITPICK-REACH-003 actually demands.
    res = arms_mod.check_failsafe_arms(
        root, bld, os.path.join(root, "build", "arms"))
    if res.problems:
        rep.fail(res.name, res.headline)
        for p in res.problems:
            rep.note("")
            for line in str(p).rstrip().splitlines():
                rep.note(line)
    else:
        rep.say("  ok    %-24s %s" % (res.name, res.headline))
    for r in res.reports:
        rep.note("report: %s" % r)

    for name, cycle, why in checks_mod.PENDING:
        rep.pend("%s (cycle %s)" % (name, cycle), why)


# ---------------------------------------------------------------------------
# 6. the parse stage
# ---------------------------------------------------------------------------

def run_parse(rep, root, bld):
    """Every `.npk` in the tree in front of the real parser, each exactly once.

    THE DENOMINATOR IS THE WHOLE TREE AND THAT IS WHY THE STAGE IS WORTH ITS
    COST. Re-measured at cycle 0.0.6: of the 78 `.npk` files here
    [[sweep: npk_total=78]] the library build roots 4 [[sweep: lib_reach=4]],
    the suite roots 41 [[sweep: suite_roots=41]], and 3 more are reached by
    `use` from a suite root [[sweep: support_total=3]] -- so 30 are put in
    front of the compiler by NOTHING ELSE. Five of those are the remaining
    `src/` placeholders and 24 are the reproductions under
    `tests/probe/defect/` [[sweep: defect_total=24]] -- the directory whose
    files went two days with no expectation at all (TM-115), and whose markers
    then went three cycles asserted by nothing (TM-141), for exactly this
    reason.

        78 = 4 (library) + 41 (suite roots) + 3 (reached by `use`) + 30

    EVERY NUMBER IN THAT SENTENCE IS TAGGED AND CHECKED (TM-142). It read
    `50 = 1 + 27 + 3 + 19` until cycle 0.0.6, three subcycles after the tree
    stopped being that size, and nothing anywhere compared it to the line this
    function PRINTS on every run.
    """
    files = all_npk(root)
    verdicts = {"parses": 0, "refused later": 0, "does not parse": 0}
    problems = 0
    rep.say("[6/%d] parse -- %d .npk, each rooted once at `npkc` (there is no "
            "parse-only mode: TM-123)" % (STEPS, len(files)))
    for rel in files:
        try:
            e = stages.read(root, rel)
        except stages.MarkerError:
            # No usable marker block. Every `src/` file is here by design, and
            # a broken header is check 4's finding, not this stage's.
            e = None
        probs, note = stages.parse_verdict(bld, rel, e)
        if probs:
            problems += 1
            for p in probs:
                rep.fail("parse: %s" % rel, p)
            continue
        if note.startswith("does not parse"):
            verdicts["does not parse"] += 1
            rep.say("  ok    %-46s %s" % (rel, note))
        elif "refused later" in note:
            verdicts["refused later"] += 1
        else:
            verdicts["parses"] += 1
    rep.say("      %d parse cleanly, %d parse and are refused by a later phase, "
            "%d must not parse and do not, %d failed"
            % (verdicts["parses"], verdicts["refused later"],
               verdicts["does not parse"], problems))
    if not files:
        rep.fail("parse", "opened 0 .npk files. A stage with an empty "
                          "denominator reports green while checking nothing "
                          "(V-1b).")
    total = sum(verdicts.values()) + problems
    if total != len(files):
        rep.fail("parse", "the verdicts sum to %d and %d files were opened"
                 % (total, len(files)))


# ---------------------------------------------------------------------------
# 7. the library
# ---------------------------------------------------------------------------

def build_library(rep, root, bld):
    """One build per run, both legs, scanned. It is a check, not an input.

    `npkc` has no separate-compilation mode (TM-117), so nothing links against
    this object -- every program re-emits the whole graph it reaches. What this
    step asserts is that the library's entry point emits, survives `opt -O2`,
    assembles at both optimisation levels, and needs no symbol the runtime does
    not define.
    """
    entry = bld.manifest["build"]["entry"]
    reached = build_mod.reachable_sources(os.path.join(root, entry))
    rep.say("[7/%d] library -- %s, reaching %d source(s) by `use`"
            % (STEPS, entry, len(reached)))
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
# 9. the suite
# ---------------------------------------------------------------------------

def select(root, entry):
    """The files a `[[test]]` entry selects: `<path>/*.npk`, non-recursive.

    NOT recursive, and the omission is load-bearing (the manifest says so at
    length): a plain glob over `tests/probe/` is exactly the 32
    [[sweep: probe_dir=32]] probe programs and excludes `support/` -- three
    library modules with no `main` -- and `defect/`, whose files are
    reproductions rather than tests of this library and are judged by
    `run_defect_corpus` instead (TM-141). The schema has no `recursive` key, so
    writing one is refused by name rather than silently ignored.
    """
    d = os.path.join(root, entry["path"])
    if not os.path.isdir(d):
        return None
    return sorted(
        os.path.join(entry["path"], n).replace(os.sep, "/")
        for n in os.listdir(d) if n.endswith(".npk"))


def run_entry(rep, root, bld, entry, only, quick):
    name, stage, path = entry["name"], entry["stage"], entry["path"]

    # B-9: `sweep` is separable but NOT optional, and a skip is announced
    # through this Report like everything else -- so the transcript and the
    # summary cannot disagree about what ran.
    if stage == "sweep" and quick:
        files = select(root, entry) or []
        rep.skip("[[test]] %s (%d file(s), stage `sweep`)" % (name, len(files)),
                 "--quick. THE EXHAUSTIVE GATE DID NOT RUN. `ntime`'s strongest "
                 "claim is a sweep over a whole domain (V-2, V-3), and this run "
                 "did not make it. The flag exists for a developer iterating on "
                 "one function; nothing is concluded from a run that used it "
                 "(B-9).")
        return

    files = select(root, entry)
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
    refusals, runs = 0, 0
    for rel in chosen:
        try:
            e = stages.read(root, rel)
        except stages.MarkerError as err:
            rep.unit(rel, [str(err)])
            continue

        # THE FILE'S OWN HEADER DECIDES (B-4c, TM-119) -- but an entry's stage
        # decides what KIND of member is legal in it. A `check` entry holding a
        # file that wants to run, or a `golden` entry holding one with no
        # golden, is an entry whose stage disagrees with its files, which is
        # worse than an empty one because it fails for a reason that is not the
        # library's.
        if stage == "check":
            if not e.is_refusal:
                rep.unit(rel, [
                    "%s is under a `check` entry and carries `expect-exit:`. "
                    "Every member of the `check` stage must be refused with "
                    "exactly its expected codes (B-7); a file that wants to "
                    "RUN belongs under a `program` entry." % rel])
                continue
            refusals += 1
            rep.unit(rel, stages.refusal(bld, rel, e),
                     "refused %s" % ", ".join(sorted(set(e.errors))))
            continue

        if e.is_refusal:
            refusals += 1
            rep.unit(rel, stages.refusal(bld, rel, e),
                     "refused %s" % ", ".join(sorted(set(e.errors))))
            continue

        runs += 1
        t0 = time.time()
        if stage == "golden":
            problems = stages.golden(bld, rel, e)
            note = "exit %d, both legs, golden `%s`, %.1f s" % (
                e.exit, e.golden or "<none>", time.time() - t0)
        elif stage == "sweep":
            problems = stages.sweep(bld, rel, e)
            note = "exit %d, both legs, swept %s, %.1f s" % (
                e.exit, e.sweep_count, time.time() - t0)
        else:
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

USAGE = ("usage: run.py [--only SUBSTRING] [--quick] [--verdicts PATH] "
         "[--root DIR]")


def main(argv):
    only, verdicts_path, quick, root = None, None, False, None
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
        elif a == "--root" and i + 1 < len(argv):
            root, i = argv[i + 1], i + 2
        elif a.startswith("--root="):
            root, i = a.split("=", 1)[1], i + 1
        elif a == "--quick":
            quick, i = True, i + 1
        else:
            sys.stderr.write("run.py: unknown argument %r\n%s\n" % (a, USAGE))
            return 2
        continue

    inner = root is not None
    root = os.path.abspath(root) if root else HERE
    rep = Report(verdicts_path)
    t0 = time.time()
    rep.say("ntime harness -- cycle 0.0.3. The self-check runs FIRST (V-15) and")
    # SEVEN, NOT EIGHT, AND THE NUMBER IS DERIVED (TM-142). V-14 names eight
    # cases and case 6 is `PEND` until cycle 0.5, so seven faults are planted.
    # This line said "eight" for three cycles and `0.0/README.md`'s Gate --
    # which says seven -- was the only place that had it right.
    import selfcheck as selfcheck_mod        # local: `selfcheck` imports this
    rep.say("this runner has been shown able to fail %d ways (V-14), of the "
            "%d V-14 names."
            % (selfcheck_mod.PLANTED_CASES, selfcheck_mod.V14_CASES))

    # P-22: a FILTERED RUN CONCLUDES NOTHING, and it says so twice.
    if only is not None:
        rep.say("")
        rep.say("*** --only %r: THIS RUN CONCLUDES NOTHING. A filtered run is "
                "for iterating; ***" % only)
        rep.say("*** nothing is committed on the strength of one.               "
                "             ***")
    if quick:
        rep.say("")
        rep.say("*** --quick: THIS RUN CONCLUDES NOTHING. The `sweep` stage is "
                "separable but  ***")
        rep.say("*** NOT OPTIONAL (B-9); the exhaustive gate is this library's "
                "strongest claim. ***")
    rep.say("")

    # 1. THE SELF-CHECK (V-15).
    if inner:
        rep.say("[1/%d] self-check -- SKIPPED: this is an inner run against "
                "%s." % (STEPS, root))
        rep.say("      `--root` exists so `selfcheck.py` can point this runner "
                "at a tree it has")
        rep.say("      planted a fault in. Running the self-check from inside "
                "one would not")
        rep.say("      terminate. An inner run concludes nothing about the "
                "library.")
    else:
        import selfcheck as selfcheck_mod
        if not selfcheck_mod.run(rep, HERE, STEPS):
            rep.say("")
            rep.say("RED -- the SELF-CHECK failed. Nothing below it was run "
                    "(V-15).")
            rep.say("A harness that has not proven it can fail has not proven "
                    "anything, so a")
            rep.say("green suite under a red self-check is the exact state "
                    "this ordering exists")
            rep.say("to make unreachable.")
            rep.write_verdicts()
            return 1

    # 2. the manifest
    try:
        man = manifest_mod.load(root)
    except manifest_mod.ManifestError as err:
        rep.say("[2/%d] manifest" % STEPS)
        rep.fail("nitpick.toml", err)
        rep.say("")
        rep.say("RED -- the manifest is where every path and flag comes from "
                "(P-12); nothing runs without it.")
        rep.write_verdicts()
        return 1
    rep.say("[2/%d] manifest -- %s %s, entry %s, %d [[test]] entr%s"
            % (STEPS, man["project"]["name"], man["project"]["version"],
               man["build"]["entry"], len(man["test"]),
               "y" if len(man["test"]) == 1 else "ies"))

    # 3. the toolchain
    rep.say("[3/%d] toolchain -- nitpick.toml pins LLVM %s exactly"
            % (STEPS, man["toolchain"]["llvm"]))
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

    # 4. the tree sweep -- runs even when the toolchain is wrong, because it
    #    needs no toolchain and its finding is worth having either way.
    check_expect_headers(rep, root)

    if not ok_env:
        rep.say("")
        rep.say("RED -- the toolchain is a build input (D-204). Nothing was "
                "built.")
        rep.write_verdicts()
        return 1

    bld = build_mod.Build(root, man, npkc, npkrt, os.path.join(root, "build"))
    rep.say("      allowlist: %d symbol(s), derived from %s (TM-118)"
            % (len(bld.allowlist), os.path.basename(npkrt)))

    # 4b. every exemption's recorded verdict, re-derived (TM-137). It belongs
    #     to step 4 and runs here because it needs a toolchain and step 4 does
    #     not -- step 4's finding is worth having even when the toolchain is
    #     wrong, and this one cannot be taken at all without one.
    check_exemptions_live(rep, root, bld)

    # 4c. and the OTHER 21 files in the same directory, whose `expect-` markers
    #     were asserted by nothing (TM-141). It runs beside 4b because the two
    #     together are what make the coverage claim in `TESTING.md` §1 true:
    #     3 exempt + 21 asserted = the whole corpus. Not under `--only`'s or
    #     `--quick`'s control, for 4b's reason -- this is coverage, not a
    #     suite a developer iterates on.
    run_defect_corpus(rep, root, bld)

    # 5. the tree checks. `suite_roots` and `lib_reach` need the manifest, so
    #    they are measured here and handed to `check_denominators`; everything
    #    else it needs is a property of the directory.
    suite_roots = set()
    for entry in man["test"]:
        for rel in (select(root, entry) or ()):
            suite_roots.add(rel)
    try:
        lib_reach = len(build_mod.reachable_sources(
            os.path.join(root, man["build"]["entry"])))
    except Exception:
        lib_reach = -1
    run_tree_checks(rep, root, bld,
                    extra={"suite_roots": len(suite_roots),
                           "lib_reach": lib_reach})

    # 6. parse
    run_parse(rep, root, bld)

    # 7. the library
    if build_library(rep, root, bld):
        # 8. repro
        roots = [man["build"]["entry"]]
        rep.say("[8/%d] repro -- %d root(s), each built twice from two working "
                "directories (B-4)" % (STEPS, len(roots)))
        for p in repro_mod.check(bld, roots, say=rep.say):
            rep.fail("repro", p)

    # 9. the suite
    rep.say("[9/%d] suite" % STEPS)
    for entry in man["test"]:
        run_entry(rep, root, bld, entry, only, quick)

    rep.say("")
    rep.write_verdicts()
    elapsed = time.time() - t0
    tail = ""
    if rep.skipped:
        tail += "; %d SKIPPED: %s" % (len(rep.skipped), ", ".join(rep.skipped))
    if rep.pending:
        tail += "; %d pending" % len(rep.pending)
    if rep.failures:
        rep.say("RED -- %d unit(s) of %d passed; %d failure(s) in %.1f s: %s%s"
                % (rep.passed, rep.units, len(rep.failures), elapsed,
                   ", ".join(rep.failures), tail))
        return 1
    if only is not None or quick or inner:
        why = ", ".join(
            x for x in (
                "--only %r" % only if only is not None else "",
                "--quick" if quick else "",
                "--root" if inner else "") if x)
        rep.say("GREEN under %s in %.1f s -- %d unit(s) ran%s."
                % (why, elapsed, rep.units, tail))
        rep.say("*** THIS CONCLUDES NOTHING. A filtered run iterates; it never "
                "concludes. ***")
        return 0
    rep.say("GREEN -- %d unit(s), 0 failures%s, %.1f s. Read this file's "
            "header for what that does not mean." % (rep.units, tail, elapsed))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
