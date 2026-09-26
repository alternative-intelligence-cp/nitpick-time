"""Expectations, and the stages that hold a file to them. Step 5.

THE HEADER IS THE AUTHORITY (B-5), AND FROM THIS CYCLE IT ALSO DECIDES WHAT KIND
OF TEST A FILE IS (O-X7, TM-119). A `[[test]]` entry selects by DIRECTORY and
never by file, so one `program` entry over `tests/probe/` cannot be true about
both the 28 files carrying `expect-exit:` [[sweep: probe_exit=28]] and the 21
carrying `expect-error:` [[sweep: probe_error=21]]. It dispatches per file
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

from build import BuildError, run, run_capped, run_split

KEYS = ("expect-exit", "expect-error", "expect-error-at", "expect-golden",
        "stress", "argv", "env", "sweep-count", "heap", "cap")

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
        self.heap = []              # (field, op, n): the NPK_HEAP_STATS bounds (TM-184)
        self.cap = None             # (KiB, exit): the address-space belt (TM-186)
        self.measured = {}          # leg label -> {field: n}, as the run printed it
        self.capped = {}            # leg label -> the exit under the cap

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
            if name == HEAP_VAR:
                # TM-184. The harness owns this one: it sets it for a file that
                # carries `heap:` and for no other. And the runtime switches
                # the report on for the NAME -- `NPK_HEAP_STATS=0` prints the
                # line too, measured at `c3bdae2` -- so an `env:` spelling of it
                # would read as a switch it is not.
                raise MarkerError(
                    "%s:%d: `env` may not set %s. The harness sets it for a "
                    "file that carries a `heap:` marker and for no other, and "
                    "any value -- `0` included -- switches the report on "
                    "(TM-184)." % (rel, lineno, HEAP_VAR))
            if name in e.env:
                raise MarkerError("%s:%d: `env` sets %s twice" % (rel, lineno,
                                                                  name))
            e.env[name] = val
        elif key == "heap":
            # TM-184. `// heap: FIELD OP N`, one bound per line, repeatable: a
            # bound on the runtime's own `NPK_HEAP_STATS` line, which the
            # harness then asks for (`env_for`) and holds on both legs.
            m = re.fullmatch(r"(allocated|peak_live|count) (<=|>=) (0|[1-9]\d*)",
                             value)
            if not m:
                raise MarkerError(
                    "%s:%d: `heap` takes `FIELD OP N` -- FIELD one of %s, OP "
                    "`<=` or `>=`, N a non-negative integer -- not %r"
                    % (rel, lineno, ", ".join(HEAP_FIELDS), value))
            bound = (m.group(1), m.group(2), int(m.group(3)))
            if any(b[:2] == bound[:2] for b in e.heap):
                raise MarkerError("%s:%d: a second `%s %s`; a bound has one "
                                  "number" % (rel, lineno, bound[0], bound[1]))
            e.heap.append(bound)
        elif key == "cap":
            # TM-186. `// cap: N KiB, exit C` -- run again under an address-
            # space cap of N KiB (`ulimit -v N`), where the exit must be C.
            m = re.fullmatch(r"([1-9]\d*) KiB, exit (\d+)", value)
            if not m:
                raise MarkerError("%s:%d: `cap` takes `N KiB, exit C`, not %r"
                                  % (rel, lineno, value))
            if e.cap is not None:
                raise MarkerError("%s:%d: a second `cap`; a file is run under "
                                  "one" % (rel, lineno))
            e.cap = (int(m.group(1)), int(m.group(2)))

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
    if (e.heap or e.cap) and not e.is_run:
        raise MarkerError("%s: `heap` and `cap` describe a RUN, and a file "
                          "without `expect-exit` is never run (TM-184)" % rel)
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

# THE RUNTIME'S OWN ALLOCATION COUNTERS, ASKED FOR PER FILE (cycle 0.1.4b,
# TM-184). `NPK_HEAP_STATS` in a program's environment makes the runtime print
# ONE line on fd 2 as the process exits -- by any route, a clean `exit` or a
# trap's `failsafe` -- and nothing when it is absent:
#
#     heap: allocated=N peak_live=N count=N
#
# the bytes REQUESTED in total, the high-water mark of bytes live, and the
# number of allocations, `wild` and managed alike, at the sizes asked for (the
# compiler's `runtime/npkrt.ll`: `npk_hs_note_alloc`, `npk_hs_report`). They
# are a function of the program's own allocation sequence and of nothing
# else: a program that allocates nothing prints three zeros, and a
# 476-character `argv[0]` or a 20 KB environment moves no number -- measured
# at `c3bdae2`. So the variable is set for a file whose header BOUNDS the line
# and for no other: a line nobody asserts is a measurement thrown away.
HEAP_VAR = "NPK_HEAP_STATS"
HEAP_FIELDS = ("allocated", "peak_live", "count")
_HEAP_LINE = re.compile(rb"^heap: allocated=(\d+) peak_live=(\d+) count=(\d+)$",
                        re.MULTILINE)


def env_for(e):
    env = dict(BASE_ENV)
    env.update(e.env)
    if e.heap:
        env[HEAP_VAR] = "1"
    return env


def _heap_problem(e, label, err):
    """Hold one run's `heap:` line to the header's bounds. TM-184, TM-185.

    EXACTLY ONE LINE. None means the report never reached us -- a runtime
    without the instrument, or a program that closed fd 2 -- and there is
    then nothing measured, which is a failure and not a pass. Two means the
    program printed one of its own. Returns `(problem_or_None, numbers)`.
    """
    found = _HEAP_LINE.findall(err)
    if len(found) != 1:
        return ("%s: expected exactly one `heap: allocated=N peak_live=N "
                "count=N` line on stderr and found %d. The header bounds the "
                "runtime's %s report, so a run that printed none measured "
                "nothing, and a second line is not the runtime's (TM-184)."
                % (label, len(found), HEAP_VAR)), None
    got = dict(zip(HEAP_FIELDS, (int(x) for x in found[0])))
    bad = ["%s is %d; the header bounds it %s %d" % (f, got[f], op, n)
           for f, op, n in e.heap
           if (op == "<=" and got[f] > n) or (op == ">=" and got[f] < n)]
    if bad:
        return "%s: %s (TM-185)" % (label, "; ".join(bad)), got
    return None, got


# THE ADDRESS-SPACE BELT (TM-186), and its CONTROL, which is TM-131's rule with
# its instance corrected by measurement. TM-131 took a `ulimit -v` bound only
# beside `/bin/true` at the same cap, because below about 2.7 MiB every exit
# on the workbench is the dynamic loader's. At compiler `c3bdae2` that control
# no longer covers THIS runtime: a program that computes nothing and allocates
# nothing -- `peak_live=0` -- takes HeapOom (92) under every cap up to about
# 10.5 MiB, while `/bin/true` runs clean from 2.75 MiB, so between the two a
# 92 is the runtime's floor and not the program's leak. The control is
# therefore the FLOOR PROGRAM, linked against the same runtime: CAP_CONTROL
# below, the shape of `tests/probe/probe11d_floor_only.npk`, written into
# `build/` so that every tree the harness runs in has one -- the self-check's
# scratch trees included. It is built once and run once per cap, at -O0.
CAP_CONTROL = """mod:cap_control;

