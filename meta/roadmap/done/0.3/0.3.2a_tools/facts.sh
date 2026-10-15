# meta/roadmap/0.3/0.3.2a_tools/facts.sh -- `0.3.2a.md` §1: re-derive what this plan rests on, at both pins, in
# scratch copies of the tree, never in it. Sourced after `env.sh`, in one Bash call -- block 0b of the plan, run
# BEFORE step 1:
#
#     . "$REPO/meta/roadmap/0.3/0.3.2a_tools/env.sh"; . "$T/facts.sh"
#
# `head` is the working tree as it stands; `s1` is it with step 1 applied and `s2` with steps 1 and 2, each by GNU
# `patch` into the copy alone (`git apply` run inside this checkout would resolve the paths against the checkout),
# dated as `apply.py` dates them. Programs live in `$F/p`, outside every copy, but for the two that import the
# library, which sit in a copy's `tests/`; each is built and run at the pin it is asked of, under that pin's LLVM
# (`leg`). A check is asked of its OWN tree's harness. The unchanged tree's two censuses are kept as
# `$A/head_old.tsv` and `$A/head_new.tsv` for blocks 1 and 2; everything else here is removed at the end.
: "${REPO:?}" "${A:?}" "${T:?}" "${PIN:?}" "${OLD:?}" "${NTIME_RUN_DATE:?}"
F=$A/facts
fresh() {   # fresh <name> [<step>...]: the working tree as it stands at $F/<name>, then each step's patch
  local d=$1 n; shift
  mkdir -p "$F/$d"
  ( cd "$REPO" && git ls-files -co --exclude-standard -z | xargs -0 tar -cf - ) | tar -xf - -C "$F/$d"
  for n in "$@"; do
    sed "s/@@DATE032A@@/$NTIME_RUN_DATE/g" "$T/step$n.patch" | patch -p1 -s --no-backup-if-mismatch -d "$F/$d" \
      || echo "STOP: step$n does not apply to a copy of the tree"
  done
}
legs() {    # legs <pin> <src> <label>: build at <pin> under its LLVM, run at -O0 and through `opt -O2`, and print
            # `<label>: <exit> at -O0, <exit> after opt -O2` -- or the refusal's codes
  local pin=$1 src=$2 l=$3 o
  o="$F/bin/$pin.$(basename "$src" .npk)"; mkdir -p "$F/bin"
  ( leg "$pin"
    if ! ( cd "$(dirname "$src")" && "$NPKC" "$(basename "$src")" -o "$o.ll" ) > "$o.err" 2>&1; then
      echo "$l: npkc refused -- $(grep -oE '^NITPICK-[A-Z]+-[0-9]+ [^ ]+' "$o.err" | sed -E 's| ([^ ]*/)?([^/ ]+:[0-9]+:[0-9]+):$| \2|' \
        | tr '\n' ' ' | sed 's/ $//')"; exit 0
    fi
    llc -O0 -filetype=obj -relocation-model=static "$o.ll" -o "$o.o" && ld.lld -static "$o.o" "$NPKRT" -o "$o.x0" \
      && opt -O2 -S "$o.ll" -o "$o.2.ll" && llc -O2 -filetype=obj -relocation-model=static "$o.2.ll" -o "$o.2.o" \
      && ld.lld -static "$o.2.o" "$NPKRT" -o "$o.x2"
    "$o.x0" > /dev/null 2>&1; e0=$?; "$o.x2" > /dev/null 2>&1; e2=$?
    echo "$l: $e0 at -O0, $e2 after opt -O2" )
}
FAILSAFE='func:failsafe = int32(Error:e) {
    pick (e) {
        (DivByZero)         { exit 97i32; },
        (DivOverflow)       { exit 98i32; },
        (HeapBadRequest)    { exit 91i32; },
        (HeapOom)           { exit 92i32; },
        (IntOverflow)       { exit 93i32; },
        (OutOfBounds)       { exit 94i32; },
        (Unreachable)       { exit 95i32; },
        (WildLeak)          { exit 96i32; },
        (StackExhausted)    { exit 106i32; },
        (MachineFault)      { exit 107i32; },
        (DecreasesViolated) { exit 108i32; },
        (LimitViolated)     { exit 109i32; },
        (*)                 { exit 99i32; }
    }
    exit 9i32;
};'
probe() {   # probe <dir> <name> <body of main>, and any declarations before it on stdin: a program in <dir>
  { printf 'mod:%s;\n\n' "$2"; cat; printf 'func:main = int32(cstring[]:_~argv) {\n%s\n};\n\n%s\n' "$3" "$FAILSAFE"; } > "$1/$2.npk"
}

