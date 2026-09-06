"""Expectations, and the stages that hold a file to them. Step 5.

THE HEADER IS THE AUTHORITY (B-5), AND FROM THIS CYCLE IT ALSO DECIDES WHAT KIND
OF TEST A FILE IS (O-X7, TM-119). A `[[test]]` entry selects by DIRECTORY and
never by file, so one `program` entry over `tests/probe/` cannot be true about
both the 26 files carrying `expect-exit:` [[sweep: probe_exit=26]] and the 8
carrying `expect-error:` [[sweep: probe_error=8]]. It dispatches per file
instead:

    expect-error:  present  ->  a REFUSAL member. `npkc` must fail, and the SET
                               of codes it reports must EQUAL the set the header
                               names (B-7, D-237). Never assembled, never run.
    expect-exit:   present  ->  a RUN member. Emitted, scanned, assembled,
                               linked and run at -O0, then again through
                               `opt -O2` (B-3), the same exit both times.
    both           ->  a failure. The two say contradictory things.
    neither        ->  a failure, NOT a skip. A file no expectation owns is the
                       state the three `missing_failsafe` cases were in for two
                       days (TM-115).

THE MARKER BLOCK IS CONTIGUOUS FROM LINE 1, AND A LOOK-ALIKE BELOW IT IS A
FAILURE (TM-121). Two files in this tree carry `// expect-error: NITPICK-BORROW-
001".` in PROSE, at column zero, byte-identical to a real marker but for the
trailing quote -- and 0.0.1's reader, which scanned the whole leading comment,
would have read them as markers. A marker added below the block by somebody who
believed it took effect is the silent no-op this repository exists to prevent,
so the block ends at the first non-marker line and anything marker-shaped after
it is named and fails.
"""

import os
import re

from build import BuildError, run, run_split

KEYS = ("expect-exit", "expect-error", "expect-error-at", "expect-golden",
        "stress", "argv", "env", "sweep-count")

# Exactly `//`, one space, a known key, a colon. Nothing looser: `//      expect-
# error: ...` (six spaces, prose in `view_escape/case3`) must NOT match, and does
# not.
_MARKER = re.compile(r"^// (%s): ?(.*)$" % "|".join(KEYS))

# A diagnostic line: `NITPICK-XXX-000 path:line:col: message`.
_DIAG = re.compile(r"^(NITPICK-[A-Z0-9]+-\d+)\s+(\S+?):(\d+):(\d+):")


class MarkerError(Exception):
    """A header this reader will not guess about. Always names file and line."""


class Expect:
    """One file's expectations, as read from its header."""

    def __init__(self, path):
        self.path = path
        self.exit = None            # int, or None
        self.errors = []            # ordered, deduplicated on use
        self.error_at = []          # "line:col"
        self.golden = None
        self.stress = 1
        self.argv = []
        self.env = {}               # name -> value
        self.sweep_count = None     # int, the sweep stage's evidence (TM-122)

    @property
    def is_refusal(self):
        return bool(self.errors)

    @property
    def is_run(self):
        return self.exit is not None