func:main = int32(cstring[]:_~argv) {
    exit 0i32;
};

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
_CAP_CONTROL = {}      # KiB -> None when the floor program ran clean, else why not


def _cap_control(bld, kib):
    if kib not in _CAP_CONTROL:
        why = None
        src = os.path.join(bld.out_dir, "cap_control.npk")
        with open(src, "w", encoding="utf-8") as fh:
            fh.write(CAP_CONTROL)
        try:
            exe = bld.build_program(src, "cap_control", False)
        except BuildError as err:
            why = "the floor program did not build (%s)" % err.step
        else:
            st, detail = run_capped([exe], dict(BASE_ENV), kib)
            if st != 0:
                why = "the floor program %s under the same cap" % detail
        _CAP_CONTROL[kib] = why
    return _CAP_CONTROL[kib]


def _capped_problem(bld, exe, e, label):
    kib, want = e.cap
    why = _cap_control(bld, kib)
    if why:
        return ("%s: at %d KiB the cap measures the RUNTIME, not this file: "
                "%s. A bound the floor program also fails is not a statement "
                "about the program under it (TM-131, TM-186)."
                % (label, kib, why))
    st, detail = run_capped([exe] + e.argv, env_for(e), kib)
    e.capped[label] = st
    if st != want:
        return ("%s under a %d KiB address-space cap %s; the header expects "
                "exit %d (TM-186)" % (label, kib, detail, want))
    return None