rm -rf "${F:?}"; mkdir -p "$F/p"
fresh head; fresh s1 1; fresh s2 1 2

# ---- §1.2 the unchanged tree at the new pin: one self-check case's own run, the manifest as it stands; then the
# manifest's LLVM row moved -- the full run, where the self-check's trees take the row, and the same past the self-check
( leg $PIN; cd "$F/head" && python3 -B - "$F/sc" <<'PY'
import os, sys
sys.path.insert(0, "harness")
import manifest, selfcheck
where = selfcheck.make_tree(os.path.join(sys.argv[1], "case1"), manifest.load("."),
    [("tests/unit/good_exit.npk", "// expect-exit: 7\n" + selfcheck.TRIVIAL % {"mod": "good_exit", "code": "7"})],
    [("unit", "program", "tests/unit")])
st, out, v = selfcheck.invoke(where)
lines = out.split("\n")
fail = [k for k, l in enumerate(lines) if l.startswith("  FAIL  ")]
print("§1.2 self-check case 1's tree at %s, the manifest as it stands: its run exits %d with %d verdict(s), at `%s`"
      % (os.environ["PIN"], st, len(v), lines[fail[0]].strip() if fail else "no FAIL line"))
if fail:
    print("  " + lines[fail[0] + 2].strip()[:120])
PY
)
rm -rf "${F:?}/sc"
cp -r "$F/head" "$F/llvm"; sed -i 's/^llvm          = "20.1.2"$/llvm          = "20.1.8"/' "$F/llvm/nitpick.toml"
( leg $PIN; cd "$F/llvm" && python3 -B harness/run.py ) > "$A/llvm_full.log" 2>&1
echo "§1.2 the manifest's row at 20.1.8, the full run at $PIN: exit $?"
grep -E '^  FAIL  self-check|^RED -- |^  ok    the reader' "$A/llvm_full.log" | cut -c1-140 | sed 's/^/  /'
echo "§1.2 the self-check's scratch manifest takes its llvm row from the tree's: $(grep -c '"llvm": tc\["llvm"\]' "$F/llvm/harness/selfcheck.py") line of harness/selfcheck.py, \`\"llvm\": tc[\"llvm\"]\`; lines naming a release there: $(grep -c '20\.1\.[0-9]' "$F/llvm/harness/selfcheck.py")"
( leg $PIN; cd "$F/llvm" && python3 -B harness/run.py --root "$F/llvm" ) > "$A/llvm_inner.log" 2>&1
echo "§1.2 the same, as an inner run (\`--root\`, the self-check skipped): exit $?"
python3 - "$A/llvm_inner.log" <<'PY'
import re, sys
lines = open(sys.argv[1], errors="replace").read().split("\n")
stage, fails = None, []
for i, l in enumerate(lines):
    m = re.match(r"^\[(\d)/9\]", l)
    if m:
        stage = m.group(1)
    if l.startswith("  FAIL  "):
        detail = []
        for x in lines[i + 1:]:
            if not x.startswith("        "):
                break
            detail.append(x)
        fails.append((stage, l[8:].strip(), "\n".join(detail)))
by = {}
for s, n, d in fails:
    by[s] = by.get(s, 0) + 1
reader = [n for s, n, d in fails if "found `fixed uint8[]`" in d]
rest = [n for s, n, d in fails if "found `fixed uint8[]`" not in d]
print("  " + [l for l in lines if l.startswith("RED -- ") or l.startswith("GREEN -- ")][0].split(" in ")[0].split(";")[0])
print("  %d failure(s): %s" % (len(fails), ", ".join("[%s/9] %d" % kv for kv in sorted(by.items()))))
print("  %d of them a reader of a string's bytes: NITPICK-TYPE-007, expected `uint8[]`, found `fixed uint8[]`" % len(reader))
print("  the other %d: %s" % (len(rest), ", ".join(n.split("/")[-1] for n in rest)))
PY