def read(root, rel):
    """Read `rel`'s marker block. Raises `MarkerError` on anything ambiguous."""
    path = os.path.join(root, rel)
    e = Expect(rel)
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        lines = fh.read().splitlines()

    end = 0
    for i, line in enumerate(lines):
        if not _MARKER.match(line):
            end = i
            break
        end = i + 1

    for lineno, line in enumerate(lines[:end], 1):
        key, value = _MARKER.match(line).groups()
        value = value.strip()
        if key == "expect-exit":
            if e.exit is not None:
                raise MarkerError("%s:%d: a second `expect-exit`; a file has "
                                  "one exit" % (rel, lineno))
            if not re.fullmatch(r"\d+", value):
                raise MarkerError("%s:%d: `expect-exit` takes a non-negative "
                                  "integer, not %r" % (rel, lineno, value))
            e.exit = int(value)
        elif key == "expect-error":
            if not value.startswith("NITPICK-"):
                raise MarkerError("%s:%d: `expect-error` takes a diagnostic "
                                  "CODE, never message text (B-6): %r"
                                  % (rel, lineno, value))
            e.errors.append(value)
        elif key == "expect-error-at":
            if not re.fullmatch(r"\d+:\d+", value):
                raise MarkerError("%s:%d: `expect-error-at` takes `line:col`, "
                                  "not %r" % (rel, lineno, value))
            e.error_at.append(value)
        elif key == "expect-golden":
            e.golden = value
        elif key == "sweep-count":
            # TM-122. The number of cases the sweep must report having visited.
            if e.sweep_count is not None:
                raise MarkerError("%s:%d: a second `sweep-count`; a sweep has "
                                  "one domain" % (rel, lineno))
            if not re.fullmatch(r"[1-9]\d*", value):
                raise MarkerError(
                    "%s:%d: `sweep-count` takes a positive integer -- the SIZE "
                    "of the domain the sweep must visit, not %r. Zero is not "
                    "allowed: a sweep that must visit nothing is the state "
                    "this marker exists to make impossible."
                    % (rel, lineno, value))
            e.sweep_count = int(value)
        elif key == "stress":
            if not re.fullmatch(r"[1-9]\d*", value):
                raise MarkerError("%s:%d: `stress` takes a positive integer, "
                                  "not %r" % (rel, lineno, value))
            e.stress = int(value)
        elif key == "argv":
            e.argv = value.split()
        elif key == "env":
            # `// env: NAME=VALUE`, one variable per line, repeatable. TM-120.
            if "=" not in value:
                raise MarkerError("%s:%d: `env` takes `NAME=VALUE`, one "
                                  "variable per marker line, not %r"
                                  % (rel, lineno, value))
            name, _, val = value.partition("=")
            name = name.strip()
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
                raise MarkerError("%s:%d: `env` name %r is not an environment "
                                  "variable name" % (rel, lineno, name))
            if name in e.env:
                raise MarkerError("%s:%d: `env` sets %s twice" % (rel, lineno,
                                                                  name))
            e.env[name] = val

    # TM-121: a marker-shaped line below the block took effect on nobody.
    for lineno, line in enumerate(lines[end:], end + 1):
        if _MARKER.match(line):
            raise MarkerError(
                "%s:%d: a marker-shaped line BELOW the header block, where it "
                "does nothing: %s\n    The block is the run of marker lines "
                "starting at line 1 and ends at the first line that is not "
                "one. A marker added below it is a silent no-op, which is the "
                "shape this check exists to prevent (TM-121). If the line is "
                "prose, indent it so it is not marker-shaped."
                % (rel, lineno, line))

    if e.is_refusal and e.is_run:
        raise MarkerError(
            "%s: carries both `expect-error` and `expect-exit`. A file either "
            "must not compile or must run; it cannot do both (TM-119)." % rel)
    if not e.is_refusal and not e.is_run:
        raise MarkerError(
            "%s: carries neither `expect-error` nor `expect-exit`, so no check "
            "owns it. That is a failure and not a skip -- it is the state the "
            "three `missing_failsafe` cases were in for two days (TM-115)."
            % rel)
    if e.error_at and not e.is_refusal:
        raise MarkerError("%s: `expect-error-at` without `expect-error`" % rel)
    return e


# ---------------------------------------------------------------------------
# the run environment
# ---------------------------------------------------------------------------

# CONSTRUCTED, NEVER INHERITED (TM-120). A test program's environment is this
# base plus its own `// env:` markers, and nothing else. The reason is concrete
# rather than tidy: `probe09_environ_split` exits 30 when `TZ` is absent and 39
# when it is present and wrong, so a harness that passed its own environment
# through would give a different verdict on a developer's shell with `TZ=UTC`
# set than in CI without it -- a suite whose answer depends on who ran it, which
# is exactly what D-076 and B-4 exist to prevent.
#
# THE BASE IS NON-EMPTY, AND THAT IS MEASURED RATHER THAN CHOSEN. Built with an
# empty base, `probe09_environ_split` exits 10 -- `env.len <= 0`, one of its
# SUBSTANTIVE codes, meaning "`environ()` returned nothing". That is TM-116's
# failure through a second door: an unmet precondition arriving as a verdict
# about the language. The probes were written against a shell environment, which
# is never empty. One inert variable keeps `environ()` non-trivial, and being
# declared here rather than inherited keeps it identical on every machine.
BASE_ENV = {"NTIME_HARNESS": "1"}


def env_for(e):
    env = dict(BASE_ENV)
    env.update(e.env)
    return env


# ---------------------------------------------------------------------------
# the stages
# ---------------------------------------------------------------------------

def _stem(rel):
    return os.path.basename(rel)[:-4]


