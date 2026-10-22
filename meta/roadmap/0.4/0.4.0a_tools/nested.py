#!/usr/bin/env python3
"""0.4.0a -- the census for a landing past the pin: every `func:` declared INSIDE A FUNCTION'S BODY in a tree's
`.npk` files, which the compiler's landing 141 (its DEF-268) reports once, `NITPICK-PARSE-001` at `func`, naming
D-018 -- a shape no pin of ours compiles into a nested function either way (D-018: there are no closures).

    python3 -B nested.py <tree>

Each tracked `.npk` (every `.npk`, for a copy that is no work tree) is read through <tree>'s OWN
`harness/lexical.py`, comments and literals blanked, so a `func:` in a comment or a string is never counted. A brace
that opens a function's body -- the first `{` after a `func:` header at its depth -- is a BODY brace, and every brace
inside one is too; an `impl`, a `trait`, a `struct`'s or a module's braces are not, so a method is no nested
function. A `func:` met while any body brace is open is a nested declaration, printed with its file and line.
First, the planted control: one text holding a nested function, one inside an `if` of a body, a method in an `impl`,
and the word in a comment and in a string -- two caught, three not -- or the census is not run.
"""
import os
import re
import subprocess
import sys

TOKEN = re.compile(r"\bfunc:|[{}]")

CONTROL = '''mod:control;
impl:P:Show = {
    func:show = int32(Self->:self) never fails { pass 1i32; };
};
// func:in_a_comment = int32() never fails { pass 1i32; };
func:main = int32(cstring[]:_~argv) {
    string:s = "func:in_a_string = int32() { }";
    func:inner = int32() never fails { pass 1i32; };
    if (true) {
        func:deeper = int32() never fails { pass 2i32; };
    }
    exit 0i32;
};
'''


def nested(code):
    """The 1-based lines at which a `func:` stands inside a function's body, in blanked `code`."""
    stack, pending, out = [], False, []
    for m in TOKEN.finditer(code):
        t = m.group(0)
        if t == "func:":
            if any(k == "body" for k in stack):
                out.append(code.count("\n", 0, m.start()) + 1)
            pending = True
        elif t == "{":
            if pending:
                stack.append("body")
                pending = False
            else:
                stack.append("body" if any(k == "body" for k in stack) else "decl")
        else:
            if stack:
                stack.pop()
    return out


def files(tree):
    r = subprocess.run(["git", "-C", tree, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if r.returncode == 0 and os.path.realpath(r.stdout.strip()) == os.path.realpath(tree):
        return subprocess.run(["git", "-C", tree, "ls-files", "*.npk"], capture_output=True, text=True).stdout.split()
    out = []
    for d, dirs, names in os.walk(tree):
        dirs[:] = sorted(x for x in dirs if x not in (".git", ".internal", "build"))
        out += [os.path.relpath(os.path.join(d, n), tree) for n in names if n.endswith(".npk")]
    return sorted(out)


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    tree = os.path.realpath(argv[1])
    sys.path.insert(0, os.path.join(tree, "harness"))
    import lexical
    got = nested(lexical.blank(CONTROL))
    print("the control: %d nested declaration(s) caught, at line(s) %s -- want 2, at 8 and 10"
          % (len(got), " ".join(str(g) for g in got)))
    if got != [8, 10]:
        print("STOP: the control does not hold; the census is not run")
        return 1
    fs = files(tree)
    hits = []
    for rel in fs:
        code = lexical.blank(lexical.read(os.path.join(tree, rel)))
        hits += ["%s:%d" % (rel, n) for n in nested(code)]
    print("%d .npk file(s) read: %d `func:` declared inside a function's body%s"
          % (len(fs), len(hits), (" -- " + " ".join(hits)) if hits else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
