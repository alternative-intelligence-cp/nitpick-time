# meta/roadmap/0.3/0.3.4_tools/facts.sh -- block 0b: `0.3.4.md` §1, re-derived from the tree as it stands, the
# compiler's tree at the pin and at the `main` this plan read, and the steps' own patches. Sourced after `env.sh`.
# It WRITES NOTHING in the checkout: every read is `git show`, `git grep`, `grep` or a Python reader under `-B`, and
# the one tool it runs, `archive.py check`, moves and writes nothing. The compiler's tree is read with `git show` and
# `git rev-parse` alone.

say() { printf '%s\n' "$*"; }
R=$REPO
pyread() { python3 -B -c "$1" "$R" "${@:2}"; }

say "§1.1 the tree it starts from:"
say "  decisions: $(grep -c '^### TM-' "$R/meta/DECISIONS.md") headings, the last $(grep -o '^### TM-[0-9]*' "$R/meta/DECISIONS.md" | tail -1 | cut -c5-), the highest by value TM-$(grep -o '^### TM-[0-9]*' "$R/meta/DECISIONS.md" | cut -d- -f2 | sort -n | tail -1)"
say "  open questions: $(grep -E '^### (O-|Q-)' "$R/meta/OPEN_QUESTIONS.md" | grep -v '~~' | grep -v 'NOT THIS REPOSITORY' | sed -E 's/^### ([A-Z]-[A-Z0-9]+).*/\1/' | tr '\n' ' ')"
for f in 0.3.0 0.3.1 0.3.2 0.3.2a 0.3.3; do
  say "  $f: $(head -1 "$R/meta/roadmap/0.3/$f.md" | grep -oE '(DONE|PLANNED|RUNNING) ?\(?[0-9-]*')"
done

say "§1.2 the bytecode: the self-check's child, and what it imports"
say "  $(grep -n 'argv = \[sys.executable' "$R/harness/selfcheck.py" | sed -E 's/ +/ /g')"
say "  the harness's modules beside run.py: $(cd "$R/harness" && ls *.py | grep -v '^run\.py$' | sed 's/\.py$//' | tr '\n' ' ')"

