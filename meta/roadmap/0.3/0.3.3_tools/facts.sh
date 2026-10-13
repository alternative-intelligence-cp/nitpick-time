# meta/roadmap/0.3/0.3.3_tools/facts.sh -- `0.3.3.md` §1: re-derive what this plan rests on, at the pin, in scratch
# copies of the tree, never in it. Sourced after `env.sh`, in one Bash call -- block 0b of the plan, run BEFORE
# step 1:
#
#     . "$REPO/meta/roadmap/0.3/0.3.3_tools/env.sh"; . "$T/facts.sh"
#
# §1.2's note is asked form by form, every sentence of it -- the two shapes whose legs disagree built at both legs.
#
# `head` is the working tree as it stands; `new` is it with steps 1 ... 4 applied, each by GNU `patch` into the
# copy alone (`git apply` run inside this checkout would resolve the paths against the checkout), dated as
# `apply.py` dates them. Programs live in `$F/p`, outside every copy, but for the ones that import the double, which
# sit in the copy's `tests/unit/`; each is built and run at the pin, both legs. A check is asked of its OWN tree's
# harness. Everything here is removed at the end.
: "${REPO:?}" "${A:?}" "${T:?}" "${PIN:?}" "${NPKC:?}" "${NPKRT:?}" "${NTIME_RUN_DATE:?}"
F=$A/facts
fresh() {   # fresh <name> [<step>...]: the working tree as it stands at $F/<name>, then each step's patch
  local d=$1 n; shift
  mkdir -p "$F/$d"
  ( cd "$REPO" && git ls-files -co --exclude-standard -z | xargs -0 tar -cf - ) | tar -xf - -C "$F/$d"
  for n in "$@"; do
    sed "s/@@DATE033@@/$NTIME_RUN_DATE/g" "$T/step$n.patch" | patch -p1 -s --no-backup-if-mismatch -d "$F/$d" \
      || echo "STOP: step$n does not apply to a copy of the tree"
  done
}
codes() {   # codes <dir> <name>: compile <dir>/<name>.npk as a root; its codes and sites, or `compiles`
  local out
  out=$(cd "$1" && "$NPKC" "$2.npk" -o /dev/null 2>&1)
  if [ -z "$out" ]; then echo "compiles"; return; fi
  echo "$out" | grep -oE '^NITPICK-[A-Z]+-[0-9]+ [^ ]+:[0-9]+:[0-9]+' | sed -E 's| ([^ ]*/)?[^/ ]+\.npk:| |' \
    | tr '\n' ' ' | sed 's/ $//'
}
FLOOR='func:failsafe = int32(Error:e) {
    pick (e) {
        (HeapBadRequest)    { exit 91i32; },
        (HeapOom)           { exit 92i32; },
        (Unreachable)       { exit 95i32; },
        (WildLeak)          { exit 96i32; },
        (StackExhausted)    { exit 106i32; },
        (MachineFault)      { exit 107i32; },
        (*)                 { exit 99i32; }
    }
    exit 9i32;
};'
probe() {   # probe <name> <body of main>, and any declarations before it on stdin: a program in $F/p
  { printf 'mod:%s;\n\n' "$1"; cat; printf 'func:main = int32(cstring[]:_~argv) {\n%s\n};\n\n%s\n' "$2" "$FLOOR"; } \
    > "$F/p/$1.npk"
}

rm -rf "${F:?}"; mkdir -p "$F/p"
fresh head; fresh new 1 2 3 4

# ---- §1.2 what a module can keep between two calls -------------------------------------------------------------
echo "§1.2 a module's state, each asked of the pin as a program of its own:"
probe state_plain '    exit 0i32;' <<'EOF'
int64:counter = 0i64;

EOF
probe state_fixed_part '    drop set(5i64);
    exit 0i32;' <<'EOF'
fixed int64[1]:S = [0i64];

func:set = NIL(int64:v) never fails {
    S[0i64] = v;
    pass NIL;
};

EOF
probe state_call_init '    exit 0i32;' <<'EOF'
fixed buffer:B = buffer_new(16i64);

