"""The tree checks -- what the harness diffs against the documents. Step 5.

NOT TESTS. `TESTING.md` §2's family: each one diffs the library against a
document describing it, and in the compiler's tradition every one of them found
something on its first run. They run on EVERY full invocation, including the
ones whose subject is currently empty -- P-20, and the reason is the whole
lesson of TM-115: `check_no_owning_fields` over an empty set is the RIGHT
answer, and it is what makes the check exist on the day the first table type is
written rather than be invented under deadline.

EVERY CHECK STATES ITS DENOMINATOR, GREEN OR RED (V-1b). "Swept, no violations"
and "swept nothing" are the same line otherwise. A check whose subject is empty
says so with the number `0` in it, so a reader can tell the two apart without
reading this file.

EVERY CHECK HERE HAS BEEN SEEN TO FAIL. `selfcheck.py` §B plants one violation
per check in a scratch tree and requires the check to find it, then runs the
same check over the clean tree and requires silence. A check that has never
failed has never been shown to work, and the four that went live in this cycle
had never been run at all before it.

WHAT check_purity IS, AND WHAT NOTHING ELSE CAN BE READ AS.

  `check_purity` is a SOURCE-LEVEL check and it is the ONLY thing in this
  repository that answers "did this module touch the kernel". The build's
  undefined-symbol scan CANNOT: `npk_sys6` is the runtime's own syscall
  trampoline and is in the allowlist by construction, so a module that issues a
  raw syscall has exactly the same undefined set as one that does not. That was
  measured in `nitpick-regex` as RX-120 -- a symbol diff coming out EMPTY, 29
  symbols each way -- and reproduced here (`BUILD.md` B-2c, TM-118). A green
  symbol scan cited as a purity result is the failure mode this paragraph
  exists to prevent, and it is stated again in `elf.py`, `harness/README.md`,
  `BUILD.md` B-2c and `TESTING.md` §2 so that no reader meets one description
  without the other.
"""

import os
import re

import build as build_mod

# This repository's own root, from THIS file rather than from the working
# directory. The named-exemption tables below are statements about THIS tree,
# so the checks apply them only when that is the tree they are pointed at.
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# reading source the way a checker must: without its comments
# ---------------------------------------------------------------------------

def strip_comments(text):
    """Blank out `//` comments, respecting double-quoted strings.

    A CHECK OVER SOURCE MUST NOT READ PROSE, and in this tree that is not a
    hypothetical: `src/host/host.npk`'s header contains the word `mono_now()`
    while explaining the purity rule, and `src/lib.npk`'s contains
    `host_now_utc` while showing the shape a re-export line takes. A naive
    `grep` for either would fail this repository on its own documentation --
    twice, today, on the first run.

    Line structure is preserved (a comment becomes spaces, never disappears) so
    a finding can still cite a line number that matches the file.
    """
    out, i, n = [], 0, len(text)
    in_str = False
    while i < n:
        c = text[i]
        if in_str:
            if c == "\\" and i + 1 < n:
                out.append(c)
                out.append(text[i + 1])
                i += 2
                continue
            if c == '"':
                in_str = False
            out.append(c)
            i += 1
            continue
        if c == '"':
            in_str = True
            out.append(c)
            i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            j = text.find("\n", i)
            if j < 0:
                j = n
            out.append(" " * (j - i))
            i = j
            continue
        out.append(c)
        i += 1
    return "".join(out)


def code_lines(path):
    """`[(lineno, code_only_text)]` for a source file, comments blanked."""
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    return list(enumerate(strip_comments(text).splitlines(), 1))


def src_files(tree):
    """Every `.npk` under `<tree>/src/`, repo-relative, sorted."""
    root = os.path.join(tree, "src")
    out = []
    for dirpath, dirs, names in os.walk(root):
        dirs[:] = sorted(dirs)
        for n in sorted(names):
            if n.endswith(".npk"):
                out.append(os.path.relpath(os.path.join(dirpath, n), tree)
                           .replace(os.sep, "/"))
    return sorted(out)


def module_of(rel):
    """The layer a `src/` file belongs to: its directory, or `lib` for the root.

    `src/lib.npk` -> `lib`; `src/cal/cal.npk` -> `cal`. B-14 makes a file's
    `mod:` name its basename, but the LAYER is the directory -- `cal/` will hold
    more than one file and they are all in the same layer.
    """
    parts = rel.split("/")
    if len(parts) == 2:
        return "lib"
    return parts[1]


# ---------------------------------------------------------------------------
# the result shape
# ---------------------------------------------------------------------------

