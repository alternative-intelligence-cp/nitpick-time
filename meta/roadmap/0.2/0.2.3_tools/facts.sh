# meta/roadmap/0.2/0.2.3_tools/facts.sh -- `0.2.3.md` §1.8: re-derive §1 at the pin, in a
# scratch copy of the tree, never in it. Sourced after `env.sh`, in one Bash call --
# block 0b of the plan, run BEFORE step 1:
#
#     . "$REPO/meta/roadmap/0.2/0.2.3_tools/env.sh"; . "$T/facts.sh"
#
# It copies `src/`, `harness/`, `meta/specs/` and `nitpick.toml` (a copy takes the
# manifest, or the compiler renders its paths from another root: the compiler's
# D-236), writes §4.2's module over `src/span/span.npk` and §4.3's two ends into
# `src/core/limits.npk` -- EXTRACTED FROM `0.2.3.md`, the first `nitpick` fence after
# each heading -- compiles the module and reads its IR for the `int128`
# multiplication, links a program that calls it against `npkrt.o` alone at -O0 and
# after `opt -O2`, asks `NITPICK-REACH-003` and `harness/arms.py` for the bill and
# `HEAD`'s `check_int128_sites` and `check_constants_named` about the new code; runs
# the constructors at their ends and one past them, the folded minimum, the sequence
# of §1.4 and the sample of §1.5, each at -O0 and after `opt -O2`, and holds the
# last two to a transcription of the same steps in Python; computes `Duration`'s
# ends and the readings they are taken from; and prints P-3's sample and M-19 as
# `HEAD` states them.
: "${REPO:?}" "${NPKC:?}" "${NPKRT:?}" "${W:?}"
P=$W/facts; rm -rf "${P:?}"; mkdir -p "$P/tests" "$P/meta"
cp -r "$REPO/src" "$REPO/harness" "$REPO/nitpick.toml" "$P/"
cp -r "$REPO/meta/specs" "$P/meta/"
python3 - "$REPO/meta/roadmap/0.2/0.2.3.md" "$P" <<'PY'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
def fence(head):
    at = text.index("\n" + head)                 # the heading, at a line's start
    return re.search(r"```nitpick\n(.*?)```", text[at:], re.S).group(1)
