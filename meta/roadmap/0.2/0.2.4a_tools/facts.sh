# meta/roadmap/0.2/0.2.4a_tools/facts.sh -- `0.2.4a.md` §1.6: re-derive §1 at the pin,
# in scratch copies of the tree, never in it. Sourced after `env.sh`, in one Bash
# call -- block 0b of the plan, run BEFORE step 1, while `harness/` is HEAD's:
#
#     . "$REPO/meta/roadmap/0.2/0.2.4a_tools/env.sh"; . "$T/facts.sh"
#
# Each finding of the cycle audit this subcycle answers is re-measured against the
# checks as `HEAD` holds them: C3 (an owned number in `core` outside `limits.npk`),
# C8 (a bound spelled by its value), C4 (an optional of a view) and D1 (an
# integer wider than `int64`) -- each planted in a copy of `src/`, the check run
# over it -- and the facts the fixes rest on: the values `limits.npk`'s bounds
# hold, which literals in `src/` equal one, the optional and the wide types
# compiling at the pin, and the `=>!` and wrapping-operator census of `src/`.
: "${REPO:?}" "${NPKC:?}" "${NPKRT:?}" "${W:?}"
P=$W/facts; rm -rf "${P:?}"; mkdir -p "$P"
fresh() {   # fresh <name>: a copy of the working tree as it stands -- tracked and new files
  rm -rf "${P:?}/$1"; mkdir -p "$P/$1"         # -- at $P/<name>, its own harness with it
  ( cd "$REPO" && git ls-files -co --exclude-standard -z | xargs -0 tar -cf - ) | tar -xf - -C "$P/$1"
}
append() { printf '%s\n' "$2" >> "$P/$1"; }       # append <name>/<rel> <text>
headcheck() {   # headcheck <check> <name>: the copy's own check -- HEAD's -- over the copy
  python3 -B - "$1" "$P/$2" <<'PY2'
import os, sys
sys.path.insert(0, os.path.join(sys.argv[2], "harness"))
import checks
r = getattr(checks, sys.argv[1])(sys.argv[2])
print("%s: %d finding(s) -- %s" % (r.name, len(r.problems), r.headline))
for p in r.problems:
    print("  " + p.splitlines()[0][:120])
PY2
}
FS='func:failsafe = int32(Error:e) {
    pick (e) {
        (cal.ETimeValue)    { exit 80i32; },
        (HeapBadRequest)    { exit 91i32; },
        (HeapOom)           { exit 92i32; },
        (IntOverflow)       { exit 93i32; },
        (OutOfBounds)       { exit 94i32; },
        (Unreachable)       { exit 95i32; },
        (WildLeak)          { exit 96i32; },
        (DivByZero)         { exit 97i32; },
        (DivOverflow)       { exit 98i32; },
        (StackExhausted)    { exit 106i32; },
        (MachineFault)      { exit 107i32; },
        (*)                 { exit 99i32; }
    }
    exit 9i32;
};'
legs() {   # legs <dir> <name>: npkc, then -O0 and opt -O2, the two exits
  ( cd "$1" && { "$NPKC" "$2.npk" -o "$2.ll" > /dev/null 2>&1 || { echo "$2: npkc refused"; exit; }
    llc -O0 -filetype=obj -relocation-model=static "$2.ll" -o "$2.o" && ld.lld -static "$2.o" "$NPKRT" -o "$2" && ./"$2" > /dev/null; e0=$?
    opt -O2 -S "$2.ll" -o "$2.2.ll" && llc -O2 -filetype=obj -relocation-model=static "$2.2.ll" -o "$2.2.o" \
      && ld.lld -static "$2.2.o" "$NPKRT" -o "$2.2" && ./"$2.2" > /dev/null
    echo "$2: exit $e0 at -O0, $? after opt -O2"; } )
}

# ---- §1.1 C3: an owned number in `core`, outside `limits.npk`
fresh c3
append c3/src/core/bytes.npk $'\nfixed int64:ZZ_DAY = 86400i64;\nfixed int64:ZZ_NANO = 1_000_000_000i64;'
echo "C3, both numbers planted in src/core/bytes.npk:"; headcheck check_constants_named c3
fresh c3s
append c3s/src/span/span.npk $'\nfixed int64:ZZ_DAY = 86400i64;'
echo "C3, the same 86400i64 planted in src/span/span.npk:"; headcheck check_constants_named c3s

# ---- §1.2 C8: a bound spelled by its value
fresh c8
python3 -B - "$P/c8/src/span/span.npk" <<'PY'
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
old = "if (secs > NTIME_SECS_MAX)        { fail"
assert s.count(old) == 1
open(p, "w", encoding="utf-8").write(s.replace(old, "if (secs > 253402300799i64)       { fail"))
PY
echo "C8, timestamp_of's NTIME_SECS_MAX written as its value:"; headcheck check_constants_named c8
python3 -B - "$REPO" <<'PY'
import ast, os, re, sys
sys.path.insert(0, os.path.join(sys.argv[1], "harness"))
import checks, lexical
lim = os.path.join(sys.argv[1], "src/core/limits.npk")
text = lexical.read(lim); code = checks.blank_code(text)
vals = {}
for m in checks._BOUND_DECL.finditer(code):
    init = re.compile(checks._W + r"*=([^;]*);").match(code, m.end())
    expr = text[init.start(1):init.end(1)]
    lits = checks.literals(expr)
    e = expr
    for at, tok, v in reversed(lits):
        e = e[:at] + str(v) + e[at + len(tok):]
    vals[m.group(1)] = eval(compile(ast.parse(e.strip(), mode="eval"), "<b>", "eval"))
