# meta/roadmap/0.2/0.2.2_tools/facts.sh -- `0.2.2.md` §1.10: re-derive §1 at the pin, in a
# scratch copy of the tree, never in it. Sourced after `env.sh`, in one Bash call --
# block 0b of the plan, run BEFORE step 1:
#
#     . "$REPO/meta/roadmap/0.2/0.2.2_tools/env.sh"; . "$T/facts.sh"
#
# It copies `src/`, `harness/` and `nitpick.toml` (a copy takes the manifest, or the
# compiler renders its paths from another root: the compiler's D-236), writes §4.2's
# module over `src/span/span.npk` -- EXTRACTED FROM `0.2.2.md`, the first `nitpick`
# fence after the heading -- and three variants of it: the statement form of the
# refusal, `?! Unreachable`, and the truncating split; compiles each, and the
# consumer programs §1.2 ... §1.8 name; runs those that should run, at -O0 and after
# `opt -O2`; reads the emitted IR for the division and the stops; asks `harness/arms.py`
# for the bill and `harness/checks.py` -- HEAD's, the map before step 4 -- about a
# literal 86400 in two modules; transcribes the 512 days and the sixteen vectors in
# Python and holds the tree's answers to them; and lists the glossary's sites.
: "${REPO:?}" "${NPKC:?}" "${NPKRT:?}" "${W:?}"
P=$W/facts; rm -rf "${P:?}"; mkdir -p "$P/tests"
cp -r "$REPO/src" "$REPO/harness" "$REPO/nitpick.toml" "$P/"
python3 - "$REPO/meta/roadmap/0.2/0.2.2.md" "$P" <<'PY'
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
        (*)                 { exit 99i32; }
    }
    exit 9i32;
};'
prog() {   # prog <name> <body> [<more declarations>] -- a consumer of `span` and `cal`
  printf 'mod:%s;\nuse "../src/span/span.npk".*;\nuse "../src/cal/cal.npk".*;\nuse "../src/core/limits.npk".*;\nfunc:main = int32(cstring[]:_~argv) {\n%s\n    exit 0i32;\n};\n%s\n%s\n' \
    "$1" "$2" "${3:-}" "$FS" > "$P/tests/$1.npk"
}
legs() {   # legs <dir> <name>: npkc, then -O0 and opt -O2, the two exits
  ( cd "$1" && { "$NPKC" "$2.npk" -o "$2.ll" > /dev/null 2>&1 || { echo "$2: npkc refused"; exit; }
    llc -O0 -filetype=obj -relocation-model=static "$2.ll" -o "$2.o" && ld.lld -static "$2.o" "$NPKRT" -o "$2" && ./"$2" > /dev/null; e0=$?
    opt -O2 -S "$2.ll" -o "$2.2.ll" && llc -O2 -filetype=obj -relocation-model=static "$2.2.ll" -o "$2.2.o" \
      && ld.lld -static "$2.2.o" "$NPKRT" -o "$2.2" && ./"$2.2" > /dev/null
    echo "$2: exit $e0 at -O0, $? after opt -O2"; } )
}
diag() {   # diag <dir> <file>: npkc's exit and each diagnostic's code and site
  local out st; out=$(cd "$1" && "$NPKC" "$2" -o /dev/null 2>&1); st=$?
  echo "$2: npkc=$st $(echo "$out" | grep -oE '^NITPICK-[A-Z]+-[0-9]+ [^ ]+:[0-9]+:[0-9]+' \
    | sed -E 's|^(NITPICK-[A-Z]+-[0-9]+) ([^ ]*/)?([^/ ]+)$|\1 \3|' | tr '\n' ' ' | sed 's/ $//')"
}
# ---- §1.2: the module, and the refusal's three spellings --------------------------
diag "$P/src/span" span.npk
V=$W/facts_var; rm -rf "${V:?}"
for v in statement bang truncating; do
  mkdir -p "$V/$v"; cp -r "$P/src" "$P/nitpick.toml" "$V/$v/"; s="$V/$v/src/span/span.npk"
  case $v in
    statement)  swap "$s" '    CivilDate:d = days_to_date(days) ?| #unreachable();             // M-8' \
                          $'    Result<CivilDate>:d = days_to_date(days);\n    if (d.is_error) { #unreachable(); }'
                swap "$s" $'                             t.nanos => int64) ?| #unreachable();   // M-7\n    pass CivilDateTime{ date: d, time: c };' \
                          $'                             t.nanos => int64);\n    if (c.is_error) { #unreachable(); }\n    pass CivilDateTime{ date: d.value, time: c.value };'
                swap "$s" '    CivilTime:c = civil_time(' '    Result<CivilTime>:c = civil_time(' ;;
    bang)       swap "$s" 'days_to_date(days) ?| #unreachable();' 'days_to_date(days) ?! Unreachable;  '
                swap "$s" 't.nanos => int64) ?| #unreachable();' 't.nanos => int64) ?! Unreachable;  ' ;;
    truncating) swap "$s" $'    if (sod < 0i64) {                                // `/` truncates: floor it\n        days = days - 1i64;\n        sod = sod + NTIME_SECS_PER_DAY;\n    }\n' '' ;;
  esac
  echo "span.npk, $v: $(diag "$V/$v/src/span" span.npk | sed 's/^span.npk: //')"
