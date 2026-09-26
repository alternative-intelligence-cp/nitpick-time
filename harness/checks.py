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
  trampoline and is in the allowlist by construction, so the scan never FLAGS a
  module that issues a raw syscall. It SEES one -- measured at pin `c3bdae2`, a
  floor-only program has 5 undefined symbols and the same program calling
  `sys` has 8, the extra three `npk_chain_push`, `npk_raise` and `npk_sys6` --
  and allows every symbol it sees (`BUILD.md` B-2c, TM-153). Until cycle 0.1.0b
  this paragraph said the two sets were IDENTICAL, after `nitpick-regex`'s
  RX-120 (a symbol diff coming out EMPTY, 29 symbols each way) "reproduced
  here". That was true at pins that emitted the whole prelude into every
  program and has been false here since `aaffb87`, where the two sets are 2
  and 5; the conclusion drawn from it stands. A green symbol scan cited as a
  purity result is the failure mode this paragraph exists to prevent, and it is
  stated again in `elf.py`, `harness/README.md`, `BUILD.md` B-2c and
  `TESTING.md` §2 so that no reader meets one description without the other.
"""

import os
import re

import build as build_mod
import lexical
import stages

# This repository's own root, from THIS file rather than from the working
# directory. The named-exemption tables below are statements about THIS tree,
# so the checks apply them only when that is the tree they are pointed at.
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# reading source the way a checker must: without its comments
# ---------------------------------------------------------------------------

def strip_comments(text):
    """Blank every comment, and nothing else: a literal's body is KEPT.
    `text` is what `lexical.read` returns.

    A CHECK OVER SOURCE MUST NOT READ PROSE, and in this tree that is not a
    hypothetical: `src/host/host.npk`'s header contains the word `mono_now()`
    while explaining the purity rule, and `src/lib.npk`'s contains
    `host_now_utc` while showing the shape a re-export line takes. A naive
    `grep` for either would fail this repository on its own documentation --
    twice, today, on the first run.

    Line structure is preserved (a comment becomes spaces, never disappears) so
    a finding can still cite a line number that matches the file.

    THE SPANS ARE `lexical.py`'s SINCE CYCLE 0.1.5 (TM-199): `//` to byte 10
    alone, `/* */` unnested, and no comment found inside a literal the
    compiler reads -- a character literal and a template's text included. Until
    then this was a scanner of its own that knew `//` and `"` and nothing else,
    so a `//` inside a `/* */` blanked the code after the block on its line,
    and a `'"'` opened a string that never closed (`0.1.5.md` section 1.3).
    """
    return lexical.blank(text, [s for s in lexical.spans(text)
                                if s[0] == "comment"])


def blank_code(text):
    """Blank every comment AND every literal -- a string, a raw or block
    string, a character, and a template's text but never its interpolations,
    which are code -- keeping every newline, so line and column numbers are the
    file's own. `text` is what `lexical.read` returns.

    OPERATOR DETECTION CANNOT READ LITERALS. `use "./cal/cal.npk".*;` contains
    a `/` and a `*` and arms nothing; a scanner that counted them would charge
    every module in the library for a division it does not perform. Blanking
    the body rather than deleting it keeps every line number and column honest.

    (Until cycle 0.1.5 this was `strip_strings(strip_comments(...))`, moved here
    from `arms.py` at cycle 0.1.1 so that the S-6 generator and
    `check_literal_divisors` shared one definition of "what is a string" -- a
    definition that knew `"` and nothing else. Since TM-199 it is
    `lexical.blank`, and the two still share it.)
    """
    return lexical.blank(text)


# THE LEXER'S WHITESPACE, AS A PATTERN (TM-200): space, tab, CR and LF --
# `lexical._WS`, which is the compiler's `is_space`. Since cycle 0.1.5 every
# check's pattern runs over a file's WHOLE blanked text and allows this between
# any two tokens it names, because the compiler does: `mono_now ()`, a `[` on
# the line after `v.items`, and `error` then `:ETimeOops` on the next line are
# a call, an index and a declaration to it (`0.1.5.md` section 1.4), and a
# pattern matched against one LINE saw none of them.
_W = r"[ \t\r\n]"


def _line(text, at):
    """The 1-based line of offset `at` in `text`, `\\n` the only line end."""
    return text.count("\n", 0, at) + 1


def code_lines(path):
    """`[(lineno, code_only_text)]` for a source file, comments blanked.

    COMMENTS ONLY -- a literal's body is kept, whatever `check_civil_literal`'s
    docstring said while it lived (cycle 0.1.0 to 0.1.0c: "blanks comments and
    string bodies"; it never did). A check that must not read literals calls
    `blank_code` itself, as `check_literal_divisors` does. The file is read by
    `lexical.read` and split at `\\n` alone since cycle 0.1.5 (TM-199), where a
    text-mode read and `splitlines()` had split at a lone CR as well.
    """
    return list(enumerate(strip_comments(lexical.read(path)).split("\n"), 1))


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
    """`BUILD.md` §6's diagram against `src/` -- its EDGES and its NODES.

    THE WALK IS `build.reachable_sources` AND `build.imports_of`, the ones the
    build already uses. A second walker would diverge from the first, and the
    interesting case is exactly where a naive one goes wrong: a `use` cycle is
    LEGAL in this language (D-086) and is still a decomposition mistake, so the
    walk carries a seen-set rather than assuming a tree.

    THE NODE HALF ARRIVED AT CYCLE 0.0.6 AND IT IS A REPAIR (TM-142). Cycle
    0.0.1's acceptance list carried a TICKED item saying `run.py` "asserts the
    count is at least 7, because a directory whose placeholder was deleted
    rather than replaced is invisible to the sweep". No such assertion was in
    the tree: 0.0.2 replaced `run.py` rather than extending it and the
    minimum went with the old file, so the stated failure mode was live for
    four subcycles inside a ticked box. A magic minimum would have been the
    wrong repair anyway -- it goes stale the moment a directory is added --
    so the rule is the one the sentence was really about: EVERY LAYER B-17
    NAMES HAS AT LEAST ONE MODULE. A deleted placeholder is then a named
    failure and not a smaller denominator.
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

    # THE NODES. Every layer B-17 names, plus `host`, must hold a module.
    present = set(module_of(rel) for rel in files)
    for layer in sorted(set(LAYER) | {"host"}):
        if layer not in present:
            problems.append(
                "`src/%s/` holds no `.npk`. B-17's diagram names the layer, so "
                "the diagram and the tree disagree -- and a directory whose "
                "placeholder was DELETED rather than replaced is invisible to "
                "every sweep that counts files, which is why this is an "
                "assertion and not a denominator." % layer)

    # The umbrella's reach, reported rather than asserted. It is 5 since cycle
    # 0.1.0 -- `src/lib.npk`, the three `src/core/` modules and `src/cal/cal.npk`
    # -- and the four remaining placeholders are reached by no root at all,
    # which is exactly why the `parse` stage roots every file in the tree rather
    # than trusting the module graph. (It said "4 today" and "five remaining"
    # until cycle 0.1.5, cycle 0.0.4's numbers.)
    reached = build_mod.reachable_sources(os.path.join(tree, "src", "lib.npk"))
    headline = ("%d `use` edge(s) over %d file(s) in src/; %d of %d layer(s) "
                "present; the umbrella reaches %d file(s)"
                % (edges, len(files), len(present & (set(LAYER) | {"host"})),
                   len(set(LAYER) | {"host"}), len(reached)))
    if not files:
        problems.append("check_layering opened 0 files under src/. A check "
                        "with an empty denominator reports green while "
                        "checking nothing (V-1b).")
    return Result("check_layering", headline, problems)


# ---------------------------------------------------------------------------
# check_error_budget -- SAFETY.md §2
# ---------------------------------------------------------------------------

# A declaration, wherever it starts and however it is spaced (TM-200): `error`
# and its `:` may stand on two lines, and a declaration may follow another on
# one. Matched over `blank_code`, so a literal holding `error:` is not one.
_ERROR_DECL = re.compile(r"(?<![A-Za-z0-9_.])(pub%s+)?error%s*:%s*"
                         r"([A-Za-z_][A-Za-z0-9_]*)" % (_W, _W, _W))
# `SAFETY.md` §2's table rows: `| `ETimeValue` | raised when ... |`
_BUDGET_ROW = re.compile(r"^\|\s*`(E[A-Za-z][A-Za-z0-9_]*)`\s*\|")
# And S-4's, in the same section: `| `ntime/cal.npk` | `ETimeValue` | ... |` --
# the module that DECLARES each identity (cycle 0.1.5, TM-203). A row whose
# second cell is not one identity in backticks (`—`, `— (raises `cal`'s)`)
# declares nothing.
_MODULE_ROW = re.compile(r"^\|\s*`ntime/([a-z_]+)\.npk`[^|]*\|\s*"
                         r"`(E[A-Za-z][A-Za-z0-9_]*)`\s*\|")


def budget_from_spec(tree):
    """The identity names `SAFETY.md` §2's table declares. READ, never written.

    The whole point of this family is to diff the library against the document,
    so the document is parsed rather than transcribed. A transcription is the
    next stale copy, and S-2 makes the ceiling a decision -- so the ceiling has
    to come from where the decision is recorded.
    """
    rows = _spec_rows(tree)
    return None if rows is None else rows[0]


def budget_modules_from_spec(tree):
    """`{identity: module}` from S-4's table, the column that says which module
    DECLARES each budgeted identity (TM-203). READ, never written, for the
    reason `budget_from_spec` gives."""
    rows = _spec_rows(tree)
    return None if rows is None else rows[1]


def _spec_rows(tree):
    """`(names, {name: module})` from `SAFETY.md` §2, or None if it is gone."""
    path = os.path.join(tree, "meta", "specs", "SAFETY.md")
    if not os.path.isfile(path):
        # NOT A TRACEBACK. A check whose document is missing has a finding to
        # report -- "the thing I diff against is gone" -- and a stack trace is
        # the one shape that is neither a pass nor a legible failure.
        return None
    names, owners, in_section = [], {}, False
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
            m = _MODULE_ROW.match(line)
            if m:
                owners.setdefault(m.group(2), m.group(1))
    return names, owners


def check_error_budget(tree, **_):
    """Public `error:` declarations against `SAFETY.md` §2's table.

    THE UNIT IS THE COMPILER'S: A MODULE-QUALIFIED IDENTITY (cycle 0.1.5's
    audit, C2; TM-203). `NITPICK-REACH-003` names an identity by the module
    that declares it -- two modules that each declare `pub error:ETimeValue`
    and fail with it owe a consumer `moda.ETimeValue` AND `modb.ETimeValue`,
    two arms, measured at compiler `c970483` and at `c3bdae2`. Until the close's
    second half this check keyed its count by the bare NAME, so that pair read
    as one identity against a budget of three, and the only guard the budget
    has passed a second arm in silence. The module is the file's own name --
    `mod:` is its basename (D-248), which is what REACH qualifies with.

    FOUR ASSERTIONS AND ONE REPORT, and the split is deliberate.

      FAILS on an identity the table does not name; on a budgeted name declared
      in more than one module; on a budgeted name declared in a module other
      than the one S-4's table names for it; and on the count of qualified
      identities exceeding the ceiling. S-2 makes a fourth identity a recorded
      decision AND a major version (TM-013), so it must not be possible to
      acquire one by writing a line of code -- and a second module's copy of a
      budgeted name IS a fourth identity to every consumer.

      REPORTS the identities the table names and the library has not declared
      yet -- two since cycle 0.1.0 declared `ETimeValue` in `cal`: `ETimeZone`
      and `ETimeParse`, each declared by the cycle `SAFETY.md` S-4's table
      names for its module, and held to that module when it arrives. Failing on
      them would make the check red until the last of those cycles, and a red
      that means "not written yet" is a red people learn to ignore. (Until cycle
      0.1.5 this said "Today that is all three, because no module computes
      anything", and the report below said "no module raises anything before
      cycle 0.1" on every run since then.)
    """
    named = budget_from_spec(tree)
    owners = budget_modules_from_spec(tree) or {}
    files = src_files(tree)
    if named is None:
        return Result(
            "check_error_budget",
            "not run: meta/specs/SAFETY.md is not in this tree",
            ["`meta/specs/SAFETY.md` is missing, and this check DIFFS AGAINST "
             "IT rather than against a copy of its table. Without the document "
             "there is no budget to hold the tree to, and reporting green "
             "would be reporting that a check ran when it did not."])
    # `(module, name)` -> the sites that declare it.
    declared, problems = {}, []
    for rel in files:
        mod = os.path.basename(rel)[:-4]
        code = blank_code(lexical.read(os.path.join(tree, rel)))
        for m in _ERROR_DECL.finditer(code):
            declared.setdefault((mod, m.group(2)), []).append(
                "%s:%d" % (rel, _line(code, m.start())))
    by_name = {}
    for mod, name in sorted(declared):
        by_name.setdefault(name, []).append(mod)

    for name in sorted(by_name):
        mods = by_name[name]
        sites = [s for mod in mods for s in declared[(mod, name)]]
        if name not in named:
            problems.append(
                "`error:%s` is declared at %s and `SAFETY.md` §2's table does "
                "not name it. The budget is THREE (%s) and three is a ceiling "
                "(S-2): a fourth identity is a new mandatory `failsafe` arm in "
                "every consuming program, which REACH-002 enforces, so it is a "
                "recorded decision and a MAJOR version (TM-013) -- never a "
                "line of code."
                % (name, ", ".join(sites), ", ".join(named)))
        elif len(mods) > 1:
            problems.append(
                "`error:%s` is declared in %d modules -- %s -- at %s. The "
                "compiler counts MODULE-QUALIFIED identities (TM-203): each "
                "copy is its own arm in every consuming program, so a budgeted "
                "name declared twice is a fourth identity reached by a line of "
                "code, which S-2 forbids."
                % (name, len(mods), ", ".join("%s.%s" % (m, name) for m in mods),
                   ", ".join(sites)))
        elif name in owners and mods[0] != owners[name]:
            problems.append(
                "`error:%s` is declared in module `%s` (%s), and `SAFETY.md` "
                "S-4's table names module `%s` for it. A consumer's `failsafe` "
                "names `%s.%s`, so the module IS the identity (TM-203): moving "
                "one is a decision that amends S-4, never a line of code."
                % (name, mods[0], ", ".join(sites), owners[name], owners[name],
                   name))
    if len(declared) > len(named):
        problems.append(
            "%d error identities are declared, each qualified by its module as "
            "the compiler counts them, and `SAFETY.md` §2's table names %d."
            % (len(declared), len(named)))

    missing = [n for n in named if n not in by_name]
    reports = []
    if missing:
        reports.append(
            "%d of %d budgeted identities are not declared yet (%s) -- "
            "expected: each arrives with the module `SAFETY.md` S-4's table "
            "names for it, which this check holds it to."
            % (len(missing), len(named),
               ", ".join("%s.%s" % (owners[n], n) if n in owners else n
                         for n in missing)))
    headline = ("%d identit(y|ies) declared over %d file(s) in src/ (%s), "
                "against a budget of %d"
                % (len(declared), len(files),
                   ", ".join("%s.%s" % k for k in sorted(declared)) or "none",
                   len(named)))
    if not named:
        problems.append("`SAFETY.md` §2's table parsed to 0 identities. The "
                        "check reads the document rather than a copy, so an "
                        "empty parse means the document moved and this check "
                        "is now checking nothing (V-1b).")
    unowned = [n for n in named if n not in owners]
    if unowned:
        problems.append("`SAFETY.md` S-4's table names no module for %s, so "
                        "the module that may declare it is not stated and this "
                        "check cannot hold it to one (TM-203). The table is "
                        "read rather than copied, so a row missing from it is "
                        "the document moving (V-1b)." % ", ".join(unowned))
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
    r"(?<![A-Za-z0-9_.])(?:pub%s+)?fixed%s+[A-Za-z_][A-Za-z0-9_<>\[\]]*%s*:%s*"
    r"([A-Z][A-Z0-9_]*(?:_MAX|_MIN|_LIMIT|_BOUND))\b" % (_W, _W, _W, _W))
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
        text = lexical.read(os.path.join(tree, rel))
        decls, code = blank_code(text), strip_comments(text)
        for m in _BOUND_DECL.finditer(decls):
            bounds += 1
            if rel != limits_rel:
                problems.append(
                    "%s:%d declares the bound `%s`. Every named bound "
                    "lives in `%s`, with the specification rule that set "
                    "it written beside it -- a bound in the module that "
                    "uses it is a bound nobody can review against the "
                    "range it is supposed to enforce."
                    % (rel, _line(decls, m.start()), m.group(1), limits_rel))
        for m in _NUMBER.finditer(code):
            num = m.group(1)
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
                    % (rel, _line(code, m.start()), num, owner, limits_rel))
    headline = ("%d bound declaration(s) and %d owned-constant occurrence(s) "
                "over %d file(s) in src/" % (bounds, hits, len(files)))
    return Result("check_constants_named", headline, problems)