# ---- §1.3 landing 103's readers, enumerated: every file as a root at both pins -- the checkout itself, as it stands
echo "§1.3 the unchanged tree, every .npk a root:"
census $OLD "$REPO" head_old | sed 's/^/  /'
census $PIN "$REPO" head_new | sed 's/^/  /'
python3 -B "$T/census.py" sites "$A/head_new.tsv" NITPICK-TYPE-007 | sed 's/^/  /'
echo "§1.3 each file at $OLD against $PIN, NITPICK-TYPE-007 left out of the second:"
python3 -B "$T/census.py" compare "$A/head_old.tsv" "$A/head_new.tsv" NITPICK-TYPE-007 | sed 's/^/  /' | cut -c1-150

# ---- §1.4 the spellings, and the statement form, asked of both compilers
probe "$F/p" p_local '    string:v = "abc";
    fixed uint8[]:bs = string_bytes(v);
    exit (bs.len =>! int32);' < /dev/null
probe "$F/p" p_param '    string:v = "abcd";
    exit ((raw count(string_bytes(v))) =>! int32);' <<'NPK'
func:count = int64(fixed uint8[]:src) never fails {
    pass src.len;
};

NPK
probe "$F/p" p_field '    string:v = "abcde";
    Hold:h = Hold{ view: string_bytes(v), n: 1i64 };
    exit ((h.view.len + h.n) =>! int32);' <<'NPK'
struct:Hold = { fixed uint8[]:view; int64:n; };

NPK
probe "$F/p" p_return '    string:s = string_concat("ab", "");
    fixed uint8[]:v = raw view_of(s);
    exit (v.len =>! int32);' <<'NPK'
func:view_of = fixed uint8[](string:s) never fails {
    pass string_bytes(s);
};

NPK
probe "$F/p" p_return_plain '    string:s = string_concat("ab", "");
    uint8[]:v = raw view_of(s);
    exit (v.len =>! int32);' <<'NPK'
func:view_of = fixed uint8[](string:s) never fails {
    pass string_bytes(s);
};