def refusal(bld, rel, e):
    """A file that must not compile. B-7/D-237: the code SETS must be equal."""
    src = os.path.join(bld.root, rel)
    ll = os.path.join(bld.out_dir, _stem(rel) + ".refused.ll")
    st, out = bld.emit_expecting_refusal(src, ll)

    if st == 0:
        return ["npkc exited 0. The header expects it to refuse with %s.%s"
                % (", ".join(sorted(set(e.errors))),
                   "" if not os.path.isfile(ll) else
                   " It also wrote %s." % ll)]

    got_codes, got_at = set(), set()
    for line in out.splitlines():
        m = _DIAG.match(line)
        if m:
            got_codes.add(m.group(1))
            got_at.add("%s:%s" % (m.group(3), m.group(4)))

    problems = []
    want_codes = set(e.errors)
    missing = sorted(want_codes - got_codes)
    unexpected = sorted(got_codes - want_codes)
    if missing:
        problems.append("expected and not reported: %s" % ", ".join(missing))
    if unexpected:
        # B-7 is the half people forget: an UNEXPECTED diagnostic fails a test
        # as surely as a missing one.
        problems.append("reported and not expected: %s (B-7: the set reported "
                        "must EQUAL the set expected)" % ", ".join(unexpected))
    for at in e.error_at:
        if at not in got_at:
            problems.append("expected a diagnostic at %s; got %s"
                            % (at, ", ".join(sorted(got_at)) or "none"))
    if problems:
        problems.append("npkc exit %d, verbatim:\n%s"
                        % (st, "\n".join("      " + l
                                         for l in out.rstrip().splitlines())))
    return problems


def _run_once(exe, e, label):
    """Run once. Returns `(problem_or_None, stdout_bytes)`."""
    env = env_for(e)
    st, out, err = run_split([exe] + e.argv, env=env)
    if st != e.exit:
        detail = ["%s exited %d; the header expects %d" % (label, st, e.exit)]
        if e.env:
            detail.append("      environment: %s"
                          % " ".join("%s=%s" % kv for kv in sorted(e.env.items())))
        text = (out + err).decode("utf-8", "replace")
        if text.strip():
            detail.extend("      " + l for l in text.rstrip().splitlines())
        return "\n".join(detail), out
    return None, out


def _legs(bld, rel, e, require_failsafe=True):
    """Build and run both legs (B-3). Returns `(problems, {label: stdout})`.

    The optimised leg is not an optional extra: the same program re-emitted
    through `opt -O2` + `llc -O2` must produce the same answer, and the first
    run of that instrument in the compiler project found a real defect that had
    passed for six cycles.
    """
    src = os.path.join(bld.root, rel)
    stem = _stem(rel)
    problems, captured = [], {}
    for optimised in (False, True):
        label = "opt -O2" if optimised else "-O0"
        try:
            exe = bld.build_program(src, stem, optimised, require_failsafe)
        except BuildError as err:
            problems.append("%s: %s failed -- %s" % (label, err.step,
                                                     err.detail))
            # The optimised leg builds on the -O0 leg's `.ll`; if that failed
            # there is nothing to optimise, so stop rather than report the
            # same fault twice in different words.
            break
        # `// stress: N` -- the same answer every time (V-11). The runs are
        # separate processes, so this catches "the clock went backwards between
        # two calls", which a single green run cannot.
        for i in range(e.stress):
            bad, out = _run_once(exe, e, label if e.stress == 1
                                 else "%s run %d/%d" % (label, i + 1, e.stress))
            captured.setdefault(label, out)
            if bad:
                problems.append(bad)
                break
    return problems, captured


def program(bld, rel, e, require_failsafe=True):
    """The `program` stage: both legs, the same exit required (B-3)."""
    problems, _ = _legs(bld, rel, e, require_failsafe)
    if e.sweep_count is not None:
        # TM-121's rule applied to a marker that is real but in the wrong
        # stage. `sweep-count` is read by the `sweep` stage and by nothing
        # else, so on a `program` member it is an expectation that does
        # nothing -- which is worse than none.
        problems.append(
            "%s carries `sweep-count`, which only the `sweep` stage reads. "
            "Here it is an expectation that does nothing (V-1f). Move the file "
            "under a `sweep` entry, or drop the marker." % rel)
    return problems


# ---------------------------------------------------------------------------
# the `parse` stage -- BUILD.md §3, TESTING.md §1
# ---------------------------------------------------------------------------

# THE PARSE PHASE'S TWO CODE FAMILIES, read out of the compiler at the pin
# rather than assumed: `NITPICK-LEX-*` is declared in
# `src/frontend/diag_codes.npk` (the lexer's) and `NITPICK-PARSE-*` in
# `src/frontend/parse_codes.npk` (the parser's). Every other family in that tree
# -- RESOLVE, TYPE, BORROW, MOVE, REACH, ASSIGN, LOCK, TAINT, WILDX, SUSPEND,
# RUNG, PICK, MACRO, DERIVE, EXTERN, DIAG -- is declared by a later phase, so a
# file reported with one of THOSE necessarily parsed.
PARSE_FAMILIES = ("NITPICK-LEX-", "NITPICK-PARSE-")