# ---------------------------------------------------------------------------
# check_literal_divisors -- CALENDAR.md C-11 (TM-163)
# ---------------------------------------------------------------------------

# C-11 is the CALENDAR's rule, so the scope is `src/cal/`. `SAFETY.md` S-16's
# library-wide rule admits a divisor PROVEN nonzero on the same path, which no
# text check can see; C-11 admits only a literal, which one can.
LITERAL_DIVISOR_SCOPE = "src/cal/"

# `/` and `%`, and with a trailing `=` the compound forms, which divide too.
_DIVIDE = re.compile(r"[/%]")
# THE ONE SPELLING C-11 ADMITS: a positive decimal integer with its width
# suffix, `400i64` -- this library's house spelling of every literal. Unsigned
# because a NEGATIVE divisor opens `MIN / -1` (D-007's other trap), and in the
# grammar `-4i64` is not a literal anyway: it is `-` applied to one. Anything
# else -- a name, an expression, `4` bare, `146_097i64`, a hex literal -- is a
# finding, including the legal nonzero spellings: the rule is a spelling a
# reader can check at a glance, and refusing is the safe direction.
_POSITIVE_LITERAL = re.compile(
    r"[1-9][0-9]*[iu](?:8|16|32|64|128)(?![A-Za-z0-9_])")
