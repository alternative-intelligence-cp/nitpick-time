# meta/roadmap/0.3/0.3.0_tools/facts.sh -- `0.3.0.md` §1.12: re-derive §1 at the pin, in
# scratch copies of the tree, never in it. Sourced after `env.sh`, in one Bash call --
# block 0b of the plan, run BEFORE step 1:
#
#     . "$REPO/meta/roadmap/0.3/0.3.0_tools/env.sh"; . "$T/facts.sh"
#
# It copies the working tree into `$W/facts`: `head`, as it stands; `one`, with step
# 1's patch, the check that reads a literal's width; `new`, with steps 2 and 3's, the
# clocks' module, the umbrella's five names and the unit; and two plants of a wide
# literal. Each patch is applied by GNU `patch` to the copy alone -- `git apply` run
# inside this checkout would resolve the paths against the checkout, not the copy.
# Then it asks the pinned compiler, at -O0 and after `opt -O2`, and the checks --
# THIS checkout's, which are `HEAD`'s before step 1, or a copy's where it says so --
# what §1 says: the literals alone (§1.2), `clock_getres` (§1.3), the module and the
# drafts refused on its way (§1.5), the live checks before the arrow (§1.6), the bills
# (§1.7), the unit forty times a leg (§1.8), the mutants (§1.9) and the IR (§1.10).
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
FLOOR='        (HeapBadRequest)    { exit 91i32; },
        (HeapOom)           { exit 92i32; },
        (Unreachable)       { exit 95i32; },
        (WildLeak)          { exit 96i32; },
        (StackExhausted)    { exit 106i32; },
        (MachineFault)      { exit 107i32; },'
fs() {      # fs <arm line>...: a `failsafe` naming the floor and the arms given, then `(*)`
  printf 'func:failsafe = int32(Error:e) {\n    pick (e) {\n%s\n' "$FLOOR"
  local a; for a in "$@"; do printf '        %s\n' "$a"; done
  printf '        (*)                 { exit 99i32; }\n    }\n    exit 9i32;\n};\n'
}
ARITH=('(IntOverflow)       { exit 93i32; },' '(OutOfBounds)       { exit 94i32; },'
       '(DivByZero)         { exit 97i32; },' '(DivOverflow)       { exit 98i32; },')
