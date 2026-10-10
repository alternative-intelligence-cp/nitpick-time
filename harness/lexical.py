"""THE HARNESS'S ONE READING OF NITPICK SOURCE -- cycle 0.1.5, TM-199.

EVERY `.npk` FILE THIS HARNESS OPENS IS OPENED BY `read()` HERE, and every
reading of one as CODE goes through `spans()`, `blank()` and `imports()`: the
import walk (`build.imports_of`, and through it `check_layering`, the library's
reach and the arm generator's subgraph), the arm generator's operator scan
(`arms.code_only`), the exemption verdict (`run._verdict`), the expectation
markers (`stages.read`), the two whole-tree scanners (`check_specs_current` and
`check_denominators`, whose line numbers are therefore `git grep -n`'s), the
umbrella's re-export count, and every tree check (`checks.strip_comments`,
`checks.blank_code`, `checks.code_lines`).

WHY, MEASURED AT CYCLE 0.1.5'S PLANNING, AT COMPILER `c970483`. Until then the
harness opened source in Python's TEXT MODE at seven sites, and blanked comments
and strings with two scanners of its own that knew `//` and `"` and nothing
else. The compiler's lexer does not read source that way, and eight shapes, each
planted in a scratch tree against the check it could fool, disagreed with it:
a lone CR ended a `//` comment here and not there, so what followed it was a
phantom import (`check_layering` RED over a program that imports nothing) or
opened a phantom string that blanked the next line's division
(`check_literal_divisors` silent); a `//` inside a `/* */` blanked the rest of
its line, hiding a clock call from `check_purity` and a fourth `error:` from
`check_error_budget`; a `'"'` character literal and a template's `//` each hid
a division; an escaped `use` path, `"..\\x2fhost/host.npk"`, hid an import of
`host` from `check_layering`, because the walk read the literal's TEXT and the
compiler reads its DECODED VALUE; and a `pub use` inside a `/* */` was
counted as a re-export (`check_denominators` RED over a count that was
right). Each form was run through the compiler too, as a program of its own,
with the same reading at `c970483` and `c3bdae2`, and the compiler's reading
is the one below. `0.1.5.md` section 1.3 has the table.

WHERE THIS MODULE COMES FROM. `nitpick-regex` met the same class at its cycle
0.0 close -- its fourth and fifth audits -- and answered it with this module
(its RX-157 and RX-165). THE EXECUTABLE CODE BELOW IS THAT REPOSITORY'S
`harness/lexical.py` AT ITS `fb37391`, STATEMENT FOR STATEMENT: `0.1.5.md`
compares the two files' syntax trees with every docstring removed, and they
are equal. The docstrings and the comments are this repository's; where they
cite a decision of `nitpick-regex`'s they say whose. One reader in two
libraries is one thing to re-read when the compiler's lexer moves.

WHAT IT MIRRORS, READ AT COMPILER `c970483` WITH `git show`, NOT FROM A
SUMMARY: `src/frontend/lexer.npk`'s `is_space`, `lexer_skip_trivia` and
`lexer_next`; `src/frontend/escapes.npk`'s `escape_decode` and
`decode_string`; and `p_parse_import` in `src/frontend/parse_decl.npk`.
AND AGAIN AT `5fbaf4a` (cycle 0.2.0a, the re-read TM-202 makes every
adoption's; TM-208), where `lexer.npk` differs only in a character literal's
WIDTH -- the compiler's DEF-145: one above U+00FF, or written `\\u{...}`, is
`char32` -- and not in what a literal spans, and `escapes.npk`,
`p_parse_import` and `LEXICAL_REFERENCE.md` not at all, so nothing below
moved.
AND AGAIN AT `7e91730` (cycle 0.3.2a, TM-259), where `lexer.npk` reads a
FLOAT literal by its production -- `num_float_scan`, the body and one
suffix or nothing (the compiler's DEF-166), a sign only where a digit
follows it (DEF-164) -- and keeps a refused integer literal a literal token
(DEF-164); `numeric.npk` gained the float's scan, and `parse_decl.npk` and
`LEXICAL_REFERENCE.md` §6.2 the float's production; `escapes.npk` did not
move, and `p_parse_import` and `num_scan` read the same at both pins. No
span this module finds moved, so nothing below moved -- and the float case
the list below names, `e+r"` after one, now reads as this module reads it:
`1.5e+r"a"` is `NITPICK-LEX-009` at its tail and then a raw string.

  * THE TEXT IS BYTES. `read()` maps each byte to one character (latin-1), so
    every offset is the compiler's byte offset, `\\n` (byte 10) is the only
    line end, and nothing translates a CR. WHITESPACE is exactly the lexer's
    `is_space`: space, tab, CR and LF.
  * `//` runs to the end of the line -- to byte 10, whatever precedes it.
  * `/* ... */` does NOT NEST: the first `*/` closes it, and an unterminated
    one runs to the end of the file.
  * `"..."`: `\\` skips the byte after it; a NEWLINE ends the literal (the
    lexer's "newline in a string literal").
  * `""` followed by anything but `"` is an EMPTY string; three quotes open a
    BLOCK string, which closes at the first unescaped three -- the compiler's
    close since its 1.6.0 step 3e (DEF-98), in `c970483` and not in `c3bdae2`,
    which closed at the first `""`. No `.npk` here holds a block string.
  * `r"..."` is RAW -- no escapes, closed by the next `"` -- when the `r`
    begins a token.
  * `'x'`: a `\\` escape or ONE code point, then `'`; without the closing
    quote the lexer resyncs past the next `'` on the line, and so does this.
  * `` `...` ``: a TEMPLATE. Its text is literal and is not trivia -- a `//`
    in it is text -- and `&{` opens an interpolation that is CODE until the
    `}` that closes it at the brace depth it opened at.

WHAT IT IS NOT: a lexer. It finds the spans that are not code and nothing
else. `spans()` returns them; `blank()` replaces each with spaces, keeping every
newline, so a check's line and column numbers are the file's own; `imports()`
reads `use` declarations as `p_parse_import` does, and the path is the
literal's DECODED value.

WHAT IT STILL DOES NOT MIRROR, and each is confined to files the compiler
REFUSES -- which the `parse` stage, rooting every `.npk` in the tree at
`npkc`, turns red whatever this module reads in them: a NUL byte; an
interpolation nested more than eight deep; `_?`, `_!`, `_~`, `_^` at the start
of a template part; `e+r"` after a float; an invalid escape or UTF-8 sequence;
and a path that begins neither `./`, `../` nor `/`.

ITS OWN TEST IS THE SELF-CHECK'S PART E (`selfcheck.part_e`): one text holding
every form above, written to a FILE, read back through `read()`, and required
to give exactly the imports and the code the compiler would see -- and one
program holding the forms a run can observe that `selfcheck._FORMS_EXIT` names,
each literal's VALUE asserted, compiled by the pinned `npkc` and
required to exit 0, so a re-pin that moves the lexer ON ONE OF THOSE FORMS is a
red run and not a silent disagreement. A form it does not hold is not asked --
which is why the adoption that moves the pin re-reads `src/frontend/lexer.npk`
whatever part E says (TM-202). *(Until cycle 0.1.5's second half this said
"every form a run can observe" over a program of seven, with no block, raw,
escaped or empty string and no interpolation, and the block string's close --
the one move between the kept pins, DEF-98 -- passed it at both: the audit's
C1.)*
"""
import os
import re

