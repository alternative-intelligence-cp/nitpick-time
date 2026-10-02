# meta/roadmap/0.2/0.2.3a_tools/facts.sh -- `0.2.3a.md` §1.9: re-derive §1 at the pin,
# in a scratch copy of the tree, never in it. Sourced after `env.sh`, in one Bash
# call -- block 0b of the plan, run BEFORE step 1:
#
#     . "$REPO/meta/roadmap/0.2/0.2.3a_tools/env.sh"; . "$T/facts.sh"
#
# It reads the tree as it stands -- the plan's commit -- with readers of its own,
# none of them the code the steps add: the family's four statements, the result
# type of every function in `src/`, every `int128` in `src/` and §5's table, and
# `HEAD`'s `check_constants_named` over a plant of every spelling of an owned
# number. It compiles one program of every spelling and runs it on both legs, so
# the values are the pinned compiler's; and it reads `meta/scratch/github.txt` and
# the live GitHub description, through `gh`.
: "${REPO:?}" "${NPKC:?}" "${NPKRT:?}" "${W:?}"
P=$W/facts; rm -rf "${P:?}"; mkdir -p "$P"
cp -r "$REPO/src" "$REPO/harness" "$REPO/nitpick.toml" "$P/"
# ---- §1.2: the family's four statements, read apart ------------------------------
python3 -B - "$REPO" <<'PY'
import ast, os, re, sys
root = sys.argv[1]
doc = open(os.path.join(root, "meta/specs/TESTING.md"), encoding="utf-8").read().split("\n")
s2 = doc.index(next(l for l in doc if l.startswith("## 2. ")))
s3 = next(i for i in range(s2 + 1, len(doc)) if doc[i].startswith("## "))
rows, pend, table = [], {}, None
for l in doc[s2:s3]:
    if not l.startswith("|"):
        table = None
        continue
    cells = [c.strip() for c in l.strip().strip("|").split("|")]
    if table is None:
        table = cells[0]
        continue
    m = re.match(r"^\|\s*`([a-z_0-9]+)`", l)
    if m and table == "Check":
        rows.append(m.group(1))
    elif m and table == "Pending":
        pend[m.group(1)] = cells[1]
ck = ast.parse(open(os.path.join(root, "harness/checks.py")).read())
live = pending = None
for n in ck.body:
    if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name):
        if n.targets[0].id == "LIVE":
            live = [e.id for e in n.value.elts]
        if n.targets[0].id == "PENDING":
            pending = {e.elts[0].value: e.elts[1].value for e in n.value.elts}
defs = set()
for f in ("checks.py", "arms.py", "run.py"):
    t = ast.parse(open(os.path.join(root, "harness", f)).read())
    defs |= {n.name for n in ast.walk(t) if isinstance(n, ast.FunctionDef) and n.name.startswith("check_")}
rt = ast.parse(open(os.path.join(root, "harness/run.py")).read())
calls = []
for n in ast.walk(rt):
    if isinstance(n, ast.Call):
        f = n.func
        nm = f.id if isinstance(f, ast.Name) else getattr(f, "attr", None)
        if nm and (nm in rows or nm in defs) and nm not in calls:
            calls.append(nm)
print("the family: %d row(s) in §2 = %d in LIVE + %d driven by run.py (%s) + %d pending; "
      "the pending table %s checks.PENDING, names and cycles"
      % (len(rows), len(live), len(calls), ", ".join(sorted(calls)), len(pending),
         "equals" if pend == pending else "DIFFERS FROM"))
print("rows nothing runs: %d; checks run with no row: %d"
      % (len([r for r in rows if r not in live and r not in pending and r not in calls]),
         len([c for c in live + calls + list(pending) if c not in rows])))
PY
# ---- §1.3: what `src/`'s functions return ---------------------------------------
python3 -B - "$P" <<'PY'
import os, re, sys
sys.path.insert(0, os.path.join(sys.argv[1], "harness"))
import checks, lexical
W = r"[ \t\r\n]"
FUNC = re.compile(r"(?<![A-Za-z0-9_.])func%s*:%s*([A-Za-z_][A-Za-z0-9_]*)%s*(<[^=]*>)?%s*=%s*([^(]*)\("
                  % (W, W, W, W, W))
n, views = 0, []
for rel in checks.src_files(sys.argv[1]):
    code = checks.blank_code(lexical.read(os.path.join(sys.argv[1], rel)))
    for m in FUNC.finditer(code):
        n += 1
        t = "".join(m.group(3).split())
        if t.endswith("[]") or t == "cstring" or "[]" in t:
            views.append("%s %s" % (m.group(1), t))