EOF
probe state_atomic_bare '    exit 0i32;' <<'EOF'
fixed atomic<int64>:A;

EOF
probe state_atomic_literal '    exit 0i32;' <<'EOF'
fixed atomic<int64>:A = 0i64;

EOF
for p in state_plain state_fixed_part state_call_init state_atomic_bare state_atomic_literal; do
  echo "  $p: $(codes "$F/p" "$p")"
done
grep -m1 -oE 'module state is `fixed` \(D-211\): .{0,200}keep mutable process state in `main`.s scope' \
  <(cd "$F/p" && "$NPKC" state_plain.npk -o /dev/null 2>&1) | sed 's/^/  TYPE-055 says: /'

# ---- §1.2's note: every other form, and the two shapes whose legs disagree ---------------------------------------
# Each a program of its own, as above. A form that compiles is built at both legs by `legs`, and what the note says
# of it read off the run and the emission: the exits, `main`'s body after `opt -O2`, and the addresses `nm` gives.
echo "§1.2's note -- every other form, each asked of the pin as a program of its own:"
form() {    # form <name> <declarations> [<body of main>]: the program, then its codes
  printf '%s\n\n' "$2" | probe "$1" "${3:-    exit 0i32;}"
  codes "$F/p" "$1"
}
leg2() {    # leg2 <name>: `<exit> / <exit>` of the program at both legs
  legs "$F/p/$1.npk" | sed 's/^[^:]*: //'
}
echo "  initialised -- stack: $(form n_stack 'stack int64:c = 0i64;'); wild: $(form n_wild 'wild int64:c = 0i64;'); wildx: $(form n_wildx 'wildx int64:c = 0i64;'); pub: $(form n_pub 'pub int64:c = 0i64;'); const: $(form n_const 'const int64:c = 0i64;')"
echo "  a fixed one written whole: $(form n_whole 'fixed int64:C = 0i64;

func:set = NIL(int64:v) never fails {
    C = v;
    pass NIL;
};' '    drop set(5i64);
    exit 0i32;')"
echo "  a field of a fixed struct written: $(form n_field 'struct:P = { int64:x; };
fixed P:Q = P{ x: 0i64 };

func:set = NIL(int64:v) never fails {
    Q.x = v;
    pass NIL;
};' '    drop set(5i64);
    exit 0i32;')"
echo "  its address -- @: $(form n_addr 'fixed int64:C = 0i64;' '    int64->:p = @C;
    exit 0i32;'); \$\$m: $(form n_borrow 'fixed int64:C = 0i64;' '    int64:x = $$m C;
    exit 0i32;')"
echo "  an atomic in a fixed struct: $(form n_ast 'struct:W = { atomic<int64>:a; };
fixed W:X = W{ a: 0i64 };'); .store: $(form n_ast_store 'struct:W = { atomic<int64>:a; };
fixed W:X = W{ a: 0i64 };' '    X.a.store(5i64);
    exit 0i32;'); .load: $(form n_ast_load 'struct:W = { atomic<int64>:a; };
fixed W:X = W{ a: 0i64 };' '    int64:v = X.a.load();
    exit 0i32;')"
echo "  an atomic in a fixed array: $(form n_aar 'fixed atomic<int64>[1]:Y = [0i64];'); .store: $(form n_aar_store 'fixed atomic<int64>[1]:Y = [0i64];' '    Y[0i64].store(5i64);
    exit 0i32;'); .load: $(form n_aar_load 'fixed atomic<int64>[1]:Y = [0i64];' '    int64:v = Y[0i64].load();
    exit 0i32;')"
echo "  a fixed pointer -- = NULL: $(form n_pnull 'fixed int64->:P = NULL;'); wild, = NULL: $(form n_pwnull 'fixed wild int64->:P = NULL;'); = 4096i64: $(form n_pint 'fixed int64->:P = 4096i64;'); = NIL: $(form n_pnil 'fixed int64->:P = NIL;'); = #wild_ptr<int64>(4096i64): $(form n_pwp 'fixed int64->:P = #wild_ptr<int64>(4096i64);'); re-pointed: $(form n_prep 'fixed int64->:P = NULL;' '    P = NULL;
    exit 0i32;')"