say "§1.3 the documents audit's four findings, each where it stands:"
say "  TA-8  $(grep -n 'span/ .*Duration interop and Period' "$R/README.md" | cut -d: -f1 | sed 's/^/README.md:/') $(grep -n 'span/ .*Duration interop and Period' "$R/CLAUDE.md" | cut -d: -f1 | sed 's/^/CLAUDE.md:/')"
say "  TA-9  $(grep -n 'the one impure module: the clocks and the system-zone discovery |' "$R/meta/specs/README.md" | cut -d: -f1 | sed 's/^/meta\/specs\/README.md:/')"
say "  TA-10 tests/double/host_double.npk:$(grep -n "the compiler's D-211, \"keep mutable" "$R/tests/double/host_double.npk" | cut -d: -f1); meta/DECISIONS.md:$(grep -n "(the compiler's D-211: \*\"module state is" "$R/meta/DECISIONS.md" | cut -d: -f1), under TM-261"
say "        CLAUDE.md:$(grep -n "NITPICK-TYPE-055\`, the compiler's D-211" "$R/CLAUDE.md" | cut -d: -f1) names D-211 and quotes nothing: $(grep -c "keep mutable process state" "$R/CLAUDE.md") line(s) of CLAUDE.md hold the message's words"
say "  TA-11 meta/roadmap/0.3/README.md:$(grep -n "\`double_readings\`' 60 and 61, the belts its header names" "$R/meta/roadmap/0.3/README.md" | cut -d: -f1); the test's header names $(sed -n '/BUT FOUR BELTS/,/62 \.\.\. 66 hold it/p' "$R/tests/unit/double_readings.npk" | grep -oE '\b(40|44|60|61)\b' | sort -un | tr '\n' ' ')as its belts"

say "§1.4 the compiler at the pin, ${PIN}:"
say "  NITPICK-TYPE-055's message holds the quoted words: $(git -C "$NPK_TREE" show "$PIN:src/frontend/type_stmt.npk" | grep -c "keep mutable process state in \`main\`'s scope where it flows through the calls that need it") line(s), citing D-211: $(git -C "$NPK_TREE" show "$PIN:src/frontend/type_stmt.npk" | grep -c 'module state is `fixed` (D-211)')"
d211=$(git -C "$NPK_TREE" show "$PIN:meta/specs/DECISIONS.md" | sed -n '/^## D-211 /,/^## D-212 /p')
say "  D-211's text: $(printf '%s\n' "$d211" | grep -c '^## D-211 ') heading, $(printf '%s' "$d211" | tr '\n' ' ' | grep -o 'mutable process state lives in `main`.s scope and flows explicitly' | wc -l) of \"mutable process state lives in main's scope and flows explicitly\", $(printf '%s' "$d211" | tr '\n' ' ' | grep -o 'where it flows through the calls that need it' | wc -l) of the message's \"where it flows through the calls that need it\""

say "§1.5 the 0.3.3 batch heading:"
say "  $(grep -n '^# Cycle 0.3.3 ' "$R/meta/DECISIONS.md" | cut -c1-60); \"accepted by the orchestrator at the plan's\": line $(awk '/^# Cycle 0.3.3 /{h=1} h && /accepted by the orchestrator at the plan.s/{print NR; exit}' "$R/meta/DECISIONS.md")"

say "§1.6 the compiler's D-341, cycle 0.3's adoption item 4:"
say "  at ${PIN}: $(git -C "$NPK_TREE" show "$PIN:meta/specs/DECISIONS.md" | grep -c '^## D-341 .*SETTLED') heading SETTLED"
say "  at ${MAIN_SEEN}, $(git -C "$NPK_TREE" rev-parse "$MAIN_SEEN"): $(git -C "$NPK_TREE" show "$MAIN_SEEN:meta/specs/DECISIONS.md" | grep -c '^## D-341 .*SETTLED') heading SETTLED; OPEN_DECISIONS \"buffer's indexing is a plan (D-341)\": $(git -C "$NPK_TREE" show "$MAIN_SEEN:meta/roadmap/OPEN_DECISIONS.md" | grep -c "\`buffer\`'s indexing is a plan (D-341)")"
say "  landings ${PIN}..${MAIN_SEEN}: $(git -C "$NPK_TREE" show -s --format=%s "$PIN..$MAIN_SEEN" | grep -c 'landing'), their messages naming D-341: $(git -C "$NPK_TREE" show -s --format=%B "$PIN..$MAIN_SEEN" | grep -c 'D-341')"
say "  src/'s #wild_slice in code, comments and literals blanked: $(pyread '
import os, sys
sys.path.insert(0, os.path.join(sys.argv[1], "harness"))
import lexical
out = []
for f in ("src/core/bytes.npk", "src/core/vec.npk"):
    out.append("%s %d" % (f, lexical.blank(lexical.read(os.path.join(sys.argv[1], f))).count("#wild_slice")))
total = 0
for d, _, fs in os.walk(os.path.join(sys.argv[1], "src")):
    for n in fs:
        if n.endswith(".npk"):
            total += lexical.blank(lexical.read(os.path.join(d, n))).count("#wild_slice")
print(", ".join(out) + "; all of src/ %d" % total)')"

say "§1.7 the gate's clock tests -- every file carrying \`// stress: 40\`, and what it imports from host:"
for f in $(git -C "$R" grep -l '^// stress: 40' -- 'tests/*.npk'); do
  say "  $f: $(grep -cE '^use "\.\./\.\./src/host/host\.npk"|^use "\.\./double/host_double\.npk"' "$R/$f") host use(s)"
done

say "§1.8 cycle 0.4's documents, read against each other:"
say "  0.4 README:$(grep -n '^\*\*Open questions to settle:\*\* O-X4' "$R/meta/roadmap/0.4/README.md" | cut -d: -f1) O-X4 \"to settle\"; :$(grep -n 'check_no_format_string` goes live\*\*' "$R/meta/roadmap/0.4/README.md" | cut -d: -f1) the check live at 0.4.0; :$(grep -n 'Unix seconds, ISO 8601 duration$' "$R/meta/roadmap/0.4/README.md" | cut -d: -f1) the duration among 0.4.1's emitters"
say "  0.7 README:$(grep -n '^| 0.7.0 | \*\*`Period`\*\*.*ISO 8601 duration format' "$R/meta/roadmap/0.7/README.md" | cut -d: -f1) 0.7.0 holds Period and the duration format; :$(grep -n '^- \[ \] `period_to_iso` / `period_parse_iso`' "$R/meta/roadmap/0.7/README.md" | cut -d: -f1) its two functions"
say "  FORMAT_MODEL.md:$(grep -n '^| ISO 8601 duration' "$R/meta/specs/FORMAT_MODEL.md" | cut -d: -f1) F-2's duration row; COMPAT.md:$(grep -n 'ISO 8601 durations.*implemented for `Period`' "$R/meta/specs/COMPAT.md" | cut -d: -f1) \"implemented for Period\""
say "  FORMAT_MODEL.md F-4's FmtPart: $(sed -n '/^pub enum:FmtPart = {/,/^};/p' "$R/meta/specs/FORMAT_MODEL.md" | sed '1d;$d' | sed 's|//.*||' | tr ';' '\n' | sed 's/^ *//;s/ *$//' | grep -vc '^$') variant(s), $(sed -n '/^pub enum:FmtPart = {/,/^};/p' "$R/meta/specs/FORMAT_MODEL.md" | sed 's|//.*||' | grep -o '[A-Za-z0-9_]*([a-z0-9]*)' | tr '\n' ' ')the one with a payload; Layout: $(grep -c '^pub struct:Layout = { Vec<FmtPart>:parts; Bytes:pool; };' "$R/meta/specs/FORMAT_MODEL.md")"
say "  check_no_format_string PENDING: \"layout interpreter\" $(grep -c 'what it needs is the layout interpreter F-5 is' "$R/harness/checks.py") in checks.py, $(grep -c 'needs the layout interpreter F-5 is written against' "$R/meta/specs/TESTING.md") in TESTING.md; layout_lit takes a string in F-4's example: $(grep -c 'drop layout_lit(@l, "-");' "$R/meta/specs/FORMAT_MODEL.md")"
say "  O-X4: \"Open by design until cycle 0.8's benchmark\": $(grep -c "Open by design until cycle 0.8's benchmark" "$R/meta/OPEN_QUESTIONS.md")"
cur=$(grep '^| [^-D]' "$R/meta/research/CURRENCY.md")
say "  CURRENCY.md: $(printf '%s\n' "$cur" | wc -l) row(s); $(printf '%s\n' "$cur" | awk -F'|' '{print $2}' | grep -cE '^ *RFC') a row for an RFC; the rows naming RFC 3339 at all: $(printf '%s\n' "$cur" | grep -c 'RFC 3339'), each for another standard -- $(printf '%s\n' "$cur" | grep 'RFC 3339' | awk -F'|' '{print $2}' | sed -E 's/^ *([A-Za-z0-9 -]{1,10}[A-Za-z0-9]).*/\1/' | tr '\n' ' ')"
say "  src/fmt/fmt.npk's code, comments blanked: $(pyread '
import os, sys
sys.path.insert(0, os.path.join(sys.argv[1], "harness"))
import lexical
print(" ".join(lexical.blank(lexical.read(os.path.join(sys.argv[1], "src/fmt/fmt.npk"))).split()))')"
say "  tags: $(grep -oh '\[\[sweep: \(arms_fmt\|lib_reexports\|family_rows\|family_live\|family_pending\)=[0-9]*\]\]' "$R/meta/specs/SAFETY.md" "$R/src/lib.npk" "$R/meta/specs/TESTING.md" | sed -E 's/\[\[sweep: (.*)\]\]/\1/' | sort -u | tr '\n' ' ')"
say "  hand-ons with no live home -- \"timespec_ns\" in 0.8's README: $(grep -c 'timespec_ns' "$R/meta/roadmap/0.8/README.md"); \"period_add\" in 0.7's: $(grep -c 'period_add' "$R/meta/roadmap/0.7/README.md"); \"fixeduint8\" in 0.4's: $(grep -c 'fixeduint8' "$R/meta/roadmap/0.4/README.md")"
say "  nitpick.toml's golden entry: $(grep -A2 '^name  = "golden"' "$R/nitpick.toml" | tr -s ' ' | tr '\n' ' ')"