class Result:
    """One check's outcome: a headline that always carries a denominator, the
    problems (which fail the run) and the reports (which do not)."""

    def __init__(self, name, headline, problems=None, reports=None):
        self.name = name
        self.headline = headline
        self.problems = list(problems or ())
        self.reports = list(reports or ())

    @property
    def ok(self):
        return not self.problems


# ---------------------------------------------------------------------------
# check_layering -- BUILD.md B-17
# ---------------------------------------------------------------------------

# B-17's diagram as a partial order. `core` is the base; each layer may import
# strictly below itself. `host` is NOT in the chain: it may reach zone, cal and
# core, and NOTHING may reach IT except `src/lib.npk` -- which is `SAFETY.md`
# §3's purity boundary expressed as a layering rule, and the reason this check
# and `check_host_isolation` are two checks rather than one. They fail on
# different things: an `import` of host, and a mention of a `host_` name.
LAYER = {"core": 0, "cal": 1, "span": 2, "zone": 3, "fmt": 4}
HOST_MAY_IMPORT = {"zone", "cal", "core"}


def check_layering(tree, **_):
    """Every `use` edge in `src/` against `BUILD.md` §6's diagram.

    THE WALK IS `build.reachable_sources` AND `build.imports_of`, the ones the
    build already uses. A second walker would diverge from the first, and the
    interesting case is exactly where a naive one goes wrong: a `use` cycle is
    LEGAL in this language (D-086) and is still a decomposition mistake, so the
    walk carries a seen-set rather than assuming a tree.
    """
    files = src_files(tree)
    problems, edges = [], 0
    for rel in files:
        here = module_of(rel)
        abs_path = os.path.join(tree, rel)
        for imp in build_mod.imports_of(abs_path):
            edges += 1
            target = os.path.normpath(
                os.path.join(os.path.dirname(rel), imp)).replace(os.sep, "/")
            if not target.startswith("src/"):
                problems.append(
                    "%s imports `%s`, which leaves `src/`. `ntime` depends on "
                    "the language, its prelude and nothing else (B-10, "
                    "TM-027); an import that escapes the tree is a dependency "
                    "however it is spelled." % (rel, imp))
                continue
            there = module_of(target)
            if here == there:
                continue                      # within a layer: always fine
            if here == "lib":
                continue                      # the umbrella re-exports anything
            if there == "host":
                problems.append(
                    "%s imports `%s` (layer `host`). NOTHING imports `host` "
                    "except `src/lib.npk` and an application (B-17). That is "
                    "`SAFETY.md` §3's purity boundary written as a layering "
                    "rule: the impure module is a leaf, so a pure module "
                    "cannot acquire a clock by transitive import."
                    % (rel, imp))
                continue
            if here == "host":
                if there not in HOST_MAY_IMPORT:
                    problems.append(
                        "%s imports `%s` (layer `%s`). `host` may import "
                        "%s and nothing else (B-17)."
                        % (rel, imp, there,
                           ", ".join(sorted(HOST_MAY_IMPORT))))
                continue
            if here not in LAYER:
                problems.append(
                    "%s is in layer `%s`, which B-17's diagram does not name. "
                    "A new layer is a decision, not a directory." % (rel, here))
                continue
            if there not in LAYER:
                problems.append(
                    "%s imports `%s`, whose layer `%s` B-17's diagram does not "
                    "name." % (rel, imp, there))
                continue
            if LAYER[there] >= LAYER[here]:
                problems.append(
                    "%s (layer `%s`) imports `%s` (layer `%s`). B-17's arrows "
                    "point one way -- fmt -> zone -> span -> cal -> core -- and "
                    "`ntime`'s layers are acyclic. A `use` cycle is legal in "
                    "the language (D-086) and is still a decomposition mistake."
                    % (rel, here, imp, there))

    # The umbrella's reach, reported rather than asserted. It is 1 today because
    # `src/lib.npk` re-exports nothing yet, and the six placeholders are
    # therefore reached by no root at all -- which is exactly why the `parse`
    # stage roots every file in the tree rather than trusting the module graph.
    reached = build_mod.reachable_sources(os.path.join(tree, "src", "lib.npk"))
    headline = ("%d `use` edge(s) over %d file(s) in src/; the umbrella reaches "
                "%d of them" % (edges, len(files), len(reached)))
    if not files:
        problems.append("check_layering opened 0 files under src/. A check "
                        "with an empty denominator reports green while "
                        "checking nothing (V-1b).")
    return Result("check_layering", headline, problems)


