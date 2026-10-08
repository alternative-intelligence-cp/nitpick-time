# meta/roadmap/0.3/0.3.0_tools/env.sh -- sourced at the top of EVERY command block of
# `0.3.0.md`, because a Bash call keeps no variables and no functions from the call
# before it. Set REPO first, to the dispatch's REPO line:
#
#     REPO=<the dispatch's REPO>; . "$REPO/meta/roadmap/0.3/0.3.0_tools/env.sh"
#
# `0.2.4b_tools/env.sh`'s helpers -- `codes`, `harness`, `ctl`, `swap`, `reach`, `run4`,
# `dryrun` and `check` -- pointed at this subcycle's tools and its scratch,
# `.internal/w030`; with 0.2.4a's `plants`, and `mutants` for step 3. The paths are
# the CHECKOUT's: `WB` is the directory above it and `NPK_TREE` the compiler beside
# that, so a block run in a relocated copy finds another workbench or none -- run
# the blocks in the checkout the dispatch names (the workbench `PLAYBOOK.md` §12).
# `$NPK_TREE` is read with `git` read commands only -- never written, built or
# fetched in. Every `rm` names its target through `${VAR:?}`. Nothing prints a path
# above the repository, so no output carries a home directory into a record.
# TMPDIR is left as the session has it.
#
# THE RUN IS DATED ONCE (the workbench `PLAYBOOK.md` §12, "a patch dated by the day it
# applies breaks a run that crosses midnight"): the first block that sources this
# file writes today's date to `$A/run_date`, and `apply.py` writes that date for
# every `@@DATE@@` of every step, whatever day it runs.
: "${REPO:?set REPO to the REPO line of the dispatch, first}"
REPO=$(realpath "$REPO")
WB=$(realpath "$REPO/..")
NPK_TREE=$(realpath "$WB/../nitpick")
PIN=5fbaf4a                                   # the pin this subcycle is planned and rehearsed at
PIN_FULL=5fbaf4a40a2f6b213754cd71b6c69700f8aa2c87
NPKC=$WB/.internal/toolchain/$PIN/npkc
NPKRT=$WB/.internal/toolchain/$PIN/npkrt.o
T=$REPO/meta/roadmap/0.3/0.3.0_tools          # these tools
A=$REPO/.internal/w030                         # gitignored scratch
W=$A                                           # facts.sh's name for it
CHECK=$HOME/.claude/skills/npk/skills/check/scripts
mkdir -p "$A"
[ -s "$A/run_date" ] || date +%F > "$A/run_date"
NTIME_RUN_DATE=$(cat "$A/run_date")
export NPKC NPKRT                              # the harness reads them from the ENVIRONMENT
export REPO W T NTIME_RUN_DATE

# Compile each file as a root from its own directory and print `<file> at <pin>:` and
# each diagnostic's code and site -- `L:C` in the file itself, `<name>:L:C` in
# another -- or `compiles`.        codes <pin> <file>...   (a relative file is the repository's)
codes() {
  local pin=$1; shift
  local cc=$WB/.internal/toolchain/$pin/npkc f src out b
  for f in "$@"; do
    src=$f; [ "${f#/}" = "$f" ] && src="$REPO/$f"
    b=$(basename "$src")
    out=$(cd "$(dirname "$src")" && "$cc" "$b" -o /dev/null 2>&1)
    if [ -z "$out" ]; then echo "$b at $pin compiles"; continue; fi
    echo "$b at $pin: $(echo "$out" | grep -oE '^NITPICK-[A-Z]+-[0-9]+ [^ ]+:[0-9]+:[0-9]+' \
      | sed -E "s|^(NITPICK-[A-Z]+-[0-9]+) ([^ ]*/)?([^/ ]+):([0-9]+):([0-9]+)$|\1 \3:\4:\5|; s| $b:| |" \
      | tr '\n' ' ' | sed 's/ $//')"
  done
}