fields = []
for name, fl in checks._structs(sys.argv[1], checks.src_files(sys.argv[1])).items():
    for rel, ln, ftext in fl:
        ft = checks._field_type(ftext)
        if ft.endswith("[]") or ft == "cstring":
            fields.append(name)
print("src/'s functions: %d, returning a slice or a cstring: %s; struct fields that are one: %d"
      % (n, ", ".join(views) or "none", len(fields)))
PY
# ---- §1.4: `int128` in `src/`, and §5's table ------------------------------------
python3 -B - "$P" "$REPO" <<'PY'
import os, re, sys
sys.path.insert(0, os.path.join(sys.argv[1], "harness"))
import checks, lexical
hits = []
for rel in checks.src_files(sys.argv[1]):
    code = checks.blank_code(lexical.read(os.path.join(sys.argv[1], rel)))
    for m in re.finditer(r"(?<![A-Za-z0-9_])int128(?![A-Za-z0-9_])", code):
        line = code[:m.start()].count("\n") + 1
        hits.append("%s:%d `%s`" % (rel, line, " ".join(code.split("\n")[line - 1].split())[:60]))
print("int128 in src/'s code: %d -- %s" % (len(hits), "; ".join(hits)))
doc = open(os.path.join(sys.argv[2], "meta/specs/SPAN_MODEL.md"), encoding="utf-8").read().split("\n")
s5 = doc.index(next(l for l in doc if l.startswith("## 5.")))
rows = [l for l in doc[s5:s5 + 30] if l.startswith("| `") or l.startswith("| ISO")]
print("§5's table: %d rows; its Answer says `int128` in %d -- %s; a row names `timestamp_to_civil`: %s"
      % (len(rows), len([r for r in rows if "`int128`" in r]),
         "; ".join(r.split("|")[1].strip() for r in rows if "`int128`" in r),
         any("timestamp_to_civil" in r for r in rows)))
PY
# ---- §1.5: every spelling, to the compiler and to `HEAD`'s check ------------------
FS='func:failsafe = int32(Error:e) {
    pick (e) {
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
        (*)                 { exit 99i32; }
    }
    exit 9i32;
};'
mkdir -p "$P/tests"
cat > "$P/tests/m_spellings.npk" <<EOF
mod:m_spellings;
func:main = int32(cstring[]:_~argv) {
    int64:d = 86400i64;
    int64:g = 1000000000i64;
    if (86_400i64 != d) { exit 10i32; }
    if (86__400i64 != d) { exit 11i32; }
    if (86400_i64 != d) { exit 12i32; }
    if (086400i64 != d) { exit 13i32; }
    if (15180hexi64 != d) { exit 14i32; }
    if (10101000110000000bini64 != d) { exit 15i32; }
    if (250600octi64 != d) { exit 16i32; }
    if (1111TTTT000ti64 != d) { exit 17i32; }
    if (142dc0ni64 != d) { exit 18i32; }
    if ((86400i128 =>! int64) != d) { exit 19i32; }
    if (1_000_000_000i64 != g) { exit 20i32; }
    if (3B9ACA00hexi64 != g) { exit 21i32; }
    if (7346545000octi64 != g) { exit 22i32; }
    if (111011100110101100101000000000bini64 != g) { exit 23i32; }
    if ((1000000000i128 =>! int64) != g) { exit 24i32; }
    if (01000000000i64 != g) { exit 25i32; }
    if (86400hexi64 != 549888i64) { exit 26i32; }
    if (('\u{15180}' => int64) != d) { exit 27i32; }
    int64:last = 0i64;
    for (int64:k in 0i64...86400i64) { last = k; }
    if (last != 86399i64) { exit 28i32; }
    exit 0i32;
};
$FS
EOF
( cd "$P/tests" && "$NPKC" m_spellings.npk -o m_spellings.ll > /dev/null 2>&1 \
  && llc -O0 -filetype=obj -relocation-model=static m_spellings.ll -o m.o && ld.lld -static m.o "$NPKRT" -o m && ./m; e0=$?
  opt -O2 -S m_spellings.ll -o m2.ll && llc -O2 -filetype=obj -relocation-model=static m2.ll -o m2.o \
  && ld.lld -static m2.o "$NPKRT" -o m2 && ./m2; echo "every spelling, compiled: exit $e0 at -O0, $? after opt -O2" )
python3 -B - "$P" <<'PY'
import os, shutil, sys
sys.path.insert(0, os.path.join(sys.argv[1], "harness"))
import checks
SPELLINGS = ["86400i64", "86_400i64", "86__400i64", "86400_i64", "086400i64", "15180hexi64",
             "10101000110000000bini64", "250600octi64", "1111TTTT000ti64", "142dc0ni64", "86400i128",
             "('\\u{15180}' => int64)", "1_000_000_000i64", "01000000000i64", "3B9ACA00hexi64",
             "7346545000octi64", "111011100110101100101000000000bini64", "1000000000i128"]