_ZERO_LITERAL = re.compile(r"0+(?:[iu](?:8|16|32|64|128))?(?![A-Za-z0-9_])")
# AND WHAT MAY NOT FOLLOW IT: an operator that binds TIGHTER than `/` (the
# compiler's `OP_REFERENCE.md` §0) takes the literal as ITS operand, so the
# divisor is no longer the literal. `256i64 =>! uint8` is 0. A cast (`=>!`,
# `=>`), a pipeline (`|>`, `<|`) and the postfix forms (`.`, `?.`, `(`, `[`).
# `=>!` is tried before `=>` so a finding names the operator actually there.
_TIGHTER_THAN_DIVIDE = re.compile(r"=>!|=>|\|>|<\||\?\.|[.(\[]")


def _skip_ws(text, i):
    while i < len(text) and text[i] in " \t\r\n":
        i += 1
    return i


def _operand_text(code, k, limit=40):
    """The divisor as written, for a finding: a balanced `( ... )` group, or
    the token run from `k`, cut at `limit` characters and at the line's end."""
    if k < len(code) and code[k] == "(":
        depth, j = 0, k
        while j < len(code) and j - k < limit and code[j] != "\n":
            if code[j] == "(":
                depth += 1
            elif code[j] == ")":
                depth -= 1
                if depth == 0:
                    return code[k:j + 1]
            j += 1
        return code[k:j].rstrip() + " ..."
    m = re.match(r"[-!~]*[A-Za-z0-9_.]+", code[k:k + limit])
    if m:
        return m.group(0)
    return code[k:k + 12].split("\n")[0].strip() or "nothing"