NPK
probe "$F/p" p_stmt '    Result<int64>:r = take(4i64);
    if (r.is_error) { #unreachable(); }
    exit (r.value =>! int32);' <<'NPK'
error:ETake;

func:take = int64(int64:k) {
    if (k > 9i64) { fail ETake; }
    pass k;
};

NPK
sed -i 's/^        (DivByZero) /        (ETake)             { exit 80i32; },\n        (DivByZero) /' "$F/p/p_stmt.npk"
sed 's/^mod:p_stmt;/mod:p_qmark;/; s/^    Result<int64>:r = take(4i64);$/    int64:k = take(4i64) ?| #unreachable();/; /^    if (r.is_error) { #unreachable(); }$/d; s/^    exit (r.value =>! int32);$/    exit (k =>! int32);/' \
  "$F/p/p_stmt.npk" > "$F/p/p_qmark.npk"
for pr in "p_local:a fixed local of a string's bytes (3)" "p_param:a fixed parameter handed one (4)" \
    "p_field:a fixed field a literal fills (6)" "p_return:a fixed view returned (2)" \
    "p_return_plain:that return bound into a plain local" \
    "p_stmt:the statement form of #unreachable() before r.value (4)" "p_qmark:r ?| #unreachable() (4)"; do
  for p in $OLD $PIN; do legs $p "$F/p/${pr%%:*}.npk" "§1.4 ${pr#*:} at $p"; done
done
mkdir -p "$F/s1/tests/zz"
probe "$F/s1/tests/zz" zz_view_write '    Bytes:b = raw bytes_init(4i64);
    drop bytes_push(@b, 97u8);
    uint8[]:v = raw bytes_view(@b);
    v[0i64] = 65u8;
    uint8[]:w = raw bytes_view(@b);
    exit (w[0i64] =>! int32);' <<'NPK'
use "../../src/core/bytes.npk".*;

NPK
for p in $OLD $PIN; do legs $p "$F/s1/tests/zz/zz_view_write.npk" "§1.4 a write through bytes_view's answer, read back from the sink (65) at $p"; done
probe "$F/s1/tests/zz" zz_civil_time '    CivilTime:t = CivilTime{ hour: 24u8, minute: 0u8, second: 0u8, nanos: 0u32 };
    exit 0i32;' <<'NPK'
use "../../src/cal/cal.npk".*;

NPK
for p in $OLD $PIN; do codes $p "$F/s1/tests/zz/zz_civil_time.npk" | sed 's/^/§1.4 a consumer'"'"'s CivilTime literal, four sealed fields: /'; done
rm -rf "${F:?}/s1/tests/zz"

# ---- §1.5 the re-spelling's extent, and the slots it leaves plain
python3 - "$F/head" "$F/s1" "$F/s2" "$REPO" <<'PY'
import os, re, subprocess, sys
head, s1, s2 = sys.argv[1:4]
fs = [f for f in subprocess.run(["git", "-C", sys.argv[4], "ls-files", "*.npk"], capture_output=True,
                                text=True).stdout.split() if f.split("/")[0] in ("src", "tests")]
def code(l):
    return "" if l.lstrip().startswith("//") else l.split("//", 1)[0]
def count(t, pat):
    n, files = 0, 0
    for f in fs:
        k = sum(len(re.findall(pat, code(l))) for l in open(os.path.join(t, f), encoding="utf-8").read().split("\n"))
        n += k; files += bool(k)
    return n, files
FIXED, PLAIN = r"fixed uint8\[\]", r"(?<!fixed )\buint8\[\]"
for t, lab in ((s1, "step 1"), (s2, "steps 1 and 2")):
    n, k = count(t, FIXED)
    print("§1.5 after %s: %d slot(s) `fixed uint8[]` in %d file(s)" % (lab, n, k))
for t, lab in ((head, "as it stands"), (s1, "after step 1"), (s2, "after step 2")):
    n, k = count(t, PLAIN)
    print("§1.5 plain `uint8[]` slot(s) on code lines, %s: %d in %d file(s)" % (lab, n, k))
for f in fs:
    lines = open(os.path.join(s2, f), encoding="utf-8").read().split("\n")
    for i, l in enumerate(lines):
        c = code(l)
        for m in re.finditer(PLAIN, c):
            ret = re.search(r"func:(\w+)\s*=\s*$", c[:m.start()])
            name = re.match(r":(\w+)", c[m.end():])
            if ret:
                print("  %s:%d %s's result -- a view of a Bytes' body" % (f, i + 1, ret.group(1)))
                continue
            nm = name.group(1)
            body = "\n".join(code(x) for x in lines[i + 1:])
            wrote = re.search(r"(?<![\w.])%s\[[^]]*\]\s*=[^=]" % re.escape(nm), body)
            src = "string_bytes" if "string_bytes" in c else ("bytes_view" if "bytes_view" in c else "#wild_slice")
            print("  %s:%d %s -- %s, %s" % (f, i + 1, nm, src, "written through" if wrote else "read only"))
PY

# ---- §1.6 the runner's own judge of every refusal, the unchanged tree, at both pins
echo "§1.6 every refusal judged by the unchanged tree's own stages.refusal:"
refusals "$REPO" $OLD $PIN | sed 's/^/  /' | cut -c1-170

# ---- §1.7 the compiler's lexer, re-read (TM-202)
echo "§1.7 the files the re-read names, $OLD to $PIN:"
git -C "$NPK_TREE" diff --stat $OLD $PIN -- src/frontend/lexer.npk src/frontend/escapes.npk src/frontend/parse_decl.npk \
  meta/specs/LEXICAL_REFERENCE.md src/frontend/numeric.npk src/frontend/num_width.npk | sed 's/^/ /'
for fn in parse_decl.npk:p_parse_import numeric.npk:num_scan num_width.npk:num_width_of; do for p in $OLD $PIN; do
  echo "§1.7 ${fn#*:} at $p: $(git -C "$NPK_TREE" show $p:src/frontend/${fn%%:*} | awk "/^(pub )?func:${fn#*:} /,/^};/" | sha256sum | cut -c1-16)"
done; done
printf 'mod:p_tail;\n\nfunc:main = int32(cstring[]:_~argv) {\n    flt64:x = 1.5e+r"a";\n    exit 0i32;\n};\n\n%s\n' "$FAILSAFE" > "$F/p/p_tail.npk"
codes $OLD "$F/p/p_tail.npk" | sed 's/^/§1.7 `1.5e+r"a"`: /'; codes $PIN "$F/p/p_tail.npk" | sed 's/^/§1.7 `1.5e+r"a"`: /'
python3 - "$F/p/p_tail.npk" "$REPO/harness" <<'PY'
import sys
sys.path.insert(0, sys.argv[2])
import lexical
t = lexical.read(sys.argv[1])
print("§1.7 `1.5e+r\"a\"` as harness/lexical.py reads it: " + ", ".join("%s %s" % (k, t[s:e]) for k, s, e in lexical.spans(t) if k != "comment"))
PY

# ---- §1.8 the cycle README's adoption list: the int128 arithmetic, D-341, and the builtins and prelude
mkdir -p "$F/ir"
for p in $OLD $PIN; do
  ( leg $p; cd "$F/s1/src" && "$NPKC" lib.npk -o "$F/ir/lib.$p.ll" \
    && llc -O0 -filetype=obj -relocation-model=static "$F/ir/lib.$p.ll" -o "$F/ir/lib.$p.0.o" \
    && opt -O2 -S "$F/ir/lib.$p.ll" -o "$F/ir/lib.$p.2.ll" \
    && llc -O2 -filetype=obj -relocation-model=static "$F/ir/lib.$p.2.ll" -o "$F/ir/lib.$p.2.o"
    echo "§1.8 at $p, the umbrella after step 1 declares $(grep -oE 'declare [^@]*@llvm\.s(mul|sub)\.with\.overflow\.i128' "$F/ir/lib.$p.ll" | grep -oE 'llvm\.s(mul|sub)[a-z.]*i128' | sort | tr '\n' ' ')"
    for o in 0 2; do
      echo "§1.8 at $p, its object at -O$o: $(llvm-nm -u "$F/ir/lib.$p.$o.o" | wc -l) undefined symbol(s), $(llvm-nm -u "$F/ir/lib.$p.$o.o" | awk '{print $NF}' | grep -vcE '^(npk_[a-z0-9_]+|__morestack)$') of them not the runtime's"
    done )
done
echo "§1.8 D-341 at $PIN: $(git -C "$NPK_TREE" show $PIN:meta/roadmap/OPEN_DECISIONS.md | grep -oE "\`buffer\`'s indexing is a plan \(D-341\)" | head -1)"
echo "§1.8 src/'s #wild_slice sites on code lines: $(git -C "$REPO" grep -h '#wild_slice' -- 'src/*.npk' | grep -vcE '^\s*//')"
for p in $OLD $PIN; do
  git -C "$NPK_TREE" show $p:src/frontend/builtins.npk | awk '/func:is_builtin_name /,/^};/' | grep -oE '"[a-z_0-9]+"' | sort -u > "$F/bi.$p"
  git -C "$NPK_TREE" show $p:src/prelude/prelude.npk | grep -oE '^pub (async )?func:[A-Za-z_0-9]+' | sort -u > "$F/pre.$p"
done
echo "§1.8 the builtin table's names: $(wc -l < "$F/bi.$OLD") at $OLD, $(wc -l < "$F/bi.$PIN") at $PIN, $(comm -3 "$F/bi.$OLD" "$F/bi.$PIN" | wc -l) differing"
echo "§1.8 the prelude's public functions: $(wc -l < "$F/pre.$OLD") at $OLD, $(wc -l < "$F/pre.$PIN") at $PIN, $(comm -3 "$F/pre.$OLD" "$F/pre.$PIN" | wc -l) differing"
echo "§1.8 the builtin rows that moved: $(git -C "$NPK_TREE" diff $OLD $PIN -- src/frontend/builtins.npk | grep -E '^\+ ' | sed 's/^+ *//')"

# ---- §1.9 the readings of npkc's output, over step 1's tree, which both compilers build
emissions "$F/s1" $OLD $PIN | sed 's/^/§1.9 /' | cut -c1-170

# ---- §1.10 CI's rows
echo "§1.10 $PIN is $(git -C "$NPK_TREE" rev-parse $PIN); its emission row: $(grep -m1 ' npkc.ll ' "$WB/.internal/toolchain/$PIN/PIN.md" | awk '{print $2, $3}')"
echo "§1.10 the workbench's digests: $(cut -c1-16 "$WB/.internal/toolchain/$PIN/SHA256SUMS" | tr '\n' ' ')"
git -C "$NPK_TREE" diff --quiet $OLD $PIN -- bootstrap/harness/quickemit.py && echo "§1.10 bootstrap/harness/quickemit.py: the same at both pins"
git -C "$NPK_TREE" cat-file -e $PIN:npkg/main.npk && echo "§1.10 npkg/main.npk: present at $PIN"

# ---- §1.11 the allocator's guard past a buffer of 4 095 bytes: a verdict, not a rate
for g in "4095:97u8" "4096:plus"; do
  off=${g%%:*}; how=${g#*:}
  if [ "$how" = plus ]; then
    w="    uint8:gb = <-(#ptr_add<uint8>(a.ptr, ${off}i64));
    (<-(#ptr_add<uint8>(a.ptr, ${off}i64))) = gb +% 1u8;"
  else
    w="    (<-(#ptr_add<uint8>(a.ptr, ${off}i64))) = $how;"
  fi
  { printf 'mod:g_%s;\n\nfunc:touch = int64() {\n    buffer:a = buffer_new(4095i64);\n%s\n    pass 1i64;\n};\n\n' "$off" "$w"
    printf 'func:main = int32(cstring[]:_~argv) {\n    int64:k = touch() ?| 0i64;\n    exit 0i32;\n};\n\n%s\n' "$FAILSAFE"; } > "$F/p/g_$off.npk"
done
for p in $OLD $PIN; do
  legs $p "$F/p/g_4095.npk" "§1.11 at $p, 97 written at offset 4095 of a 4 095-byte buffer, into the rounding"
  legs $p "$F/p/g_4096.npk" "§1.11 at $p, the guard's own byte at offset 4096 written back plus one"
done

# ---- §1.12 BUILD.md §7's reserved locals, dated at the old pin, asked again
for n in uid gid pid tid fd thread cfg arena; do
  printf 'mod:sh_%s;\n\nfunc:main = int32(cstring[]:_~argv) {\n    int64:%s = 1i64;\n    exit 0i32;\n};\n\n%s\n' "$n" "$n" "$FAILSAFE" > "$F/p/sh_$n.npk"
done
for p in $OLD $PIN; do
  echo "§1.12 at $p: $(for n in uid gid pid tid fd thread cfg arena; do codes $p "$F/p/sh_$n.npk"; done | grep -oE 'NITPICK-[A-Z]+-[0-9]+ [0-9]+:[0-9]+' | sort | uniq -c | sed 's/^ *//' | tr '\n' ' ')"
done

# ---- §1.13 what the patches add
python3 - "$T" "$REPO" <<'PY'
import os, re, sys
T, R = sys.argv[1], sys.argv[2]
added, touched, cites1 = [], set(), 0
for n in (1, 2, 3, 4):
    f = None
    for l in open(os.path.join(T, "step%d.patch" % n), encoding="utf-8"):
        if l.startswith("+++ b/"):
            f = l[6:].strip(); touched.add(f)
        elif l.startswith("+") and not l.startswith("+++") and f:
            if n == 1 and "TM-259" in l:
                cites1 += 1
            if f.endswith(".npk"):
                added.append(l[1:])
def blank(l):
    l = re.sub(r'"([^"\\]|\\.)*"', '""', l)
    return l.split("//", 1)[0]
code = [blank(l) for l in added]
pats = [("comptime", r"\bcomptime\b"), ("a macro", r"\bmacro\b|#\[macro"), ("a float literal", r"\b\d+\.\d"),
        ("an enum", r"\benum:"), ("a generic declaration", r"func:\w+\s*<|struct:\w+\s*<"),
        ("an explicit variant value", r"^\s*\w+\s*=\s*-?\d+\s*,?\s*$"), ("`?|` or `#unreachable`", r"\?\||#unreachable"),
        ("`#wild_slice`", r"#wild_slice"), ("a write through a slice", r"\w\[[^]]*\]\s*=[^=]"),
        ("an assignment to a parameter", r"^\s*(src|needle|lit|view)\s*=[^=]")]
print("§1.13 the patches' %d added `.npk` lines, comments and strings blanked:" % len(added))
print("  " + "; ".join("%s %d" % (n, sum(1 for c in code if re.search(p, c))) for n, p in pats))
held = [f for f in sorted(touched) if os.path.exists(os.path.join(R, f)) and "@@DATE032A@@" in open(os.path.join(R, f), encoding="utf-8").read()]
print("§1.13 the %d file(s) the patches touch that hold `@@DATE032A@@` as the tree stands: %s" % (len(touched), ", ".join(held) or "none"))
print("§1.13 step 1's added lines citing the decision step 2 declares: %d" % cites1)
PY

rm -rf "${F:?}"