open(sys.argv[2] + "/src/span/span.npk", "w", encoding="utf-8").write(fence("### 4.2 "))
lim = sys.argv[2] + "/src/core/limits.npk"
s = open(lim, encoding="utf-8").read()
anchor = "pub fixed int64:NTIME_NANOS_PER_SEC = 1000000000i64;\n"
assert s.count(anchor) == 1
open(lim, "w", encoding="utf-8").write(s.replace(anchor, anchor + "\n" + fence("### 4.3 ")))
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
prog() {   # prog <name> <body> [<more declarations>] -- a consumer of `span` and `limits`
  printf 'mod:%s;\nuse "../src/span/span.npk".*;\nuse "../src/core/limits.npk".*;\nfunc:main = int32(cstring[]:_~argv) {\n%s\n    exit 0i32;\n};\n%s\n%s\n' \
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
# ---- §1.2: the module, its `int128` multiplication, and the libcall it does not need
diag "$P/src/span" span.npk
diag "$P/src/core" limits.npk
( cd "$P/src/span" && "$NPKC" span.npk -o "$P/span.ll" )
python3 - "$P/span.ll" <<'PY'
import re, sys
ll = open(sys.argv[1], encoding="utf-8").read()
body = re.search(r'^define [^\n]*@"npk\.span\.timestamp_since"\(.*?^}', ll, re.S | re.M).group(0)
print("timestamp_since's IR: %d call(s) of llvm.smul.with.overflow.i128, %d of __muloti4; the module's: "
      "%d __muloti4, %d __divti3, %d __modti3"
      % (body.count("call { i128, i1 } @llvm.smul.with.overflow.i128("), body.count("__muloti4"),
         ll.count("__muloti4"), ll.count("__divti3"), ll.count("__modti3")))
PY
prog m_since '    Result<Timestamp>:a = timestamp_of(1i64, 0i64);
    Result<Timestamp>:b = timestamp_of(0i64, 0i64);
    if (a.is_error) { exit 10i32; }
    if (b.is_error) { exit 10i32; }
    Result<Duration>:d = timestamp_since(a.value, b.value);
    if (d.is_error) { exit 11i32; }
    if (d.value.ns != NTIME_NANOS_PER_SEC) { exit 12i32; }'
legs "$P/tests" m_since
echo "m_since's objects, undefined __*ti*: $( (nm -u "$P/tests/m_since.o"; nm -u "$P/tests/m_since.2.o") | grep -c 'ti[34]$')"
echo "npkrt.o defines: $(nm "$NPKRT" | awk '$2 ~ /^[TW]$/ {print $3}' | grep -E '^__(mul|div|mod)ti3$|^__muloti4$' | sort | tr '\n' ' ' | sed 's/ $//')"
# ---- §1.3: the bill, and the instruments 0.2.3a built, over the new code ------------
cd "$P/tests"
printf 'mod:b_span;\nuse "../src/span/span.npk".*;\nfunc:main = int32(cstring[]:_~argv) {\n    exit 0i32;\n};\n' > b_span.npk
echo "b_span: $("$NPKC" b_span.npk -o /dev/null 2>&1 | grep -oE 'NITPICK-REACH-003|[0-9]+ identities: [^-]*' | tr '\n' ' ' | sed 's/ *$//')"
cd "$P" && python3 -B - <<'PY'
import sys
sys.path.insert(0, "harness")
import arms, checks
a, info = arms.compute_bill(".", "src/span/span.npk")
print("compute_bill span.npk: %d -- %s" % (len(a), ", ".join(sorted(x for x in a if "." in x))))
for name in ("check_int128_sites", "check_constants_named"):
    r = getattr(checks, name)(".")
    print("HEAD's %s over it: %d finding(s) -- %s" % (name, len(r.problems), r.headline))
PY
cd "$P/tests"
# ---- §1.4: the constructors at their ends, and one past ----------------------------
prog m_ends '    Duration:a = raw duration_mins(153722867i64);
    if ((a.ns => int128) != 153722867i128 * 60000000000i128) { exit 10i32; }
    a = raw duration_mins(0i64 - 153722867i64);
    if ((a.ns => int128) != (0i128 - 153722867i128) * 60000000000i128) { exit 10i32; }
    a = raw duration_hours(2562047i64);
    if ((a.ns => int128) != 2562047i128 * 3600000000000i128) { exit 11i32; }
    a = raw duration_hours(0i64 - 2562047i64);
    if ((a.ns => int128) != (0i128 - 2562047i128) * 3600000000000i128) { exit 11i32; }
    a = raw duration_days(106751i64);
    if ((a.ns => int128) != 106751i128 * 86400000000000i128) { exit 12i32; }
    a = raw duration_days(0i64 - 106751i64);
    if ((a.ns => int128) != (0i128 - 106751i128) * 86400000000000i128) { exit 12i32; }
    a = raw duration_weeks(15250i64);
    if ((a.ns => int128) != 15250i128 * 604800000000000i128) { exit 13i32; }
    a = raw duration_weeks(0i64 - 15250i64);
    if ((a.ns => int128) != (0i128 - 15250i128) * 604800000000000i128) { exit 13i32; }'
legs "$P/tests" m_ends
for c in "mins 153722868" "hours 2562048" "days 106752" "weeks 15251"; do
  set -- $c
  prog "m_past_$1_hi" "    Duration:d = raw duration_$1($2i64);
    if (d.ns > 0i64) { exit 10i32; }
    exit 11i32;"
  prog "m_past_$1_lo" "    Duration:d = raw duration_$1(0i64 - $2i64);
    if (d.ns > 0i64) { exit 10i32; }
    exit 11i32;"
  legs "$P/tests" "m_past_$1_hi"; legs "$P/tests" "m_past_$1_lo"
done
python3 - <<'PY'
M = (1 << 63) - 1
for unit, ns in (("minute", 60 * 10**9), ("hour", 3600 * 10**9), ("day", 86400 * 10**9), ("week", 604800 * 10**9)):
    print("the %s's largest argument: %d; one more is %s int64" % (unit, M // ns, "past" if (M // ns + 1) * ns > M else "INSIDE"))
print("every minute: %d arguments; a stride of 262 divides 2 x 153722867 into %d steps, remainder %d"
      % (2 * 153722867 + 1, (2 * 153722867) // 262, (2 * 153722867) % 262))
PY
# ---- §1.5: the folded minimum, and the sequence of additions -----------------------
prog m_fixed '    if (NTIME_DURATION_NS_MAX != (((~0u64) >> 1u64) =>! int64)) { exit 10i32; }
    if (NTIME_DURATION_NS_MIN != ((0i64 - NTIME_DURATION_NS_MAX) - 1i64)) { exit 11i32; }
    if ((NTIME_DURATION_NS_MIN + 1i64) != (0i64 - NTIME_DURATION_NS_MAX)) { exit 12i32; }'
legs "$P/tests" m_fixed
SAY='    string:line = string_concat(text, "\n");
    Result<cstring>:c = to_cstring(line);
    if (c.is_error) { exit 20i32; }
    cstring:s = move(c.value);
    Result<int64>:w = sys(1i64, 1i64, s.ptr, s.len);
    if (w.is_error) { exit 21i32; }'
prog m_seq "    int128:lo = (NTIME_SECS_MIN => int128) * (NTIME_NANOS_PER_SEC => int128);
    int128:hi = ((NTIME_SECS_MAX => int128) * (NTIME_NANOS_PER_SEC => int128)) + ((NTIME_NANOS_PER_SEC - 1i64) => int128);
    Result<Timestamp>:t0 = timestamp_of(0i64, 0i64);
    if (t0.is_error) { exit 10i32; }
    Timestamp:t = t0.value;
    uint64:x = 20261001u64;
    int64:acc = 0i64;
    int64:above = 0i64;
    int64:below = 0i64;
    for (int64:k in 1i64..100000i64) {
        x = x ^ (x << 13u64);
        x = x ^ (x >> 7u64);
        x = x ^ (x << 17u64);
        int64:dn = x =>! int64;
        if ((k % 2i64) == 0i64) { dn = ((x % 2000000000u64) =>! int64) - 1000000000i64; }
        int128:want = ((t.secs => int128) * (NTIME_NANOS_PER_SEC => int128)) + (t.nanos => int128) + (dn => int128);
        Result<Timestamp>:r = timestamp_add(t, raw duration_ns(dn));
        if (r.is_error) {
            if (want > hi) { above = above + 1i64; } else { below = below + 1i64; }
        } else {
            t = r.value;
            acc = acc + 1i64;
        }
    }
    string:text = string_concat(string_concat(string_concat(int_to_string(acc), \" \"),
                      string_concat(int_to_string(above), \" \")),
                      string_concat(string_concat(int_to_string(below), \" \"),
                      string_concat(string_concat(int_to_string(t.secs), \" \"), int_to_string(t.nanos => int64))));
$SAY"
( cd "$P/tests" && "$NPKC" m_seq.npk -o m_seq.ll > /dev/null 2>&1 && llc -O0 -filetype=obj -relocation-model=static m_seq.ll -o m_seq.o \
  && ld.lld -static m_seq.o "$NPKRT" -o m_seq && ./m_seq > m_seq.txt; e0=$?
  opt -O2 -S m_seq.ll -o m_seq.2.ll && llc -O2 -filetype=obj -relocation-model=static m_seq.2.ll -o m_seq.2.o \
  && ld.lld -static m_seq.2.o "$NPKRT" -o m_seq.2 && ./m_seq.2 > m_seq.2.txt
  echo "m_seq: exit $e0 at -O0, $? after opt -O2; the two legs print $(cmp -s m_seq.txt m_seq.2.txt && echo the same || echo DIFFERENT)" )
python3 - "$P/tests/m_seq.txt" <<'PY'
import sys
M, E9 = (1 << 64) - 1, 10**9
lo, hi = -377705116800 * E9, 253402300799 * E9 + E9 - 1
x, t = 20261001, 0
acc = ref = above = below = carries = borrows = 0
for k in range(1, 100001):
    x ^= (x << 13) & M; x ^= x >> 7; x ^= (x << 17) & M
    dn = x - (1 << 64) if x >= 1 << 63 else x
    if k % 2 == 0:
        dn = x % 2000000000 - 1000000000
    nanos = t % E9
    q = abs(dn) // E9 * (1 if dn >= 0 else -1)          # `/` truncates toward zero
    n2 = nanos + (dn - q * E9)
    if lo <= t + dn <= hi:
        acc += 1; t += dn; carries += n2 >= E9; borrows += n2 < 0
    else:
        ref += 1; above += t + dn > hi; below += t + dn < lo
mine = "%d %d %d %d %d" % (acc, above, below, t // E9, t % E9)
got = open(sys.argv[1]).read().strip()
print("the sequence: the program's %s the transcription's -- %d answered, %d refused, %d above the range "
      "and %d below; %d carries and %d borrows among the answered; the last (%d s, %d ns)"
      % ("equal" if got == mine else "DIFFER FROM", acc, ref, above, below, carries, borrows, t // E9, t % E9))
PY
# ---- §1.6: `Duration`'s ends, the readings they are taken from, and the sample -----
prog m_sample "    uint64:span = ((NTIME_SECS_MAX - NTIME_SECS_MIN) + 1i64) =>! uint64;
    int128:wmax = NTIME_DURATION_NS_MAX => int128;
    int128:wmin = NTIME_DURATION_NS_MIN => int128;
    uint64:x = 20261001u64;
    int64:answered = 0i64;
    int64:refused = 0i64;
    for (int64:k in 1i64..100000i64) {
        x = raw step(x);
        int64:es = NTIME_SECS_MIN + ((x % span) =>! int64);
        x = raw step(x);
        int64:en = (x % 1000000000u64) =>! int64;
        x = raw step(x);
        int64:off = ((x % 37869120001u64) =>! int64) - 18934560000i64;
        int64:ls = es + off;
        if (ls < NTIME_SECS_MIN || ls > NTIME_SECS_MAX) { ls = es - off; }
        x = raw step(x);
        int64:ln = (x % 1000000000u64) =>! int64;
        Result<Timestamp>:a = timestamp_of(ls, ln);
        Result<Timestamp>:b = timestamp_of(es, en);
        if (a.is_error) { exit 10i32; }
        if (b.is_error) { exit 10i32; }
        Result<Duration>:d = timestamp_since(a.value, b.value);
        if (d.is_error) { refused = refused + 1i64; } else { answered = answered + 1i64; }
    }
    string:text = string_concat(string_concat(int_to_string(answered), \" \"), int_to_string(refused));
$SAY" 'func:step = uint64(uint64:x0) never fails {
    uint64:x = x0 ^ (x0 << 13u64);
    x = x ^ (x >> 7u64);
    pass x ^ (x << 17u64);
};'
( cd "$P/tests" && "$NPKC" m_sample.npk -o m_sample.ll > /dev/null 2>&1 && llc -O0 -filetype=obj -relocation-model=static m_sample.ll -o m_sample.o \
  && ld.lld -static m_sample.o "$NPKRT" -o m_sample && ./m_sample > m_sample.txt; e0=$?
  opt -O2 -S m_sample.ll -o m_sample.2.ll && llc -O2 -filetype=obj -relocation-model=static m_sample.2.ll -o m_sample.2.o \
  && ld.lld -static m_sample.2.o "$NPKRT" -o m_sample.2 && ./m_sample.2 > m_sample.2.txt
  echo "m_sample: exit $e0 at -O0, $? after opt -O2; the two legs print $(cmp -s m_sample.txt m_sample.2.txt && echo the same || echo DIFFERENT)" )
python3 - "$P/tests/m_sample.txt" <<'PY'
import sys
M, E9 = (1 << 64) - 1, 10**9
LO, HI, SIX = -377705116800, 253402300799, 18934560000
DMAX, DMIN = (1 << 63) - 1, -(1 << 63)
def step(x):
    x ^= (x << 13) & M; x ^= x >> 7
    return x ^ ((x << 17) & M)
x, ans, ref = 20261001, 0, 0
for _ in range(100000):
    x = step(x); es = LO + x % (HI - LO + 1)
    x = step(x); en = x % E9
    x = step(x); off = x % (2 * SIX + 1) - SIX
    ls = es + off if LO <= es + off <= HI else es - off
    x = step(x); ln = x % E9
    d = (ls - es) * E9 + (ln - en)
    ans += DMIN <= d <= DMAX; ref += not DMIN <= d <= DMAX
got = open(sys.argv[1]).read().strip()
print("the sample: the program's %s the transcription's -- %d answered, %d refused"
      % ("equal" if got == "%d %d" % (ans, ref) else "DIFFER FROM", ans, ref))
print("six hundred years: 600 x 365.25 x 86 400 = %d s; the range's seconds differ by at most %d, times 10^9 %.1e"
      % (600 * 36525 * 864, HI - LO, (HI - LO) * 1e9))
smax, nmax = divmod(DMAX, E9)
smin, nmin = divmod(DMIN, E9)
print("Duration's ends: %d s + %d ns above, %d s + %d ns below" % (smax, nmax, smin, nmin))
bs = HI - smax - 1
print("the maximum from (%d s, 999999999 ns) lands on (%d s, %d ns), the range's last second: %s"
      % (bs, *divmod(bs * E9 + E9 - 1 + DMAX, E9), divmod(bs * E9 + E9 - 1 + DMAX, E9)[0] == HI))
bs = LO - smin
print("the minimum from (%d s, 0 ns) lands on (%d s, %d ns), the range's first second: %s"
      % (bs, *divmod(bs * E9 + DMIN, E9), divmod(bs * E9 + DMIN, E9)[0] == LO))
print("int128 holds every difference two int64 seconds and two uint32 nanos can make: %s"
      % (((1 << 64) * E9 + (1 << 32)) < (1 << 127)))
PY
# ---- §1.7 and §1.8: P-3's sample, M-19 and §9, as `HEAD` states them -----------------
cd "$REPO"
echo "P-3's timestamp_add sample: $(grep -A3 '^pub func:timestamp_add' meta/specs/VERIFICATION.md | sed -n '2,4p' | tr -s ' ' | tr '\n' ';' | sed 's/;$//')"
echo "M-19: $(grep -m1 '^\*\*Rule M-19' meta/specs/TIME_MODEL.md | cut -c1-90)"
echo "§9's timestamp_until row: $(grep -m1 '| `timestamp_until` |' meta/specs/TIME_MODEL.md | tr -s ' ')"
echo "cycle 0.7.3's date_until item: $(grep -c '^- \[ \] `date_until(a, b, unit)`' meta/roadmap/0.7/README.md)"