def check_literal_divisors(tree, **_):
    """Every `/` and `%` in `src/cal/` divides by a positive integer literal.

    `CALENDAR.md` C-11: every divisor in the calendar is a literal, so D-007's
    divide-by-zero trap is unreachable BY CONSTRUCTION and the obligation is
    discharged by inspection -- the kind of claim `VERIFICATION.md` has to be
    able to make. C-11 used to carry a LIST of the divisors, and the list was
    incomplete the day `civil_from_days` arrived with eight more (TM-163). This
    check is the list that cannot go stale: it reads every division in the
    scope on every full run.

    READS CODE, NEVER PROSE, AND NEVER A LITERAL. `blank_code` -- because
    every `use "../core/limits.npk".X;` line in `cal.npk` holds a `/`, and its
    header explains this rule in prose with `/` and `%` in it. `code_lines`
    blanks comments only, whatever the retired `check_civil_literal` said of it
    (0.1.1's record). The clean control in `selfcheck.PLANTED` carries both
    shapes, so the exemption is proven rather than assumed.

    `+%`, `-%` AND `*%` ARE NOT DIVISIONS. They are the wrapping `+ - *`
    (the compiler's D-312), and their `%` is the marker, not the operator.

    WHAT IT DID NOT MODEL UNTIL CYCLE 0.1.5, and this paragraph said the gap
    was safe: *"Block comments, character literals, raw and block strings and
    template literals: `src/cal/` holds none. In a block comment, a character
    literal or a template's text a `/` or `%` reads as a division and fails
    LOUD -- the safe direction."* Measured at 0.1.5's planning, two of those
    shapes HID a division instead: a `'"'` opened a string that blanked the
    rest of the file, and a `//` in a template's text blanked the rest of its
    line -- as did a lone CR in a `//` comment followed by a `"`; and a `//`
    inside a `/* */` blanked the rest of ITS line, which hid a clock call and a
    declaration from the checks beside this one. Since TM-199 the blanking is
    `lexical.py`'s, the compiler lexer's spans, and each shape is planted in
    `selfcheck.PLANTED`.
    """
    files = [f for f in src_files(tree) if f.startswith(LITERAL_DIVISOR_SCOPE)]
    problems, divisions = [], 0
    for rel in files:
        code = blank_code(lexical.read(os.path.join(tree, rel)))
        for m in _DIVIDE.finditer(code):
            i = m.start()
            if code[i] == "%" and i > 0 and code[i - 1] in "+-*":
                continue                  # `+%` `-%` `*%` -- wrapping (D-312)
            divisions += 1
            lineno = code.count("\n", 0, i) + 1
            j = i + 1
            if j < len(code) and code[j] == "=":
                j += 1                    # `/=` and `%=` divide as well
            k = _skip_ws(code, j)
            lit = _POSITIVE_LITERAL.match(code, k)
            if lit:
                after = _skip_ws(code, lit.end())
                tighter = _TIGHTER_THAN_DIVIDE.match(code, after)
                if not tighter:
                    continue
                problems.append(
                    "%s:%d divides by `%s` followed by `%s`, which binds "
                    "tighter than `%s` (the compiler's OP_REFERENCE.md §0): the "
                    "divisor is not the literal but what `%s` makes of it, and "
                    "a narrowing cast can make it zero -- `256i64 =>! uint8` "
                    "is 0. C-11's literal must stand alone."
                    % (rel, lineno, lit.group(0), tighter.group(0), code[i],
                       tighter.group(0)))
                continue
            if _ZERO_LITERAL.match(code, k):
                problems.append(
                    "%s:%d divides by `%s`, a literal zero: D-007's "
                    "divide-by-zero trap is not merely reachable here, it is "
                    "reached on every call (C-11)."
                    % (rel, lineno, _operand_text(code, k)))
                continue
            problems.append(
                "%s:%d divides by `%s`, which is not a nonzero literal in the "
                "one spelling C-11 admits -- a positive decimal integer with "
                "its width suffix, like `400i64` (C-11, TM-163): the "
                "divide-by-zero trap, and `MIN / -1`'s, are no longer "
                "unreachable by construction. A divisor proven nonzero on its "
                "path is S-16's and belongs outside `src/cal/`."
                % (rel, lineno, _operand_text(code, k)))
    headline = ("%d division(s) over %d file(s) in %s, %s"
                % (divisions, len(files), LITERAL_DIVISOR_SCOPE,
                   "every divisor a positive integer literal" if not problems
                   else "%d divisor(s) NOT a positive integer literal"
                   % len(problems)))
    if not files:
        problems.append("check_literal_divisors opened 0 files under %s. An "
                        "empty denominator reports green while checking "
                        "nothing (V-1b)." % LITERAL_DIVISOR_SCOPE)
    return Result("check_literal_divisors", headline, problems)


# ---------------------------------------------------------------------------
# check_no_owning_fields -- SAFETY.md S-19b / TESTING.md §2
# ---------------------------------------------------------------------------

# WHAT IS TRUE, MEASURED at every pin this repository has kept, `0dfddac` to
# `c3bdae2` (cycle 0.1.3b; `tests/probe/probe17*` and
# `tests/probe/defect/fixed_move_out/`): a `fixed` table MAY hold an owning
# value -- a `string` as its element, or a struct holding one -- and every read
# that does not move it works: a scalar field, a lend (a by-value argument),
# `.clone()`. What the language refuses is a COPY of an owning row or element,
# `NITPICK-TYPE-046`, which is the read `SAFETY.md` S-17's accessor pair does;
# and what it did NOT stop, through compiler `c3bdae2`, is a MOVE out of `fixed`
# storage, which compiled and then faulted -- a compiler defect, reproduced in
# `fixed_move_out/` (O-N20, the compiler's DEF-99). At compiler `c970483` the
# move is refused as well, `NITPICK-TYPE-084` (cycle 0.1.4c, TM-189). So a table
# whose rows own can be read neither by value nor by move, and this library's
# tables hold none (S-19b): the zone tables hold OFFSETS into a name pool for
# exactly this reason (`ZONE_MODEL.md` Z-7).
#
# (Until cycle 0.1.3b this comment read: "An owning field is one the language
# will not let a table hold: a `string`, a `buffer`, an owning container, or a
# `wild` pointer. TYPE-046 makes owning values move-only, so a value COPIED out
# of a table cannot have one -- and a `fixed` table is read-only data that
# nothing may move out of." The first sentence was false at every kept pin; a
# `wild` pointer was never among the types the code looked for, and it does
# not make a struct owning -- a whole-`Vec` copy compiled (question 9,
# measured at cycle 0.1.0c; refused `NITPICK-TYPE-046` since cycle 0.1.3c's
# marker, TM-193); and the last clause described the compiler's
# defect as though it were the language's rule.)
#
# An owning TYPE, for this check: `string`, `buffer`, `Bytes`, any `Vec<...>`,
# and a struct with a field of an owning type, at any depth. A field's type is
# the last token before its `:`, after any qualifier (`sealed`, `hidden`,
# `limit<R>`), so a field NAMED `string_off` owns nothing.
_OWNING_TYPES = ("string", "buffer", "Bytes")
_FIXED_TABLE = re.compile(
    r"(?<![A-Za-z0-9_.])(?:pub%s+)?fixed%s+([A-Za-z_][A-Za-z0-9_]*(?:<[^>\[\]]*>)?)"
    r"%s*\[%s*\d*%s*\]%s*:" % (_W, _W, _W, _W, _W, _W))
_STRUCT_DECL = re.compile(r"(?<![A-Za-z0-9_.])(?:pub%s+)?struct%s*:%s*"
                          r"([A-Za-z_][A-Za-z0-9_]*)" % (_W, _W, _W))


def _absorb(out, cur, rel, code, start):
    """Read `code` from `start` -- just past a declaration's `{` -- as struct
    body text: fields separated by `;`, the body ending at the first `}`. One
    function for every spelling, so there is one place that knows what a field
    looks like. A field's text is its tokens joined by single spaces, and its
    line is the line its first token is on (TM-200: a field may span lines).
    """
    close = code.find("}", start)
    end = close if close >= 0 else len(code)
    pos = start
    for field in code[start:end].split(";"):
        text = " ".join(field.split())
        if text and ":" in text:
            lead = len(field) - len(field.lstrip())
            out[cur].append((rel, _line(code, pos + lead), text))
        pos += len(field) + 1


