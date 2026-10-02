# meta/roadmap/0.2/0.2.0_tools/facts.sh -- `0.2.0.md` §1.8: re-derive §1 at the pin, in a
# scratch copy of the tree, never in it. Sourced after `env.sh`, in one Bash call --
# block 0b of the plan:
#
#     . "$REPO/meta/roadmap/0.2/0.2.0_tools/env.sh"; . "$T/facts.sh"
#
# It writes §4.2's module and §4.4's specimen EXTRACTED FROM `0.2.0.md` (the first
# `nitpick` fence after each heading), the consumer programs §1.3 … §1.6 name, compiles
# each with the pinned `npkc`, runs `m2_use` at -O0 and after `opt -O2`, and asks
# `harness/arms.py` for the bill it computes -- then prints one line per fact. It is
# rehearsed: its output at planning is §1.8's Expect. Since 0.2.0's step rehearsal
# it also compiles §4.2's module with the derives taken off the enum, and with `Copy`
# on `Instant` alone -- PD-53's two measured refusals, which until then §1.2 stated
# and nothing re-derived.
: "${REPO:?}" "${NPKC:?}" "${NPKRT:?}" "${W:?}"
P=$W/facts; rm -rf "${P:?}"; mkdir -p "$P/tests/probe/support"
cp -r "$REPO/src" "$REPO/harness" "$P/" && cp "$REPO"/tests/probe/support/*.npk "$P/tests/probe/support/"
python3 - "$REPO/meta/roadmap/0.2/0.2.0.md" "$P" <<'PY'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
def fence(heading):
    at = text.index(heading)
    return re.search(r"```nitpick\n(.*?)```", text[at:], re.S).group(1)
open(sys.argv[2] + "/src/span/span.npk", "w").write(fence("### 4.2 "))
open(sys.argv[2] + "/tests/probe/support/probe11_relay_lib.npk", "w").write(fence("### 4.4 "))
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
        (*)                 { exit 99i32; }
    }
    exit 9i32;
};'
FS12=${FS%%'        (StackExhausted)'*}'        (LimitViolated)     { exit 109i32; },
        (StackExhausted)'${FS#*'        (StackExhausted)'}
cat > "$P/tests/m2_use.npk" <<NPK
mod:m2_use;
use "../src/span/span.npk".*;
use "../src/core/vec.npk".*;
func:main = int32(cstring[]:_~argv) {
    Instant:a = raw instant_of(1000i64, InstantClock.Monotonic);
    Instant:b = raw instant_of(4500i64, InstantClock.Monotonic);
    Result<Duration>:d = instant_since(b, a);
    if (d.is_error) { exit 10i32; }
    if (d.value.ns != 3500i64) { exit 11i32; }
    Instant:c = raw instant_add(a, d.value);
    Result<Ordering>:o = instant_cmp(c, b);
    if (o.is_error) { exit 12i32; }
    if (o.value != Ordering.Equal) { exit 13i32; }
    if (c.clock != InstantClock.Monotonic) { exit 14i32; }
    Vec<Instant>:v = raw vec_init::<Instant>(2i64);
    drop vec_push(@v, b);
    Instant:r1 = raw vec_at(v, 0i64);
    Instant:r2 = raw vec_at(v, 0i64);
    drop vec_free(@v);
    if (r1.ns != 4500i64 || r2.ns != 4500i64 || r2.clock != InstantClock.Monotonic) { exit 15i32; }
    Instant:x = raw instant_of(4500i64, InstantClock.Boottime);
    Result<Duration>:e = instant_since(x, a);
    if (!(e.is_error)) { exit 16i32; }
    Result<Ordering>:f = instant_cmp(x, a);
    if (!(f.is_error)) { exit 17i32; }
    exit 0i32;
};
$FS12
NPK
for m in m4_literal m8_write m5_convert; do
  case $m in
    m4_literal) body='    Instant:a = Instant{ ns: 1000i64, clock: InstantClock.Monotonic };' ;;
    m8_write)   body='    Instant:a = raw instant_of(1000i64, InstantClock.Monotonic);
    a.ns = 5i64;' ;;
    m5_convert) body='    Instant:a = raw instant_of(1000i64, InstantClock.Monotonic);
    int64:t = instant_to_timestamp(a);' ;;
  esac
  printf 'mod:%s;\nuse "../src/span/span.npk".*;\nfunc:main = int32(cstring[]:_~argv) {\n%s\n    exit 0i32;\n};\n%s\n' "$m" "$body" "$FS" > "$P/tests/$m.npk"
done
printf 'mod:m6_bill;\nuse "../src/span/span.npk".*;\nfunc:main = int32(cstring[]:_~argv) {\n    Instant:a = raw instant_of(1i64, InstantClock.Monotonic);\n    exit 0i32;\n};\n' > "$P/tests/m6_bill.npk"
printf 'mod:m7_relay;\nuse "./probe/support/probe11_relay_lib.npk".*;\nfunc:main = int32(cstring[]:_~argv) {\n    exit 0i32;\n};\n' > "$P/tests/m7_relay.npk"
cp "$REPO/src/lib.npk" "$P/src/lib.npk.orig"
python3 - "$P/src/lib.npk" <<'PY'
import sys
p = sys.argv[1]; s = open(p).read()
add = "".join('pub use "./span/span.npk".%s;\n' % n for n in
              ("InstantClock", "Instant", "instant_of", "instant_since", "instant_add", "instant_cmp"))
open(p, "w").write(s + add)
PY
printf 'mod:m9_umbrella;\nuse "../src/lib.npk".*;\nfunc:main = int32(cstring[]:_~argv) {\n    exit 0i32;\n};\n' > "$P/tests/m9_umbrella.npk"
cd "$P"
out=$("$NPKC" src/span/span.npk -o span.ll 2>&1); echo "span.npk: npkc=$? $(echo "$out" | grep -oE '^NITPICK-[A-Z]+-[0-9]+' | sort | uniq -c | tr -s ' ' | tr '\n' ';')"
for m in m2_use m4_literal m8_write m5_convert; do
  out=$(cd tests && "$NPKC" $m.npk -o ../$m.ll 2>&1); st=$?
  echo "$m: npkc=$st $(echo "$out" | grep -oE '^NITPICK-[A-Z]+-[0-9]+ [^ ]+' | sed -E 's|[^ ]*/([^/ ]+)$|\1|' | tr '\n' ' ')"