legs() {    # legs <src> <label> [<arg>...]: build at both legs, run once per arg (or once)
  local src=$1 l=$2 o; shift 2
  o="$P/bin/$(basename "$src" .npk)"; mkdir -p "$P/bin"
  if ! ( cd "$(dirname "$src")" && "$NPKC" "$(basename "$src")" -o "$o.ll" ) > "$o.err" 2>&1; then
    echo "$l: npkc refused -- $(grep -oE '^NITPICK-[A-Z]+-[0-9]+' "$o.err" | tr '\n' ' ' | sed 's/ $//')"; return
  fi
  llc -O0 -filetype=obj -relocation-model=static "$o.ll" -o "$o.o" && ld.lld -static "$o.o" "$NPKRT" -o "$o.x0" \
    && opt -O2 -S "$o.ll" -o "$o.2.ll" && llc -O2 -filetype=obj -relocation-model=static "$o.2.ll" -o "$o.2.o" \
    && ld.lld -static "$o.2.o" "$NPKRT" -o "$o.x2"
  local a e0 e2; [ $# -eq 0 ] && set -- ""
  for a in "$@"; do "$o.x0" $a > /dev/null 2>&1; e0=$?; "$o.x2" $a > /dev/null 2>&1; e2=$?
    echo "$l${a:+, case $a}: $e0 at -O0, $e2 after opt -O2"; done
}
fresh head; fresh one 1; fresh new 2 3; fresh lit; fresh typed
# `new`'s checks are HEAD's -- §1.6 asks them about the module before the arrow is
# drawn -- and a check reads its exemptions only over its OWN tree (`checks.REPO`), so
# §1.6 runs the copy's own checks: run over a copy, the checkout's would name
# `bytes_view`, whose S-22 exemption is the checkout's.
cp "$P/head/harness/"*.py "$P/new/harness/"

# ---- §1.2 a literal widens unnamed: three programs in a consumer, then two plants
{ printf 'mod:lit1;\nfunc:main = int32(cstring[]:_~argv) {\n    int64:y = (3i256 * 5i256) =>! int64;\n'
  printf '    if (y != 15i64) { exit 10i32; }\n    int64:z = (10000000000i256 * 10000000000i256) =>! int64;\n'
  printf '    if (z != 7766279631452241920i64) { exit 11i32; }\n    exit 0i32;\n};\n'; fs "${ARITH[0]}"; } > "$P/head/tests/lit1.npk"
{ printf 'mod:lit2;\nfunc:main = int32(cstring[]:argv) {\n    int64:x = argv.len;\n'
  printf '    int64:y = (x * 5i256) =>! int64;\n    exit 0i32;\n};\n'; fs "${ARITH[0]}"; } > "$P/head/tests/lit2.npk"
{ printf 'mod:lit3;\nfunc:main = int32(cstring[]:argv) {\n    int64:x = argv.len;\n'
  printf '    int64:y = ((x => int256) * 5i256) =>! int64;\n    if (y != 5i64) { exit 10i32; }\n    exit 0i32;\n};\n'
  fs "${ARITH[0]}"; } > "$P/head/tests/lit3.npk"
legs "$P/head/tests/lit1.npk" "§1.2 (3i256 * 5i256) =>! int64, and 10^20 held to its low 64 bits"
( cd "$P/head/tests" && "$NPKC" lit2.npk -o /dev/null 2>&1 ) | grep -oE '^NITPICK-[A-Z]+-[0-9]+ [^ ]+ .*' \
  | sed -E 's|^(NITPICK-[A-Z]+-[0-9]+) [^ ]+ |§1.2 (x * 5i256) =>! int64: \1 -- |' | cut -c1-240
legs "$P/head/tests/lit3.npk" "§1.2 ((x => int256) * 5i256) =>! int64"
printf 'func:wide_literal = int64() never fails {\n    pass (3i256 * 5i256) =>! int64;\n};\n' >> "$P/lit/src/span/span.npk"
printf 'func:wide_literal = int64() never fails {\n    pass ((3i64 => int256) * 5i256) =>! int64;\n};\n' >> "$P/typed/src/span/span.npk"
echo "§1.2 the plant, $(codes "$PIN" "$P/lit/src/span/span.npk")"
echo "§1.2 HEAD's check over the plant: $(check check_int128_sites "$P/lit" | head -1)"
echo "§1.2 HEAD's check over the typed plant: $(check check_int128_sites "$P/typed" | head -1)"
echo "§1.2 step 1's check over the tree:"; check check_int128_sites "$P/one" "$P/one"
echo "§1.2 step 1's check over the plant:"; check check_int128_sites "$P/lit" "$P/one" | cut -c1-120
echo "§1.2 step 1's check over the typed plant:"; check check_int128_sites "$P/typed" "$P/one" | cut -c1-120

# ---- §1.3 `clock_getres`, 229: clocks 0, 1 and 7 answer {0 s, 1 ns}; 99 is an errno
{ printf 'mod:res;\nfunc:main = int32(cstring[]:argv) {\n    int64:k = 0i64;\n'
  printf '    if (argv.len > 1i64) { k = (argv[1i64].ptr[0i64] => int64) - 48i64; }\n    int64:id = 0i64;\n'
  printf '    if (k == 1i64) { id = 1i64; }\n    if (k == 2i64) { id = 7i64; }\n    if (k == 3i64) { id = 99i64; }\n'
  printf '    buffer:ts = buffer_new(16i64);\n    Result<int64>:r = sys(229i64, id, ts.ptr);\n'
  printf '    if (r.is_error) { exit 20i32; }\n    if (r.value != 0i64) { exit 21i32; }\n'
  printf '    int64:secs = <-(#ptr_add<int64>(ts.ptr, 0i64));\n    int64:nanos = <-(#ptr_add<int64>(ts.ptr, 1i64));\n'
  printf '    if (secs != 0i64) { exit 22i32; }\n    if (nanos != 1i64) { exit 23i32; }\n    exit 0i32;\n};\n'
  fs "${ARITH[0]}" "${ARITH[1]}"; } > "$P/head/tests/res.npk"
legs "$P/head/tests/res.npk" "§1.3 sys(229, id, ts.ptr): 0 for ids 0, 1, 7 at {0 s, 1 ns}, 20 an errno" 0 1 2 3
echo "§1.3 clock_getres in the compiler's tree at the pin: $(git -C "$NPK_TREE" grep -i -c clock_getres $PIN | wc -l) file(s)"
echo "§1.3 npk_mono_now's call: $(git -C "$NPK_TREE" show $PIN:runtime/npkrt.ll | grep -oE 'call i64 @npk_sys6\(i64 228, i64 1,' | head -1)"

# ---- §1.5 the module, and the drafts refused on its way
echo "§1.5 the module as a root: $(codes "$PIN" "$P/new/src/host/host.npk")"
echo "§1.5 the umbrella: $(codes "$PIN" "$P/new/src/lib.npk")"
cp -r "$P/new" "$P/d1"
swap "$P/d1/src/host/host.npk" "pass raw instant_of(mono_now(), InstantClock.Monotonic);" "pass instant_of(mono_now(), InstantClock.Monotonic);" \
  && echo "§1.5 no raw before a never-fails callee: $(codes "$PIN" "$P/d1/src/host/host.npk")"
for r in "" raw; do
  { printf 'mod:cmpd;\nuse "../src/span/span.npk".*;\nfunc:main = int32(cstring[]:_~argv) {\n'
    printf '    Result<Timestamp>:a = timestamp_of(1i64, 0i64);\n    if (a.is_error) { exit 10i32; }\n'
    printf '    Result<Timestamp>:b = timestamp_of(2i64, 0i64);\n    if (b.is_error) { exit 10i32; }\n'
    printf '    Ordering:o = %s b.value.cmp(a.value);\n    exit 0i32;\n};\n' "$r"
    fs '(cal.ETimeValue)    { exit 80i32; },' "${ARITH[@]}"; } > "$P/new/tests/cmpd.npk"
  echo "§1.5 Timestamp's derived cmp, ${r:-no raw}: $(codes "$PIN" "$P/new/tests/cmpd.npk")"
done
{ printf 'mod:durd;\nuse "../src/host/host.npk".*;\nfunc:main = int32(cstring[]:_~argv) {\n'
  printf '    Result<Duration>:r = host_clock_res(HostClock.Realtime);\n    if (r.is_error) { exit 10i32; }\n'
  printf '    Duration:d = raw duration_ns(r.value);\n    exit 0i32;\n};\n'
  fs '(cal.ETimeValue)    { exit 80i32; },' "${ARITH[@]}"; } > "$P/new/tests/durd.npk"
echo "§1.5 duration_ns(r.value): $(codes "$PIN" "$P/new/tests/durd.npk")"
mkdir -p "$P/new/tests/sysmod"
printf 'mod:sys;\npub fixed int64:SYS_CLOCK_GETTIME = 228i64;\n' > "$P/new/tests/sysmod/sys.npk"
{ printf 'mod:sysroot;\nuse "./sys.npk".SYS_CLOCK_GETTIME;\nfunc:main = int32(cstring[]:_~argv) {\n'
  printf '    buffer:ts = buffer_new(16i64);\n    Result<int64>:r = sys(SYS_CLOCK_GETTIME, 0i64, ts.ptr);\n'
  printf '    if (r.is_error) { exit 10i32; }\n    exit 0i32;\n};\n'; fs "${ARITH[0]}" "${ARITH[1]}"; } > "$P/new/tests/sysmod/sysroot.npk"
legs "$P/new/tests/sysmod/sysroot.npk" "§1.5 mod:sys beside the builtin sys, called with its constant"

# ---- §1.6 the live checks over the copy with the module, HEAD's checks
check check_layering "$P/new" "$P/new" | sed 's/^/§1.6 /' | cut -c1-200
for c in check_error_budget check_purity check_host_isolation check_int128_sites check_constants_named \
         check_raw_index check_no_view_returns check_no_owning_fields check_literal_divisors; do
  check $c "$P/new" "$P/new" | head -1 | sed -E 's/^([a-z_0-9]+: [0-9]+ finding\(s\)).*/§1.6 \1/'
done

# ---- §1.7 the bills
mkdir -p "$P/new/tests/r"
printf 'mod:host_only;\nuse "../../src/host/host.npk".*;\nfunc:main = int32(cstring[]:_~argv) {\n    discard(raw host_now_instant());\n    exit 0i32;\n};\n' > "$P/new/tests/r/host_only.npk"
printf 'mod:lib_only;\nuse "../../src/lib.npk".*;\nfunc:main = int32(cstring[]:_~argv) {\n    exit 0i32;\n};\n' > "$P/new/tests/r/lib_only.npk"
sed -e '/^func:failsafe/,$d' -e 's/^mod:host_clocks;/mod:unit_nofs;/' "$P/new/tests/unit/host_clocks.npk" > "$P/new/tests/unit/unit_nofs.npk"
echo "§1.7 $(reach "$P/new/tests/r/host_only.npk")"
echo "§1.7 $(reach "$P/new/tests/r/lib_only.npk")"
echo "§1.7 $(reach "$P/new/tests/unit/unit_nofs.npk")"
python3 -B - "$REPO" "$P/new" <<'PY'
import os, sys
sys.path.insert(0, os.path.join(sys.argv[1], "harness"))
import arms
a, _ = arms.compute_bill(sys.argv[2], "src/host/host.npk")
print("§1.7 arms.compute_bill over src/host/host.npk: %d -- %s" % (len(a), ", ".join(sorted(a))))
PY

# ---- §1.8 the unit, forty runs a leg
legs "$P/new/tests/unit/host_clocks.npk" "§1.8 the unit, once" > "$P/unit.txt"; cat "$P/unit.txt"
for l in x0 x2; do n=0; for i in $(seq 40); do "$P/bin/host_clocks.$l" > /dev/null 2>&1 || n=$((n + 1)); done
  echo "§1.8 the unit, forty runs ($l): $n nonzero"; done

# ---- §1.9 the mutants of the module, the unit at both legs
mutants "$P/new" | sed 's/^/§1.9 /'

# ---- §1.10 the module's IR: its globals, and where the kernel is called
( cd "$P/new/src/host" && "$NPKC" host.npk -o "$P/host.ll" )
echo "§1.10 the module as a root: $(grep -cE '^@[^ ]+ = ' "$P/host.ll") global(s), $(grep -E '^@[^ ]+ = ' "$P/host.ll" | grep -vcE '= (private |internal )?(unnamed_addr )?constant ') not constant"
python3 -B - "$P/bin/host_clocks.ll" <<'PY'
import re, sys
ir = open(sys.argv[1]).read()
for m in re.finditer(r'^define [^@]*@"npk\.host\.(host_[a-z_]+)"\(.*?^}', ir, re.S | re.M):
    print("§1.10 %s: %d npk_sys6 call(s), %d mono_now call(s)"
          % (m.group(1), m.group(0).count("@npk_sys6("), len(re.findall(r"@npk_mono_now\(", m.group(0)))))
print("§1.10 host's globals: " + ", ".join(sorted(
    "%s %s" % (g, k) for g, k in re.findall(r'^@"npk\.host\.([^"]+)" = (?:internal )?(constant|global)', ir, re.M))))
PY
