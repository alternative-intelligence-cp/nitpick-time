# meta/roadmap/0.3/0.3.2_tools/facts.sh -- `0.3.2.md` §1.11: re-derive §1 at the pin, in
# scratch copies of the tree, never in it. Sourced after `env.sh`, in one Bash call --
# block 0b of the plan, run BEFORE step 1:
#
#     . "$REPO/meta/roadmap/0.3/0.3.2_tools/env.sh"; . "$T/facts.sh"
#
# It copies the working tree into `$W/facts`: `head`, as it stands; `one`, with step
# 1's patch, every generic function read in an emission; and `three`, with all three
# steps', the system zone and its units. Each patch is applied by GNU `patch` to the
# copy alone -- `git apply` run inside this checkout would resolve the paths against
# the checkout, not the copy. Then it asks the pinned compiler, at -O0 and after
# `opt -O2`, and EACH COPY'S OWN checks -- a check reads its exemptions only over its
# own tree -- what §1 says: the four generic shapes 0.3.1's fix found (§1.2) and step
# 1's reading of them (§1.3), the arms a truncation of descriptors brings (§1.4), the
# machine and a namespace of the program's own (§1.5, §1.6), the language's shapes the
# system zone needs (§1.7), and the module, its bills and its units (§1.8).
: "${REPO:?}" "${NPKC:?}" "${NPKRT:?}" "${W:?}" "${T:?}" "${NTIME_RUN_DATE:?}"
P=$W/facts; rm -rf "${P:?}"; mkdir -p "$P/bin" "$A/legs"
fresh() {   # fresh <name> [<step>...]: the working tree as it stands at $P/<name>, then each step
  local d=$1 n; shift
  rm -rf "${P:?}/$d"; mkdir -p "$P/$d"
  ( cd "$REPO" && git ls-files -co --exclude-standard -z | xargs -0 tar -cf - ) | tar -xf - -C "$P/$d"
  for n in "$@"; do
    sed "s/@@RUN_DATE@@/$NTIME_RUN_DATE/g" "$T/step$n.patch" | patch -p1 -s --no-backup-if-mismatch -d "$P/$d" \
      || echo "STOP: step$n does not apply to a copy of the tree"
  done
}
reach() {   # reach <tree> <file, relative to the tree>: NITPICK-REACH-003's count and list for a root importing it
  mkdir -p "$1/zz"
  printf 'mod:zz_root;\nuse "../%s".*;\nfunc:main = int32(cstring[]:_~argv) {\n    exit 0i32;\n};\n' "$2" > "$1/zz/zz_root.npk"
  ( cd "$1/zz" && "$NPKC" zz_root.npk -o /dev/null 2>&1 ) | grep -oE '[0-9]+ identities: [^-]*' | sed 's/ *$//'
  rm -rf "${1:?}/zz"
}
inst_root() {   # inst_root <tree> <line>: the instances' unit importing `cal` too, with <line>, and `cal`'s arms
  local f="$1/tests/unit/generic_instances.npk"
  sed -i 's|^use "../../src/core/vec.npk".\*;|use "../../src/core/vec.npk".*;\nuse "../../src/cal/cal.npk".*;|' "$f"
  sed -i 's|^        (HeapBadRequest)    { exit 91i32; },|        (cal.ETimeValue)    { exit 80i32; },\n        (DivByZero)         { exit 97i32; },\n        (DivOverflow)       { exit 98i32; },\n        (HeapBadRequest)    { exit 91i32; },|' "$f"
  printf '%s\n' "$2" >> "$f"
}
first() { sed -n 2p | sed 's/^  //' | cut -c1-"${1:-150}"; }
fresh head; fresh one 1; fresh three 1 2 3

