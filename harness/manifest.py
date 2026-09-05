"""`nitpick.toml`, read and schema-checked. P-12.

WHY A READER AND NOT A CONSTANT. Cycle 0.0.1's floor hardcoded the LLVM version
and both flag lists in `run.py`, three lines below a comment saying they came
from the manifest. That is the shape D-204 warns about and the manifest's own
header names: *a stated flag nothing consumes is the next stale document*. So
every tool invocation in this harness is built from the values below, and the
manifest is the only place they are written.

WHY OUR OWN PARSER. Python's `tomllib` is 3.11+, and this harness has to run
wherever the compiler does; more to the point, the schema check is the valuable
half and `tomllib` has none. The subset here is exactly what the compiler's
`BUILD_REFERENCE.md` §1 schema (D-077) allows and nothing more:

    [table]                 a table header
    [[array-of-table]]      an array-of-table header (only `[[test]]`)
    key = "string"
    key = 0                 a non-negative integer
    key = ["a", "b"]        an array of strings, on one line
    # comment               to end of line, outside a string

THE SCHEMA REFUSES BY NAME, IN BOTH DIRECTIONS. An unknown key is named and the
read fails -- `npkg`'s own parser refuses a key the schema lacks, and a harness
that quietly ignored one would accept a manifest `npkg` will not. A key the
schema requires and the file omits is named too. Both matter here for the same
reason: this manifest was written ahead of the tool that reads it, so nobody has
ever seen it accepted.
"""

import os


class ManifestError(Exception):
    """A manifest that cannot be read, or that the schema refuses.

    Always carries the file, the line number and the offending text, because a
    parser that says only "bad syntax" is a parser you debug by bisection.
    """


# ---------------------------------------------------------------------------
# the schema
# ---------------------------------------------------------------------------
#
# `str`, `int`, `[str]` are the three value shapes. `None` as a table's value
# means "the table exists and may hold nothing" -- `[dependencies]` is required
# to be present and required to be EMPTY (B-10, TM-027): its emptiness is a
# decision, and a decision is checked, not assumed.

STR, INT, STRLIST = "string", "integer", "array of strings"

SCHEMA = {
    "project": {
        "name": STR, "version": STR, "description": STR,
        "authors": STRLIST, "target": STR,
    },
    "build": {
        "entry": STR, "output": STR, "opt-level": INT,
    },
    "toolchain": {
        "llvm": STR,
        "llc-flags": STRLIST, "llc-opt-flags": STRLIST,
        "opt-flags": STRLIST, "lld-flags": STRLIST,
    },
    "dependencies": {},
    "test": {
        "name": STR, "stage": STR, "kind": STR, "path": STR,
    },
}

# Required keys, per table. Everything else in SCHEMA is optional -- `kind` is
# the only optional `[[test]]` key, and it is optional because it is meaningful
# only on a `compile` entry (B-4b).
REQUIRED = {
    "project": ("name", "version", "target"),
    "build": ("entry", "output", "opt-level"),
    "toolchain": ("llvm", "llc-flags", "llc-opt-flags", "opt-flags",
                  "lld-flags"),
    "dependencies": (),
    "test": ("name", "stage", "path"),
}

ARRAY_TABLES = ("test",)

# The stages this library's harness knows. `BUILD.md` §3 lists nine; an entry
# naming one it cannot honour is refused BY NAME rather than skipped -- the
# compiler's rule, and O-X7's own argument: "an entry a runner cannot honour is
# refused by name before anything runs, never skipped". A skipped entry is a
# suite reporting green while checking nothing.
KNOWN_STAGES = ("compile", "parse", "accept", "check", "program", "golden",
                "sweep", "fixture")
IMPLEMENTED_STAGES = ("compile", "check", "program", "golden", "sweep")

# `parse` IS A WHOLE-TREE STAGE HERE, NOT A DIRECTORY ENTRY. `BUILD.md` §3's
# own Directory column reads "every `.npk` in the tree" for it, and that is the
# point of the stage: the files it is worth running on are precisely the ones no
# `[[test]]` entry selects. Writing `stage = "parse"` on an entry would narrow
# it to one directory and silently un-cover the rest, so it is refused by name.
WHOLE_TREE_STAGES = ("parse",)