# ---------------------------------------------------------------------------
# check_error_budget -- SAFETY.md §2
# ---------------------------------------------------------------------------

_ERROR_DECL = re.compile(r"^\s*(pub\s+)?error:([A-Za-z_][A-Za-z0-9_]*)")
# `SAFETY.md` §2's table rows: `| `ETimeValue` | raised when ... |`
_BUDGET_ROW = re.compile(r"^\|\s*`(E[A-Za-z][A-Za-z0-9_]*)`\s*\|")


def budget_from_spec(tree):
    """The identity names `SAFETY.md` §2's table declares. READ, never written.

    The whole point of this family is to diff the library against the document,
    so the document is parsed rather than transcribed. A transcription is the
    next stale copy, and S-2 makes the ceiling a decision -- so the ceiling has
    to come from where the decision is recorded.
    """
    path = os.path.join(tree, "meta", "specs", "SAFETY.md")
    if not os.path.isfile(path):
        # NOT A TRACEBACK. A check whose document is missing has a finding to
        # report -- "the thing I diff against is gone" -- and a stack trace is
        # the one shape that is neither a pass nor a legible failure.
        return None
    names, in_section = [], False
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith("## "):
                in_section = line.startswith("## 2.")
                continue
            if not in_section:
                continue
            m = _BUDGET_ROW.match(line)
            if m and m.group(1) not in names:
                names.append(m.group(1))
    return names


def check_error_budget(tree, **_):
    """Public `error:` declarations against `SAFETY.md` §2's table.

    TWO ASSERTIONS AND ONE REPORT, and the split is deliberate.

      FAILS on an identity the table does not name, and on the count exceeding
      the ceiling. S-2 makes a fourth identity a recorded decision AND a major
      version (TM-013), so it must not be possible to acquire one by writing a
      line of code.

      REPORTS the identities the table names and the library has not declared
      yet. Today that is all three, because no module computes anything --
      failing on it would make the check red until cycle 0.4 and a red that
      means "not written yet" is a red people learn to ignore.
    """
    named = budget_from_spec(tree)
    files = src_files(tree)
    if named is None:
        return Result(
            "check_error_budget",
            "not run: meta/specs/SAFETY.md is not in this tree",
            ["`meta/specs/SAFETY.md` is missing, and this check DIFFS AGAINST "
             "IT rather than against a copy of its table. Without the document "
             "there is no budget to hold the tree to, and reporting green "
             "would be reporting that a check ran when it did not."])
    declared, problems = {}, []
    for rel in files:
        for lineno, line in code_lines(os.path.join(tree, rel)):
            m = _ERROR_DECL.match(line)
            if not m:
                continue
            name = m.group(2)
            declared.setdefault(name, []).append("%s:%d" % (rel, lineno))

    for name in sorted(declared):
        if name not in named:
            problems.append(
                "`error:%s` is declared at %s and `SAFETY.md` §2's table does "
                "not name it. The budget is THREE (%s) and three is a ceiling "
                "(S-2): a fourth identity is a new mandatory `failsafe` arm in "
                "every consuming program, which REACH-002 enforces, so it is a "
                "recorded decision and a MAJOR version (TM-013) -- never a "
                "line of code."
                % (name, ", ".join(declared[name]), ", ".join(named)))
    if len(declared) > len(named):
        problems.append(
            "%d error identities are declared and `SAFETY.md` §2's table names "
            "%d." % (len(declared), len(named)))

    missing = [n for n in named if n not in declared]
    reports = []
    if missing:
        reports.append(
            "%d of %d budgeted identities are not declared yet (%s) -- "
            "expected: no module raises anything before cycle 0.1."
            % (len(missing), len(named), ", ".join(missing)))
    headline = ("%d identit(y|ies) declared over %d file(s) in src/, against a "
                "budget of %d" % (len(declared), len(files), len(named)))
    if not named:
        problems.append("`SAFETY.md` §2's table parsed to 0 identities. The "
                        "check reads the document rather than a copy, so an "
                        "empty parse means the document moved and this check "
                        "is now checking nothing (V-1b).")
    return Result("check_error_budget", headline, problems, reports)


# ---------------------------------------------------------------------------
# check_constants_named -- TESTING.md §2
# ---------------------------------------------------------------------------

