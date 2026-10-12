#!/usr/bin/env python3
"""0.3.3 -- every SINGLE-SITE mutant of the double, `tests/double/host_double.npk`,
generated, never chosen (the plan's §1.9).

    python3 -B mutate.py list <host_double.npk>   # one line each: id, operator, old, new

THE CODE is the file from `pub struct:MachineHost` to its end -- the machine's
host, the double, its setters and its readings; the module header, its imports
and the trait's five signatures declare and do nothing. A line's `//` tail,
outside a string, is never mutated.

ONE SITE, ONE CHANGE. The operators, each applied at every site it matches:

  ror   a comparison `==` `!=` `<` `<=` `>` `>=` (spaced) -> each of the other five
  aor   a binary `+` or `-` (spaced) -> the other, and `*`; `/` <-> `%`
  lit   an integer literal N -> N+1, N-1 and 0 (each that differs, in its type's range)
  bool  `true` <-> `false`
  neg   `if (C)` -> `if (!(C))`
  sdl   a statement deleted: a line's whole statement, or one inside a
        one-line block, `{ h.mono = i; }` among them
  enum  `ZoneSource.X` and `InstantClock.X` -> each other variant
  str   a string literal -> `""` and its last byte dropped (non-empty), `"x"` (empty)
  field a field of the double read or written -> the other of its type:
        `utc_secs` <-> `utc_nanos`, `mono` <-> `boot`
  const `NTIME_NANOS_PER_SEC` -> `(NTIME_NANOS_PER_SEC - 1i64)` and `(NTIME_NANOS_PER_SEC + 1i64)`
  arg   `host_clock_res(which)` -> each `HostClock` variant in place of `which`

An id is `<line>.<n>`, `n` counting the line's mutants in the order above, so
it is stable while the file's text is. `mutants()` gives each as a list of
edits `(line index, start, end, new)`.
"""
import re
import sys

START = "pub struct:MachineHost"
ROR = ["==", "!=", "<", "<=", ">", ">="]
TYPES = {"i64": (-(2 ** 63), 2 ** 63 - 1), "i32": (-(2 ** 31), 2 ** 31 - 1)}
ENUMS = {"ZoneSource": ["TzEnvironment", "EtcLocaltime", "EtcTimezone", "NotFound"],
         "InstantClock": ["Monotonic", "Boottime"]}
FIELDS = {"utc_secs": "utc_nanos", "utc_nanos": "utc_secs", "mono": "boot", "boot": "mono"}


def code_end(line):
    in_str, i = False, 0
    while i < len(line):
        c = line[i]
        if c == '"':
            in_str = not in_str
        elif c == "\\" and in_str:
            i += 1
        elif not in_str and line.startswith("//", i):
            return i
        i += 1
    return len(line)


def strings(code):
    out, i = [], 0
    while i < len(code):
        if code[i] == '"':
            j = i + 1
            while j < len(code) and code[j] != '"':
                j += 2 if code[j] == "\\" else 1
            out.append((i, j + 1))
            i = j + 1
        else:
            i += 1
    return out


def matching_paren(code, i):
    depth = 0
    for j in range(i, len(code)):
        if code[j] == "(":
            depth += 1
        elif code[j] == ")":
            depth -= 1
            if depth == 0:
                return j
    return -1


def lit_values(v, ty):
    lo, hi = TYPES[ty]
    out = []
    for w in (v + 1, v - 1, 0):
        if w != v and lo <= w <= hi and w not in out:
            out.append(w)
    return out


def depth(code):
    return code.count("(") - code.count(")") + code.count("{") - code.count("}")