echo "  a channel -- its send in a synchronous function: $(form n_send 'Channel<int64, 1, 4>:ch;

func:put = NIL(int64:v) {
    pass (relay (await ch.send(move(v), raw duration_ns(1000i64))));
};'); = channel(): $(form n_chan 'fixed Channel<int64, 1, 4>:ch = channel();')"
bare=0; zero=0
for b in 'int64:counter;' 'struct:P = { int64:x; };
P:counter;' 'stack int64:counter;' 'wild int64:counter;' 'wildx int64:counter;' 'pub int64:counter;' \
         'atomic<int64>:counter;' 'Channel<int64, 1, 4>:counter;'; do
  printf '%s\n\n' "$b" | probe n_bare '    exit 0i32;'
  if ( cd "$F/p" && "$NPKC" n_bare.npk -o n_bare.ll ) > /dev/null 2>&1; then
    bare=$((bare + 1))
    grep -qE '^@"npk\.n_bare\.counter" = constant .* zeroinitializer$' "$F/p/n_bare.ll" && zero=$((zero + 1))
  fi
done
echo "  bare, no initialiser -- int64, a struct, stack, wild, wildx, pub, atomic<int64>, Channel<int64, 1, 4>: $bare of 8 compile, $zero emitted \`constant ... zeroinitializer\`"
printf 'int64:counter;\n\nfunc:set = NIL(int64:v) never fails {\n    counter = v;\n    pass NIL;\n};\n\n' \
  | probe n_wint '    drop set(5i64);
    if (counter != 5i64) { exit 11i32; }
    exit 0i32;'
printf 'struct:P = { int64:x; };\nP:q;\n\n' | probe n_wstruct '    q.x = 5i64;
    if (q.x != 5i64) { exit 11i32; }
    exit 0i32;'
printf 'atomic<int64>:a;\n\n' | probe n_watomic '    a.store(5i64);
    if (a.load() != 5i64) { exit 11i32; }
    exit 0i32;'
echo "  the bare int64 written by a function and read back: $(leg2 n_wint); a bare struct's field: $(leg2 n_wstruct); a bare atomic's .store: $(leg2 n_watomic)"
printf 'fixed int64->:P = NULL;\n\n' | probe n_null '    <-P = 5i64;
    exit 0i32;'
printf '' | probe n_lnull '    int64->:p = NULL;
    <-p = 5i64;
    exit 0i32;'
{ printf 'mod:n_null_helper;\n\nfixed int64->:P = NULL;\n\nfunc:main = int32(cstring[]:_~argv) {\n    <-P = 5i64;\n    exit 0i32;\n};\n\n'
  printf 'func:helper = int32(int32:x) never fails {\n    pass x;\n};\n\n%s\n' "$FLOOR"; } > "$F/p/n_null_helper.npk"
at1() {     # at1 <name> <symbol>: whether `main` and <symbol> share an address in the -O2 binary
  nm "$A/legs/$1.x2" | awk -v s="$2" '$3 == "main" {m = $1} $3 == s {o = $1} END {print (m != "" && m == o) ? "one address" : "apart"}'
}
body() {    # body <name>: `main`'s body after `opt -O2`, its instructions on one line
  awk '/^define .*@main\(/ {on = 1; next} on && /^}/ {exit} on && !/^[a-z0-9_]+:$/ {gsub(/^ +/, ""); printf "%s%s", (n++ ? "; " : ""), $0}' "$A/legs/$1.2.ll"
}
echo "  a store through the fixed NULL pointer: $(leg2 n_null); at -O2 main is \`$(body n_null)\`, main and npk_failsafe at $(at1 n_null npk_failsafe)"
echo "  the same, a never-fails helper declared between main and failsafe: $(leg2 n_null_helper); main and the helper at $(at1 n_null_helper npk.n_null_helper.helper)"
echo "  a store through a local NULL pointer: $(leg2 n_lnull); at -O2 main is \`$(body n_lnull)\`, main and npk_failsafe at $(at1 n_lnull npk_failsafe)"
echo "  the bare int64's write at -O2: main is \`$(body n_wint)\`"