# `npkc` HAS NO PARSE-ONLY MODE, AND THAT IS THE MEASUREMENT THIS STAGE RESTS
# ON. Its usage line at pin `0dfddac` is
# `npkc <root.npk> [-o out.ll] [--obligations DIR] [--elide ...]
# [--extra-picky=no-wildx]` -- no `--parse`, no `-fsyntax-only`. `BUILD.md` §3
# and this subcycle's plan both name the compiler's `tools/parse_check` for this
# stage, and that tool is a `.npk` SOURCE FILE (`tools/parse_check.npk`, 131
# lines, importing twenty of the compiler's frontend modules). Building it would
# mean building the compiler -- from a tree that is AHEAD of our pin and moving,
# which W-18 forbids and which would put an UNPINNED parser behind a stage whose
# siblings are held to an exact LLVM patch release. So the stage asks `$NPKC`,
# the pinned artefact, and reads the CODE FAMILY of what comes back. TM-123.
#
# WHAT THAT COSTS AND WHAT IT BUYS, both measured at this cycle:
#   costs  ~0.8 s per file that compiles, because the whole pipeline runs and
#          every root re-emits the prelude (TM-117). A file that does not parse
#          costs 0.03 s -- it fails at once and writes nothing.
#   buys   MORE than `parse_check` would: a file that reaches this stage
#          clean has been through resolve, the type checker and reachability
#          as well. The stage asserts only the parse half, which is the half
#          that is true of every file in the tree.


def parse_verdict(bld, rel, e):
    """Hold one file to "it parses", or to "it does not" if its header says so.

    `e` may be `None` for a file with no marker block at all -- every `src/`
    file, which carries none by design (a library module has no exit code and
    no diagnostic to expect).

    THE RULE IS ONE LINE AND ITS CONSEQUENCE IS NOT OBVIOUS: a file must parse
    UNLESS its own header names a parse-phase code. That is what lets the stage
    cover the 16 files in this tree [[sweep: tests_error=16]] that must NOT
    compile -- they are refused at PARSE-001, LEX-004, PARSE-002, TYPE-009,
    BORROW-001, BORROW-012, REACH-002, REACH-003 and EMIT-002, and every family
    after the first three is a phase that only runs on something that parsed.
    TWO files in the tree are expected not to parse, and the check is that it
    is exactly those two: `probe02d_wide_literal_refused.npk` (LEX-004,
    PARSE-002) and, since cycle 0.1.0,
    `probe14_error_payload_refused.npk` (PARSE-001, an `error:` given a
    payload -- TM-147). This sentence said "exactly one" until the second
    arrived, which is the ordinary way a hand-written count in prose beside a
    tagged number goes stale: the TAG moves under `check_denominators` and the
    SENTENCE does not.
    """
    want_refusal = bool(e) and any(
        code.startswith(PARSE_FAMILIES) for code in e.errors)
    ll = os.path.join(bld.out_dir, _stem(rel) + ".parse.ll")
    st, out = bld.emit_expecting_refusal(os.path.join(bld.root, rel), ll)
    got = sorted({m.group(1) for m in
                  (_DIAG.match(l) for l in out.splitlines()) if m})
    parse_codes = [c for c in got if c.startswith(PARSE_FAMILIES)]

    if want_refusal:
        if parse_codes:
            return [], "does not parse: %s" % ", ".join(parse_codes)
        return ([
            "%s: its header names a parse-phase code (%s) and the parser "
            "accepted it. npkc exit %d%s." % (
                rel, ", ".join(c for c in e.errors
                               if c.startswith(PARSE_FAMILIES)), st,
                "" if not got else ", reporting " + ", ".join(got))
        ], "")
    if parse_codes:
        return ([
            "%s: the parser refused it -- %s. Every source in the tree is "
            "readable by the real parser, or the grammar has been quietly made "
            "partial (TESTING.md §1). npkc exit %d, verbatim:\n%s"
            % (rel, ", ".join(parse_codes), st,
               "\n".join("      " + l for l in out.rstrip().splitlines()))
        ], "")
    later = [c for c in got if not c.startswith(PARSE_FAMILIES)]
    return [], ("parses" if not later
                else "parses; refused later at %s" % ", ".join(later))


# ---------------------------------------------------------------------------
# the `golden` stage -- BUILD.md §3
# ---------------------------------------------------------------------------

