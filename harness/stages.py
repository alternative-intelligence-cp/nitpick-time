"""Expectations, and the stages that hold a file to them. Step 5.

THE HEADER IS THE AUTHORITY (B-5), AND FROM THIS CYCLE IT ALSO DECIDES WHAT KIND
OF TEST A FILE IS (O-X7, TM-119). A `[[test]]` entry selects by DIRECTORY and
never by file, so one `program` entry over `tests/probe/` cannot be true about
both the nineteen files carrying `expect-exit:` and the seven carrying
`expect-error:`. It dispatches per file instead:

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

from build import BuildError, run

KEYS = ("expect-exit", "expect-error", "expect-error-at", "expect-golden",
        "stress", "argv", "env")

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
    env = env_for(e)
    st, out = run([exe] + e.argv, env=env)
    if st != e.exit:
        detail = ["%s exited %d; the header expects %d" % (label, st, e.exit)]
        if e.env:
            detail.append("      environment: %s"
                          % " ".join("%s=%s" % kv for kv in sorted(e.env.items())))
        if out.strip():
            detail.extend("      " + l for l in out.rstrip().splitlines())
        return "\n".join(detail)
    return None


def program(bld, rel, e, require_failsafe=True):
    """The `program` stage: both legs, the same exit required (B-3).

    Returns a list of problems -- empty is a pass -- and the two exit codes it
    saw, so the caller can print them whether or not anything is wrong.
    """
    src = os.path.join(bld.root, rel)
    stem = _stem(rel)
    problems = []
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
            bad = _run_once(exe, e, label if e.stress == 1
                            else "%s run %d/%d" % (label, i + 1, e.stress))
            if bad:
                problems.append(bad)
                break
    return problems