done
( cd "$P/src/span" && "$NPKC" span.npk -o "$P/span.ll" ) && ( cd "$V/bang/src/span" && "$NPKC" span.npk -o "$P/span_bang.ll" )
python3 - "$P/span.ll" "$P/span_bang.ll" <<'PY'
import re, sys
for path, label in ((sys.argv[1], "?| #unreachable()"), (sys.argv[2], "?! Unreachable")):
    ll = open(path, encoding="utf-8").read()
    body = re.search(r'^define [^\n]*@"npk\.span\.timestamp_to_utc"\(.*?^}', ll, re.S | re.M).group(0)
    print("timestamp_to_utc, %s: %d load(s) of NTIME_SECS_PER_DAY, %d DivByZero trap(s) (-4097), "
          "%d npk_trap(-4102), %d npk_raise(-4102)" % (label,
          body.count('load i64, ptr @"npk.limits.NTIME_SECS_PER_DAY"'), body.count("@npk_trap(i32 -4097)"),
          body.count("@npk_trap(i32 -4102)"), body.count("@npk_raise(i32 -4102)")))
PY
# ---- §1.3 and §1.4: the chain both ways, and the truncation -------------------------
prog m_chain '    for (int64:i in 0i64..7i64) {
        Result<Timestamp>:r = timestamp_of(CS[i], CN[i]);
        if (r.is_error) { exit 10i32; }
        CivilDateTime:c = raw timestamp_to_utc(r.value);
        if ((c.date.year => int64) != WY[i] || (c.date.month => int64) != WM[i]) { exit 11i32; }
        if ((c.date.day => int64) != WD[i] || (c.time.second => int64) != WS[i]) { exit 11i32; }
        if ((c.time.nanos => int64) != CN[i]) { exit 12i32; }
        Result<Timestamp>:b = civil_to_utc(c);
        if (b.is_error) { exit 13i32; }
        if (b.value.secs != CS[i] || (b.value.nanos => int64) != CN[i]) { exit 14i32; }
    }' 'fixed int64[8]:CS = [ -2i64, -1i64, -1i64, -1i64, -1i64, 0i64, 0i64, 1i64 ];
fixed int64[8]:CN = [ 999999999i64, 0i64, 1i64, 500000000i64, 999999999i64, 0i64, 1i64, 0i64 ];
fixed int64[8]:WY = [ 1969i64, 1969i64, 1969i64, 1969i64, 1969i64, 1970i64, 1970i64, 1970i64 ];
fixed int64[8]:WM = [ 12i64, 12i64, 12i64, 12i64, 12i64, 1i64, 1i64, 1i64 ];
fixed int64[8]:WD = [ 31i64, 31i64, 31i64, 31i64, 31i64, 1i64, 1i64, 1i64 ];
fixed int64[8]:WS = [ 58i64, 59i64, 59i64, 59i64, 59i64, 0i64, 0i64, 1i64 ];'
prog m_first '    int64:count = 0i64;
    for (int64:n in NTIME_DAY_MIN..NTIME_DAY_MAX) {
        Result<Timestamp>:r = timestamp_of(n * NTIME_SECS_PER_DAY, 0i64);
        if (r.is_error) { exit 10i32; }
        Result<CivilDate>:d = days_to_date(n);
        if (d.is_error) { exit 11i32; }
        CivilDateTime:c = raw timestamp_to_utc(r.value);
        if (c.date.year != d.value.year || c.date.month != d.value.month || c.date.day != d.value.day) { exit 12i32; }
        count = count + 1i64;
    }
    if (count != 7304484i64) { exit 13i32; }'
