# meta/roadmap/0.2/0.2.4b_tools/facts.sh -- `0.2.4b.md` §1.8: re-derive §1 at the pin, in
# scratch copies of the tree, never in it. Sourced after `env.sh`, in one Bash call --
# block 0b of the plan, run BEFORE step 1:
#
#     . "$REPO/meta/roadmap/0.2/0.2.4b_tools/env.sh"; . "$T/facts.sh"
#
# It copies the working tree twice into `$W/facts` -- `head`, as it stands, and `new`,
# with §4.1's module written over `src/span/span.npk`, EXTRACTED FROM `0.2.4b.md` (the
# first `nitpick` fence after the heading, which a line begins) -- and asks the pinned
# compiler, at -O0 and after `opt -O2`, about each finding of the cycle audit this
# subcycle answers: `timestamp_add` handed a forged `secs` at `int64`'s ends (C1),
# `instant_since` handed two readings `instant_of` builds near them (C6), a consumer
# building an `Instant` from a `Timestamp`'s numbers and back (C2), a forged hour of 24
# (K2), the statement form of `#unreachable()` (S2), and every contract comment made a
# live clause (C5); and of §4.1's module, its IR and its bill.
: "${REPO:?}" "${NPKC:?}" "${NPKRT:?}" "${W:?}"
P=$W/facts; rm -rf "${P:?}"; mkdir -p "$P"
fresh() {   # fresh <name>: the working tree as it stands, tracked and new files, at $P/<name>
  rm -rf "${P:?}/$1"; mkdir -p "$P/$1"
  ( cd "$REPO" && git ls-files -co --exclude-standard -z | xargs -0 tar -cf - ) | tar -xf - -C "$P/$1"
}
fresh head; fresh new
python3 -B - "$REPO/meta/roadmap/0.2/0.2.4b.md" "$P/new/src/span/span.npk" <<'PY'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
at = text.index("\n### 4.1 ")                      # the heading, at a line's start
code = re.search(r"```nitpick\n(.*?)```", text[at:], re.S).group(1)
s = open(sys.argv[2], encoding="utf-8").read()
open(sys.argv[2], "w", encoding="utf-8").write(s[:s.index("mod:span;")] + code)
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
build() {   # build <tree> <name>: compile tests/<name>.npk of <tree> at -O0 and after opt -O2
  ( cd "$P/$1/tests" && "$NPKC" "$2.npk" -o "$P/$1.$2.ll" > "$P/$1.$2.err" 2>&1 \
    || { echo "$2: npkc refused -- $(grep -oE '^NITPICK-[A-Z]+-[0-9]+ [^ ]+' "$P/$1.$2.err" | sed -E 's| tests/| |' | tr '\n' ' ')"; exit 1; }
    llc -O0 -filetype=obj -relocation-model=static "$P/$1.$2.ll" -o "$P/$1.$2.o" && ld.lld -static "$P/$1.$2.o" "$NPKRT" -o "$P/$1.$2.x0" \
    && opt -O2 -S "$P/$1.$2.ll" -o "$P/$1.$2.2.ll" && llc -O2 -filetype=obj -relocation-model=static "$P/$1.$2.2.ll" -o "$P/$1.$2.2.o" \
    && ld.lld -static "$P/$1.$2.2.o" "$NPKRT" -o "$P/$1.$2.x2" )
}
cases() {   # cases <tree> <name> <label> <arg>...: run each case at both legs
  local t=$1 n=$2 l=$3 a e0 e2; shift 3
  for a in "$@"; do "$P/$t.$n.x0" "$a" > /dev/null 2>&1; e0=$?; "$P/$t.$n.x2" "$a" > /dev/null 2>&1; e2=$?
    echo "$l $a: $e0 at -O0, $e2 after opt -O2"; done
}
# ---- §1.1 C1: `timestamp_add` handed a forged `secs`
for t in head new; do cat > "$P/$t/tests/c1.npk" <<EOT
mod:c1;
use "../src/span/span.npk".*;
struct:RawTs = { int64:secs; uint32:nanos; };
func:main = int32(cstring[]:argv) {
    int64:imax = ((~0u64) >> 1u64) =>! int64;
    int64:imin = (0i64 - imax) - 1i64;
    int64:k = 0i64;
    if (argv.len > 1i64) { k = (argv[1i64].ptr[0i64] => int64) - 48i64; }
    int64:ts = 0i64;
    uint32:tn = 0u32;
    int64:dn = 0i64;
    if (k == 0i64) { ts = imax; dn = 1000000000i64; }
    if (k == 1i64) { ts = imax; tn = 999999999u32; dn = 1i64; }
    if (k == 2i64) { ts = imin; dn = -1i64; }
    if (k == 3i64) { ts = imax; }
    if (k == 4i64) { ts = imax; tn = 999999999u32; }
    if (k == 5i64) { ts = imin; }
    if (k == 6i64) { ts = imax - 9223372036i64; tn = 999999999u32; dn = imax; }
    if (k == 7i64) { ts = imax - 9223372037i64; tn = 999999999u32; dn = imax; }
    if (k == 8i64) { ts = imin + 9223372036i64; dn = imin; }
    if (k == 9i64) { ts = imin + 9223372037i64; dn = imin; }
    wild int8->:mem = alloc(#size_of<Timestamp>());
    wild RawTs->:w = mem =>! wild RawTs->;
    <-w = RawTs{ secs: ts, nanos: tn };
    wild Timestamp->:p = mem =>! wild Timestamp->;
    Timestamp:t = <-p;
    dalloc(mem);
    Result<Timestamp>:r = timestamp_add(t, raw duration_ns(dn));
    if (r.is_error) { exit 10i32; }
    exit 0i32;
};
$FS
EOT
build $t c1 && cases $t c1 "C1 $t, case" 0 1 2 3 4 5 6 7 8 9; done
# ---- §1.2 C6: `instant_since` handed two readings `instant_of` builds
for t in head new; do cat > "$P/$t/tests/c6.npk" <<EOT
mod:c6;
use "../src/span/span.npk".*;
func:main = int32(cstring[]:argv) {
    int64:imax = ((~0u64) >> 1u64) =>! int64;
    int64:imin = (0i64 - imax) - 1i64;
    int64:k = 0i64;
    if (argv.len > 1i64) { k = (argv[1i64].ptr[0i64] => int64) - 48i64; }
    int64:a = imax;
    int64:b = -1i64;
    if (k == 1i64) { b = 0i64; }
    if (k == 2i64) { a = imin; b = 1i64; }
    if (k == 3i64) { a = imin + 1i64; b = 1i64; }
    Result<Duration>:r = instant_since(raw instant_of(a, InstantClock.Monotonic),
                                       raw instant_of(b, InstantClock.Monotonic));
    if (r.is_error) { exit 10i32; }
    if ((k == 1i64 && r.value.ns != imax) || (k == 3i64 && r.value.ns != imin)) { exit 11i32; }
    exit 0i32;
};
$FS
EOT
build $t c6 && cases $t c6 "C6 $t, case" 0 1 2 3; done
# ---- §1.3 C2: a consumer builds an `Instant` from a `Timestamp`'s numbers, and back
cat > "$P/head/tests/c2.npk" <<EOT
mod:c2;
use "../src/span/span.npk".*;
func:main = int32(cstring[]:_~argv) {
    Result<Timestamp>:rt = timestamp_of(1759363200i64, 250000000i64);
    if (rt.is_error) { exit 10i32; }
    Timestamp:t = rt.value;
    Instant:i = raw instant_of((t.secs * 1000000000i64) + (t.nanos => int64), InstantClock.Monotonic);
    Result<Duration>:d = instant_since(raw instant_add(i, raw duration_secs(5i64)), i);
    if (d.is_error) { exit 11i32; }
    if (d.value.ns != 5000000000i64) { exit 12i32; }
    Result<Timestamp>:back = timestamp_of(i.ns / 1000000000i64, i.ns % 1000000000i64);
    if (back.is_error) { exit 13i32; }
    if (back.value.secs != t.secs || back.value.nanos != t.nanos) { exit 14i32; }
    exit 0i32;
};
$FS
EOT
build head c2 && cases head c2 "C2, no wild and no =>!:" run
printf 'mod:c2b;\nuse "../src/span/span.npk".*;\nfunc:main = int32(cstring[]:_~argv) {\n    Timestamp:t = 5i128 =>! Timestamp;\n    exit 0i32;\n};\n%s\n' "$FS" > "$P/head/tests/c2b.npk"
( cd "$P/head/tests" && "$NPKC" c2b.npk -o /dev/null 2>&1 | grep -oE '^NITPICK-[A-Z]+-[0-9]+' | sed 's/^/C2, 5i128 =>! Timestamp: /' )
# ---- §1.4 K2: a forged hour of 24
cat > "$P/head/tests/k2.npk" <<EOT
mod:k2;
use "../src/cal/cal.npk".*;
use "../src/span/span.npk".*;
struct:RawTime = { uint8:hour; uint8:minute; uint8:second; uint32:nanos; };
func:main = int32(cstring[]:_~argv) {
    Result<CivilDate>:d = civil_date(2026i64, 10i64, 2i64);
    if (d.is_error) { exit 10i32; }
    wild int8->:mem = alloc(#size_of<CivilTime>());
    wild RawTime->:w = mem =>! wild RawTime->;
    <-w = RawTime{ hour: 24u8, minute: 0u8, second: 0u8, nanos: 0u32 };
    wild CivilTime->:p = mem =>! wild CivilTime->;
    CivilTime:c = <-p;
    dalloc(mem);
    Result<Timestamp>:r = civil_to_utc(CivilDateTime{ date: d.value, time: c });
    if (r.is_error) { exit 11i32; }
    Result<CivilDate>:next = civil_date(2026i64, 10i64, 3i64);
    if (next.is_error) { exit 12i32; }
    if (r.value.secs != (raw date_to_days(next.value)) * 86400i64 || r.value.nanos != 0u32) { exit 13i32; }
    exit 0i32;
};
func:failsafe = int32(Error:e) {
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
};
EOT
build head k2 && cases head k2 "K2, a forged hour of 24 on 2026-10-02, the next day's midnight =" run
# ---- §1.5 S2: the statement form, and `?|`
printf 'mod:s2;\nfunc:take = int64() { pass 5i64; };\nfunc:main = int32(cstring[]:_~argv) {\n    Result<int64>:r = take();\n    if (r.is_error) { #unreachable(); }\n    if (r.value != 5i64) { exit 10i32; }\n    exit 0i32;\n};\nfunc:failsafe = int32(Error:e) {\n    pick (e) {\n        (Unreachable)       { exit 95i32; },\n        (HeapBadRequest)    { exit 91i32; },\n        (HeapOom)           { exit 92i32; },\n        (WildLeak)          { exit 96i32; },\n        (StackExhausted)    { exit 106i32; },\n        (MachineFault)      { exit 107i32; },\n        (*)                 { exit 99i32; }\n    }\n    exit 9i32;\n};\n' > "$P/head/tests/s2.npk"
printf 'mod:s2b;\nfunc:take = int64() { pass 5i64; };\nfunc:main = int32(cstring[]:_~argv) {\n    int64:v = take() ?| #unreachable();\n    if (v != 5i64) { exit 10i32; }\n    exit 0i32;\n};\nfunc:failsafe = int32(Error:e) {\n    pick (e) {\n        (Unreachable)       { exit 95i32; },\n        (HeapBadRequest)    { exit 91i32; },\n        (HeapOom)           { exit 92i32; },\n        (WildLeak)          { exit 96i32; },\n        (StackExhausted)    { exit 106i32; },\n        (MachineFault)      { exit 107i32; },\n        (*)                 { exit 99i32; }\n    }\n    exit 9i32;\n};\n' > "$P/head/tests/s2b.npk"
for f in s2 s2b; do ( cd "$P/head/tests" && out=$("$NPKC" $f.npk -o "$P/$f.ll" 2>&1); echo "S2, $f: npkc=$? $(echo "$out" | grep -oE '^NITPICK-[A-Z]+-[0-9]+' | tr '\n' ' ')" ); done
# ---- §1.6 C5: every contract comment of HEAD made a live clause
python3 -B "$T/contracts.py" "$P/head" | tail -1 | sed 's/^/C5, as written: /'
python3 -B "$T/contracts.py" "$P/head" answer | grep -v ' compiles$' | sed 's/^/C5, answer read as result: /'
# ---- §1.7 §4.1's module: its IR, its link, its bill
( cd "$P/new/src/span" && "$NPKC" span.npk -o "$P/span_new.ll" > /dev/null 2>&1; echo "§4.1's span.npk: npkc=$?" )
python3 -B - "$P/span_new.ll" <<'PY'
import re, sys
ll = open(sys.argv[1], encoding="utf-8").read()
body = re.search(r'^define [^\n]*@"npk\.span\.instant_since"\(.*?^}', ll, re.S | re.M).group(0)
print("instant_since's IR: %d llvm.ssub.with.overflow.i128, %d call(s) of a __*ti3 or __*ti4 libcall; the module's: %d"
      % (body.count("@llvm.ssub.with.overflow.i128("), len(re.findall(r"@__\w+ti[34]\b", body)),
         len(re.findall(r"@__\w+ti[34]\b", ll))))
PY
printf 'mod:b_span;\nuse "../src/span/span.npk".*;\nfunc:main = int32(cstring[]:_~argv) {\n    exit 0i32;\n};\n' > "$P/new/tests/b_span.npk"
printf 'mod:b_lib;\nuse "../src/lib.npk".*;\nfunc:main = int32(cstring[]:_~argv) {\n    exit 0i32;\n};\n' > "$P/new/tests/b_lib.npk"
for f in b_span b_lib; do ( cd "$P/new/tests" && echo "$f: $("$NPKC" $f.npk -o /dev/null 2>&1 | grep -oE '[0-9]+ identities' | head -1)" ); done
python3 -B - "$P/new" <<'PY'
import os, sys
sys.path.insert(0, os.path.join(sys.argv[1], "harness"))
import checks
for name in ("check_int128_sites", "check_constants_named", "check_no_view_returns"):
    r = getattr(checks, name)(sys.argv[1])
    print("%s over §4.1's module: %d finding(s) -- %s" % (r.name, len(r.problems), r.headline))
    for p in r.problems:
        print("  " + p.splitlines()[0][:150])
PY
