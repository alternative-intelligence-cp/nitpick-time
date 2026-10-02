#!/usr/bin/env python3
"""0.2.4b -- `contracts.py <tree> [answer]`. `VERIFICATION.md` P-1b says the switch from a
comment-form obligation to a live clause is mechanical: uncomment it. This makes
every contract comment in `src/` LIVE, one at a time, in a scratch copy of its
module, and asks the pinned compiler (`$NPKC`) whether it compiles.

A contract comment is a `//` comment whose text begins with a backtick and
`ensures`, `requires` or `prove`, running to the closing backtick across
continued `//` lines. An `ensures` or `requires` is inserted before the body's
`{` of the next function declared after it; a `prove` must stand inside a body,
and is uncommented where it stands -- one above a function is reported, since
nothing makes it a statement. `answer` substitutes `result` for `answer` first
(the measurement of the tree before the subcycle). Prints one line a clause and
a summary; writes only under `$W/contracts`, env.sh's scratch, which it removes.
Run under `python3 -B`, with `NPKC` and `W` set by env.sh.
"""
import os, re, shutil, subprocess, sys

NPKC = os.environ["NPKC"]
tree = os.path.realpath(sys.argv[1])
subst = len(sys.argv) > 2 and sys.argv[2] == "answer"
MODULES = ["src/cal/cal.npk", "src/core/bytes.npk", "src/core/vec.npk",
           "src/span/span.npk"]
OPEN = re.compile(r"^(\s*)//\s?`((?:ensures|requires|prove)\b.*)$")
FUNC = re.compile(r"^(?:pub\s+)?func:([A-Za-z_][A-Za-z0-9_]*)")
work = os.path.join(os.environ["W"], "contracts")    # env.sh's scratch, under .internal/


def clauses(lines):
    """[(first, last, text)] -- 0-based line span of each contract comment."""
    out, i = [], 0
    while i < len(lines):
        m = OPEN.match(lines[i])
        if not m:
            i += 1
            continue
        text, j = m.group(2), i
        while "`" not in text and j + 1 < len(lines):
            j += 1
            text += " " + re.sub(r"^\s*//\s*", "", lines[j])
        out.append((i, j, text[:text.index("`")] if "`" in text else text))
        i = j + 1
    return out


def body_of(lines, i):
    """The function whose body holds line i, as (name, open_line), or None."""
    depth, name = 0, None
    for k in range(i, -1, -1):
        depth += lines[k].count("}") - lines[k].count("{")
        if depth < 0:
            m = FUNC.match(lines[k].lstrip())
            if m:
                return m.group(1)
            return "<body>"
    return None


def compile_one(rel, new_lines):
    if os.path.exists(work):
        shutil.rmtree(work)
    shutil.copytree(os.path.join(tree, "src"), os.path.join(work, "src"))
    shutil.copy(os.path.join(tree, "nitpick.toml"), work)   # the manifest too (the compiler's D-236)
    with open(os.path.join(work, rel), "w", encoding="utf-8") as fh:
        fh.write("\n".join(new_lines))
    d = os.path.dirname(os.path.join(work, rel))
    r = subprocess.run([NPKC, os.path.basename(rel), "-o", "/dev/null"], cwd=d,
                       capture_output=True, text=True)
    codes = re.findall(r"^(NITPICK-[A-Z]+-\d+) ", r.stdout + r.stderr, re.M)
    return "compiles" if r.returncode == 0 and not codes else " ".join(sorted(set(codes))) or "exit %d" % r.returncode


total, live, refused = 0, 0, 0
for rel in MODULES:
    lines = open(os.path.join(tree, rel), encoding="utf-8").read().split("\n")
    for first, last, text in clauses(lines):
        total += 1
        if subst:
            text = re.sub(r"\banswer\b", "result", text)
        kind = text.split("(")[0].split()[0]
        if kind == "prove":
            owner = body_of(lines, first)
            if owner is None:
                print("%s:%d %-26s prove, above a function: no place to uncomment it" % (rel, first + 1, "-"))
                refused += 1
                continue
            new = lines[:first] + [lines[first][:len(lines[first]) - len(lines[first].lstrip())] + text] + lines[last + 1:]
            fn = owner
        else:
            j = next((k for k in range(last + 1, len(lines)) if FUNC.match(lines[k])), None)
            k = j
            while "{" not in lines[k]:
                k += 1
            at = lines[k].index("{")
            new = list(lines)
            new[k] = lines[k][:at] + text + " " + lines[k][at:]
            fn = FUNC.match(lines[j]).group(1)
        verdict = compile_one(rel, new)
        if verdict == "compiles":
            live += 1
        else:
            refused += 1
        print("%s:%d %-26s %-8s %s" % (rel, first + 1, fn, kind, verdict))
shutil.rmtree(work, ignore_errors=True)
print("contracts: %d comment(s), %d compile as live clauses, %d do not" % (total, live, refused))