_IDENT = frozenset("abcdefghijklmnopqrstuvwxyz"
                   "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")
# The lexer's `is_space`, exactly: space, tab, carriage return, newline. Python's
# `\s` also matches VT, FF, 0x1C-0x1F, 0x85 and 0xA0, which the lexer calls
# unexpected characters.
_WS = " \t\r\n"


def read(path):
    """A `.npk` file's text AS THE COMPILER READS IT (TM-199).

    BYTES, one character per byte (latin-1): every offset is the compiler's byte
    offset and no line end is translated, so `\\n` is the only one -- where
    Python's text mode (`newline=None`) had made a lone CR a line end and hidden
    code from the checks behind it. THE ONE WAY THE HARNESS OPENS A `.npk` FILE.
    Raises `OSError` like `open()`; the callers keep their own handling."""
    with open(path, "rb") as fh:
        return fh.read().decode("latin-1")


def _hex(c):
    """`hex_value` in `escapes.npk`: the digit's value, or -1."""
    if "0" <= c <= "9":
        return ord(c) - 48
    if "a" <= c <= "f":
        return ord(c) - 87
    if "A" <= c <= "F":
        return ord(c) - 55
    return -1


_SIMPLE_ESCAPES = {"n": 10, "r": 13, "t": 9, "\\": 92, '"': 34, "'": 39, "0": 0}


