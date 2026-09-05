"""`check_failsafe_arms` -- the S-6 generator, and the compiler as its oracle.

WHAT S-6 ASKS FOR. The exact arm set a consuming program owes, per import, is
GENERATED into the documentation and checked by a test that builds a program
importing each public module and asserts its `failsafe` compiles with exactly
the documented arms AND NO MORE. An out-of-date arm list is the kind of document
that goes stale silently, so it is derived, not written.

THE THREE CONSTRAINTS TM-107 MEASURED, EACH OF WHICH THE OBVIOUS IMPLEMENTATION
GETS WRONG -- and each of which has a specimen in this tree, so none of them is
taken on trust:

  1. IT COUNTS `fail`, `?!` AND `!!!` SITES, NEVER `error:` DECLARATIONS.
     `tests/probe/support/probe11_silent_lib.npk` declares `pub
     error:EProbeSilent` and never raises it. Measured at pin `0dfddac`: a
     program importing it owes FOUR identities -- the floor -- and
     `EProbeSilent` is NOT among them. An implementation that counted
     declarations would publish five and be wrong in the direction no build
     can catch (constraint 3).

  2. IT INCLUDES THE SYSTEM ARMS THE IMPORTED SUBGRAPH'S ARITHMETIC ARMS.
     `probe11_calc_lib.npk` declares no error at all and costs an importing
     program EIGHT: the floor of four, plus `DivByZero` and `DivOverflow` from
     its `/` and `%`, `IntOverflow` from its `+` and `-`, and `OutOfBounds`
     from its one index. 8 - 4 = 4, which is S-4b's measured "four extra arms"
     from a module that declares nothing. A table that listed only declared
     identities would be short by exactly those four for every row that
     imports `cal`.

  3. "AND NO MORE" IS THIS HARNESS'S ASSERTION, NEVER THE COMPILER'S. A
     SUPERSET OF THE REQUIRED ARMS COMPILES -- `probe07_negative_div.npk`
     names `(OutOfBounds)`, contains no index expression, and exits 0. So a
     published table that OVERSTATES the bill would never turn a build red,
     and the only thing that can catch it is a set equality asserted here. It
     is asserted in BOTH directions below, which is the whole reason this file
     computes a bill from source instead of reading one out of the compiler
     and reprinting it.

THE ORACLE, AND WHY IT IS NOT CIRCULAR. `npkc` refuses a root with `main` and no
`failsafe` (`NITPICK-REACH-003`, the compiler's DEF-5, TM-112) and the
diagnostic LISTS THE IDENTITIES OWED. That list is the truth: it is what the
consuming program will actually have to write. This file computes the same set
from SOURCE -- from the `fail` sites and the arithmetic -- and the check is that
the two agree. The source computation is the thing under test and the thing S-6
publishes, because a table a reader can be shown the reason for is worth more
than a number scraped out of a diagnostic; the compiler is what says whether the
reasoning is right.

    computed from source  ==  what NITPICK-REACH-003 lists

A disagreement is a defect in THIS file, never in the compiler, and it is a red
run rather than a quiet drift.
"""

import os
import re

import build as build_mod
from build import BuildError
from checks import Result, strip_comments


# The unconditional floor, measured rather than read: a program with `main`, no
# `failsafe`, no import, no arithmetic and no allocation owes exactly these four
# (`tests/probe/probe11d_floor_only.npk`, and re-measured at this cycle).
FLOOR = ("Unreachable", "HeapOom", "HeapBadRequest", "WildLeak")

# The system arms, and the machinery in a module's TEXT that arms each. S-4b.
DIV_ARMS = ("DivByZero", "DivOverflow")
OVERFLOW_ARM = "IntOverflow"
INDEX_ARM = "OutOfBounds"

_REACH_003 = re.compile(r"--\s+(\d+)\s+identit(?:y|ies):\s+(.*?)\s+--")
_FAIL_SITE = re.compile(r"\bfail\s+([A-Z][A-Za-z0-9_]*)")
_PROPAGATE = re.compile(r"\?!|!!!")


def strip_strings(text):
    """Blank double-quoted string bodies, preserving length and line structure.

    OPERATOR DETECTION CANNOT READ STRINGS. `use "./cal/cal.npk".*;` contains a
    `/` and a `*` and arms nothing; a scanner that counted them would charge
    every module in the library for a division it does not perform. Blanking the
    body rather than deleting it keeps every line number and column honest.
    """
    out, i, n, in_str = [], 0, len(text), False
    while i < n:
        c = text[i]
        if in_str:
            if c == "\\" and i + 1 < n:
                out.append("  ")
                i += 2
                continue
            if c == '"':
                in_str = False
                out.append(c)
            else:
                out.append(" " if c != "\n" else "\n")
            i += 1
            continue
        if c == '"':
            in_str = True
        out.append(c)
        i += 1
    return "".join(out)