# THE OWNER MAP IS THE SPECIFICATIONS' AND NOT THIS FILE'S OPINION. `SAFETY.md`
# S-16 says in as many words that *the calendar algorithms* divide by 4, 100,
# 400, 146097, 86400 and 1000000000, and `CALENDAR.md` §4 is where 146097 and
# 719468 appear in Hinnant's civil-from-days. So all four belong to `cal` as the
# documents stand TODAY. When 0.2 gives `span` its own nanosecond arithmetic the
# right move is to amend S-16 and this map together, in one commit -- which is
# the whole contract of this check family: it fails when the tree and the
# document disagree, and the fix is whichever of the two is wrong.
CONSTANT_OWNER = {
    "146097": "cal",        # days in 400 Gregorian years -- CALENDAR.md §4
    "719468": "cal",        # the 0000-03-01 era shift  -- CALENDAR.md §4
    "86400": "cal",         # seconds per day           -- SAFETY.md S-16
    "1000000000": "cal",    # nanoseconds per second    -- SAFETY.md S-16
}

# B-15: constants are SCREAMING_SNAKE. A *bound* is the subset this rule is
# about -- `limits.npk` exists so that every named bound is in one file with the
# specification rule that set it beside it (0.0.4's checklist).
_BOUND_DECL = re.compile(
    r"^\s*(?:pub\s+)?fixed\s+[A-Za-z_][A-Za-z0-9_<>\[\]]*\s*:"
    r"([A-Z][A-Z0-9_]*(?:_MAX|_MIN|_LIMIT|_BOUND))\b")
# A NUMERIC LITERAL CARRIES ITS TYPE SUFFIX, so `\b(\d+)\b` does not match
# `86400i64` -- the `i` is a word character and kills the trailing boundary.
# That is not a hypothetical: the first draft of this check used `\b…\b` and
# `selfcheck.py`'s planted `86400i64` walked straight past it. Every integer
# literal in this language is written `<digits><i|u><width>`, so the match ends
# at "not another digit" and the LEADING boundary is what keeps it off the
# `12` in `int64[12]` and the `64` in `int64`.
_NUMBER = re.compile(r"(?<![0-9A-Za-z_.])(\d{4,})(?![0-9])")


def check_constants_named(tree, **_):
    """No bound outside `src/core/limits.npk`; no magic number outside its owner.

    The four numbers are the ones a date library gets wrong by copying: 146097
    and 719468 are Hinnant's era constants, 86400 is a day that is not always
    86400 seconds to a caller who has heard of leap seconds, and 1000000000 is
    the one that decides whether a nanosecond field is `uint32`. Each belongs to
    exactly one module, and a second copy is how two modules come to disagree.
    """
    files = src_files(tree)
    problems, hits, bounds = [], 0, 0
    limits_rel = "src/core/limits.npk"
    for rel in files:
        mod = module_of(rel)
        for lineno, line in code_lines(os.path.join(tree, rel)):
            m = _BOUND_DECL.match(line)
            if m:
                bounds += 1
                if rel != limits_rel:
                    problems.append(
                        "%s:%d declares the bound `%s`. Every named bound "
                        "lives in `%s`, with the specification rule that set "
                        "it written beside it -- a bound in the module that "
                        "uses it is a bound nobody can review against the "
                        "range it is supposed to enforce."
                        % (rel, lineno, m.group(1), limits_rel))
            for num in _NUMBER.findall(line):
                if num not in CONSTANT_OWNER:
                    continue
                hits += 1
                owner = CONSTANT_OWNER[num]
                if mod not in (owner, "core"):
                    problems.append(
                        "%s:%d spells the magic number %s, which belongs to "
                        "module `%s` (SAFETY.md S-16, CALENDAR.md §4). Give it "
                        "a name in `%s` and import the name: a second literal "
                        "copy is how two modules come to disagree about a "
                        "constant neither of them owns."
                        % (rel, lineno, num, owner, limits_rel))
    headline = ("%d bound declaration(s) and %d owned-constant occurrence(s) "
                "over %d file(s) in src/" % (bounds, hits, len(files)))
    return Result("check_constants_named", headline, problems)


# ---------------------------------------------------------------------------
# check_no_owning_fields -- SAFETY.md §5 / TESTING.md §2
# ---------------------------------------------------------------------------

# An owning field is one the language will not let a table hold: a `string`, a
# `buffer`, an owning container, or a `wild` pointer. TYPE-046 makes owning
# values move-only, so a value COPIED out of a table cannot have one -- and a
# `fixed` table is read-only data that nothing may move out of.
_OWNING_TYPES = ("string", "buffer", "Bytes", "Vec<")
_FIXED_TABLE = re.compile(
    r"^\s*(?:pub\s+)?fixed\s+([A-Za-z_][A-Za-z0-9_]*)\s*\[\s*\d*\s*\]\s*:")