# The full harness at the pin, its log kept, its summary lines printed.
#     harness <label>
harness() {
  free -g | awk '/^Mem:/ {print "available GiB:", $7}'
  ( cd "$REPO" && python3 -B harness/run.py ) > "$A/$1.log" 2>&1
  echo "harness exit $?"
  grep -E '^\[1/9\] self-check|^  ok    target|^  FAIL  |^  ok    npkc .*B of IR$|^\[4/9\]|S-6 arm generator  |exemption verdicts|parse cleanly|^\[5/9\]|^  ok    the tree checks|^  ok    the reader|^\[7/9\]|^(GREEN|RED) -- ' \
    "$A/$1.log" | cut -c1-150
}

# A copy of the working tree AS IT STANDS -- tracked and new files, not the ignored --
# at $A/ctl/<name>, for a mutant or a control to change one thing in. Prints nothing.
#     ctl <name>
ctl() {
  local d="$A/ctl/$1"
  rm -rf "${d:?}"; mkdir -p "$d"
  ( cd "$REPO" && git ls-files -co --exclude-standard -z | xargs -0 tar -cf - ) | tar -xf - -C "$d"
}

# Replace the ONE occurrence of <old> in <file> with <new>; any other count is a STOP,
# printed, and the file is left as it was. A mutant is one edit, and an edit that
# matched twice or not at all is not the mutant the plan names. `\n` in <old> or
# <new> is a newline.
#     swap <file> <old> <new>
swap() {
  python3 -B - "$1" "$2" "$3" <<'PY'
import sys
p, old, new = sys.argv[1], sys.argv[2].replace("\\n", "\n"), sys.argv[3].replace("\\n", "\n")
s = open(p, encoding="utf-8").read()
if s.count(old) != 1:
    print("STOP swap: %d occurrence(s) of %r in %s" % (s.count(old), old[:60], p.split("/")[-1]))
    sys.exit(1)
open(p, "w", encoding="utf-8").write(s.replace(old, new))
PY
}

# The identities `NITPICK-REACH-003` names for a root with no `failsafe`.
#     reach <file>       (a relative file is the repository's)
reach() {
  local src=$1; [ "${1#/}" = "$1" ] && src="$REPO/$1"
  echo "$(basename "$src") at $PIN: $(cd "$(dirname "$src")" && "$NPKC" "$(basename "$src")" -o /dev/null 2>&1 \
    | grep -oE '[0-9]+ identities: [^-]*' | sed 's/ *$//')"
}

# Build a program and run it at -O0 and through `opt -O2`: `npkc`, `llc`, `ld.lld`, the
# binary -- all four, because `npkc` exit 0 is not well-formedness (TM-112). A
# refusal prints its codes and sites, as `codes` does.
#     run4 <file>...     (a relative file is the repository's)
run4() {
  local f src b o r0 r2
  mkdir -p "$A/run4"
  for f in "$@"; do
    src=$f; [ "${f#/}" = "$f" ] && src="$REPO/$f"
    b=$(basename "$src" .npk); o="$A/run4/$b"
    if ! ( cd "$(dirname "$src")" && "$NPKC" "$(basename "$src")" -o "$o.ll" ) > "$o.npkc" 2>&1; then
      echo "$b: npkc refused -- $(grep -oE '^NITPICK-[A-Z]+-[0-9]+ [^ ]+:[0-9]+:[0-9]+' "$o.npkc" \
        | sed -E 's|^(NITPICK-[A-Z]+-[0-9]+) ([^ ]*/)?[^/ ]+:([0-9]+:[0-9]+)$|\1 \3|' | tr '\n' ' ' | sed 's/ $//')"; continue
    fi
    llc -O0 -filetype=obj -relocation-model=static "$o.ll" -o "$o.o" && ld.lld -static "$o.o" "$NPKRT" -o "$o"
    "$o" > /dev/null 2>&1; r0=$?
    opt -O2 -S "$o.ll" -o "$o.2.ll" && llc -O2 -filetype=obj -relocation-model=static "$o.2.ll" -o "$o.2.o" \
      && ld.lld -static "$o.2.o" "$NPKRT" -o "$o.2"
    "$o.2" > /dev/null 2>&1; r2=$?
    echo "$b: -O0 $r0, -O2 $r2"
  done
}