def _structs(tree, files):
    """`{name: [(rel, lineno, field_text), ...]}` for every struct in `src/`.

    BOTH SPELLINGS, AND THE SINGLE-LINE ONE IS WHAT THIS REPOSITORY WRITES
    (TM-138). Until cycle 0.0.6 this function did `continue` after matching a
    declaration line, so the rest of THAT line -- which for a one-liner is
    every field the type has -- was never read, and `cur` was never cleared
    because the closing `};` had been on the same line. The following lines
    were then attributed to the struct as fields until some later line began
    `};`. Measured on this tree, `Vec` "had" four fields, all of them
    `vec_init`'s statements, and `Bytes` two, and neither type's real fields
    (`wild T->:items`, `buffer:body`) had ever been examined.

    The check was still RED on the self-check's plant, because that plant is
    written multi-line. A check that is red on the fixture its author imagined
    and silent on the same fault in the form the tree uses is worse than no
    check, and the plant beside it is now written BOTH ways (`selfcheck.py`
    `PLANTED`).
    """
    out = {}
    for rel in files:
        # THE WHOLE TEXT, NOT A LINE AT A TIME, SINCE CYCLE 0.1.5 (TM-200): the
        # declaration's tokens may stand on separate lines -- `struct` and
        # `:Row = {` compile as a struct, measured -- and the body is read from
        # its `{` to its first `}` wherever the line breaks fall, which is
        # what the single-line spelling above needed as well.
        code = blank_code(lexical.read(os.path.join(tree, rel)))
        for m in _STRUCT_DECL.finditer(code):
            out.setdefault(m.group(1), [])
            brace = code.find("{", m.end())
            if brace >= 0:
                _absorb(out, m.group(1), rel, code, brace + 1)
    return out


def _owning_type(t):
    """`string`, `buffer`, `Bytes` or a `Vec<...>` -- the owning TYPES."""
    return t in _OWNING_TYPES or t.startswith("Vec<")


def _field_type(ftext):
    """A field's type: the last token before its `:`, so that `sealed`,
    `hidden`, `wild` and `limit<R>` are skipped as the qualifiers they are."""
    head = ftext.split(":", 1)[0].split()
    return head[-1] if head else ""


def _owners(structs, name, seen=()):
    """The fields of struct `name` that own, AT ANY DEPTH: a list of
    `(rel, lineno, field_text, via)`, where `via` names the struct a nested
    owner was found through and is None for a field that owns itself."""
    out = []
    for rel, lineno, ftext in structs.get(name, ()):
        ftype = _field_type(ftext)
        if _owning_type(ftype):
            out.append((rel, lineno, ftext, None))
        elif ftype in structs and ftype != name and ftype not in seen:
            if _owners(structs, ftype, seen + (name,)):
                out.append((rel, lineno, ftext, ftype))
    return out


def check_no_owning_fields(tree, **_):
    """No `fixed` table holds an owning value -- neither an owning ELEMENT nor
    a struct with an owning field at any depth (`SAFETY.md` S-19b).

    ONE TABLE TODAY, AND IT IS NOT A ZONE TABLE. `src/cal/cal.npk`'s
    `MONTH_LENGTH` (`int64[12]`) has been the one `fixed` table in `src/` since
    cycle 0.1.0, and the run log's `against 5 struct(s)` counts the types whose
    fields were actually read -- `Vec`, `Bytes`, `CivilDate`, `CivilTime`,
    `CivilDateTime`. Cycle 0.5's zone tables meet an instrument that already
    works. *(Until cycle 0.1.3b this docstring said "`src/` holds two real
    structs ... and no `fixed` table, so this reports `0 table(s) ... against
    2 struct(s)`" -- true at cycle 0.0.4, and two numbers stale for four
    subcycles: a docstring's claim about its own coverage is a list to check.)*

    "0 tables" AND "cannot see the fields" READ THE SAME IN THE HEADLINE, which
    is how `_structs`' single-line blindness survived three cycles (TM-138).
    AND TWO MORE BLIND SPOTS LASTED UNTIL CYCLE 0.1.3b, found by re-measuring
    the premise rather than by a failure: a table whose ELEMENT owns -- `fixed
    string[2]` -- was never looked at, because only struct fields were read;
    and an owner two structs down -- `Row` holds `Name`, `Name` holds a
    `string` -- was not either. Both are planted in `selfcheck.py`, and were
    seen red before this function could see them.
    """
    files = src_files(tree)
    structs = _structs(tree, files)
    problems, tables = [], 0
    for rel in files:
        code = blank_code(lexical.read(os.path.join(tree, rel)))
        for m in _FIXED_TABLE.finditer(code):
            lineno = _line(code, m.start())
            tables += 1
            elem = m.group(1)
            if _owning_type(elem):
                problems.append(
                    "%s:%d stores `%s` in a table: an owning element. A copy "
                    "of it out of the table is refused (TYPE-046), and so is "
                    "a move out of `fixed` storage since compiler c970483 "
                    "(TYPE-084; before it the move compiled and faulted, "
                    "tests/probe/defect/fixed_move_out/), so the table can "
                    "be read by neither (SAFETY.md S-19b)."
                    % (rel, lineno, elem))
                continue
            for frel, flineno, ftext, via in _owners(structs, elem):
                problems.append(
                    "%s:%d stores `%s` in a table, and `%s` has an owning "
                    "field at %s:%d -- `%s`%s. A row copied out of the table "
                    "is refused (TYPE-046) and so is a move out of `fixed` "
                    "storage since compiler c970483 (TYPE-084), so an owning "
                    "row can be read by neither; the "
                    "zone tables hold OFFSETS into a name pool for exactly "
                    "this reason (ZONE_MODEL.md Z-7, SAFETY.md S-19b)."
                    % (rel, lineno, elem, elem, frel, flineno, ftext,
                       "" if via is None else ", which owns through `%s`" % via))
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

# A binding whose TYPE is a bare pointer: `wild T->:name`, in a declaration, a
# field or a parameter. The name it binds is then a bare pointer wherever it is
# used, and indexing it is unguarded however it was reached.
_WILD_BINDING = re.compile(r"\bwild%s+[A-Za-z_][A-Za-z0-9_<>]*%s*->%s*:%s*"
                           r"([A-Za-z_][A-Za-z0-9_]*)" % (_W, _W, _W, _W))
# Each owned field's INDEX, however it is spaced (TM-200): `v.items [0i64]`,
# and a `[` on the line after, index the bare pointer exactly as `v.items[` --
# AND SO DO `v.` WITH `items[0i64]` ON THE NEXT LINE, AND `v . items [0i64]`:
# the `.` is a token of its own, so the lexer's whitespace may stand AFTER it as
# well as before the `[`. Until the close's second half the pattern allowed
# none there (the audit's C12): `b .` then ` arr [2i64]` on the next line
# compiles and reads the element at `c970483`, and the check was silent on
# `v.` then `items[0i64]` on the next line, and on `b.body. ptr[0i64]`.
_RAW_INDEX = dict((needle, re.compile(re.escape(needle[0]) + _W + "*"
                                      + re.escape(needle[1:-1]) + _W + "*\\["))
                  for needle in RAW_INDEX_OWNERS)