_STRUCT_DECL = re.compile(r"^\s*(?:pub\s+)?struct:([A-Za-z_][A-Za-z0-9_]*)")


def _structs(tree, files):
    """`{name: [(rel, lineno, field_text), ...]}` for every struct in `src/`."""
    out = {}
    for rel in files:
        cur = None
        for lineno, line in code_lines(os.path.join(tree, rel)):
            m = _STRUCT_DECL.match(line)
            if m:
                cur = m.group(1)
                out.setdefault(cur, [])
                continue
            if cur is None:
                continue
            if line.strip().startswith("};"):
                cur = None
                continue
            if ":" in line:
                out[cur].append((rel, lineno, line.strip()))
    return out


def check_no_owning_fields(tree, **_):
    """Every value stored in a table declares no owning field.

    NOTHING TO CHECK TODAY, AND THAT IS THE RIGHT ANSWER (P-20). `src/` holds
    six placeholders and one umbrella; there is no table and no struct, so this
    reports `0 of 0`. The check exists now so that cycle 0.1's zone tables meet
    an instrument that already works, rather than one written the same week as
    the thing it guards.
    """
    files = src_files(tree)
    structs = _structs(tree, files)
    problems, tables = [], 0
    for rel in files:
        for lineno, line in code_lines(os.path.join(tree, rel)):
            m = _FIXED_TABLE.match(line)
            if not m:
                continue
            tables += 1
            elem = m.group(1)
            for frel, flineno, ftext in structs.get(elem, ()):
                for owning in _OWNING_TYPES:
                    if owning in ftext:
                        problems.append(
                            "%s:%d stores `%s` in a table, and `%s` has an "
                            "owning field at %s:%d -- `%s`. Owning values are "
                            "move-only (TYPE-046), so a row copied out of a "
                            "table cannot carry one; the zone tables hold "
                            "OFFSETS into a name pool for exactly this reason "
                            "(ZONE_MODEL.md)."
                            % (rel, lineno, elem, elem, frel, flineno, ftext))
                        break
    headline = ("%d table(s) over %d file(s) in src/, against %d struct(s)"
                % (tables, len(files), len(structs)))
    return Result("check_no_owning_fields", headline, problems)


# ---------------------------------------------------------------------------
# check_raw_index -- TM-108 / SAFETY.md S-17b
# ---------------------------------------------------------------------------

RAW_INDEX_OWNERS = {
    ".items[": "src/core/vec.npk",
    ".ptr[": "src/core/bytes.npk",
}


def check_raw_index(tree, **_):
    """No `.items[` outside `vec.npk`, no `.ptr[` outside `bytes.npk`.

    `Vec<T>.items` is a `wild T->` and `Bytes`' body is a `buffer` indexed
    through its `.ptr` -- BOTH are bare pointers to the emitter, and the
    language does not bounds-check a bare pointer (TM-108, S-17b: the check
    attaches to the TYPE, and `ExprIndexExpr` has four branches of which only
    the pointer one omits `emit_bounds_guard`). So the accessor pair is the
    only bound that exists, and this check is what keeps every index inside it.
    """
    files = src_files(tree)
    problems, hits = [], 0
    for rel in files:
        for lineno, line in code_lines(os.path.join(tree, rel)):
            for needle, owner in RAW_INDEX_OWNERS.items():
                if needle in line:
                    hits += 1
                    if rel != owner:
                        problems.append(
                            "%s:%d indexes `%s` raw. That is a BARE POINTER "
                            "and the language does not bounds-check one "
                            "(TM-108, S-17b) -- an out-of-range index is a "
                            "wrong value, not a crash. Go through the accessor "
                            "in `%s`, which checks `0 <= i` as well as "
                            "`i < count`." % (rel, lineno, needle, owner))
    headline = ("%d raw-index site(s) over %d file(s) in src/, %d owner(s) "
                "allowed" % (hits, len(files), len(RAW_INDEX_OWNERS)))
    return Result("check_raw_index", headline, problems)


# ---------------------------------------------------------------------------
# check_purity -- SAFETY.md S-10. THE MOST IMPORTANT CHECK IN THE SUITE.
# ---------------------------------------------------------------------------

# S-10's ban list, verbatim. Each is matched CALL-SHAPED (`name(`) rather than
# as a bare word, because `open` and `write` are ordinary English and this check
# reads code, not prose -- see `strip_comments` above for the other half of that
# argument, which this tree needed on its first run.
PURITY_BAN = ("sys(", "mono_now(", "environ(", "read_file(", "open(", "write(")
HOST_DIR = "src/host/"