# `accept` IS DELIBERATELY NOT IMPLEMENTED, AND THAT IS A DECISION, NOT A GAP
# (TM-124, B-4b, TM-114). It stops at "accepted in silence", and this repository
# holds the reproduction of what that misses: a root with `main` and no
# `failsafe` was accepted by `npkc` at exit 0 and refused only by the linker
# (`tests/probe/defect/missing_failsafe/`, O-N11). `TESTING.md` §1 and
# `BUILD.md` §3 both already say this library does not use the stage; a runner
# that implemented it anyway would be offering the shape those rules exist to
# keep out of reach.
DECLINED_STAGES = {
    "accept": "it stops at \"accepted in silence\", which is the shape a "
              "program with no `failsafe` walks through (B-4b, TM-114). Use "
              "`compile` with `kind = \"positive\"`, which is judged on the "
              "RUN.",
}
KNOWN_KINDS = ("positive", "negative", "diagnostic")


def _strip_comment(line):
    """Drop a `#` comment, respecting double-quoted strings.

    Naive `line.split('#')` would truncate `description = "a # b"`. Nothing in
    this manifest has one today, which is exactly why the parser must not be
    the reason it never can.
    """
    out, in_str, i = [], False, 0
    while i < len(line):
        c = line[i]
        if in_str and c == "\\" and i + 1 < len(line):
            out.append(c)
            out.append(line[i + 1])
            i += 2
            continue
        if c == '"':
            in_str = not in_str
        elif c == "#" and not in_str:
            break
        out.append(c)
        i += 1
    return "".join(out)


def _value(raw, path, lineno):
    raw = raw.strip()
    if raw.startswith('"'):
        if not raw.endswith('"') or len(raw) < 2:
            raise ManifestError(
                "%s:%d: a string value must open and close with `\"`: %s"
                % (path, lineno, raw))
        return raw[1:-1].replace('\\"', '"'), STR
    if raw.startswith("["):
        if not raw.endswith("]"):
            raise ManifestError(
                "%s:%d: an array must close on the same line (the schema has "
                "no multi-line arrays): %s" % (path, lineno, raw))
        body = raw[1:-1].strip()
        if not body:
            return [], STRLIST
        items = []
        for part in body.split(","):
            part = part.strip()
            if not part:
                continue
            if not (part.startswith('"') and part.endswith('"')
                    and len(part) >= 2):
                raise ManifestError(
                    "%s:%d: an array holds double-quoted strings and nothing "
                    "else; found %s" % (path, lineno, part))
            items.append(part[1:-1].replace('\\"', '"'))
        return items, STRLIST
    if raw.isdigit():
        return int(raw), INT
    raise ManifestError(
        "%s:%d: a value is a string, a non-negative integer or an array of "
        "strings; found %s" % (path, lineno, raw))


def parse(path):
    """Parse `path` into `{table: dict}` plus `{'test': [dict, ...]}`.

    Raises `ManifestError` on anything it cannot read. It never guesses: a
    manifest that half-parses is worse than one that does not parse, because
    the half that vanished is silently no longer enforced.
    """
    with open(path, "r", encoding="utf-8") as fh:
        lines = fh.read().splitlines()

    doc, current, cur_name = {}, None, None
    for lineno, raw in enumerate(lines, 1):
        line = _strip_comment(raw).strip()
        if not line:
            continue
        if line.startswith("[["):
            if not line.endswith("]]"):
                raise ManifestError("%s:%d: unterminated `[[`: %s"
                                    % (path, lineno, raw))
            cur_name = line[2:-2].strip()
            current = {}
            doc.setdefault(cur_name, []).append(current)
            continue
        if line.startswith("["):
            if not line.endswith("]"):
                raise ManifestError("%s:%d: unterminated `[`: %s"
                                    % (path, lineno, raw))
            cur_name = line[1:-1].strip()
            if cur_name in doc and not isinstance(doc[cur_name], list):
                raise ManifestError("%s:%d: table [%s] appears twice"
                                    % (path, lineno, cur_name))
            current = {}
            doc[cur_name] = current
            continue
        if "=" not in line:
            raise ManifestError(
                "%s:%d: expected `key = value`, a `[table]` or a "
                "`[[array-of-table]]`: %s" % (path, lineno, raw))
        if current is None:
            raise ManifestError("%s:%d: a key outside any table: %s"
                                % (path, lineno, raw))
        key, _, rest = line.partition("=")
        key = key.strip()
        if key in current:
            raise ManifestError("%s:%d: key `%s` appears twice in [%s]"
                                % (path, lineno, key, cur_name))
        value, kind = _value(rest, path, lineno)
        current[key] = (value, kind, lineno)
    return doc