# ---- §1.2 four generic shapes, each appended to a copy's `src/cal/cal.npk` --------
declare -A PLANT INST
PLANT[die]='pub func:p_gen_die<T: Copy> = NIL(move ByteReader:r) never fails {
    pass NIL;
};'
PLANT[trunc]='pub func:p_gen_trunc<T: Copy> = NIL(List<ByteReader>->:l) never fails {
    drop list_truncate(l, 0i64);
    pass NIL;
};'
PLANT[alias]='pub func:p_gen_alias<T: Copy> = int64() never fails {
    func int64() never fails:f = mono_now;
    pass raw f();
};'
PLANT[await]='pub async func:p_gen<T: Copy> = NIL(TextReader<ByteReader>->:tr) {
    string:l = relay await text_read_line(tr, raw duration_secs(1i64));
    pass NIL;
};'
INST[die]='func:inst_die = NIL(move ByteReader:r) { drop p_gen_die::<int64>(move(r)); pass NIL; };'
INST[trunc]='func:inst_trunc = NIL(List<ByteReader>->:l) { drop p_gen_trunc::<int64>(l); pass NIL; };'
INST[alias]='func:inst_alias = int64() { pass raw p_gen_alias::<int64>(); };'
INST[await]='func:inst_await = NIL(TextReader<ByteReader>->:tr) { drop p_gen::<int64>(tr); pass NIL; };'
for k in die trunc alias await; do
  cp -r "$P/head" "$P/h-$k"; printf '%s\n' "${PLANT[$k]}" >> "$P/h-$k/src/cal/cal.npk"; emit "$P/h-$k"
  echo "§1.2 $k, at HEAD: $(check check_purity "$P/h-$k" "$P/h-$k" | head -1 | cut -d' ' -f1-3) $(check check_call_edges "$P/h-$k" "$P/h-$k" | head -1 | cut -d' ' -f1-3)"
done

# ---- §1.3 step 1's reading of each: with no instance, and with one --------------
for k in die trunc alias await; do
  cp -r "$P/one" "$P/o-$k"; printf '%s\n' "${PLANT[$k]}" >> "$P/o-$k/src/cal/cal.npk"; emit "$P/o-$k"
  echo "§1.3 $k, no instance: $(check check_call_edges "$P/o-$k" "$P/o-$k" | first 110)"
  cp -r "$P/one" "$P/i-$k"; printf '%s\n' "${PLANT[$k]}" >> "$P/i-$k/src/cal/cal.npk"; inst_root "$P/i-$k" "${INST[$k]}"
  out=$(emit "$P/i-$k" 2>&1)
  if [ -n "$out" ]; then
    echo "§1.3 $k, an instance: the instances refused, $(cd "$P/i-$k" && "$NPKC" tests/unit/generic_instances.npk -o /dev/null 2>&1 | grep -oE '^NITPICK-[A-Z]+-[0-9]+' | head -1)"
  else
    echo "§1.3 $k, an instance: $(check check_call_edges "$P/i-$k" "$P/i-$k" | first 90)"
  fi
done
emit "$P/one"
echo "§1.3 the tree, step 1: $(check check_call_edges "$P/one" "$P/one" | head -1)"
echo "§1.3 the tree, step 1: $(check check_wide_types "$P/one" "$P/one" | head -1)"
emit "$P/head"
echo "§1.3 the tree, HEAD:   $(check check_call_edges "$P/head" "$P/head" | head -1)"
python3 -B - "$P/one" <<'PY'
import os, sys
sys.path.insert(0, os.path.join(sys.argv[1], "harness"))
import checks
got = checks.read_emission(os.path.join(sys.argv[1], checks.INSTANCES))
defines, declares, globs = got
mods, host = checks._src_modules(sys.argv[1])
syms = set()
for n in sorted(defines):
    if checks._ir_module(n) in mods and "<" in n:
        s, _src, _odd = checks._reach(n, defines, declares, globs, mods)
        syms |= set(s)
print("§1.3 the nine instances reach: " + ", ".join(sorted(syms)))
PY