done
llc -O0 -filetype=obj -relocation-model=static m2_use.ll -o m2.o && ld.lld -static m2.o "$NPKRT" -o m2 && ./m2; e0=$?
opt -O2 -S m2_use.ll -o m2o.ll && llc -O2 -filetype=obj -relocation-model=static m2o.ll -o m2o.o && ld.lld -static m2o.o "$NPKRT" -o m2o && ./m2o
echo "m2_use: exit $e0 at -O0, $? after opt -O2"
Q=$W/facts_nocopy; rm -rf "${Q:?}"; mkdir -p "$Q/tests"; cp -r "$P/src" "$Q/"
sed -i 's/#\[derive(Eq, Clone, Debug, Copy)\]/#[derive(Eq, Clone, Debug)]/' "$Q/src/span/span.npk"
cp "$P/tests/m2_use.npk" "$Q/tests/"
echo "m2_use, Copy dropped from both derives: $(cd "$Q/tests" && "$NPKC" m2_use.npk -o /dev/null 2>&1 \
  | grep -oE '^NITPICK-[A-Z]+-[0-9]+ [^ ]+' | sed -E 's|[^ ]*/([^/ ]+)$|\1|' | tr '\n' ' ')"
for v in no_enum_derive copy_on_instant_alone; do
  sed -n '/^mod:span;/,$p' "$P/src/span/span.npk" > "$Q/src/span/span.npk"
  case $v in
    no_enum_derive)        python3 - "$Q/src/span/span.npk" <<'PY2'
import sys; p = sys.argv[1]; s = open(p).read()
s = s.replace("#[derive(Eq, Clone, Debug, Copy)]\npub enum:InstantClock", "pub enum:InstantClock")
s = s.replace("#[derive(Eq, Clone, Debug, Copy)]\npub struct:Instant", "#[derive(Eq, Clone, Debug)]\npub struct:Instant")
open(p, "w").write(s)
PY2
                           ;;
    copy_on_instant_alone) python3 - "$Q/src/span/span.npk" <<'PY2'
import sys; p = sys.argv[1]; s = open(p).read()
s = s.replace("#[derive(Eq, Clone, Debug, Copy)]\npub enum:InstantClock", "#[derive(Eq, Clone, Debug)]\npub enum:InstantClock")
open(p, "w").write(s)
PY2
                           ;;
  esac
  echo "span.npk, $v: $(cd "$Q/src/span" && "$NPKC" span.npk -o /dev/null 2>&1 \
    | grep -oE '^NITPICK-[A-Z]+-[0-9]+ [^ ]+' | sed -E 's|[^ ]*/([^/ ]+)$|\1|' | tr '\n' ' ')"
done
sed '/^func:failsafe/,$d; s/^mod:m2_use;/mod:m3_bill;/' "$P/tests/m2_use.npk" > "$P/tests/m3_bill.npk"
for m in m3_bill m6_bill m7_relay m9_umbrella; do
  echo "$m: $(cd tests && "$NPKC" $m.npk -o /dev/null 2>&1 | grep -oE 'NITPICK-REACH-003|[0-9]+ identities: [^-]*' | tr '\n' ' ' | sed 's/ *$//')"
done
python3 -B - <<'PY'
import sys
sys.path.insert(0, "harness")
import arms
for rel in ("src/span/span.npk", "tests/probe/support/probe11_relay_lib.npk"):
    a, info = arms.compute_bill(".", rel)
    print("compute_bill %s: %d -- %s" % (rel.split("/")[-1], len(a), ", ".join(sorted(x for x in a if "." in x))))
PY
cd "$REPO"