# ---- §1.3 what a `use` line can name ----------------------------------------------------------------------------
echo "§1.3 npkc at the pin:"
git -C "$NPK_TREE" show "$PIN:src/npkc.npk" | grep -m1 -oE 'usage: npkc [^"]*' | sed 's/^/  its source: /'
( cd "$F/p" && "$NPKC" -I ../double state_plain.npk -o /dev/null ) > "$F/flag.txt" 2>&1
echo "  \`npkc -I ../double <root>\`: exit $?, $(head -1 "$F/flag.txt")"

# ---- §1.4 the seam, the double and its three tests, in the patched copy --------------------------------------
echo "§1.4 the double, in the copy holding steps 1 ... 4:"
echo "  its imports: $(grep -oE '^use "[^"]+"' "$F/new/tests/double/host_double.npk" | sed -E 's/^use "(\.\.\/)*//; s/"$//' \
  | sed -E 's|^src/||' | sort | uniq -c | awk '{printf "%s%s x%s", (NR>1?", ":""), $2, $1}')"
printf 'mod:double_bill;\n\nuse "../double/host_double.npk".*;\n\nfunc:main = int32(cstring[]:_~argv) {\n    FakeHost:h = raw fake_host();\n    exit 0i32;\n};\n' \
  > "$F/new/tests/unit/double_bill.npk"
( cd "$F/new/tests/unit" && "$NPKC" double_bill.npk -o /dev/null ) > "$F/bill.txt" 2>&1
echo "  a root importing it, no failsafe: $(grep -oE '^NITPICK-[A-Z]+-[0-9]+' "$F/bill.txt") -- $(grep -oE '[0-9]+ identities: [^-]*' "$F/bill.txt" | sed 's/ $//')"
rm -f "$F/new/tests/unit/double_bill.npk"
( REPO=$F/new legs tests/unit/double_readings.npk tests/unit/double_substitution.npk tests/golden/double_transcript.npk ) \
  | sed 's/^/  /'

# ---- §1.5 the golden, re-derived ---------------------------------------------------------------------------------
python3 -B "$T/oracle.py" > "$F/oracle.txt"
echo "§1.5 the oracle: $(wc -l < "$F/oracle.txt") lines, $(wc -c < "$F/oracle.txt") B; double_transcript.txt: $(cmp -s "$F/oracle.txt" "$F/new/tests/golden/double_transcript.txt" && echo the same bytes || echo DIFFERENT)"

# ---- §1.6 the double's one owner ----------------------------------------------------------------------------------
echo "§1.6 the zone's name replaced N times, NPK_HEAP_STATS:"
for n in 1000 100000; do
  printf 'mod:double_owner;\n\nuse "../double/host_double.npk".*;\nuse "../../src/host/host.npk".ZoneSource;\n\nfunc:main = int32(cstring[]:_~argv) {\n    FakeHost:h = raw fake_host();\n    for (int64:k in 1i64..%di64) {\n        drop fake_set_zone(@h, "Europe/Kyiv", ZoneSource.TzEnvironment);\n    }\n    exit 0i32;\n};\n\n%s\n' \
    "$n" "$(sed -n '/^func:failsafe/,$p' "$F/new/tests/unit/double_readings.npk")" > "$F/new/tests/unit/double_owner.npk"
  ( cd "$F/new/tests/unit" && "$NPKC" double_owner.npk -o "$F/owner.ll" ) > /dev/null 2>&1 \
    && llc -O0 -filetype=obj -relocation-model=static "$F/owner.ll" -o "$F/owner.o" \
    && ld.lld -static "$F/owner.o" "$NPKRT" -o "$F/owner"
  echo "  $n: exit $(env -i NTIME_HARNESS=1 NPK_HEAP_STATS=1 "$F/owner" 2> "$F/owner.err" > /dev/null; echo $?), $(grep -oE 'peak_live=[0-9]+ count=[0-9]+' "$F/owner.err")"
done
rm -f "$F/new/tests/unit/double_owner.npk"