def check_raw_index(tree, **_):
    """No index through a bare pointer in `src/` -- by FIELD or by BINDING.

    `Vec<T>.items` is a `wild T->` and `Bytes`' body is a `buffer` indexed
    through its `.ptr` -- BOTH are bare pointers to the emitter, and the
    language does not bounds-check a bare pointer (TM-108, S-17b: the check
    attaches to the TYPE, and `ExprIndexExpr` has four branches of which only
    the pointer one omits `emit_bounds_guard`). So the accessor pair is the
    only bound that exists, and this check is what keeps every index inside it.

    THE FIELD HALF WAS THE WHOLE CHECK UNTIL CYCLE 0.0.6, AND IT WAS EVADABLE
    IN ONE LINE (the audit's B1). Two literal substrings, `.items[` and
    `.ptr[`, enumerate the KNOWN bare pointers by field name; they do not find
    bare pointers. Bind one to a local and index the local:

        wild int64->:p = v.items;
        int64:x = p[v.count + 4i64];

    Built at pin `aaffb87` that reads four elements past the live prefix, runs,
    and exits with the wrong value -- and the check reported `0 raw-index
    site(s)`. The library contains no such alias, so it was never a live defect;
    it was the answer to "what would this miss", which is the question a check
    of this shape has to survive.

    So the binding half is here too: every `wild T->:name` in `src/` is
    collected, and `name[` anywhere in the same file is a finding. That is
    lexical and per-file, which is the honest limit -- **a bare pointer passed
    to another function and indexed there under a different name is still not
    covered.** Cycle 0.5 gets the widening, when `src/zone/` gives it a second
    subject; the ceiling on the damage until then is that `src/` has exactly two
    bare pointers and both are in the file that owns them.
    """
    files = src_files(tree)
    problems, hits, bindings = [], 0, 0
    for rel in files:
        # The whole comment-blanked text (TM-200): a binding, its index and a
        # field's index are each matched however the line breaks fall.
        code = strip_comments(lexical.read(os.path.join(tree, rel)))
        bound = {}
        for m in _WILD_BINDING.finditer(code):
            bound.setdefault(m.group(1), _line(code, m.start()))
        bindings += len(bound)
        for needle, owner in RAW_INDEX_OWNERS.items():
            for m in _RAW_INDEX[needle].finditer(code):
                hits += 1
                if rel != owner:
                    problems.append(
                        "%s:%d indexes `%s` raw. That is a BARE POINTER "
                        "and the language does not bounds-check one "
                        "(TM-108, S-17b) -- an out-of-range index is a "
                        "wrong value, not a crash. Go through the accessor "
                        "in `%s`, which checks `0 <= i` as well as "
                        "`i < count`."
                        % (rel, _line(code, m.start()), needle, owner))
        for name, at in bound.items():
            for m in re.finditer(r"\b%s%s*\[" % (re.escape(name), _W), code):
                hits += 1
                problems.append(
                    "%s:%d indexes `%s`, which is bound as a BARE POINTER "
                    "at %s:%d (`wild ... ->:%s`). The language does not "
                    "bounds-check one (TM-108, S-17b), so this index is "
                    "UNGUARDED and an out-of-range read is a wrong value "
                    "rather than a crash. Lay a `#wild_slice` over the "
                    "live count and index THAT, which is S-17c and puts "
                    "the compiler's own `emit_bounds_guard` back."
                    % (rel, _line(code, m.start()), name, rel, at, name))
    headline = ("%d raw-index site(s) over %d file(s) in src/, %d owner(s) "
                "allowed, %d bare-pointer binding(s) watched"
                % (hits, len(files), len(RAW_INDEX_OWNERS), bindings))
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
# THE CALL SHAPE IS THE LEXER'S, NOT A SPELLING (TM-200): a banned name, then the
# lexer's whitespace -- a newline included -- then `(`. `mono_now ()`, and a
# `sys` whose `(` begins the next line, are calls to the compiler (measured at
# `c970483`, `0.1.5.md` section 1.4) and neither contains `sys(`; so each entry
# above is matched over the file's WHOLE comment-blanked text, never a line.
_PURITY_CALL = re.compile(
    "(%s)%s*\\(" % ("|".join(re.escape(b[:-1]) for b in PURITY_BAN), _W))


def check_purity(tree, **_):
    """`src/` outside `src/host/` against S-10's ban list. SOURCE-LEVEL.

    AND SOURCE-LEVEL IS THE POINT, NOT A LIMITATION TO APOLOGISE FOR. The
    build's undefined-symbol scan cannot answer this question at all: the
    runtime's own syscall trampoline `npk_sys6` is in its allowlist by
    construction, so a module that issues a raw syscall passes the scan exactly
    as one that does not. Its undefined set GROWS -- 5 symbols to 8 at pin
    `c3bdae2`, `npk_sys6` among the three -- and every one is allowed (TM-153,
    B-2c). Until cycle 0.1.0b this said the two sets were IDENTICAL, after
    `nitpick-regex`'s RX-120 (29 symbols each way) "reproduced here": true at
    pins that emitted the whole prelude into every program, false here since
    `aaffb87`. This check is the only thing in the repository that answers
    "did this module touch the kernel", and a green symbol scan must never be
    cited for it.

    WHAT IT CANNOT SEE, stated so nobody over-reads this one either: a syscall
    reached through a name it does not know -- an alias, or a helper in a file
    it is not scanning. The defence against that is `check_host_isolation` plus
    B-17's layering, which together make `host` a leaf nothing may import.
    """
    files = [f for f in src_files(tree) if not f.startswith(HOST_DIR)]
    total = len(src_files(tree))
    problems = []
    for rel in files:
        code = strip_comments(lexical.read(os.path.join(tree, rel)))
        for m in _PURITY_CALL.finditer(code):
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
                % (rel, _line(code, m.start()), m.group(1)))
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
# A citation's ENDS ARE ASCII LOOK-AROUNDS, NOT `\b` (cycle 0.1.5's second
# half, TM-206). This scanner reads every kind of file through `lexical.read`,
# one character per BYTE (TM-199), so in UTF-8 prose the lead byte of any
# multi-byte character is a latin-1 LETTER -- an em dash's 0xE2 is `â` -- and a
# `\b` after `TM-107` then an em dash, or `S-4b` then a curly apostrophe, found
# no boundary there: the citation was neither counted nor resolved nor reported
# (the first half's execution finding 1, the audit's C11). ASCII look-arounds
# read the same under either decoding.
_CITATION = re.compile(r"(?<![A-Za-z0-9_])(TM|S|B|V|M|Z|N|F|C)-(\d+[a-z]?)"
                       r"(?![A-Za-z0-9_])")
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
    ("meta/roadmap/done/0.0/0.0.0.md", "S-23"):
        "it cites the SIBLING library's rule, and the sentence says so: "
        "\"The sibling `nitpick-regex`'s own S-23 table omits it too\". Every "
        "library in this ecosystem numbers its own `S-` rules, so the "
        "namespaces collide by design; a cross-repository citation is verified "
        "by reading that repository, and this one was.",
    ("meta/roadmap/done/0.0/0.0.3.md", "S-23"):
        "cycle 0.0.3's execution record quotes the citation above while "
        "recording that this check found it on its first run and that it "
        "resolves in the sibling library. The finding is the entry directly "
        "above this one; this is the write-up of it.",
}
# THERE IS NO WHOLE-FILE EXEMPTION IN THIS TABLE ANY MORE, and that is a rule
# rather than a coincidence (TM-145). `harness/selfcheck.py` had one, excused
# for containing "DELIBERATELY dangling citations" as its fixtures -- and
# `checks.py:737` marks a whole-file entry excused as long as the FILE EXISTS,
# so the reason was never re-derived. That is TM-137's shape exactly, in the
# mechanism written to prevent it, and it silently un-checked the eleven real
# citations in that file. The fixtures are now ASSEMBLED from pieces
# (`"TM-" + "999"`), so they are invisible to the scanner and no exemption is
# needed. Reach for that first; a whole-file exemption is a hole that cannot
# expire.
#
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
        # Every kind of file this scans is read as bytes and split at `\n`
        # alone (TM-199), so a line number here is `git grep -n`'s.
        lines = lexical.read(os.path.join(tree, rel)).split("\n")
        for lineno, line in enumerate(lines, 1):
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
    # THE OTHER DIRECTION (V-1c), AND IT FAILS RATHER THAN REPORTS (TM-145).
    # An exemption that outlives what it excused is how the next dangling
    # citation at that site gets excused without anyone deciding to excuse it.
    # This check REPORTS an unresolved citation on purpose -- a renumbering is
    # not a reason to stop a build -- but a stale exemption is a different
    # animal: it is V-1c's both-directions rule, which is a FAILURE everywhere
    # else in this harness, and it is the one thing here a green run would
    # otherwise hide. It matters concretely at a cycle close: two of this
    # table's keys are `meta/roadmap/done/0.0/...` paths, and archiving the cycle
    # moves them.
    problems = []
    for key in sorted(exempt, key=lambda k: (k[0], k[1] or "")):
        if key not in excused:
            problems.append(
                "stale exemption: CITATION_EXEMPT names %s%s and nothing there "
                "needed excusing. An exemption that outlives what it excused "
                "silently excuses the next thing at that site (V-1c). If the "
                "file MOVED -- a cycle archived into meta/roadmap/done/, say --"
                " the key moves with it."
                % (key[0], "" if key[1] is None else " / " + key[1]))
    headline = ("%d citation(s) over %d file(s); %d declared rule(s) across %d "
                "document(s); %d unresolved, %d stale exemption(s)"
                % (cited, len(set(targets)),
                   sum(len(v) for v in declared.values()), len(declared),
                   len(unresolved), len(problems)))
    return Result("check_specs_current", headline, problems, reports)