def _escape(s, at):
    """`escape_decode`: `(codepoint, bytes consumed)` for the escape at `s[at]`
    (a backslash), or None where the compiler's is invalid -- `LEX-BAD-ESCAPE`,
    and the file is refused."""
    if at + 1 >= len(s):
        return None
    e = s[at + 1]
    if e in _SIMPLE_ESCAPES:
        return _SIMPLE_ESCAPES[e], 2
    if e == "x":                               # \xHH -- exactly two
        if at + 3 >= len(s):
            return None
        h1, h2 = _hex(s[at + 2]), _hex(s[at + 3])
        if h1 < 0 or h2 < 0:
            return None
        return h1 * 16 + h2, 4
    if e == "u":                               # \u{...}
        if at + 2 >= len(s) or s[at + 2] != "{":
            return None
        i, acc, seen = at + 3, 0, False
        while i < len(s):
            if s[i] == "}":
                if not seen or acc > 0x10FFFF:
                    return None
                return acc, (i - at) + 1
            h = _hex(s[i])
            if h < 0:
                return None
            acc, seen, i = acc * 16 + h, True, i + 1
        return None                            # unterminated
    return None


def _decode(content):
    """`decode_string`: a plain literal's CONTENT (between its quotes, one
    character per source byte) to the BYTES of its value. An escape becomes its
    code point in UTF-8 -- `\\x2f` is `/`, and `\\xC3` is two bytes, U+00C3 --
    and an invalid one is skipped at its backslash, as the compiler does while
    refusing the file."""
    out = bytearray()
    i = 0
    while i < len(content):
        if content[i] == "\\":
            r = _escape(content, i)
            if r is None:
                i += 1
                continue
            out += chr(r[0]).encode("utf-8", "surrogatepass")
            i += r[1]
        else:
            out.append(ord(content[i]))
            i += 1
    return bytes(out)


# A `use` KEYWORD in blanked code: not the tail of an identifier, not a field
# (`x.use` -- a reserved word IS accepted as a field name, `nitpick-regex`'s
# RX-134), and not the head of a longer identifier.
_USE_KW = re.compile(r"(?<![A-Za-z0-9_.])use(?![A-Za-z0-9_])")
# `pub`, then any of the declaration modifiers `p_parse_decl` accepts between
# it and the keyword, then the end of the text before `use`. Whitespace is the
# lexer's (`_WS`), never Python's `\s`.
_PUB_BEFORE = re.compile(
    r"(?<![A-Za-z0-9_.])pub(?:[ \t\r\n]+(?:inline|noinline|comptime|async|thread))*[ \t\r\n]*$")


