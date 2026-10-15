# meta/roadmap/0.3/0.3.1_tools/facts.sh -- `0.3.1.md` §1.11: re-derive §1 at the pin, in
# scratch copies of the tree, never in it. Sourced after `env.sh`, in one Bash call --
# block 0b of the plan, run BEFORE step 1:
#
#     . "$REPO/meta/roadmap/0.3/0.3.1_tools/env.sh"; . "$T/facts.sh"
#
# It copies the working tree into `$W/facts` -- `head`, as it stands; `one`, step 1's
# patch applied; `two`, steps 1 and 2's -- and a copy of `head` per plant. Each patch is
# applied by GNU `patch` to the copy alone: `git apply` run inside this checkout would
# resolve the paths against the checkout, not the copy. Each check is asked of a copy's
# OWN harness -- a check reads its exemptions only over its own tree (`checks.REPO`).
# Then it asks the pinned compiler, at -O0 and after `opt -O2` where a program runs, and
# the checks what §1 says: the language at the pin (§1.2), what `src/` calls (§1.3),
# the plants a list of names passes (§1.4), the emission (§1.5), the shapes no name
# reads (§1.6), O-X11's counter-example (§1.7), `HostClock` (§1.8) and a generic's
# instances (§1.9).
: "${REPO:?}" "${NPKC:?}" "${NPKRT:?}" "${W:?}" "${T:?}" "${NTIME_RUN_DATE:?}"
P=$W/facts; rm -rf "${P:?}"; mkdir -p "$P"
fresh() {   # fresh <name> [<step>...]: the working tree as it stands at $P/<name>, then each step
  local d=$1 n; shift
  rm -rf "${P:?}/$d"; mkdir -p "$P/$d"
  ( cd "$REPO" && git ls-files -co --exclude-standard -z | xargs -0 tar -cf - ) | tar -xf - -C "$P/$d"
  for n in "$@"; do
    sed "s/@@DATE@@/$NTIME_RUN_DATE/g" "$T/step$n.patch" | patch -p1 -s --no-backup-if-mismatch -d "$P/$d" \
      || echo "STOP: step$n does not apply to a copy of the tree"
  done
}
plant() {   # plant <copy> <file-rel> <text>: a copy of `head` with <text> appended to <file-rel>
  rm -rf "${P:?}/$1"; cp -r "$P/head" "$P/$1"; printf '%s\n' "$3" >> "$P/$1/$2"
}
FLOOR='        (HeapBadRequest)    { exit 91i32; },
        (HeapOom)           { exit 92i32; },
        (IntOverflow)       { exit 93i32; },
        (OutOfBounds)       { exit 94i32; },
        (Unreachable)       { exit 95i32; },
        (WildLeak)          { exit 96i32; },
        (StackExhausted)    { exit 106i32; },
        (MachineFault)      { exit 107i32; },'
fs() {      # a `failsafe` naming the floor and the arithmetic, then `(*)`
  printf 'func:failsafe = int32(Error:e) {\n    pick (e) {\n%s\n' "$FLOOR"
  printf '        (*)                 { exit 99i32; }\n    }\n    exit 9i32;\n};\n'
}
legs() {    # legs <src> <label>: build at both legs and run once each, or name the refusal
  local src=$1 l=$2 o
  o="$P/bin/$(basename "$src" .npk)"; mkdir -p "$P/bin"
  if ! ( cd "$(dirname "$src")" && "$NPKC" "$(basename "$src")" -o "$o.ll" ) > "$o.err" 2>&1; then
    echo "$l: npkc refused -- $(grep -oE '^NITPICK-[A-Z]+-[0-9]+' "$o.err" | tr '\n' ' ' | sed 's/ $//')"; return
  fi
  llc -O0 -filetype=obj -relocation-model=static "$o.ll" -o "$o.o" && ld.lld -static "$o.o" "$NPKRT" -o "$o.x0" \
    && opt -O2 -S "$o.ll" -o "$o.2.ll" && llc -O2 -filetype=obj -relocation-model=static "$o.2.ll" -o "$o.2.o" \
    && ld.lld -static "$o.2.o" "$NPKRT" -o "$o.x2"
  local e0 e2; "$o.x0" > /dev/null 2>&1; e0=$?; "$o.x2" > /dev/null 2>&1; e2=$?
  echo "$l: $e0 at -O0, $e2 after opt -O2"
}
first() {   # first <check-output>: a check's count, and its first finding cut at 100
  head -2 | sed -E '1s/^[a-z_0-9]+: ([0-9]+ finding\(s\)).*/\1/; 2s/^  //' | cut -c1-100 | tr '\n' ' ' \
    | sed -E 's/ $//; s/\) /) -- /'
}
fresh head; fresh one 1; fresh two 1 2