def check_purity(tree, **_):
    """`src/` outside `src/host/` against S-10's ban list. SOURCE-LEVEL.

    AND SOURCE-LEVEL IS THE POINT, NOT A LIMITATION TO APOLOGISE FOR. The
    build's undefined-symbol scan cannot answer this question at all: the
    runtime's own syscall trampoline `npk_sys6` is in its allowlist by
    construction, so a module that issues a raw syscall and one that does not
    have IDENTICAL undefined sets -- measured as `nitpick-regex`'s RX-120 (29
    symbols each way, diff empty) and reproduced here (TM-118, B-2c). This
    check is the only thing in the repository that answers "did this module
    touch the kernel", and a green symbol scan must never be cited for it.

    WHAT IT CANNOT SEE, stated so nobody over-reads this one either: a syscall
    reached through a name it does not know -- an alias, or a helper in a file
    it is not scanning. The defence against that is `check_host_isolation` plus
    B-17's layering, which together make `host` a leaf nothing may import.
    """
    files = [f for f in src_files(tree) if not f.startswith(HOST_DIR)]
    total = len(src_files(tree))
    problems = []
    for rel in files:
        for lineno, line in code_lines(os.path.join(tree, rel)):
            for banned in PURITY_BAN:
                if banned in line:
                    problems.append(
                        "%s:%d calls `%s` outside `src/host/`. Every function "
                        "in `ntime` outside `src/host/` is a pure function of "
                        "its arguments (S-7, TM-018): same arguments, same "
                        "value, on every machine, forever. That is what makes "
                        "this library testable with no double and portable by "
                        "rewriting one module -- and it is the claim the "
                        "undefined-symbol scan CANNOT check, because "
                        "`npk_sys6` is in its allowlist by construction "
                        "(B-2c, TM-118, RX-120)."
                        % (rel, lineno, banned.rstrip("(")))
    headline = ("%d banned form(s) over %d of %d file(s) in src/ (%s exempt); "
                "SOURCE-level -- the symbol scan cannot answer this (B-2c)"
                % (len(problems), len(files), total, HOST_DIR))
    if not files:
        problems.append("check_purity opened 0 files outside `src/host/`. An "
                        "empty denominator reports green while checking "
                        "nothing (V-1b).")
    return Result("check_purity", headline, problems)


_HOST_SYMBOL = re.compile(r"\bhost_[A-Za-z0-9_]*")
HOST_ISOLATION_EXEMPT = ("src/lib.npk",)


def check_host_isolation(tree, **_):
    """No module outside `src/host/` and `src/lib.npk` names a `host_` symbol.

    The second half of the purity boundary. `check_purity` catches a module
    that reaches the kernel ITSELF; this catches one that reaches it through
    `host`. Together with B-17's layering rule -- `host` is a leaf -- they make
    the impure module unreachable rather than merely discouraged.

    `src/lib.npk` is exempt because it is the umbrella: it re-exports `host`'s
    five functions and is the ONE file that may (B-17). Its exemption is named
    here rather than pattern-matched, per V-1c.
    """
    files = [f for f in src_files(tree)
             if not f.startswith(HOST_DIR) and f not in HOST_ISOLATION_EXEMPT]
    total = len(src_files(tree))
    problems = []
    for rel in files:
        for lineno, line in code_lines(os.path.join(tree, rel)):
            for m in _HOST_SYMBOL.finditer(line):
                problems.append(
                    "%s:%d names `%s`. Nothing outside `src/host/` and "
                    "`src/lib.npk` may (B-17, S-8): `host` is a LEAF of the "
                    "layering, so a pure module cannot acquire a clock by "
                    "transitive import. A function that needs `now` takes a "
                    "`Timestamp` as a parameter (S-9)."
                    % (rel, lineno, m.group(0)))
    headline = ("%d `host_` mention(s) over %d of %d file(s) in src/ (%s and "
                "%s exempt)" % (len(problems), len(files), total, HOST_DIR,
                                ", ".join(HOST_ISOLATION_EXEMPT)))
    return Result("check_host_isolation", headline, problems)


# ---------------------------------------------------------------------------
# check_specs_current -- REPORTS, DOES NOT FAIL
# ---------------------------------------------------------------------------