def spans(text):
    """Every comment and every literal, as `(kind, start, end)`, end exclusive.

    Kinds: `comment`, `string` (a plain `"..."`, which is the only kind a `use`
    may name), `raw`, `block`, `char`, `template` (a template's text and its
    backticks -- never its interpolations, which are code)."""
    out = []
    n = len(text)
    i = 0
    in_template = False
    interp = []            # the brace depth at each open `&{` -- the lexer's `interp_brace`
    brace = 0
    while i < n:
        if in_template:
            s = i
            while i < n and text[i] != "`" and not (
                    text[i] == "&" and i + 1 < n and text[i + 1] == "{"):
                i += 1
            if i >= n:
                out.append(("template", s, n))
                break
            if text[i] == "`":
                out.append(("template", s, i + 1))
                i += 1
                in_template = False
                continue
            if i > s:
                out.append(("template", s, i))
            i += 2                              # `&{` -- code from here
            in_template = False
            interp.append(brace)
            continue

        c = text[i]
        nx = text[i + 1] if i + 1 < n else ""
        if c == "/" and nx == "/":
            e = text.find("\n", i)
            e = n if e < 0 else e
            out.append(("comment", i, e))
            i = e
            continue
        if c == "/" and nx == "*":
            e = text.find("*/", i + 2)
            e = n if e < 0 else e + 2
            out.append(("comment", i, e))
            i = e
            continue
        if c == "}" and interp and brace == interp[-1]:
            interp.pop()                        # closes an interpolation: text again
            i += 1
            in_template = True
            continue
        if c == "{":
            brace += 1
            i += 1
            continue
        if c == "}":
            brace -= 1
            i += 1
            continue
        if c == "`":
            out.append(("template", i, i + 1))
            i += 1
            in_template = True
            continue
        if c == "r" and nx == '"' and (i == 0 or text[i - 1] not in _IDENT):
            e = text.find('"', i + 2)
            e = n if e < 0 else e + 1
            out.append(("raw", i, e))
            i = e
            continue
        if c == '"':
            if nx == '"':
                if i + 2 < n and text[i + 2] == '"':
                    # A BLOCK STRING CLOSES AT `"""` (DEF-98, the compiler's 1.6.0
                    # step 3e) -- through `c3bdae2` at the first `""`.
                    j = i + 3
                    while j < n:
                        if (text[j] == '"' and j + 2 < n and text[j + 1] == '"'
                                and text[j + 2] == '"'):
                            break
                        if text[j] == "\\":
                            j += 1
                        j += 1
                    e = min(n, j + 3)
                    out.append(("block", i, e))
                    i = e
                    continue
                out.append(("string", i, i + 2))      # `""`, the empty string
                i += 2
                continue
            j = i + 1
            while j < n:
                if text[j] == "\n":
                    break                             # the lexer stops the literal here
                if text[j] == '"':
                    j += 1
                    break
                if text[j] == "\\":
                    j += 1
                j += 1
            e = min(n, j)
            out.append(("string", i, e))
            i = e
            continue
        if c == "'":
            j = i + 1
            if j < n and text[j] == "\\":
                if j + 1 < n and text[j + 1] == "x":
                    j += 4
                elif j + 2 < n and text[j + 1] == "u" and text[j + 2] == "{":
                    k = text.find("}", j + 3)
                    j = n if k < 0 else k + 1
                else:
                    j += 2
            elif j < n:
                j += 1                                # ONE code point
            if j < n and text[j] == "'":
                e = j + 1
            else:
                e = j                                 # the lexer's resync
                while e < n and text[e] != "\n":
                    if text[e] == "'":
                        e += 1
                        break
                    e += 1
            e = min(n, e)
            out.append(("char", i, e))
            i = e
            continue
        i += 1
    return out


def blank(text, sp=None):
    """The text with every comment and literal replaced by spaces, NEWLINES KEPT,
    so offsets, lines and columns are the file's own. Interpolations stay: they
    are code, and a `/` in one arms `DivByZero` like any other."""
    chars = list(text)
    for _, s, e in (spans(text) if sp is None else sp):
        for k in range(s, e):
            if chars[k] != "\n":
                chars[k] = " "
    return "".join(chars)


def imports(text):
    """Every `use` declaration the compiler would read: `[(line, target, pub)]`.

    `text` is what `read()` returns. `target` is the string literal's DECODED
    value, as a filesystem path -- `os.fsdecode` of the bytes `_decode` gives,
    which is the path the compiler's `p_parse_import` takes. Until cycle 0.1.5
    this harness read the literal's TEXT (`build.imports_of`), so
    `"..\\x2fhost/host.npk"` was a directory named `..\\x2fhost` inside the
    importer's own layer, and an import of `host` passed `check_layering`. A `use`
    inside a comment, a string or a template is not code and is not an import."""
    sp = spans(text)
    code = blank(text, sp)
    trivia = {s: e for k, s, e in sp if k == "comment"}
    plain = {s: e for k, s, e in sp if k == "string"}
    out = []
    n = len(text)
    for m in _USE_KW.finditer(code):
        j = m.end()
        while j < n:
            if text[j] in _WS:
                j += 1
            elif j in trivia:
                j = trivia[j]
            else:
                break
        if j not in plain:
            continue                          # a logical path (`use std.x.*;`), or not an import
        target = os.fsdecode(_decode(text[j + 1:plain[j] - 1]))
        if not target:
            continue
        pub = _PUB_BEFORE.search(code, 0, m.start()) is not None
        out.append((text.count("\n", 0, m.start()) + 1, target, pub))
    return out
