# meta/roadmap/0.2/0.2.1_tools/facts.sh -- `0.2.1.md` §1.9: re-derive §1 at the pin, in a
# scratch copy of the tree, never in it. Sourced after `env.sh`, in one Bash call --
# block 0b of the plan, run BEFORE step 1:
#
#     . "$REPO/meta/roadmap/0.2/0.2.1_tools/env.sh"; . "$T/facts.sh"
#
# It copies `src/`, `harness/` and `nitpick.toml` (a copy takes the manifest, or the
# compiler renders its paths from another root: the compiler's D-236), writes §4.2's
# module over `src/span/span.npk` -- EXTRACTED FROM `0.2.1.md`, the first `nitpick`
# fence after the heading -- and the consumer programs §1.2 ... §1.7 name; compiles
# each with the pinned `npkc`; runs the three that should run at -O0 and after
# `opt -O2`; and asks `harness/arms.py` for the bill it computes. Then it measures
# 0.2.0's test gap: the unit as 0.2.0 left it, read from its record commit
# `e0e8547`, against a `span` whose `instant_add` hard-codes `Monotonic` -- the
# gap -- and one that hard-codes `Boottime` -- why step 1 moves the clock checks.
: "${REPO:?}" "${NPKC:?}" "${NPKRT:?}" "${W:?}"
P=$W/facts; rm -rf "${P:?}"; mkdir -p "$P/tests"
cp -r "$REPO/src" "$REPO/harness" "$REPO/nitpick.toml" "$P/"
python3 - "$REPO/meta/roadmap/0.2/0.2.1.md" "$P" <<'PY'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
at = text.index("### 4.2 ")
code = re.search(r"```nitpick\n(.*?)```", text[at:], re.S).group(1)
open(sys.argv[2] + "/src/span/span.npk", "w", encoding="utf-8").write(code)
PY
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
        (DecreasesViolated) { exit 108i32; },
        (LimitViolated)     { exit 109i32; },
        (*)                 { exit 99i32; }
    }
    exit 9i32;
};'
prog() {   # prog <name> <body> [<more declarations>] -- a consumer of `span`, the superset `failsafe`
  printf 'mod:%s;\nuse "../src/span/span.npk".*;\nuse "../src/core/vec.npk".*;\nfunc:main = int32(cstring[]:_~argv) {\n%s\n    exit 0i32;\n};\n%s\n%s\n' \
    "$1" "$2" "${3:-}" "$FS" > "$P/tests/$1.npk"
}
TS='    Result<Timestamp>:r = timestamp_of(1000i64, 0i64);
    if (r.is_error) { exit 10i32; }'
IN='    Instant:a = raw instant_of(1000i64, InstantClock.Monotonic);'
prog m_use '    Result<Timestamp>:r = timestamp_of(-1i64, 500000000i64);
    if (r.is_error) { exit 10i32; }
    Timestamp:t = r.value;
    if (t.secs != -1i64) { exit 11i32; }
    if (t.nanos != 500000000u32) { exit 12i32; }
    Result<Timestamp>:z = timestamp_of(0i64, 0i64);
    if (z.is_error) { exit 13i32; }
    Result<Ordering>:o = z.value.cmp(t);
    if (o.is_error) { exit 14i32; }
    if (o.value != Ordering.Greater) { exit 15i32; }
    Result<Timestamp>:bad = timestamp_of(0i64, 1000000000i64);
    if (!(bad.is_error)) { exit 16i32; }
    Vec<Timestamp>:v = raw vec_init::<Timestamp>(1i64);
    drop vec_push(@v, t);
    Timestamp:back = raw vec_at(v, 0i64);
    drop vec_free(@v);
    if (back.secs != -1i64 || back.nanos != 500000000u32) { exit 17i32; }'
prog m_literal '    Timestamp:t = Timestamp{ secs: -1i64, nanos: 1500000000u32 };'
prog m_write "$TS
    Timestamp:t = r.value;
    t.nanos = 1500000000u32;"
prog m_i_cmp "$IN
$TS
    Result<Ordering>:o = r.value.cmp(a);"
prog m_i_param "$IN
    int64:s = raw seconds_of(a);" 'func:seconds_of = int64(Timestamp:t) never fails {
    pass t.secs;
};'
prog m_i_bind "$IN
    Timestamp:t = a;"
prog m_t_since "$IN
$TS
    Result<Duration>:d = instant_since(a, r.value);"
prog m_t_bind "$TS
    Instant:a = r.value;"
prog m_i_cast "$IN
    Timestamp:t = a =>! Timestamp;"
prog m_i_ccast "$IN
    Timestamp:t = a => Timestamp;"
prog m_t_cast "$TS
    Instant:a = r.value =>! Instant;"
prog m_t_ccast "$TS
    Instant:a = r.value => Instant;"
prog m_mono '    int64:first = mono_now();
    int64:second = mono_now();
    if (second < first) { exit 10i32; }'
prog m_wild '    wild int8->:mem = alloc(#size_of<Instant>());
    wild Instant->:pi = mem =>! wild Instant->;
    <-pi = raw instant_of(1000i64, InstantClock.Boottime);
    wild Timestamp->:pt = mem =>! wild Timestamp->;
    Timestamp:t = <-pt;
    int64:s = t.secs;
    int64:n = t.nanos => int64;
    dalloc(mem);
    if (s != 1000i64) { exit 10i32; }
    exit (20i64 + n) =>! int32;'
for ty in Instant Timestamp InstantClock; do prog "m_size_$ty" "    exit #size_of<$ty>() =>! int32;"; done
prog m_hreads "$IN
    int64:n = a.ns;
$TS
    int64:s = r.value.secs;"