def code_only(path):
    """A file's text with comments AND string bodies blanked."""
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return strip_strings(strip_comments(fh.read()))


def _arith_arms(text):
    """The system arms a module's own text arms. S-4b, and each exclusion is
    a false positive this tree actually contains."""
    arms = set()
    # `/` and `%`. Both are DivByZero AND DivOverflow: the walk does not know a
    # divisor is a nonzero literal, and the over-approximation is the
    # compiler's deliberate direction (`reach.npk`: "the walk may require an arm
    # the backend's emitted guards never fire, never the reverse").
    if re.search(r"[/%]", text):
        arms.update(DIV_ARMS)
    # `+ - *` on plain integers. `->` is a POINTER, not a subtraction, and
    # `wild T->:items` is the shape this library's own `Vec<T>` takes -- so the
    # minus is matched only where a `>` does not follow it.
    if re.search(r"\+|\*|-(?!>)", text):
        arms.add(OVERFLOW_ARM)
    # An index. `[` also opens an array TYPE (`int64[12]`) and a fixed-array
    # literal, neither of which indexes anything, so the match wants a `[` that
    # follows a name or a `]`.
    if re.search(r"[A-Za-z0-9_\]]\s*\[", text):
        arms.add(INDEX_ARM)
    return arms


def compute_bill(tree, module_rel):
    """The arm set a program importing `module_rel` owes, computed from SOURCE.

    Over the module's whole `use` subgraph -- `build.reachable_sources`, the
    walk the build already uses, carrying a seen-set because a `use` cycle is
    legal (D-086). Returns `(arms, evidence)` where `evidence` says which rule
    put each arm in, so the published table can be read rather than believed.
    """
    root = os.path.join(tree, module_rel)
    subgraph = build_mod.reachable_sources(root)
    arms = set(FLOOR)
    evidence = {a: "the unconditional floor (S-4b)" for a in FLOOR}
    fail_sites, propagate_sites = 0, 0

    for path in subgraph:
        text = code_only(path)
        mod = os.path.basename(path)[:-4]
        for arm in _arith_arms(text):
            if arm not in arms:
                arms.add(arm)
                evidence[arm] = "arithmetic in %s (S-4b)" % mod
        # CONSTRAINT 1: SITES, never declarations. `pub error:X;` on its own
        # arms nothing -- `probe11f_declared_unraised.npk` measured that, and
        # `probe11_silent_lib.npk` is the specimen this check is calibrated on.
        for identity in _FAIL_SITE.findall(text):
            qualified = "%s.%s" % (mod, identity)
            if qualified not in arms:
                arms.add(qualified)
                evidence[qualified] = "a `fail` site in %s (S-4c)" % mod
            fail_sites += 1
        propagate_sites += len(_PROPAGATE.findall(text))

    return arms, {
        "evidence": evidence,
        "modules": len(subgraph),
        "fail_sites": fail_sites,
        "propagate_sites": propagate_sites,
    }


def measure_bill(bld, tree, module_rel, scratch_dir):
    """The arm set the COMPILER says is owed. `NITPICK-REACH-003`'s own list.

    Generates a program that imports the module, declares `main`, and declares
    NO `failsafe`. `npkc` refuses it and names every identity the absent handler
    would have to carry. The generated program contains no arithmetic of its
    own, so what comes back is the imported subgraph's bill and nothing else.
    """
    os.makedirs(scratch_dir, exist_ok=True)
    stem = "arm_" + os.path.basename(module_rel)[:-4]
    prog = os.path.join(scratch_dir, stem + ".npk")
    target = os.path.relpath(os.path.join(tree, module_rel), scratch_dir)
    with open(prog, "w", encoding="utf-8") as fh:
        fh.write(
            "// GENERATED by harness/arms.py -- not source, not committed.\n"
            "// A program that imports one module and declares NO `failsafe`,\n"
            "// so `NITPICK-REACH-003` lists every identity it would owe.\n"
            "mod:%s;\n"
            'use "%s".*;\n'
            "\n"
            "func:main = int32(cstring[]:_~argv) {\n"
            "    exit 0i32;\n"
            "};\n" % (stem, target.replace(os.sep, "/")))

    st, out = bld.emit_expecting_refusal(
        prog, os.path.join(scratch_dir, stem + ".ll"))
    if st == 0:
        raise BuildError(
            "arms", "%s: npkc exited 0 on a program with `main` and no "
                    "`failsafe`. The oracle this check rests on is "
                    "NITPICK-REACH-003 (TM-112); at a pin without it there is "
                    "no oracle and this check must not report success."
                    % module_rel)
    m = _REACH_003.search(out)
    if not m:
        raise BuildError(
            "arms", "%s: npkc exit %d, and no NITPICK-REACH-003 identity list "
                    "in its output:\n%s" % (module_rel, st, out.rstrip()))
    stated = int(m.group(1))
    listed = [x.strip() for x in m.group(2).split(",") if x.strip()]
    # THE DIAGNOSTIC'S OWN ARITHMETIC, CHECKED. It says "N identities" and then
    # lists them; if those two ever disagree the list is the half we parse and
    # the count is the half a reader believes, so neither is trusted alone.
    if stated != len(listed):
        raise BuildError(
            "arms", "%s: NITPICK-REACH-003 says %d identities and lists %d: %s"
                    % (module_rel, stated, len(listed), ", ".join(listed)))
    return set(listed)