# ---- §1.7 check_layering, before and after; the three plants against each tree's check -----------------------
echo "§1.7 check_layering:"
python3 -B - "$F/head" "$F/new" "$F/plants" <<'PY'
import importlib, os, sys
head, new, base = sys.argv[1:4]
def mods(tree):
    for m in ("checks", "selfcheck", "build", "lexical", "manifest", "arms", "stages", "elf", "toolchain", "repro"):
        sys.modules.pop(m, None)
    sys.path.insert(0, os.path.join(tree, "harness"))
    c, s = importlib.import_module("checks"), importlib.import_module("selfcheck")
    sys.path.pop(0)
    return c, s
hc, _ = mods(head)
nc, ns = mods(new)
for label, chk, tree in (("head", hc, head), ("new", nc, new)):
    r = chk.check_layering(tree)
    print("  %s: %s, %d finding(s)" % (label, r.headline.split("; ", 3)[-1] if label == "new" else
                                       "%s ... %s" % (r.headline.split(";")[0], r.headline.split("; ")[-1]),
                                       len(r.problems)))
rows = [(b, g) for fn, b, g, _ in ns.PLANTED if fn is nc.check_layering and b[0].startswith("tests/double/")]
print("  the self-check's plants of the double: %d; TREE_PLANTS %d" % (len(rows), ns.TREE_PLANTS))
for i, (bad, good) in enumerate(rows):
    red = ns._mini_tree(os.path.join(base, "b%d" % i), [bad])
    green = ns._mini_tree(os.path.join(base, "g%d" % i), [good])
    imp = lambda t: t[1].split("use ", 1)[1].split(".*")[0]
    print("    %-34s head's check: %s; new's: %s;  control %-30s new's: %s" % (
        imp(bad), "finds it" if hc.check_layering(red).problems else "unseen",
        "finds it" if nc.check_layering(red).problems else "unseen", imp(good),
        "silent" if not nc.check_layering(green).problems else "FIRES"))
PY

# ---- §1.8 the documents, each finding where it stands ---------------------------------------------------------
echo "§1.8 the documents, in the tree as it stands:"
at() {      # at <file> <text>: the first line of <file> holding <text>, as `<file>:<line>: <text>`, or `none`
  local n
  n=$(grep -n -m1 -F -- "$2" "$REPO/$1" | cut -d: -f1)
  printf '  %s:%s: %s\n' "$1" "${n:-none}" "$2"
}
at README.md "the host boundary, is in progress — its first"
at README.md "subcycle, the clocks, done on 2026-10-08"
at README.md "every other row is a later cycle"
at README.md "\`clock_gettime\` for the three clocks"
at README.md "# runnable demonstrations, built and run by the harness"
at CLAUDE.md "runnable demonstrations, built and run by the harness"
at CLAUDE.md "none written through — re-spelled at the OLD pin first, which saw no"
at CONTRIBUTING.md "three subcycles done — the clocks (2026-10-08), the purity boundary's"
at CONTRIBUTING.md "**Anything that reads a clock runs forty times**"
at tests/conformance/README.md "imports an umbrella that re-exports nothing"
at tests/conformance/README.md "today costs a"
at tests/conformance/import.npk "\`ETimeZone\` at 0.3"
at meta/specs/TESTING.md "on everything that reads a clock.**"
at meta/specs/TIME_MODEL.md "pub struct:CivilDate     = { int32:year;"
at meta/specs/SPAN_MODEL.md "| checked, \`ETimeValue\`/\`Overflow\` | no |"
at examples/README.md "**built and run by the harness**"
at examples/README.md "The dogfood consumers from cycle 0.7 live here too"
at meta/roadmap/1.0/README.md "| 1.0.3 | **Examples**"
at meta/roadmap/0.7/README.md "not** in this repository's"
at meta/roadmap/0.7/README.md "**Open questions to settle:** Q-4"
at harness/README.md "LLVM row moved at the self-check and then at 35 units"
at harness/run.py "150 = 7 (library) + 99 (suite roots)"
at harness/run.py "of the 159 \`.npk\` files"
echo "  files carrying \`// stress:\`: $(git -C "$REPO" grep -l -E '^// stress:' -- tests | sed -E 's|.*/||; s|\.npk$||' | tr '\n' ' ')"
d=$(grep -n -m1 '^### TM-221 ' "$REPO/meta/DECISIONS.md" | cut -d: -f1)
echo "  TM-221's markers: $(sed -n "$((d+1)),$((d+6))p" "$REPO/meta/DECISIONS.md" | grep -c '^> \*\*') bold marker lines, $(sed -n "$((d+1)),$((d+6))p" "$REPO/meta/DECISIONS.md" | grep -c '^>$') separating line"