def memory_note(e):
    """The unit line's evidence: what the run MEASURED, not the bound alone.

    `-O0` first; "on both legs" when the optimised leg printed the same, and
    each leg written out when it did not. `run.py` appends it to every run
    member's verdict line, so the numbers a document quotes are the run's.
    """
    parts = []
    if e.measured:
        fields = [f for f in HEAP_FIELDS if any(b[0] == f for b in e.heap)]

        def show(label):
            return " ".join("%s=%d" % (f, e.measured[label][f]) for f in fields)
        legs = sorted(e.measured)
        if len(legs) == 2 and e.measured[legs[0]] == e.measured[legs[1]]:
            parts.append("heap %s on both legs" % show(legs[0]))
        else:
            parts.append("; ".join("heap %s at %s" % (show(l), l)
                                   for l in legs))
    if e.capped:
        codes = sorted(set(e.capped.values()), key=str)
        parts.append("exit %s under %d KiB%s"
                     % ("/".join(str(c) for c in codes), e.cap[0],
                        " on both legs" if len(e.capped) == 2
                        and len(codes) == 1 else ""))
    return "".join(", " + p for p in parts)


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
    if e.heap:
        bad, got = _heap_problem(e, label, err)
        if got is not None:
            e.measured.setdefault(label.split(" run ")[0], got)
        if bad:
            return bad, out
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
        # TM-186: the belt runs on every leg, after the run it belts -- a second
        # instrument that shares nothing with the first but the binary.
        if e.cap:
            bad = _capped_problem(bld, exe, e, label)
            if bad:
                problems.append(bad)
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
    cover the 37 files in this tree [[sweep: tests_error=37]] that must NOT
    compile -- they are refused at PARSE-001, LEX-004, PARSE-002, TYPE-009,
    TYPE-017, TYPE-046, TYPE-047, TYPE-079, TYPE-080, TYPE-084, BORROW-001,
    BORROW-012, RESOLVE-001, REACH-002 and REACH-003, and every family after
    the first three is a phase that only runs on something that parsed. (30
    until cycle 0.1.3c, whose port made six new refusals -- four copies of an
    owner at TYPE-046, one hidden field at TYPE-080 and one owning `Pod` impl at
    TYPE-047 -- and moved `generic_owning_copy/case5` to TYPE-017. 16, with
    EMIT-002 in place of TYPE-046, until cycle 0.1.0b: O-N18 and O-N19 landed
    at compiler `c3bdae2`, TM-154. 19 until cycle 0.1.0c, whose seals made
    `probe15` and four new probes refusals at TYPE-079 and TYPE-080, TM-156
    and TM-157. 26 until cycle 0.1.4c, whose re-pin made `fixed_move_out/`'s
    three `TYPE-084` refusals and whose `fixed_import_scope/` brought one
    refused `RESOLVE-001`, TM-189 and TM-192.)
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
    both directions, 7 304 484 x 2  [[sweep: domain_every_day_number=7304484]] -- 7 304 485 until cycle 0.1.1, TM-161)
    -- and an exhaustive loop that returns early exits 0 exactly like one that
    ran. Exit code cannot tell them apart, and neither can anything else
    OUTSIDE the program.

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