say "§1.9 the archive, before anything moves -- archive.py check over the checkout, which writes nothing:"
REPO="$R" python3 -B "$T/archive.py" check | sed 's/^/  /'

say "§1.10 the patches' .npk:"
pyread '
import os, re, sys
sys.path.insert(0, os.path.join(sys.argv[1], "harness"))
import lexical
added = {}
for n in (1, 2, 4):
    f = None
    for line in open(os.path.join(sys.argv[2], "step%d.patch" % n), encoding="utf-8"):
        if line.startswith("+++ b/"):
            f = line[6:].rstrip("\n")
        elif line.startswith("+") and not line.startswith("+++") and f and f.endswith(".npk"):
            added.setdefault(f, []).append(line[1:].rstrip("\n"))
for f, lines in sorted(added.items()):
    code = [l for l in lines if lexical.blank(l).strip()]
    print("  %s: %d added line(s), %d holding code once comments and literals are blanked" % (f, len(lines), len(code)))
print("  .npk files the patches touch: %d" % len(added))' "$T"
say "  @@DATE034@@ in the tree as it stands: $(git -C "$R" grep -l '@@DATE034@@' -- . ':!meta/roadmap/0.3/0.3.4_tools' ':!meta/roadmap/0.3/0.3.4.md' | wc -l) file(s)"