OTHER = [("for (int64:k in 0i64...86400i64) { discard(k); }", "after `...`"),
         ("for (int64:k in 1i64..86400i64) { discard(k); }", "after `..`"),
         ("if (86400i64 > s) { pass 0i64; }", "left of a comparison"),
         ("int64:h = 86400hexi64;", "549 888, not 86 400"),
         ("string:t = \"86400\";", "a string's text")]
base = os.path.join(sys.argv[1], "plants")
def run(body):
    t = os.path.join(base, str(run.k)); run.k += 1
    shutil.rmtree(t, ignore_errors=True)
    os.makedirs(os.path.join(t, "src", "span"))
    open(os.path.join(t, "src", "span", "span.npk"), "w").write("mod:span;\n" + body + "\n")
    return len(checks.check_constants_named(t).problems)
run.k = 0
seen = [s for s in SPELLINGS if run("func:f = int64(int64:s) never fails { pass s / %s; };" % s)]
unseen = [s for s in SPELLINGS if s not in seen]
print("HEAD's check over each spelling in `span`: %d seen -- %s" % (len(seen), ", ".join(seen)))
print("  %d unseen -- %s" % (len(unseen), ", ".join(unseen)))
for body, what in OTHER:
    print("  %s: %s" % (what, "a finding" if run("func:f = int64(int64:s) never fails {\n    %s\n    pass s;\n};" % body)
                        else "unseen"))
PY
# ---- §1.7: the owner of 1 000 000 000 ---------------------------------------------
python3 -B - "$P" <<'PY'
import os, shutil, sys
sys.path.insert(0, os.path.join(sys.argv[1], "harness"))
import checks, lexical
occ = []
for rel in checks.src_files(sys.argv[1]):
    code = checks.strip_comments(lexical.read(os.path.join(sys.argv[1], rel)))
    for m in checks._NUMBER.finditer(code):
        if m.group(1) in checks.CONSTANT_OWNER:
            occ.append("%s %s" % (rel.split("/")[-1], m.group(1)))
print("HEAD's owned occurrences in src/: %d -- %s" % (len(occ), ", ".join(occ)))
for mod in ("cal", "span"):
    t = os.path.join(sys.argv[1], "own_" + mod)
    shutil.rmtree(t, ignore_errors=True)
    os.makedirs(os.path.join(t, "src", mod))
    open(os.path.join(t, "src", mod, mod + ".npk"), "w").write(
        "mod:%s;\nfunc:f = int64(int64:n) never fails { pass n / 1000000000i64; };\n" % mod)
    r = checks.check_constants_named(t)
    print("HEAD's map, a literal 1000000000 in %s: %d finding(s)" % (mod, len(r.problems)))
PY
grep -n 'NTIME_NANOS_PER_SEC' "$REPO/src/cal/cal.npk" "$REPO/src/span/span.npk" | grep -v '^[^:]*:[0-9]*: *//' \
  | sed -E 's|^.*/(src/[a-z]+/[a-z]+\.npk):([0-9]+):.*$|\1:\2|' | tr '\n' ' ' | sed 's/ $/\n/;s/^/NTIME_NANOS_PER_SEC read by name, outside comments: /'
# ---- §1.8: the GitHub note and the live description -------------------------------
python3 -B - "$REPO" <<'PY'
import json, os, subprocess, sys
lines = open(os.path.join(sys.argv[1], "meta/scratch/github.txt"), encoding="utf-8").read().split("\n")
r = subprocess.run(["gh", "repo", "view", "alternative-intelligence-cp/nitpick-time", "--json",
                    "description,repositoryTopics"], capture_output=True, text=True)
live = json.loads(r.stdout)
desc = live["description"]
topics = sorted(t["name"] for t in live["repositoryTopics"])
top = next(i for i, l in enumerate(lines) if l.startswith("--- topics"))
nxt = next(i for i in range(top + 1, len(lines)) if lines[i].startswith("---"))
mine = sorted(l for l in lines[top + 1:nxt] if l)
print("github.txt line 4: %r" % lines[3])
print("github.txt line 5: %d characters, the live description: %d, ending %r; equal: %s"
      % (len(lines[4]), len(desc), desc[-56:], lines[4] == desc))
print("topics: the note's %d and the live %d, equal as sets: %s" % (len(mine), len(topics), mine == topics))
PY