# ---- §1.2 the language at the pin: the builtins the resolver admits, and the prelude's reach
B=$(git -C "$NPK_TREE" show "$PIN:src/frontend/builtins.npk")
echo "$B" | sed -n '/^pub func:is_builtin_name/,/^};/p' | grep -oE 'string_eq\(name, "[a-z_0-9]+"\)' \
  | sed -E 's/.*"([a-z_0-9]+)".*/\1/' > "$P/builtins.txt"
echo "§1.2 bare-name builtins at the pin: $(wc -l < "$P/builtins.txt")"
echo "§1.2 of them pure, by the compiler's own column: $(echo "$B" | sed -n '/^pub func:builtin_pure/,/^};/p' \
  | grep -oE '"[a-z_0-9]+"' | tr -d '"' | tr '\n' ' ' | sed 's/ $//')"
git -C "$NPK_TREE" show "$PIN:src/prelude/prelude.npk" > "$P/prelude.npk"
echo "§1.2 the prelude's std_dup: $(grep -oE 'relay sys\(72i64, [^;]*;' "$P/prelude.npk")"
for f in std_in std_out std_err byte_reader_open byte_writer_create sleep io_ready io_ready2; do
  awk -v f="$f" 'index($0, "pub func:" f " ") == 1 || index($0, "pub async func:" f " ") == 1 {p = 1}
    p && /relay std_dup\(|relay open\(|suspend_until\(|suspend_io\(/ {sub(/^ +/, ""); print f ": " $0; exit}
    p && /^};/ {p = 0}' "$P/prelude.npk" | cut -c1-90 | sed 's/^/§1.2 the prelude: /'
done

# ---- §1.3 what `src/` calls, read by the harness's own reader: the builtins, by side
python3 -B - "$P/head" "$P/builtins.txt" <<'PY'
import os, re, sys
tree = sys.argv[1]
sys.path.insert(0, os.path.join(tree, "harness"))
import checks, lexical
names = open(sys.argv[2]).read().split()
call = re.compile(r"(?<![A-Za-z0-9_.])(%s)[ \t\r\n]*\(" % "|".join(sorted(names, key=len, reverse=True)))
side = {"outside src/host/": set(), "in src/host/": set()}
for rel in checks.src_files(tree):
    code = checks.blank_code(lexical.read(os.path.join(tree, rel)))
    k = "in src/host/" if rel.startswith("src/host/") else "outside src/host/"
    side[k] |= set(call.findall(code))
for k in ("outside src/host/", "in src/host/"):
    print("§1.3 builtins called %s: %s" % (k, ", ".join(sorted(side[k]))))
PY

# ---- §1.4 the plants a list of names passes -- each in `cal`, compiled in the umbrella,
# asked of HEAD's `check_purity` and of step 1's `check_call_edges` over its emission
for spec in "hw|int64() never fails { pass hardware_concurrency(); }" \
            "stdin|int64() { string:s = relay read_stdin(); pass 0i64; }" \
            "chain|int32() never fails { pass chain_depth(); }" \
            "live|int64() never fails { pass wild_live_count(); }" \
            "arena|int64() never fails { arena<int64>:a = arena_make(2i64); pass 0i64; }" \
            "exists|bool() { cstring:c = relay to_cstring(\"/etc\"); pass path_exists(c); }" \
            "stdout|int64() { discard(relay std_out()); pass 0i64; }" \
            "mono|int64() never fails { pass mono_now(); }"; do
  n=${spec%%|*}; body=${spec#*|}
  plant "p_$n" src/cal/cal.npk "pub func:p_x = $body;"
  out=$( (cd "$P/p_$n/src" && "$NPKC" lib.npk -o /dev/null) 2>&1 | grep -oE '^NITPICK-[A-Z]+-[0-9]+' | head -1)
  emit "$P/p_$n"
  pur=$(check check_purity "$P/p_$n" | first)
  edg=$(check check_call_edges "$P/p_$n" "$P/one" | sed -n 's/^  `npk\.cal\.p_x` reaches `\([^`]*\)`.*/\1/p' | sort | tr '\n' ' ' | sed 's/ $//')
  echo "§1.4 $n: ${out:-compiles}; HEAD's check_purity $pur; step 1's check_call_edges: ${edg:-nothing outside the allowlist}"
done
plant p_reopen src/cal/cal.npk "func:reopen = int64() never fails { pass 7i64; };
pub func:p_x = int64() never fails { pass raw reopen(); };"
emit "$P/p_reopen"
echo "§1.4 reopen, a pure function: HEAD's check_purity $(check check_purity "$P/p_reopen" | first)"
echo "§1.4 reopen, a pure function: step 1's check_call_edges $(check check_call_edges "$P/p_reopen" "$P/one" | first)"

# ---- §1.5 the emission at the pin -- the umbrella, as step 7 writes it -- read by step 1's checks
emit "$P/head"
python3 -B - "$P/one" "$P/head/build/ntime.ll" <<'PY'
import os, re, sys
sys.path.insert(0, os.path.join(sys.argv[1], "harness"))
import checks
d, decl, g = checks.read_emission(sys.argv[2])
print("§1.5 the emission: %d define(s), %d declare(s), %d global(s)" % (len(d), len(decl), len(g)))
mods = sorted({checks._ir_module(n) for n in d if checks._ir_module(n)})
print("§1.5 its npk.<module> prefixes: %s" % ", ".join(mods))
print("§1.5 calls through a value: %d; inline assembly: %d"
      % (sum(1 for b in d.values() if checks._IR_INDIRECT.search(b)),
         sum(1 for b in d.values() if checks._IR_ASM.search(b))))
PY
check check_call_edges "$P/head" "$P/one" | sed 's/^/§1.5 /' | cut -c1-260
check check_wide_types "$P/head" "$P/one" | sed 's/^/§1.5 /' | cut -c1-260
python3 -B - "$P/one" "$P/head" <<'PY'
import os, sys
sys.path.insert(0, os.path.join(sys.argv[1], "harness"))
import checks
d, decl, g = checks.read_emission(os.path.join(sys.argv[2], "build", "ntime.ll"))
mods, host = checks._src_modules(sys.argv[2])
reached = set()
for n in d:
    if checks._ir_module(n) in mods and checks._ir_module(n) not in host:
        s, _src, _odd = checks._reach(n, d, decl, g, mods)
        reached |= set(s)
print("§1.5 reached outside src/host/: %s" % ", ".join(sorted(x for x in reached if not x.startswith("llvm."))))
print("§1.5 and LLVM's: %s" % ", ".join(sorted(x for x in reached if x.startswith("llvm."))))
PY

# ---- §1.6 the shapes no name reads: inline assembly, a builtin as a value, a function as one
{ printf 'mod:asm1;\nfunc:main = int32(cstring[]:_~argv) {\n'
  printf '    Result<int64>:r = asm<int64>("x86_64", "mov $39, %%0", "=r");\n    exit 0i32;\n};\n'; fs; } > "$P/head/tests/asm1.npk"
echo "§1.6 $(codes "$PIN" "$P/head/tests/asm1.npk")"
{ printf 'mod:fv_bound;\nfunc:main = int32(cstring[]:_~argv) {\n'
  printf '    func int64() never fails:f = mono_now;\n    int64:t = raw f();\n'
  printf '    if (t > 0i64) { exit 0i32; }\n    exit 10i32;\n};\n'; fs; } > "$P/head/tests/fv_bound.npk"
echo "§1.6 $(codes "$PIN" "$P/head/tests/fv_bound.npk")"
( cd "$P/head/tests" && "$NPKC" fv_bound.npk -o /dev/null 2>&1 ) | grep -oE 'the emitter could not lower this[^;]*; a defect in the compiler' | sed 's/^/§1.6 /'
{ printf 'mod:fv_passed;\nfunc:call_it = int64(func int64() never fails:g) never fails { pass raw g(); };\n'
  printf 'func:main = int32(cstring[]:_~argv) {\n    int64:t = raw call_it(mono_now);\n'
  printf '    if (t > 0i64) { exit 0i32; }\n    exit 10i32;\n};\n'; fs; } > "$P/head/tests/fv_passed.npk"
echo "§1.6 $(codes "$PIN" "$P/head/tests/fv_passed.npk")"
{ printf 'mod:fv_named;\nfunc:seven = int64() never fails { pass 7i64; };\n'
  printf 'func:main = int32(cstring[]:_~argv) {\n    func int64() never fails:f = seven;\n'
  printf '    int64:t = raw f();\n    if (t != 7i64) { exit 10i32; }\n    exit 0i32;\n};\n'; fs; } > "$P/head/tests/fv_named.npk"
legs "$P/head/tests/fv_named.npk" "§1.6 an ordinary function as a value, called"
plant p_value src/cal/cal.npk "func:seven = int64() never fails { pass 7i64; };
pub func:p_x = int64() never fails { func int64() never fails:f = seven; pass raw f(); };"
emit "$P/p_value"
echo "§1.6 the same in cal: HEAD's check_purity $(check check_purity "$P/p_value" | first)"
echo "§1.6 the same in cal: step 1's check_call_edges $(check check_call_edges "$P/p_value" "$P/one" | first)"

# ---- §1.7 O-X11's counter-example, in span, a §5 row marking `wide`
plant p_wide src/span/span.npk 'func:wide = int256() never fails {
    pass 7i256;
};
func:g = int64() never fails {
    pass ((raw wide()) * (raw wide())) =>! int64;
};'
python3 -B - "$P/p_wide/meta/specs/SPAN_MODEL.md" <<'PY'
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
row = "| `bytes_put_int`'s loop measure |"
i = s.index(row); j = s.index("\n", i)
open(p, "w", encoding="utf-8").write(s[:j + 1] + "| `wide` | a test's | the test's | **yes** |\n" + s[j + 1:])
PY
echo "§1.7 the counter-example: $(codes "$PIN" "$P/p_wide/src/span/span.npk")"
emit "$P/p_wide"
echo "§1.7 HEAD's check_int128_sites $(check check_int128_sites "$P/p_wide" | first)"
echo "§1.7 step 1's check_wide_types $(check check_wide_types "$P/p_wide" "$P/one" | first)"
echo "§1.7 npk.span.g's product: $(grep -oE 'call \{ i256, i1 \} @llvm\.smul\.with\.overflow\.i256' "$P/p_wide/build/ntime.ll" | head -1)"

# ---- §1.8 `HostClock` named in `cal`: without an import, and with one, in the umbrella
plant p_clock src/cal/cal.npk 'pub func:p_x = int64(HostClock:c) never fails { pass 0i64; };'
echo "§1.8 HostClock with no import: $(codes "$PIN" "$P/p_clock/src/cal/cal.npk")"
echo "§1.8   HEAD's check_host_isolation $(check check_host_isolation "$P/p_clock" | first)"
rm -rf "${P:?}/p_clock2"; cp -r "$P/head" "$P/p_clock2"
sed -i 's#^use "../core/limits.npk".NTIME_YEAR_MIN;$#&\nuse "../host/host.npk".HostClock;#' "$P/p_clock2/src/cal/cal.npk"
printf 'pub func:p_x = int64(HostClock:c) never fails { pass 0i64; };\n' >> "$P/p_clock2/src/cal/cal.npk"
echo "§1.8 HostClock imported, the umbrella: $(codes "$PIN" "$P/p_clock2/src/lib.npk")"
echo "§1.8 HostClock imported, cal.npk as a root: $(codes "$PIN" "$P/p_clock2/src/cal/cal.npk")"
echo "§1.8   HEAD's check_layering $(check check_layering "$P/p_clock2" | first)"
echo "§1.8   HEAD's check_host_isolation $(check check_host_isolation "$P/p_clock2" | first)"
echo "§1.8   step 2's check_host_isolation $(check check_host_isolation "$P/p_clock2" "$P/two" | first)"
# the root's refusal, alone: two modules in two directories, each importing the other
mkdir -p "$P/cyc/a" "$P/cyc/b"
printf 'mod:a;\nuse "../b/b.npk".g;\npub error:EA;\npub func:f = int64() never fails { pass 1i64; };\n' > "$P/cyc/a/a.npk"
printf 'mod:b;\nuse "../a/a.npk".EA;\nuse "../a/a.npk".f;\npub func:g = int64() {\n    if (raw f() > 5i64) { fail EA; }\n    pass 1i64;\n};\n' > "$P/cyc/b/b.npk"
echo "§1.8 a.npk as a root, importing b, which imports it back from another directory: $(codes "$PIN" "$P/cyc/a/a.npk")"
echo "§1.8   b.npk as the root of the same two: $(codes "$PIN" "$P/cyc/b/b.npk")"

# ---- §1.9 a generic's instances, in a unit's emission
( cd "$P/head/tests/unit" && "$NPKC" vec_boundaries.npk -o "$P/vecb.ll" )
echo "§1.9 vec_boundaries' instances: $(grep -oE '^define [^@]*@"npk\.vec\.[a-z_]+<[a-z0-9]+>"' "$P/vecb.ll" \
  | sed -E 's/.*"npk\.vec\.([^"]+)"/\1/' | sort | tr '\n' ' ' | sed 's/ $//')"