def diff_bill(tree, bld, module_rel, scratch_dir):
    """Computed against measured. Returns `(problems, computed, measured, meta)`."""
    computed, meta = compute_bill(tree, module_rel)
    measured = measure_bill(bld, tree, module_rel, scratch_dir)
    problems = []
    short = sorted(measured - computed)
    over = sorted(computed - measured)
    if short:
        problems.append(
            "%s: the generated table is SHORT by %d arm(s) -- %s. A consumer "
            "written from it would not compile (REACH-002), which is the "
            "direction a build does catch, one cycle later and a long way from "
            "here." % (module_rel, len(short), ", ".join(short)))
    if over:
        problems.append(
            "%s: the generated table OVERSTATES by %d arm(s) -- %s. THIS IS "
            "THE DIRECTION NOTHING ELSE CATCHES (TM-107 constraint 3): a "
            "superset of the required arms compiles and runs, so a consumer "
            "would write arms it can never enter and no build would ever say "
            "so." % (module_rel, len(over), ", ".join(over)))
    return problems, computed, measured, meta


def public_modules(tree):
    """The `src/` modules a consumer can import: every layer's own file.

    `src/lib.npk` is excluded -- it is the umbrella, and its bill is the union
    of everything it re-exports, which is a row of its own once there is
    anything to re-export.
    """
    out = []
    base = os.path.join(tree, "src")
    if not os.path.isdir(base):
        return out
    for d in sorted(os.listdir(base)):
        sub = os.path.join(base, d)
        if not os.path.isdir(sub):
            continue
        for n in sorted(os.listdir(sub)):
            if n.endswith(".npk") and n[:-4] == d:
                out.append("src/%s/%s" % (d, n))
    return out


def check_failsafe_arms(tree, bld=None, scratch_dir=None, **_):
    """S-6: the per-import arm table, generated and diffed against the compiler.

    ZERO ROWS TODAY, AND THAT IS THE RIGHT ANSWER (P-20). `src/` holds six
    placeholder modules; none declares an error, none raises one, and none is
    re-exported, so there is no consumer-visible bill to publish. The check is
    wired now, reports its denominator, and is CALIBRATED against three modules
    whose bills were measured at cycle 0.0.0 -- see `selfcheck.py` §C, which is
    where it is shown able to fail.
    """
    modules = public_modules(tree)
    if bld is None:
        return Result("check_failsafe_arms",
                      "%d public module(s) in src/; not run (no toolchain)"
                      % len(modules),
                      ["check_failsafe_arms needs `npkc` and did not get it. "
                       "A check that could not run is a failure, not a skip."])
    scratch_dir = scratch_dir or os.path.join(tree, "build", "arms")
    problems, rows = [], []
    for rel in modules:
        try:
            probs, computed, measured, meta = diff_bill(
                tree, bld, rel, scratch_dir)
        except BuildError as err:
            problems.append("%s: %s" % (rel, err.detail))
            continue
        problems.extend(probs)
        rows.append("%s owes %d arm(s) over %d module(s): %s"
                    % (rel, len(measured), meta["modules"],
                       ", ".join(sorted(measured))))
    headline = ("%d public module(s) in src/, %d row(s) generated and diffed "
                "against NITPICK-REACH-003" % (len(modules), len(rows)))
    return Result("check_failsafe_arms", headline, problems, rows)