# ---- §1.4 a truncation of descriptors: the identities it brings, module by module
for m in cal:src/cal/cal.npk vec:src/core/vec.npk bytes:src/core/bytes.npk; do
  name=${m%%:*}; f=${m#*:}
  cp -r "$P/head" "$P/t-$name"
  printf '%s\n' 'pub func:p_trunc<T: Copy> = NIL(List<ByteReader>->:l) never fails {' \
    '    drop list_truncate(l, 0i64);' '    pass NIL;' '};' >> "$P/t-$name/$f"
  before=$(reach "$P/head" "$f"); after=$(reach "$P/t-$name" "$f")
  new=$(comm -13 <(echo "${before#*: }" | tr ',' '\n' | sed 's/^ *//' | sort) <(echo "${after#*: }" | tr ',' '\n' | sed 's/^ *//' | sort) | tr '\n' ' ' | sed 's/ $//')
  echo "§1.4 $name: ${before%%:*} without it, ${after%%:*} with it; new: ${new:-none}"
done

# ---- §1.5 the machine ----------------------------------------------------------------
echo "§1.5 kernel.apparmor_restrict_unprivileged_userns = $(sysctl -n kernel.apparmor_restrict_unprivileged_userns 2>&1)"
[ -L /etc/localtime ] && echo "§1.5 /etc/localtime: a link" || echo "§1.5 /etc/localtime: not a link"
[ -e /etc/timezone ] && echo "§1.5 /etc/timezone: present" || echo "§1.5 /etc/timezone: absent"

# ---- §1.6 a namespace of the program's own: probe22, and the machine's /etc after --
before=$(readlink /etc/localtime)
echo "§1.6 probe22, a program's own /etc: $(legs2 "$P/three/tests/probe" probe22_private_etc) (-O0/-O2)"
[ "$(readlink /etc/localtime)" = "$before" ] && echo "§1.6 the machine's /etc/localtime: unchanged" || echo "§1.6 the machine's /etc/localtime: CHANGED"

# ---- §1.7 the language's shapes ------------------------------------------------------
mkdir -p "$P/shape"
for n in uid gid; do
  printf 'mod:sh_%s;\nfunc:main = int32(cstring[]:_~argv) {\n    int64:%s = 1i64;\n    exit 0i32;\n};\n' "$n" "$n" > "$P/shape/sh_$n.npk"
  echo "§1.7 a local named $n: $(codes "$PIN" "$P/shape/sh_$n.npk")"
done
{ printf 'mod:sh_for;\nfunc:main = int32(cstring[]:_~argv) {\n    int64:trips = 0i64;\n'
  printf '    for (int64:i in 0i64..(0i64 - 1i64)) { trips = trips + 1i64; }\n'
  printf '    if (trips != 0i64) { exit 10i32; }\n    for (int64:i in 0i64..2i64) { trips = trips + 1i64; }\n'
  printf '    if (trips != 3i64) { exit 11i32; }\n    exit 0i32;\n};\n'
  printf 'func:failsafe = int32(Error:e) {\n    pick (e) {\n        (HeapBadRequest) { exit 91i32; },\n'
  printf '        (HeapOom) { exit 92i32; },\n        (IntOverflow) { exit 93i32; },\n        (Unreachable) { exit 95i32; },\n'
  printf '        (WildLeak) { exit 96i32; },\n        (StackExhausted) { exit 106i32; },\n        (MachineFault) { exit 107i32; },\n'
  printf '        (*) { exit 99i32; }\n    }\n    exit 9i32;\n};\n'; } > "$P/shape/sh_for.npk"
echo "§1.7 for over 0..-1 runs no trip, over 0..2 three: $(legs2 "$P/shape" sh_for) (-O0/-O2)"
cp -r "$P/three" "$P/while"
python3 -B - "$P/while/src/host/host.npk" <<'PY'
import re, sys
p = sys.argv[1]; s = open(p).read()
n = 0
for old, new in (("    for (int64:k in 0i64..(env.len - 1i64)) {",
                  "    int64:k = -1i64;\n    while ((k + 1i64) < env.len) decreases env.len - k {\n        k = k + 1i64;"),):
    n += s.count(old); s = s.replace(old, new)
open(p, "w").write(s); print("§1.7 the TZ step's for loop, written as a while loop: %d replaced" % n)
PY
echo "§1.7 host with that while loop: $(reach "$P/while" src/host/host.npk | cut -d: -f1)"

# ---- §1.8 the module, its bills, its readings, and its units -------------------------
echo "§1.8 the module as a root: $(codes "$PIN" "$P/three/src/host/host.npk")"
echo "§1.8 the umbrella: $(codes "$PIN" "$P/three/src/lib.npk")"
echo "§1.8 host alone: $(reach "$P/three" src/host/host.npk)"
echo "§1.8 the umbrella: $(reach "$P/three" src/lib.npk | cut -d: -f1)"
emit "$P/three"
echo "§1.8 $(check check_host_isolation "$P/three" "$P/three" | head -1)"
echo "§1.8 $(check check_call_edges "$P/three" "$P/three" | head -1 | cut -c1-300)"
DESC='ByteReader|ByteWriter|OwnedFd|TextReader|TextWriter|LineBufWriter'
echo "§1.8 the six descriptor-owning prelude names, in src/ outside src/host/: $(grep -rwE "$DESC" "$P/three/src" --exclude-dir=host | wc -l) line(s); in src/host/: $(grep -rwE "$DESC" "$P/three/src/host" | wc -l), naming $(grep -rhowE "$DESC" "$P/three/src/host" | sort -u | tr '\n' ' ' | sed 's/ $//')"
for u in system_zone_etc system_zone_tz system_zone_tz_colon system_zone_tz_empty; do
  echo "§1.8 $u, once a leg: $(legs2 "$P/three/tests/unit" "$u") (-O0/-O2)"
done
rm -rf "${A:?}/legs"