legs "$P/tests" m_chain; legs "$P/tests" m_first
mkdir -p "$V/truncating/tests"; cp "$P/tests/m_chain.npk" "$P/tests/m_first.npk" "$V/truncating/tests/"
legs "$V/truncating/tests" m_chain | sed 's/^m_chain:/m_chain, truncating:/'
legs "$V/truncating/tests" m_first | sed 's/^m_first:/m_first, truncating:/'
# ---- §1.5: the sizes, the forge, and a forged `Timestamp` ---------------------------
for ty in CivilDate CivilTime CivilDateTime; do prog "m_size_$ty" "    exit #size_of<$ty>() =>! int32;"; legs "$P/tests" "m_size_$ty"; done
prog m_forge '    wild int8->:md = alloc(#size_of<CivilDate>());
    wild int8->:mt = alloc(#size_of<CivilTime>());
    wild RawDate->:wd = md =>! wild RawDate->;
    <-wd = RawDate{ year: 10000i32, month: 1u8, day: 1u8 };
    wild CivilDate->:rd = md =>! wild CivilDate->;
    CivilDate:cd = <-rd;
    wild RawTime->:wt = mt =>! wild RawTime->;
    <-wt = RawTime{ hour: 23u8, minute: 59u8, second: 59u8, nanos: 1000000000u32 };
    wild CivilTime->:rt = mt =>! wild CivilTime->;
    CivilTime:ct = <-rt;
    dalloc(md);
    dalloc(mt);
    if (cd.year != 10000i32 || cd.month != 1u8 || cd.day != 1u8) { exit 10i32; }
    if (ct.hour != 23u8 || ct.minute != 59u8 || ct.second != 59u8 || ct.nanos != 1000000000u32) { exit 11i32; }
    Result<Timestamp>:a = civil_to_utc(CivilDateTime{ date: cd, time: ct });
    if (!(a.is_error)) { exit 12i32; }
    Result<CivilDate>:ok = civil_date(9999i64, 12i64, 31i64);
    if (ok.is_error) { exit 13i32; }
    Result<Timestamp>:b = civil_to_utc(CivilDateTime{ date: ok.value, time: ct });
    if (!(b.is_error)) { exit 14i32; }' 'struct:RawDate = { int32:year; uint8:month; uint8:day; };
struct:RawTime = { uint8:hour; uint8:minute; uint8:second; uint32:nanos; };'
prog m_forged_ts '    wild int8->:m = alloc(#size_of<Timestamp>());
    wild RawTs->:w = m =>! wild RawTs->;
    <-w = RawTs{ secs: NTIME_SECS_MAX + 1i64, nanos: 0u32 };
    wild Timestamp->:r = m =>! wild Timestamp->;
    Timestamp:t = <-r;
    dalloc(m);
    if (t.secs != NTIME_SECS_MAX + 1i64) { exit 10i32; }
    CivilDateTime:c = raw timestamp_to_utc(t);' 'struct:RawTs = { int64:secs; uint32:nanos; };'
legs "$P/tests" m_forge; legs "$P/tests" m_forged_ts
# ---- §1.6: the bill ---------------------------------------------------------------
cd "$P/tests"
printf 'mod:b_span;\nuse "../src/span/span.npk".*;\nfunc:main = int32(cstring[]:_~argv) {\n    exit 0i32;\n};\n' > b_span.npk
printf 'pub use "./span/span.npk".timestamp_to_utc;\npub use "./span/span.npk".civil_to_utc;\n' >> "$P/src/lib.npk"
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
# ---- §1.7: the 512 days, the program's and a transcription's ----------------------
prog m_days '    uint64:x = 20261001u64;
    for (int64:k in 1i64..512i64) {
        x = x ^ (x << 13u64);
        x = x ^ (x >> 7u64);
        x = x ^ (x << 17u64);
        int64:n = NTIME_DAY_MIN + ((x % 7304484u64) =>! int64);
        string:line = string_concat(int_to_string(n), "\n");
        Result<cstring>:c = to_cstring(line);
        if (c.is_error) { exit 10i32; }
        cstring:s = move(c.value);
        Result<int64>:w = sys(1i64, 1i64, s.ptr, s.len);
        if (w.is_error) { exit 11i32; }
    }'
( cd "$P/tests" && "$NPKC" m_days.npk -o m_days.ll > /dev/null 2>&1 && llc -O0 -filetype=obj -relocation-model=static m_days.ll -o m_days.o \
  && ld.lld -static m_days.o "$NPKRT" -o m_days && ./m_days > m_days.txt; echo "m_days: exit $?, $(wc -l < m_days.txt) line(s)" )
python3 - "$P/tests/m_days.txt" <<'PY'
import datetime, sys
M, DAY_MIN, SPAN = (1 << 64) - 1, -4371587, 7304484
x, mine = 20261001, []
for _ in range(512):
    x ^= (x << 13) & M; x ^= x >> 7; x ^= (x << 17) & M
    mine.append(DAY_MIN + x % SPAN)
got = [int(l) for l in open(sys.argv[1])]
def date(n):
    k = 0
    while n < -719162:
        n += 146097; k += 1
    d = datetime.date(1970, 1, 1) + datetime.timedelta(days=n)
    return "%d-%02d-%02d" % (d.year - 400 * k, d.month, d.day)
print("the 512 days: the program's %s the transcription's; %d distinct, %d before the epoch, from %s to %s"
      % ("equal" if got == mine else "DIFFER FROM", len(set(got)), sum(1 for n in got if n < 0),
         date(min(got)), date(max(got))))
PY
# ---- §1.8: the sixteen vectors, both ways, apart from `cal` --------------------------
python3 - "$T/step3.patch" <<'PY'
import datetime, re, sys
# The tables as `step3.patch` writes them into `tests/unit/utc_vectors.npk`.
patch = open(sys.argv[1], encoding="utf-8").read()
part = patch[patch.index("+++ b/tests/unit/utc_vectors.npk"):]
part = part[:part.find("\ndiff --git") if "\ndiff --git" in part else len(part)]
src = "\n".join(l[1:] for l in part.split("\n") if l.startswith("+") and not l.startswith("+++"))
def table(name):
    body = re.search(r"fixed int64\[16\]:%s\s*=\s*\[(.*?)\];" % name, src, re.S).group(1)
    return [int(v.strip()[:-3]) for v in body.split(",")]
S, N, Y, Mo, D, H, Mi, Se = (table(t) for t in ("SECS", "NANOS", "YEAR", "MONTH", "DAY", "HOUR", "MIN", "SEC"))
E = datetime.datetime(1970, 1, 1)
ok = 0
for i in range(16):
    y, k = Y[i], 0
    while y < 1:
        y += 400; k += 1
    d = datetime.datetime(y, Mo[i], D[i], H[i], Mi[i], Se[i]) - E
    fwd = d.days * 86400 + d.seconds - k * 146097 * 86400
    days, sod = divmod(S[i], 86400)
    k2 = 0
    while days < -719162:
        days += 146097; k2 += 1
    c = datetime.date(1970, 1, 1) + datetime.timedelta(days=days)
    back = (c.year - 400 * k2, c.month, c.day, sod // 3600, sod // 60 % 60, sod % 60)
    ok += fwd == S[i] and back == (Y[i], Mo[i], D[i], H[i], Mi[i], Se[i]) and 0 <= N[i] < 10 ** 9
print("the sixteen vectors: %d of 16 agree both ways with Python's datetime" % ok)
PY
# ---- §1.9: the owner map as it stands, and the glossary's sites ---------------------
python3 -B - "$P" <<'PY'
import os, sys
sys.path.insert(0, os.path.join(sys.argv[1], "harness"))
import checks
for mod in ("cal", "span"):
    t = os.path.join(sys.argv[1], "own_" + mod)
    os.makedirs(os.path.join(t, "src", mod), exist_ok=True)
    open(os.path.join(t, "src", mod, mod + ".npk"), "w").write(
        "mod:%s;\nfunc:f = int64(int64:s) never fails { pass s / 86400i64; };\n" % mod)
    r = checks.check_constants_named(t)
    print("HEAD's map, a literal 86400 in %s: %d finding(s)%s" % (mod, len(r.problems),
          "" if not r.problems else " -- " + r.problems[0].split(" (SAFETY")[0].split("number 86400, ")[1]))
PY
cd "$REPO" && echo "wall, line by line over the live tree: $(git grep -n -I -i 'wall' HEAD -- . ':!meta/roadmap/done' ':!meta/audits' \
  ':!meta/DECISIONS.md' ':!meta/roadmap/0.2/0.2.0a*' ':!meta/roadmap/0.2/0.2.0b*' ':!meta/roadmap/0.2/0.2.0.md' ':!meta/roadmap/0.2/0.2.0_tools' \
  ':!meta/roadmap/0.2/0.2.1*' ':!meta/roadmap/0.2/0.2.2*' ':!meta/scratch' ':!*TRANSCRIPT.txt' | wc -l) line(s)"
python3 - <<'PY'
# A point on the UTC scale called "wall": the phrases read ACROSS line breaks, each
# line's comment marker stripped, over every tracked file but the roadmap and the
# scratch -- `meta/DECISIONS.md` included -- each hit at the line it starts on.
import bisect, re, subprocess
rx = re.compile(r"wall-clock (reading|time|one)|wall_clock_ns|steps the absolute scale", re.I)
mark = re.compile(r"^\s*(?://+|#+|\*|>)?\s?")
files = subprocess.run(["git", "ls-files", "-z", "--", ".", ":!meta/roadmap", ":!meta/scratch",
                        ":!*TRANSCRIPT.txt"], capture_output=True, text=True).stdout.split("\0")
for f in sorted(x for x in files if x):
    raw = open(f, "rb").read()
    if b"\0" in raw:
        continue
    lines = [mark.sub("", l) for l in raw.decode("utf-8", "replace").split("\n")]
    starts, pos = [], 0
    for l in lines:
        starts.append(pos); pos += len(l) + 1
    for m in rx.finditer(" ".join(lines)):
        print("%s:%d" % (f, bisect.bisect_right(starts, m.start())))
PY