def check(doc, path):
    """Diff the parsed manifest against SCHEMA, in both directions.

    Returns `{table: {key: value}}` with the line numbers dropped, or raises
    with EVERY problem listed rather than the first -- a schema check that
    stops at the first fault makes fixing a manifest an N-round trip.
    """
    problems = []

    for name in doc:
        if name not in SCHEMA:
            problems.append("unknown table [%s]; the schema has %s"
                            % (name, ", ".join(sorted(SCHEMA))))
    for name in SCHEMA:
        if name not in doc:
            problems.append("missing table [%s]" % name)

    out = {}
    for name, spec in SCHEMA.items():
        if name not in doc:
            continue
        entries = doc[name]
        if name in ARRAY_TABLES:
            if not isinstance(entries, list):
                problems.append("[%s] must be written `[[%s]]`" % (name, name))
                continue
        else:
            if isinstance(entries, list):
                problems.append("[[%s]] is not an array of tables in this "
                                "schema" % name)
                continue
            entries = [entries]

        checked = []
        for entry in entries:
            got = {}
            for key, (value, kind, lineno) in entry.items():
                if key not in spec:
                    problems.append(
                        "%s:%d: [%s] has no key `%s`; it has %s"
                        % (path, lineno, name, key,
                           ", ".join(sorted(spec)) or "no keys at all"))
                    continue
                if kind != spec[key]:
                    problems.append(
                        "%s:%d: [%s] `%s` must be a %s, and is a %s"
                        % (path, lineno, name, key, spec[key], kind))
                    continue
                got[key] = value
            for key in REQUIRED[name]:
                if key not in got:
                    problems.append("[%s] is missing the required key `%s`"
                                    % (name, key))
            checked.append(got)
        out[name] = checked if name in ARRAY_TABLES else checked[0]

    # `[dependencies]` is required to be empty, and that is B-10 made
    # mechanical rather than remembered. Anything here is a zero-dependency
    # decision and has to be argued as one.
    deps = doc.get("dependencies")
    if isinstance(deps, dict) and deps:
        problems.append(
            "[dependencies] is not empty (%s). `ntime` depends on the language "
            "and its prelude and on nothing else (BUILD.md B-10, TM-027); "
            "adding one is a decision, so this check exists to make it a "
            "deliberate one." % ", ".join(sorted(deps)))

    for i, entry in enumerate(out.get("test", [])):
        who = entry.get("name", "[[test]] #%d" % (i + 1))
        stage = entry.get("stage")
        if stage is not None and stage not in KNOWN_STAGES:
            problems.append("[[test]] `%s`: stage `%s` is not one of %s"
                            % (who, stage, ", ".join(KNOWN_STAGES)))
        elif stage in DECLINED_STAGES:
            problems.append(
                "[[test]] `%s`: stage `%s` exists upstream and this library "
                "does not use it -- %s" % (who, stage, DECLINED_STAGES[stage]))
        elif stage in WHOLE_TREE_STAGES:
            problems.append(
                "[[test]] `%s`: stage `%s` runs over the WHOLE TREE here and "
                "is not a `[[test]]` entry (BUILD.md §3's Directory column for "
                "it reads \"every `.npk` in the tree\"). An entry would narrow "
                "it to one directory and silently un-cover the rest -- and the "
                "files worth parsing are exactly the ones no entry selects."
                % (who, stage))
        elif stage is not None and stage not in IMPLEMENTED_STAGES:
            # REFUSED BY NAME, NOT SKIPPED. See KNOWN_STAGES above.
            problems.append(
                "[[test]] `%s`: stage `%s` is a real stage this harness does "
                "not implement yet (it does `%s`). An entry a runner cannot "
                "honour is refused by name before anything runs, never skipped."
                % (who, stage, "` and `".join(IMPLEMENTED_STAGES)))
        kind = entry.get("kind")
        if kind is not None and kind not in KNOWN_KINDS:
            problems.append("[[test]] `%s`: kind `%s` is not one of %s"
                            % (who, kind, ", ".join(KNOWN_KINDS)))
        if stage == "compile" and kind is None:
            problems.append(
                "[[test]] `%s`: a `compile` entry needs a `kind` (B-4b). "
                "`positive` means compiles, links, RUNS and exits as expected; "
                "`accept` -- \"accepted in silence\" -- is the shape a program "
                "with no `failsafe` walks through (TM-114)." % who)

    if problems:
        raise ManifestError("%s: %d schema problem(s):\n  - %s"
                            % (path, len(problems), "\n  - ".join(problems)))
    return out


def load(root):
    """Read and check `<root>/nitpick.toml`. The only entry point."""
    path = os.path.join(root, "nitpick.toml")
    if not os.path.isfile(path):
        raise ManifestError("%s: no manifest. Every path, flag and version "
                            "this harness uses comes from it (P-12)." % path)
    return check(parse(path), path)