cd "$P/src/span" && out=$("$NPKC" span.npk -o /dev/null 2>&1); echo "span.npk: npkc=$? $(echo "$out" | grep -oE '^NITPICK-[A-Z]+-[0-9]+' | tr '\n' ' ')"
cd "$P/tests"
for m in m_literal m_write m_i_cmp m_i_param m_i_bind m_t_since m_t_bind m_i_cast m_i_ccast m_t_cast m_t_ccast m_mono; do
  out=$("$NPKC" $m.npk -o /dev/null 2>&1); st=$?
  echo "$m: npkc=$st $(echo "$out" | grep -oE '^NITPICK-[A-Z]+-[0-9]+ [^ ]+:[0-9]+:[0-9]+' | sed -E 's|^(NITPICK-[A-Z]+-[0-9]+) ([^ ]*/)?([^/ ]+)$|\1 \3|' | tr '\n' ' ' | sed 's/ $//')"
done
legs() {   # legs <name>: npkc, then -O0 and opt -O2, the two exits
  "$NPKC" "$1.npk" -o "$1.ll" > /dev/null 2>&1 || { echo "$1: npkc refused"; return; }
  llc -O0 -filetype=obj -relocation-model=static "$1.ll" -o "$1.o" && ld.lld -static "$1.o" "$NPKRT" -o "$1" && ./"$1"; local e0=$?
  opt -O2 -S "$1.ll" -o "$1.2.ll" && llc -O2 -filetype=obj -relocation-model=static "$1.2.ll" -o "$1.2.o" && ld.lld -static "$1.2.o" "$NPKRT" -o "$1.2" && ./"$1.2"
  echo "$1: exit $e0 at -O0, $? after opt -O2"
}
legs m_use; legs m_wild
for ty in Instant Timestamp InstantClock; do legs "m_size_$ty"; done
Q=$W/facts_var; rm -rf "${Q:?}"
for v in unsealed hidden no_copy no_ord; do
  mkdir -p "$Q/$v/tests"; cp -r "$P/src" "$Q/$v/"; cp "$P/nitpick.toml" "$Q/$v/"; cp "$P"/tests/m_use.npk "$P"/tests/m_hreads.npk "$P"/tests/m_literal.npk "$Q/$v/tests/"
  s="$Q/$v/src/span/span.npk"
  case $v in
    unsealed) swap "$s" '{ sealed int64:secs; sealed uint32:nanos; }' '{ int64:secs; uint32:nanos; }' ;;
    hidden) swap "$s" 'sealed int64:ns;' 'hidden int64:ns;'
            swap "$s" '{ sealed int64:secs; sealed uint32:nanos; }' '{ hidden int64:secs; hidden uint32:nanos; }' ;;
    no_copy) swap "$s" $'#[derive(Eq, Ord, Clone, Debug, Copy)]\npub struct:Timestamp' $'#[derive(Eq, Ord, Clone, Debug)]\npub struct:Timestamp' ;;
    no_ord)  swap "$s" $'#[derive(Eq, Ord, Clone, Debug, Copy)]\npub struct:Timestamp' $'#[derive(Eq, Clone, Debug, Copy)]\npub struct:Timestamp' ;;
  esac
  f=m_use; [ $v = hidden ] && f=m_hreads; [ $v = unsealed ] && f=m_literal
  out=$(cd "$Q/$v/tests" && "$NPKC" $f.npk -o /dev/null 2>&1); st=$?
  echo "$f, $v: npkc=$st $(echo "$out" | grep -oE '^NITPICK-[A-Z]+-[0-9]+ [^ ]+:[0-9]+:[0-9]+' \
    | sed -E 's|^(NITPICK-[A-Z]+-[0-9]+) ([^ ]*/)?([^/ ]+)$|\1 \3|' | tr '\n' ' ' | sed 's/ $//')"
done
printf 'mod:b_span;\nuse "../src/span/span.npk".*;\nfunc:main = int32(cstring[]:_~argv) {\n    exit 0i32;\n};\n' > b_span.npk
python3 - "$P/src/lib.npk" <<'PY'
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
s += 'pub use "./span/span.npk".Timestamp;\npub use "./span/span.npk".timestamp_of;\n'
open(p, "w", encoding="utf-8").write(s)
PY
printf 'mod:b_lib;\nuse "../src/lib.npk".*;\nfunc:main = int32(cstring[]:_~argv) {\n    exit 0i32;\n};\n' > b_lib.npk
for m in b_span b_lib; do
  echo "$m: $("$NPKC" $m.npk -o /dev/null 2>&1 | grep -oE 'NITPICK-REACH-003|[0-9]+ identities: [^-]*' | tr '\n' ' ' | sed 's/ *$//')"
done
cd "$P" && python3 -B - <<'PY'
import sys
sys.path.insert(0, "harness")
import arms
for rel in ("src/span/span.npk", "src/lib.npk"):
    a, info = arms.compute_bill(".", rel)
    print("compute_bill %s: %d -- %s" % (rel.split("/")[-1], len(a), ", ".join(sorted(x for x in a if "." in x))))
PY
for clk in Monotonic Boottime; do
  G=$W/facts_gap_$clk; rm -rf "${G:?}"; mkdir -p "$G/tests/unit"; cp -r "$P/src" "$P/nitpick.toml" "$G/"
  git -C "$REPO" show e0e8547:tests/unit/instant_ops.npk > "$G/tests/unit/instant_ops.npk"
  swap "$G/src/span/span.npk" 'clock: t.clock }' "clock: InstantClock.$clk }"
  ( cd "$G/tests/unit" && legs instant_ops | sed "s/^instant_ops:/instant_ops as 0.2.0 left it, instant_add hard-coding $clk:/" )
done
cd "$REPO"