# Rule prefix -> the document that declares it, and the shape a declaration
# takes there. The compiler's own `D-nnn` decisions are DELIBERATELY ABSENT:
# they are declared in a repository this one may only read, the authority is the
# pinned commit rather than that repository's moving tree (W-18), and a check
# that silently answered "resolved" from an unpinned checkout would be worse
# than no check. They are cited here by number and verified by reading.
CITATION_SOURCES = {
    "TM": ("meta/DECISIONS.md", r"^### TM-%s\b"),
    "S": ("meta/specs/SAFETY.md", r"^\*\*Rule S-%s\b"),
    "B": ("meta/specs/BUILD.md", r"^\*\*Rule B-%s\b"),
    "V": ("meta/specs/TESTING.md", r"^\*\*Rule V-%s\b"),
    "M": ("meta/specs/TIME_MODEL.md", r"^\*\*Rule M-%s\b"),
    "Z": ("meta/specs/ZONE_MODEL.md", r"^\*\*Rule Z-%s\b"),
    "N": ("meta/specs/SPAN_MODEL.md", r"^\*\*Rule N-%s\b"),
    "F": ("meta/specs/FORMAT_MODEL.md", r"^\*\*Rule F-%s\b"),
    "C": ("meta/specs/CALENDAR.md", r"^\*\*Rule C-%s\b"),
}
_CITATION = re.compile(r"\b(TM|S|B|V|M|Z|N|F|C)-(\d+[a-z]?)\b")
SPEC_SCAN_DIRS = ("meta/specs", "meta/roadmap", "harness", "src", "tests")
SPEC_SCAN_ROOT_FILES = ("CLAUDE.md", "CONTRIBUTING.md", "README.md",
                        "nitpick.toml", "meta/DECISIONS.md",
                        "meta/OPEN_QUESTIONS.md")

# EXEMPTIONS ARE NAMED, CARRY THEIR REASON, AND ARE DIFFED IN BOTH DIRECTIONS
# (V-1c). Both of these were found by this check's FIRST run, and neither is a
# stale citation -- which is exactly why they are written down rather than
# filtered out by a cleverer pattern that would also hide a real one.
#
# `(file, rule)` -> why. `(file, None)` exempts the whole file.
CITATION_EXEMPT = {
    ("meta/roadmap/0.0/0.0.0.md", "S-23"):
        "it cites the SIBLING library's rule, and the sentence says so: "
        "\"The sibling `nitpick-regex`'s own S-23 table omits it too\". Every "
        "library in this ecosystem numbers its own `S-` rules, so the "
        "namespaces collide by design; a cross-repository citation is verified "
        "by reading that repository, and this one was.",
    ("harness/selfcheck.py", None):
        "it contains DELIBERATELY dangling citations as the fixtures that "
        "prove this check reports one. A check whose own test fixtures appear "
        "in its output every run is a check people learn to skim.",
    ("meta/roadmap/0.0/0.0.3.md", "S-23"):
        "cycle 0.0.3's execution record quotes the citation above while "
        "recording that this check found it on its first run and that it "
        "resolves in the sibling library. The finding is the entry directly "
        "above this one; this is the write-up of it.",
}
# And this file, which cannot explain an exemption without spelling the rule it
# excuses. Per-rule rather than whole-file, so every OTHER citation in this file
# is still resolved -- there are a dozen and they are the reasons the checks
# give when they fail.
for _r in ("S-23", "S-77", "TM-999"):
    CITATION_EXEMPT[("harness/checks.py", _r)] = (
        "named in this file's own exemption table while explaining why it is "
        "excused elsewhere. Exempting the whole file would stop the dozen "
        "REAL citations in it being checked.")
del _r