def line_mutants(code, whole_statement):
    spans = strings(code)
    muts = []

    def outside(a, b):
        return all(b <= s or a >= e for s, e in spans)

    def add(op, a, b, new):
        if op == "str" or outside(a, b):
            muts.append((op, a, b, new))

    for m in re.finditer(r"(?<= )(==|!=|<=|>=|<|>)(?= )", code):
        for alt in ROR:
            if alt != m.group(1):
                add("ror", m.start(), m.end(), alt)
    for m in re.finditer(r"(?<=[\w\])] )([+\-/%])(?= )", code):
        alts = {"+": ["-", "*"], "-": ["+", "*"], "/": ["%"], "%": ["/"]}[m.group(1)]
        for alt in alts:
            add("aor", m.start(), m.end(), alt)
    for m in re.finditer(r"(?<![\w.])(-?)(\d+)(i64|i32)\b", code):
        neg, digits, ty = m.groups()
        if neg and not re.search(r"[=|(,] $", code[:m.start()]):
            continue
        v = int(digits) * (-1 if neg else 1)
        for w in lit_values(v, ty):
            add("lit", m.start(), m.end(), "%d%s" % (w, ty))
    for m in re.finditer(r"\b(true|false)\b", code):
        add("bool", m.start(), m.end(), "false" if m.group(1) == "true" else "true")
    for m in re.finditer(r"\bif \(", code):
        o = m.end() - 1
        c = matching_paren(code, o)
        if c > 0:
            add("neg", o, c + 1, "(!(%s))" % code[o + 1:c])
    stripped = code.strip()
    lead = len(code) - len(code.lstrip())
    declaration = re.match(r"(fixed |pub |func:|#\[|struct:|enum:|impl:|use |hidden )", stripped)
    if (whole_statement and stripped.endswith(";") and not stripped.startswith("}")
            and not declaration):
        add("sdl", lead, len(code.rstrip()), "")
    for m in ([] if declaration else re.finditer(r"\{ ([^{}]*;) \}", code)):
        inner, base = m.group(1), m.start(1)
        for part in re.finditer(r"[^;]+;", inner):
            a = base + part.start() + (len(part.group()) - len(part.group().lstrip()))
            add("sdl", a, base + part.end(), "")
    for m in re.finditer(r"\b(ZoneSource|InstantClock)\.(\w+)", code):
        for v in ENUMS[m.group(1)]:
            if v != m.group(2):
                add("enum", m.start(2), m.end(2), v)
    for a, b in spans:
        body = code[a + 1:b - 1]
        if body:
            add("str", a, b, '""')
            add("str", a, b, '"%s"' % body[:-1])
        else:
            add("str", a, b, '"x"')
    for m in re.finditer(r"\b(?:self|h)\.(utc_secs|utc_nanos|mono|boot)\b", code):
        add("field", m.start(1), m.end(1), FIELDS[m.group(1)])
    for m in re.finditer(r"\bNTIME_NANOS_PER_SEC\b", code):
        if code.lstrip().startswith("use "):
            continue
        for alt in ("(NTIME_NANOS_PER_SEC - 1i64)", "(NTIME_NANOS_PER_SEC + 1i64)"):
            add("const", m.start(), m.end(), alt)
    for m in re.finditer(r"\bhost_clock_res\((which)\)", code):
        for v in ("HostClock.Realtime", "HostClock.Monotonic", "HostClock.Boottime"):
            add("arg", m.start(1), m.end(1), v)
    return muts


def section(lines):
    for i, l in enumerate(lines):
        if l.startswith(START):
            return i
    raise SystemExit("STOP: no `%s` line" % START)


def mutants(path):
    """`(lines, [(id, op, old, new, [(line index, start, end, new)])])`."""
    lines = open(path, encoding="utf-8").read().split("\n")
    first = section(lines)
    codes = {i: lines[i][:code_end(lines[i])] for i in range(first, len(lines))}
    # A statement spanning lines: its first line opens a paren or brace it does
    # not close, and it is not a block's opening line.
    spanning, i = {}, first
    while i < len(lines):
        c = codes[i].strip()
        if c and depth(codes[i]) > 0 and not c.endswith("{"):
            j, d = i, 0
            while j < len(lines):
                d += depth(codes[j])
                if d <= 0:
                    break
                j += 1
            spanning[i] = j
            i = j + 1
        else:
            i += 1
    inside = {k for s, e in spanning.items() for k in range(s, e + 1)}
    out = []
    for i in range(first, len(lines)):
        code = codes[i]
        if not code.strip():
            continue
        n, seen = 0, set()
        for op, a, b, new in line_mutants(code, i not in inside):
            if (a, b, new) in seen:
                continue
            seen.add((a, b, new))
            n += 1
            out.append(("%d.%d" % (i + 1, n), op, code[a:b], new, [(i, a, b, new)]))
        if i in spanning:
            e = spanning[i]
            text = " ".join(codes[k].strip() for k in range(i, e + 1))
            if text.endswith(";") and not re.match(r"(fixed |pub |func:|impl:|use )", text):
                n += 1
                edits = [(k, len(codes[k]) - len(codes[k].lstrip()), len(codes[k].rstrip()), "")
                         for k in range(i, e + 1)]
                out.append(("%d.%d" % (i + 1, n), "sdl", text, "", edits))
    return lines, out


def apply(lines, edits):
    ml = list(lines)
    for i, a, b, new in edits:
        ml[i] = ml[i][:a] + new + ml[i][b:]
    return ml


def main(argv):
    if len(argv) == 3 and argv[1] == "list":
        _, muts = mutants(argv[2])
        for mid, op, old, new, _ in muts:
            print("\t".join([mid, op, old, new]))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