# ---------------------------------------------------------------------------
# the registry
# ---------------------------------------------------------------------------

# LIVE: run on every full invocation, and each one FAILS the run.
# `check_specs_current` is live and reports only -- its Result carries no
# problems by construction.
# ---------------------------------------------------------------------------
# check_denominators -- TESTING.md V-1g / TM-142
# ---------------------------------------------------------------------------

# The directories no sweep in this repository enters. Kept here rather than in
# `run.py` so that one walk answers for the runner and for this check; two
# walks that could disagree about what "every `.npk` in the tree" means is the
# defect this check exists to prevent, one level up.
WALK_SKIP = {".git", ".internal", "build", "__pycache__"}

# AND A NESTED REPOSITORY IS NOT THIS TREE (TM-146). Found by CI's FIRST RUN,
# which is the only place it could be found: `.github/workflows/ci.yml` checks
# the pinned compiler out at `<workspace>/.nitpick`, because `actions/checkout`
# cannot place a `path:` outside the workspace. Every whole-tree sweep here
# then walked the entire compiler -- hundreds of `.npk` reported as
# "unowned .npk", `npk_total` wrong by hundreds, and `run_parse` putting the
# compiler's own source in front of `npkc` one file at a time.
#
# The rule is by SHAPE and not by name, because the next tool checked out
# beside it will not be called `.nitpick`: a directory holding a `.git` entry
# is a separate repository and is not this tree. `.nitpick` is named as well,
# so a checkout made without `.git` (an export, a tarball) is caught too.
#
# AND THE PRUNING IS NEVER SILENT. `nested_repos()` returns what was pruned and
# `run.py` prints it beside the denominator, because "78 files, 1 nested
# repository pruned" and "78 files" are different statements and only the first
# can be checked (V-1b).
VENDORED = {".nitpick"}


def _is_nested_repo(path, name):
    return name in VENDORED or os.path.exists(os.path.join(path, ".git"))


def nested_repos(root):
    """Directories pruned as separate repositories, repo-relative and sorted."""
    out = []
    for dirpath, dirs, _names in os.walk(root):
        keep = []
        for d in sorted(dirs):
            if d in WALK_SKIP:
                continue
            full = os.path.join(dirpath, d)
            if _is_nested_repo(full, d):
                out.append(os.path.relpath(full, root).replace(os.sep, "/"))
            else:
                keep.append(d)
        dirs[:] = keep
    return sorted(out)

# `[[sweep: name=N]]`. Deliberately ugly, deliberately greppable, and it
# renders as nothing in markdown. Its spaces are ASCII `[ \t]`, not `\s`, since
# the close's second half (TM-206): this scanner reads every file one character
# per byte (TM-199), where `\s` also matches the bytes 0x85 and 0xA0 -- halves
# of UTF-8 characters -- so the pattern read differently under the two
# decodings. No tag in the tree spells anything but a space there.
_SWEEP_MARK = re.compile(r"\[\[sweep:[ \t]*([a-z_]+)[ \t]*=[ \t]*(-?\d+)[ \t]*"
                         r"\]\]")

_TAGGABLE = (".md", ".py", ".toml", ".yml", ".yaml", ".npk", ".txt")

# The `sweep` stage's directory (`BUILD.md` §3). `denominators()` measures the
# domain each member there DECLARES, as `domain_<stem>` (cycle 0.1.2).
SWEEP_DIR = "tests/unit/sweep"


def _walk(root):
    """`os.walk` with this repository's pruning: skipped dirs and nested repos."""
    for dirpath, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs
                         if d not in WALK_SKIP
                         and not _is_nested_repo(os.path.join(dirpath, d), d))
        yield dirpath, dirs, names


def all_npk(root):
    """Every `.npk` in the tree, repository-relative, sorted. ONE walk."""
    found = []
    for dirpath, _dirs, names in _walk(root):
        for n in sorted(names):
            if n.endswith(".npk"):
                found.append(os.path.relpath(os.path.join(dirpath, n), root)
                             .replace(os.sep, "/"))
    return sorted(found)