def check_specs_current(tree, **_):
    """Cited rule identifiers that no longer resolve. REPORTS, never fails.

    It does not fail on purpose: a citation can be wrong in two ways -- the rule
    was renumbered, or the citation was a typo -- and neither is a reason to
    stop a build. It is the check that keeps a document set honest as it grows,
    and it is worth having at cycle 0.0 precisely because the citations are
    dense here before any code exists.
    """
    declared = {}
    for prefix, (relpath, pattern) in CITATION_SOURCES.items():
        path = os.path.join(tree, relpath)
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        found = set()
        for line in text.splitlines():
            m = re.match(pattern.replace("%s", r"(\d+[a-z]?)"), line)
            if m:
                found.add(m.group(1))
        declared[prefix] = found

    targets = []
    for rel in SPEC_SCAN_ROOT_FILES:
        if os.path.isfile(os.path.join(tree, rel)):
            targets.append(rel)
    for d in SPEC_SCAN_DIRS:
        base = os.path.join(tree, d)
        if not os.path.isdir(base):
            continue
        for dirpath, dirs, names in os.walk(base):
            dirs[:] = sorted(x for x in dirs if x != "__pycache__")
            for n in sorted(names):
                if n.endswith((".md", ".npk", ".py", ".toml", ".txt")):
                    targets.append(
                        os.path.relpath(os.path.join(dirpath, n), tree)
                        .replace(os.sep, "/"))

    # THE EXEMPTIONS NAME FILES IN THIS REPOSITORY, so they apply to it and to
    # no other tree. `selfcheck.py` runs this check over scratch trees that
    # contain none of them, and a both-directions diff would report all four as
    # stale every time -- the same fault `EXPECT_EXEMPT` had, found on the same
    # run. See `run.py`'s `exemptions_for`.
    exempt = (CITATION_EXEMPT if os.path.abspath(tree) == REPO else {})

    unresolved, cited, excused = {}, 0, set()
    for rel in sorted(set(targets)):
        if (rel, None) in exempt:
            excused.add((rel, None))
            continue
        with open(os.path.join(tree, rel), "r", encoding="utf-8",
                  errors="replace") as fh:
            for lineno, line in enumerate(fh, 1):
                for prefix, number in _CITATION.findall(line):
                    if prefix not in declared:
                        continue
                    cited += 1
                    if number in declared[prefix]:
                        continue
                    rule = "%s-%s" % (prefix, number)
                    if (rel, rule) in exempt:
                        excused.add((rel, rule))
                        continue
                    # A lettered suffix inherits its parent's declaration only
                    # when the parent declares it; `S-4b` IS declared as a rule
                    # of its own in this tree, so no inheritance is assumed.
                    unresolved.setdefault(rule, []).append("%s:%d"
                                                           % (rel, lineno))

    reports = []
    for rule in sorted(unresolved):
        where = unresolved[rule]
        reports.append("%s cited at %d site(s), first %s -- no `%s` declares it"
                       % (rule, len(where), where[0],
                          CITATION_SOURCES[rule.split("-")[0]][0]))
    # THE OTHER DIRECTION (V-1c). An exemption that outlives what it excused is
    # how the next dangling citation at that site gets excused without anyone
    # deciding to excuse it.
    for key in sorted(exempt, key=lambda k: (k[0], k[1] or "")):
        if key not in excused:
            reports.append(
                "stale exemption: CITATION_EXEMPT names %s%s and nothing there "
                "needed excusing" % (key[0],
                                     "" if key[1] is None else " / " + key[1]))
    headline = ("%d citation(s) over %d file(s); %d declared rule(s) across %d "
                "document(s); %d unresolved"
                % (cited, len(set(targets)),
                   sum(len(v) for v in declared.values()), len(declared),
                   len(unresolved)))
    return Result("check_specs_current", headline, [], reports)


# ---------------------------------------------------------------------------
# the registry
# ---------------------------------------------------------------------------

# LIVE: run on every full invocation, and each one FAILS the run.
# `check_specs_current` is live and reports only -- its Result carries no
# problems by construction.
LIVE = (
    check_layering,
    check_error_budget,
    check_constants_named,
    check_no_owning_fields,
    check_raw_index,
    check_purity,
    check_host_isolation,
    check_specs_current,
)

# PENDING: named, with the cycle that turns each on and WHY it cannot run today.
# PRINTED, NEVER SILENT (P-19). A check nobody can see is missing is a check
# nobody adds, and this list is the difference between "the family is complete"
# and "the family is these eight".
PENDING = (
    ("check_int128_sites", "0.2",
     "`SPAN_MODEL.md` N-20 says three `int128` sites and §5's table marks one "
     "(O-X6). The sites must be named before they can be counted, and a rule "
     "invented to make a count come out right is worse than an acknowledged "
     "gap."),
    ("check_no_format_string", "0.4",
     "F-5's rule is that no function takes a pattern `string` and interprets "
     "it. There is no function in `src/` at all yet, so the check would have "
     "no signature to read."),
    ("check_tables_regenerate", "0.5",
     "the mechanism EXISTS -- `repro.py --between` runs a generator between "
     "two builds and requires the IR unchanged, and it has been seen red "
     "against a non-deterministic one (0.0.2 §5.3). What is missing is "
     "`tools/gen_tzdb.py` and a committed table to regenerate."),
    ("check_table_invariants", "0.5",
     "sorted, in range, indices valid -- of tables that do not exist."),
)