def golden(bld, rel, e):
    """As `program`, and the emitted text matches the committed golden EXACTLY.

    Two assertions, and the second is the one a single-leg runner would miss:
    the bytes match the committed file, AND the two optimisation legs produced
    the same bytes as each other. A formatter whose output changed under
    `opt -O2` would otherwise pass whichever leg the golden was recorded from.
    """
    if not e.golden:
        return ["%s is a `golden` member and carries no `expect-golden:` "
                "marker. The stage has nothing to compare against, and a "
                "golden test with no golden is a `program` test wearing the "
                "wrong name -- which is a suite reporting green while checking "
                "nothing (B-8)." % rel]
    problems, captured = _legs(bld, rel, e)
    path = os.path.join(bld.root, os.path.dirname(rel), e.golden + ".txt")
    if not os.path.isfile(path):
        problems.append(
            "%s expects golden `%s`, and %s does not exist. A missing golden "
            "is a failure and not a skip." % (rel, e.golden,
                                              os.path.relpath(path, bld.root)))
        return problems
    with open(path, "rb") as fh:
        want = fh.read()
    legs = sorted(captured)
    if len(legs) == 2 and captured[legs[0]] != captured[legs[1]]:
        problems.append(
            "%s: the two optimisation legs wrote DIFFERENT bytes (%d at %s, %d "
            "at %s). B-3 requires the same answer from both, and for a golden "
            "member the output IS the answer." % (
                rel, len(captured[legs[0]]), legs[0],
                len(captured[legs[1]]), legs[1]))
    for label in legs:
        got = captured[label]
        if got == want:
            continue
        off = next((i for i in range(min(len(got), len(want)))
                    if got[i] != want[i]), min(len(got), len(want)))
        problems.append(
            "%s (%s): output does not match %s. %d B written, %d B expected; "
            "first difference at byte %d.\n      wrote:    %r\n"
            "      expected: %r" % (
                rel, label, os.path.relpath(path, bld.root), len(got),
                len(want), off, got[max(0, off - 20):off + 20],
                want[max(0, off - 20):off + 20]))
    return problems


# ---------------------------------------------------------------------------
# the `sweep` stage -- BUILD.md B-9, TESTING.md V-2, and TM-122
# ---------------------------------------------------------------------------

_SWEPT = re.compile(rb"^swept (\d+)$", re.MULTILINE)


def sweep(bld, rel, e):
    """As `program`, but it must PROVE it did the work. TM-122.

    THIS IS THIS LIBRARY'S MOST PLAUSIBLE WAY TO BE GREEN AND WRONG, and the
    reason is structural rather than hypothetical. `ntime`'s strongest claim is
    an exhaustive sweep (V-2, V-3: every day in [-9999-01-01, +9999-12-31],
    both directions, 7 304 485 x 2) -- and an exhaustive loop that returns
    early exits 0 exactly like one that ran. Exit code cannot tell them apart,
    and neither can anything else OUTSIDE the program.

    So the evidence has to come from the program: a sweep member prints
    `swept <N>` and the harness requires N to equal the `// sweep-count:` its
    header declares. A sweep that returned after one iteration prints `swept 1`
    and is red; one that never entered the loop prints `swept 0` or nothing and
    is red; one whose domain was silently narrowed is red at the number.

    THE OTHER TWO WAYS A SWEEP DOES NOT RUN ARE CAUGHT ELSEWHERE, and all three
    are needed: an entry that selects no files fails in `run.py`'s `run_entry`
    (a suite naming an empty directory), and `--quick` announces what it skipped
    through the SAME `Report` object every other line goes through, so the
    summary and the transcript cannot disagree about it.
    """
    problems, captured = _legs(bld, rel, e)
    if e.sweep_count is None:
        problems.append(
            "%s is a `sweep` member and declares no `// sweep-count:`. The "
            "stage would then assert only its exit code, which is exactly what "
            "an exhaustive test that quietly did not run also produces. A "
            "sweep with no declared domain is not a sweep." % rel)
        return problems
    for label in sorted(captured):
        out = captured[label]
        found = _SWEPT.findall(out)
        if len(found) != 1:
            problems.append(
                "%s (%s): expected exactly one `swept <N>` line on stdout and "
                "found %d. The header declares a domain of %d; without the "
                "line there is no evidence the sweep ran at all, and an "
                "exhaustive loop that returned early exits 0 just like one "
                "that finished."
                % (rel, label, len(found), e.sweep_count))
            continue
        got = int(found[0])
        if got != e.sweep_count:
            problems.append(
                "%s (%s): swept %d of the %d its header declares -- %d case(s) "
                "were NOT visited. This is the failure V-14 case 7 exists for: "
                "the run is green on exit code and the exhaustive claim is "
                "false." % (rel, label, got, e.sweep_count,
                            e.sweep_count - got))
    return problems