def denominators(tree, extra=None):
    """The numbers the documents keep quoting, MEASURED. `{name: value}`.

    Everything here is derived from the directory, so this check is a pure
    function of a tree and can be commissioned like the rest (V-14c). The two
    values that need the manifest -- how many files the `[[test]]` entries
    select, and how many sources the library entry reaches -- are handed in by
    `run.py` as `extra`, because computing them here would mean a second copy
    of `select()`.
    """
    files = all_npk(tree)
    src = [f for f in files if f.startswith("src/")]
    tests = [f for f in files if f.startswith("tests/")]
    probe = [f for f in tests
             if f.startswith("tests/probe/") and f.count("/") == 2]
    d = {
        "npk_total": len(files),
        "npk_src": len(src),
        "npk_tests": len(tests),
        "npk_elsewhere": len(files) - len(src) - len(tests),
        "probe_dir": len(probe),
        "defect_total": len([f for f in tests
                             if f.startswith("tests/probe/defect/")]),
        "support_total": len([f for f in tests
                              if f.startswith("tests/probe/support/")]),
    }
    # THE MARKER SPLIT IS READ THROUGH `stages.read`, the same parser the suite
    # dispatches on, so the count and the dispatch cannot disagree about what a
    # header says -- which is TM-121's rule applied to a denominator.
    for label, group in (("probe", probe), ("tests", tests)):
        n_exit = n_error = n_none = 0
        for rel in group:
            try:
                e = stages.read(tree, rel)
            except stages.MarkerError:
                n_none += 1
                continue
            if e.is_refusal:
                n_error += 1
            else:
                n_exit += 1
        d[label + "_exit"] = n_exit
        d[label + "_error"] = n_error
        d[label + "_nomarker"] = n_none
    # THE FILES WHOSE MANAGED MEMORY IS ASSERTED -- cycle 0.1.4b, TM-184 and
    # TM-186. Every statement of how many there are is TAGGED, so the day a
    # subcycle bounds another file the sentences are held to it, as every
    # other count here is (TM-142).
    heap_n = cap_n = 0
    for rel in tests:
        try:
            e = stages.read(tree, rel)
        except stages.MarkerError:
            continue                  # `check_expect_headers` names the file
        heap_n += 1 if e.heap else 0
        cap_n += 1 if e.cap else 0
    d["heap_bounded"] = heap_n
    d["cap_belted"] = cap_n
    # THE DOMAIN EACH `sweep` MEMBER DECLARES, as `domain_<stem>` -- cycle
    # 0.1.2, `TESTING.md` V-1h. A member's `// sweep-count:` is the test's
    # statement of a number the specifications state too (7 304 484 days in
    # `CALENDAR.md` §2, 239 988 months in `TESTING.md` V-2), and the `sweep`
    # stage holds the program's printed count to it (TM-122). Measured here,
    # every statement of it can be TAGGED, which makes the test's number and
    # the specification's one list: `probe07` asserted the range's right first
    # day for three weeks beside a `CALENDAR.md` that stated the wrong one,
    # and nothing compared the two (TM-161). A stem outside `[a-z_]` could not
    # be named by a tag (`_SWEEP_MARK`); no member's is.
    for rel in tests:
        if not rel.startswith(SWEEP_DIR + "/") or rel.count("/") != 3:
            continue
        try:
            e = stages.read(tree, rel)
        except stages.MarkerError:
            continue                  # `check_expect_headers` names the file
        if e.sweep_count is not None:
            d["domain_" + os.path.basename(rel)[:-4]] = e.sweep_count
    lib = os.path.join(tree, "src", "lib.npk")
    if os.path.isfile(lib):
        # THE COMPILER'S COUNT (TM-199): every `pub use` that is code, however
        # it is spaced -- where this counted every LINE that began with the
        # words, a `pub use` inside a `/* */` included.
        d["lib_reexports"] = sum(
            1 for _, _, pub in lexical.imports(lexical.read(lib)) if pub)
    # THE ARM BILLS `SAFETY.md` S-4 PUBLISHES, one per public module, as
    # `arms_<module>` -- the umbrella's is `arms_lib` (cycle 0.1.5's second
    # half, the audit's C6; TM-205). The bill is `arms.compute_bill`'s, from
    # SOURCE, and `check_failsafe_arms` holds that to `NITPICK-REACH-003`'s own
    # list on every full run, so on a green run this number is the compiler's.
    # Until the close's second half nothing read the totals S-4 and the summary
    # pages WRITE -- S-4 said its row "cannot go stale in silence" and it could:
    # the generated bill was checked and the written one was not. Every
    # present-tense statement of one is tagged now, and this is what the tag is
    # held to. Imported here and not at the top, because `arms` imports THIS
    # module.
    import arms as arms_mod
    for rel in arms_mod.public_modules(tree):
        d["arms_" + os.path.basename(rel)[:-4]] = len(
            arms_mod.compute_bill(tree, rel)[0])
    d.update(extra or {})
    return d


def check_denominators(tree, extra=None, **_):
    """Every number TAGGED in a document equals what the sweep measures.

    THE NUMBERS TRAVEL, AND NOTHING USED TO CATCH THEM (TM-142). The tree went
    from 50 `.npk` to 78 across cycles 0.0.4 and 0.0.5, and ELEVEN sites in six
    live files still carried the 0.0.3 figures -- `run.py`'s own header, two
    docstrings in `stages.py`, `BUILD.md`, `TESTING.md`, `nitpick.toml` and
    `OPEN_QUESTIONS.md`. The harness PRINTS every denominator on every run
    (V-1b) and no document was ever diffed against the print, so a reader had
    two numbers and no way to tell which was current.

    THE MECHANISM IS NARROWER THAN "EVERY NUMBER IN EVERY DOCUMENT", AND THE
    NAME SAYS SO. It cannot read prose; it checks the numbers somebody TAGGED
    `[[sweep: name=N]]`. A new untagged number is not covered -- that is the
    honest limit, and it is why the marker is ugly enough to notice in review.
    What it does guarantee is that a tagged number cannot go stale in silence,
    which is exactly what these eleven did.

    It is the shape `check_error_budget` already uses on `SAFETY.md` §2: the
    document is the thing read, the tree is the authority, and the diff is the
    check.
    """
    known = denominators(tree, extra)
    problems, tagged, files_seen = [], 0, 0
    for dirpath, _dirs, names in _walk(tree):
        for n in sorted(names):
            if not n.endswith(_TAGGABLE):
                continue
            path = os.path.join(dirpath, n)
            rel = os.path.relpath(path, tree).replace(os.sep, "/")
            files_seen += 1
            # Bytes, and `\n` the only line end (TM-199): a line number here
            # is `git grep -n`'s, for every kind of file this reads.
            for lineno, line in enumerate(lexical.read(path).split("\n"), 1):
                for m in _SWEEP_MARK.finditer(line):
                    name, claimed = m.group(1), int(m.group(2))
                    tagged += 1
                    if name not in known:
                        problems.append(
                            "%s:%d tags `%s`, which this sweep does not "
                            "measure. A tag naming nothing is excused by "
                            "nothing. Known: %s"
                            % (rel, lineno, name, ", ".join(sorted(known))))
                    elif known[name] != claimed:
                        problems.append(
                            "%s:%d says %s = %d; the tree says %d. The "
                            "tree is the authority (TM-002). Either the "
                            "sentence is stale, or the tree grew a file "
                            "nobody meant to add."
                            % (rel, lineno, name, claimed, known[name]))
    headline = ("%d tagged number(s) over %d file(s), against %d measured "
                "denominator(s)" % (tagged, files_seen, len(known)))
    res = Result("check_denominators", headline, problems)
    res.reports.append("measured: %s"
                       % "  ".join("%s=%d" % kv for kv in sorted(known.items())))
    return res


LIVE = (
    check_denominators,
    check_layering,
    check_error_budget,
    check_constants_named,
    check_literal_divisors,
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
     "it, and the functions it governs are `src/fmt/`'s, which cycle 0.4 "
     "writes. `src/` has held functions since cycle 0.0.4 -- `bytes_extend_str` "
     "takes a `string` and copies it -- so a check that read signatures alone "
     "would fire on those; what it needs is the layout interpreter F-5 is "
     "written against, to tell interpreting from copying. Until 0.4 nothing "
     "enforces F-5, and a format-string function added now would leave the run "
     "green. (This said \"There is no function in `src/` at all yet\" until "
     "cycle 0.1.5's second half -- false since 0.0.4, the audit's C8.)"),
    ("check_tables_regenerate", "0.5",
     "the mechanism EXISTS -- `repro.py --between` runs a generator between "
     "two builds and requires the IR unchanged, and it has been seen red "
     "against a non-deterministic one (0.0.2 §5.3). What is missing is "
     "`tools/gen_tzdb.py` and its tables. The civil cross-oracle's corpus is "
     "generated too (cycle 0.1.4) and joins this check at 0.5.3; until then "
     "the subcycle that changes `tools/gen_civil_oracle.py` regenerates the "
     "corpus and compares it, a regeneration costing about 11 s (TESTING.md "
     "V-6)."),
    ("check_table_invariants", "0.5",
     "sorted, in range, indices valid -- of tables that do not exist."),
)