# ---- §1.9 the decision log and the questions -------------------------------------------------------------------
dl="$REPO/meta/DECISIONS.md"
last=$(grep -o '^### TM-[0-9]*' "$dl" | tail -1 | cut -d- -f2)
echo "§1.9 decisions: $(grep -c '^### TM-' "$dl") headings, the last TM-$last; in the copy holding steps 1 ... 4: $(grep -c '^### TM-' "$F/new/meta/DECISIONS.md"), the $(grep -o '^### TM-[0-9]*' "$F/new/meta/DECISIONS.md" | cut -d- -f2 | awk -v l="$last" '$1 > l' | wc -l) after TM-$last numbered from it in order: $(grep -o '^### TM-[0-9]*' "$F/new/meta/DECISIONS.md" | cut -d- -f2 | awk -v l="$last" '$1 > l {d = $1 - l; s = s (s ? " " : "") "+" d} END {print s}')"
echo "  open questions: $(grep -E '^### [OQ]-' "$REPO/meta/OPEN_QUESTIONS.md" | grep -vc '~~')"

# ---- §1.10 what the patches add ---------------------------------------------------------------------------------
echo "§1.10 the patches' .npk:"
python3 -B - "$F/new" "$T" <<'PY'
import os, re, sys
new, T = sys.argv[1:3]
sys.path.insert(0, os.path.join(new, "harness"))
import lexical
added = []
for n in (1, 2, 3, 4):
    f = None
    for l in open(os.path.join(T, "step%d.patch" % n), encoding="utf-8"):
        if l.startswith("+++ b/"):
            f = l[6:].strip()
        elif l.startswith("+") and not l.startswith("+++") and f and f.endswith(".npk"):
            added.append((f, l[1:].rstrip("\n")))
files = sorted({f for f, _ in added})
print("  %d added line(s) in %d file(s): %s" % (len(added), len(files), ", ".join(os.path.basename(f) for f in files)))
code = []
for f in files:
    text = lexical.blank(lexical.read(os.path.join(new, f)))
    code.extend((f, l) for l in text.split("\n"))
shapes = [("enum", r"\benum\s*:"), ("macro", r"\bmacro\b|#\w+!"), ("give/fall", r"\b(give|fall)\b"),
          ("frac", r"\bfrac\b"), ("#wild_slice", r"#wild_slice"), ("a plain uint8[]", r"(?<!fixed )uint8\[\]"),
          ("a float", r"\b\d+\.\d+"), ("comptime", r"\bcomptime\b"), ("while", r"\bwhile\b"),
          ("dyn", r"\bdyn\b"), ("#unreachable() in a statement", r"\{\s*#unreachable\(\);"), ("?|", r"\?\|")]
for name, rx in shapes:
    hits = [(f, l) for f, l in code if re.search(rx, l)]
    print("  %-30s %d" % (name, len(hits)))
moves = [l.strip() for f, l in code if "move(" in l]
print("  move( %d: %s" % (len(moves), " | ".join(sorted(set(re.sub(r"\s+", " ", m)[:70] for m in moves)))))
ex = [l.strip() for f, l in code if re.search(r"\bexit\b", l) and not re.search(r"\bexit \d+i32;", l)]
print("  an exit whose operand is no i32 literal: %s" % (" | ".join(sorted(set(ex))) or "none"))
PY
echo "  @@DATE033@@ in the tree as it stands: $(git -C "$REPO" grep -l -F '@@DATE033@@' -- . ':!meta/roadmap/0.3/0.3.3.md' ':!meta/roadmap/0.3/0.3.3_tools' | wc -l) file(s)"
rm -rf "${F:?}"