print("limits.npk's bounds: %d, their values: %s" % (len(vals), ", ".join(
    "%s=%d" % (k, v) for k, v in vals.items())))
small = {0, 1, 2, 3, 4, 7, 8, 15, 16, 24, 31, 32, 63, 64, 100, 127, 128, 255, 256}
absv = {abs(v) for v in vals.values()}
print("distinct absolute values: %d, of them in nitpick-regex's small set: %s"
      % (len(absv), ", ".join(str(v) for v in sorted(absv & small)) or "none"))
hits = []
for rel in checks.src_files(sys.argv[1]):
    if rel == "src/core/limits.npk":
        continue
    t = lexical.read(os.path.join(sys.argv[1], rel))
    for at, tok, v in checks.literals(t):
        if v is not None and abs(v) in absv - small:
            hits.append("%s:%d %s" % (rel, checks._line(t, at), tok))
print("literals in src/ outside limits.npk equal to a bound's value, the small ones aside: %d%s"
      % (len(hits), "".join("\n  " + h for h in hits)))
PY

# ---- §1.3 C4: an optional of a view
fresh c4c
printf 'mod:c4_consumer;\nuse "../src/span/span.npk".*;\nfunc:first_word = uint8[]?(uint8[]:src) never fails {\n    if (src.len == 0i64) { pass NIL; }\n    pass src;\n};\nfunc:main = int32(cstring[]:_~argv) {\n    uint8[]?:w = raw first_word(string_bytes("ab"));\n    exit 0i32;\n};\n%s\n' "$FS" > "$P/c4c/tests/c4_consumer.npk"
( cd "$P/c4c/tests" && "$NPKC" c4_consumer.npk -o c4_consumer.ll > /dev/null 2>&1; echo "first_word, returning uint8[]?, in a consumer: npkc=$? $( [ -s c4_consumer.ll ] && echo 'IR written' || echo 'no IR')" )
fresh c4
append c4/src/core/bytes.npk $'\nfunc:zz_first_word = uint8[]?(uint8[]:src) never fails { if (src.len == 0i64) { pass NIL; } pass src; };\nfunc:zz_twin = uint8[](uint8[]:src) never fails { pass src; };\nfunc:zz_cword = cstring?(cstring:src) never fails { pass NIL; };'
echo "C4, an optional uint8[] and an optional cstring planted beside a uint8[] twin:"; headcheck check_no_view_returns c4

# ---- §1.4 D1: an integer wider than `int64`
fresh d1
append d1/src/span/span.npk $'\npub func:zz_wide = int64(int64:a) never fails {\n    int256:w = (a => int256) * (a => int256);\n    pass w =>! int64;\n};\n\npub func:zz_uwide = int64(int64:a) never fails {\n    uint128:w = (a =>! uint128) * (a =>! uint128);\n    pass w =>! int64;\n};'
printf 'mod:d1_consumer;\nuse "../src/span/span.npk".*;\nfunc:main = int32(cstring[]:_~argv) {\n    if ((raw zz_wide(3i64)) != 9i64) { exit 10i32; }\n    if ((raw zz_uwide(3i64)) != 9i64) { exit 11i32; }\n    exit 0i32;\n};\n%s\n' "$FS" > "$P/d1/tests/d1_consumer.npk"
legs "$P/d1/tests" d1_consumer; rm -f "$P/d1/tests/d1_consumer"*
echo "D1, an int256 and a uint128 intermediate in span, every live check as HEAD holds them"
echo "(but check_denominators, which needs the runner's two manifest counts and moves no tag here):"
python3 -B - "$P/d1" <<'PY'
import os, sys
sys.path.insert(0, os.path.join(sys.argv[1], "harness"))
import checks
for fn in checks.LIVE:
    if fn.__name__ == "check_denominators":
        continue
    r = fn(sys.argv[1])
    print("  %s: %d finding(s)" % (r.name, len(r.problems)))
PY
fresh d1i
append d1i/src/span/span.npk $'\npub func:zz_wide = int64(int64:a) never fails {\n    int128:w = (a => int128) * (a => int128);\n    pass w =>! int64;\n};'
echo "D1, the same function in int128:"; headcheck check_int128_sites d1i | head -2

# ---- §1.5 the narrowings and the wrapping operators in src/
python3 -B - "$REPO" <<'PY'
import os, re, sys
sys.path.insert(0, os.path.join(sys.argv[1], "harness"))
import checks, lexical
n, wrap = 0, 0
for rel in checks.src_files(sys.argv[1]):
    t = lexical.read(os.path.join(sys.argv[1], rel)); code = checks.blank_code(t)
    lines = t.split("\n")
    for m in re.finditer(r"=>!", code):
        n += 1
        print("  =>! %s:%d %s" % (rel, checks._line(code, m.start()), lines[checks._line(code, m.start()) - 1].strip()[:72]))
    wrap += len(re.findall(r"[+\-*]%", code))
print("=>! in src/: %d; +%%, -%% or *%% in src/: %d" % (n, wrap))
PY