# The patches of these tools, applied in order to a throwaway clone of HEAD -- the
# check that the tree is the one they were cut from, before any is applied here.
# The clone is where it is put, not the checkout, and `apply.py` finds nothing by
# a relative path, so this leg is the same in either place.
#     dryrun <step>...
dryrun() {
  local d="$A/dry" n
  rm -rf "${d:?}"; git clone -q --shared "$REPO" "$d"
  for n in "$@"; do python3 -B "$T/apply.py" "$n" "$d" | sed 's/^/dry run: /'; done
  rm -rf "${d:?}"
}

# One tree check over a tree -- the repository by default -- with a tree's checks --
# the repository's by default -- its headline, then each finding's first line.
#     check <name> [<tree>] [<checks-tree>]
check() {
  python3 -B - "${3:-$REPO}" "$1" "${2:-$REPO}" <<'PY'
import os, sys
sys.path.insert(0, os.path.join(sys.argv[1], "harness"))
import checks
r = getattr(checks, sys.argv[2])(sys.argv[3])
print("%s: %d finding(s) -- %s" % (r.name, len(r.problems), r.headline))
for p in r.problems:
    print("  " + p.splitlines()[0][:150])
PY
}

# The self-check's tree-check plants -- part B and S-22's exemption -- from <tree>'s
# `selfcheck.py`, run against <checks-tree>'s checks (<tree>'s by default): the
# count of rows and plants, and each problem's first line. A plant red against the
# check before its decision and caught by the check after is V-14's evidence.
#     plants <tree> [<checks-tree>]
plants() {
  local d="$A/plants"
  rm -rf "${d:?}"; mkdir -p "$d/harness"
  cp "${2:-$1}"/harness/*.py "$d/harness/"
  cp "$1/harness/selfcheck.py" "$d/harness/"
  python3 -B - "$d" <<'PY'
import os, sys
d = sys.argv[1]
sys.path.insert(0, os.path.join(d, "harness"))
import selfcheck
base = os.path.join(d, "work")
os.makedirs(base)
probs = selfcheck.part_b(None, base) + selfcheck.part_b_view_exempt(None, base)
print("plants: %d PLANTED row(s), %d tree-check plant(s), %d problem(s)"
      % (len(selfcheck.PLANTED), selfcheck.TREE_PLANTS, len(probs)))
for p in probs:
    print("  " + p.splitlines()[0][:150])
PY
  rm -rf "${d:?}"
}

# Step 3's mutants: each row of `$T/mutants.tsv` -- name, the text, its replacement,
# TAB-separated, `\n` a newline -- one `swap` in a copy of <tree>'s
# `src/host/host.npk`, counted as matching ONCE; then the unit built and run once
# on each leg. Prints `<name>: -O0 <exit>, -O2 <exit>`.
#     mutants <tree>
mutants() {
  local tree=$1 name old new d r0 r2
  while IFS=$'\t' read -r name old new; do
    case "$name" in ''|'#'*) continue;; esac
    d="$A/mut/$name"; rm -rf "${d:?}"; mkdir -p "$d/tests/unit"
    cp -r "$tree/src" "$d/src"; cp "$tree/tests/unit/host_clocks.npk" "$d/tests/unit/"
    swap "$d/src/host/host.npk" "$old" "$new" || { echo "$name: not applied"; continue; }
    if ! ( cd "$d/tests/unit" && "$NPKC" host_clocks.npk -o "$d/u.ll" ) > "$d/npkc.txt" 2>&1; then
      echo "$name: npkc refused -- $(grep -oE '^NITPICK-[A-Z]+-[0-9]+' "$d/npkc.txt" | tr '\n' ' ')"; continue
    fi
    llc -O0 -filetype=obj -relocation-model=static "$d/u.ll" -o "$d/u.o" && ld.lld -static "$d/u.o" "$NPKRT" -o "$d/u0" \
      && opt -O2 -S "$d/u.ll" -o "$d/u2.ll" && llc -O2 -filetype=obj -relocation-model=static "$d/u2.ll" -o "$d/u2.o" \
      && ld.lld -static "$d/u2.o" "$NPKRT" -o "$d/u2"
    "$d/u0" > /dev/null 2>&1; r0=$?; "$d/u2" > /dev/null 2>&1; r2=$?
    echo "$name: -O0 $r0, -O2 $r2"
  done < "$T/mutants.tsv"
  rm -rf "${A:?}/mut"
}
