# meta/roadmap/0.3/0.3.2_tools/env.sh -- sourced at the top of EVERY command block of
# `0.3.2.md`, because a Bash call keeps no variables and no functions from the call
# before it. Set REPO first, to the dispatch's REPO line:
#
#     REPO=<the dispatch's REPO>; . "$REPO/meta/roadmap/0.3/0.3.2_tools/env.sh"
#
# `0.3.1_tools/env.sh`'s helpers -- `codes`, `harness`, `ctl`, `swap`, `emit`, `dryrun`,
# `check` and `plants` -- pointed at this subcycle's tools and its scratch,
# `.internal/w032`; `emit` writes the instances' emission beside the umbrella's, as
# step 7 does from step 1 on; and `mutants` runs both of this plan's tables: step 1's,
# one-line mutants of `harness/checks.py` against the self-check's plants, and step
# 3's, mutants of `src/host/host.npk` against the system zone's four units, each built
# and run on both legs in the environment its header names. The paths are the
# CHECKOUT's: `WB` is the directory above it and `NPK_TREE` the compiler beside that,
# so a block run in a relocated copy finds another workbench or none -- run the blocks
# in the checkout the dispatch names (the workbench `PLAYBOOK.md` §12). `$NPK_TREE` is
# read with `git` read commands only -- never written, built or fetched in. Every `rm`
# names its target through `${VAR:?}`. Nothing prints a path above the repository, so
# no output carries a home directory into a record. TMPDIR is left as the session has
# it.
#
# THE LIBRARIES' PRIVATE LLVM 20.1.2 IS FIRST ON PATH (the workbench's question 24,
# option (c); this machine's own `llc`, `opt` and `ld.lld` moved to 20.1.8 on
# 2026-10-08, the compiler's pin, not ours): `.internal/toolchain/llvm-20.1.2/`, byte-identical to the 20.1.2
# packages this repository pinned (its README.txt says how it was made and checked).
# The harness holds the three tools to `nitpick.toml`'s 20.1.2, so without this a
# full run refuses at its toolchain check -- and with the wrong release first it would
# measure another code generator. Block 0a prints what `llc` reports through it, and
# every block that sources this file prints a STOP line if it reports anything else:
# a toolchain mismatch, which is a stop, never a retry.
#
# THE RUN IS DATED ONCE (the workbench `PLAYBOOK.md` §12): the first block that sources
# this file writes today's date to `$A/run_date`, and `apply.py` writes that date for
# every `@@RUN_DATE@@` of every step, whatever day it runs.
: "${REPO:?set REPO to the REPO line of the dispatch, first}"
REPO=$(realpath "$REPO")
WB=$(realpath "$REPO/..")
NPK_TREE=$(realpath "$WB/../nitpick")
PIN=5fbaf4a                                   # the pin this subcycle is planned and rehearsed at
PIN_FULL=5fbaf4a40a2f6b213754cd71b6c69700f8aa2c87
NPKC=$WB/.internal/toolchain/$PIN/npkc
NPKRT=$WB/.internal/toolchain/$PIN/npkrt.o
LLVM_BIN=$WB/.internal/toolchain/llvm-20.1.2/root/usr/lib/llvm-20/bin
case ":$PATH:" in *":$LLVM_BIN:"*) ;; *) PATH=$LLVM_BIN:$PATH ;; esac
T=$REPO/meta/roadmap/0.3/0.3.2_tools          # these tools
A=$REPO/.internal/w032                         # gitignored scratch
W=$A                                           # facts.sh's name for it
CHECK=$HOME/.claude/skills/npk/skills/check/scripts
mkdir -p "$A"
[ -s "$A/run_date" ] || date +%F > "$A/run_date"
NTIME_RUN_DATE=$(cat "$A/run_date")
export NPKC NPKRT PATH                         # the harness reads them from the ENVIRONMENT
export REPO W T NTIME_RUN_DATE
case "$(llc --version 2>/dev/null | grep -o 'LLVM version [0-9.]*')" in
  "LLVM version 20.1.2") ;;
  *) echo "STOP: llc on PATH reports '$(llc --version 2>/dev/null | grep -o 'LLVM version [0-9.]*')', not LLVM version 20.1.2 -- a toolchain mismatch" ;;
esac

# Compile each file as a root from its own directory and print `<file> at <pin>:` and
# each diagnostic's code and site -- `L:C` in the file itself -- or `compiles`.
#     codes <pin> <file>...   (a relative file is the repository's)
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

# The full harness at the pin over <tree> -- the repository by default -- with that
# tree's own harness, its log kept at $A/<label>.log, its summary lines printed.
#     harness <label> [<tree>]
harness() {
  free -g | awk '/^Mem:/ {print "available GiB:", $7}'
  ( cd "${2:-$REPO}" && python3 -B harness/run.py ) > "$A/$1.log" 2>&1
  echo "harness exit $?"
  grep -E '^\[1/9\] self-check|^  ok    target|^  FAIL  |^  ok    npkc .*B of IR|^\[4/9\]|S-6 arm generator  |exemption verdicts|parse cleanly|^\[5/9\]|^  ok    the tree checks|^  ok    the reader|^\[7/9\]|^(GREEN|RED) -- ' \
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
# printed, and the file is left as it was. `\n` in <old> or <new> is a newline.
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

# The library's emissions, written where `run.py`'s step 7 writes them -- the
# umbrella's to <tree>/build/ntime.ll and, where the tree holds the unit that
# instantiates every generic function (step 1 on), the instances' to
# <tree>/build/generic_instances.ll -- by the pinned `npkc`.
#     emit [<tree>]
emit() {
  local tree=${1:-$REPO}
  mkdir -p "$tree/build"
  ( cd "$tree/src" && "$NPKC" lib.npk -o "$tree/build/ntime.ll" ) || echo "STOP emit: npkc refused the umbrella"
  rm -f "$tree/build/generic_instances.ll"
  if [ -f "$tree/tests/unit/generic_instances.npk" ]; then
    ( cd "$tree" && "$NPKC" tests/unit/generic_instances.npk -o build/generic_instances.ll ) \
      || echo "STOP emit: npkc refused the instances"
  fi
}

# The patches of these tools, applied in order to a throwaway clone of HEAD -- the
# check that the tree is the one they were cut from, before any is applied here.
#     dryrun <step>...
dryrun() {
  local d="$A/dry" n
  rm -rf "${d:?}"; git clone -q --shared "$REPO" "$d"
  for n in "$@"; do python3 -B "$T/apply.py" "$n" "$d" | sed 's/^/dry run: /'; done
  rm -rf "${d:?}"
}

# One tree check over a tree -- the repository by default -- with a tree's checks --
# the repository's by default -- its headline, then each finding's first line. The two
# checks over the emission read <tree>/build/, which `emit` writes.
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
# `selfcheck.py`, run against <checks-tree>'s checks (<tree>'s by default): the count
# of rows and plants, and each problem's first line. A plant red against the check
# before its decision and caught by the check after is V-14's evidence.
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

# Build <unit>.npk in <dir> at both legs, and run each leg once in the environment its
# header's `// env:` lines name over the harness's base, `NTIME_HARNESS=1` (V-1e).
# Prints `-O0 exit/-O2 exit`, or the refusal's first code.
#     legs2 <dir> <unit-stem>
legs2() {
  local d=$1 u=$2 r0 r2 ev
  if ! ( cd "$d" && "$NPKC" "$u.npk" -o "$A/legs/$u.ll" ) > "$A/legs/$u.npkc" 2>&1; then
    echo "npkc refused $(grep -oE '^NITPICK-[A-Z]+-[0-9]+' "$A/legs/$u.npkc" | head -1)"; return
  fi
  llc -O0 -filetype=obj -relocation-model=static "$A/legs/$u.ll" -o "$A/legs/$u.o" \
    && ld.lld -static "$A/legs/$u.o" "$NPKRT" -o "$A/legs/$u.0" \
    && opt -O2 -S "$A/legs/$u.ll" -o "$A/legs/$u.2.ll" \
    && llc -O2 -filetype=obj -relocation-model=static "$A/legs/$u.2.ll" -o "$A/legs/$u.2.o" \
    && ld.lld -static "$A/legs/$u.2.o" "$NPKRT" -o "$A/legs/$u.2"
  mapfile -t ev < <(grep -E '^// env: ' "$d/$u.npk" | sed -E 's|^// env: ||')
  env -i NTIME_HARNESS=1 "${ev[@]}" "$A/legs/$u.0" > /dev/null 2>&1; r0=$?
  env -i NTIME_HARNESS=1 "${ev[@]}" "$A/legs/$u.2" > /dev/null 2>&1; r2=$?
  echo "$r0/$r2"
}

# The mutants of `$T/mutants.tsv` whose step is <step> -- step, name, the text, its
# replacement, TAB-separated, `\n` a newline -- each one `swap`, counted as matching
# ONCE. Step 1's mutate a copy of the repository's `harness/checks.py`, and the
# self-check's plants run against it: `<name>: <n> problem(s)` and the kinds. Step 3's
# mutate a copy of `src/host/host.npk`, and the system zone's four units are built and
# run on both legs: `<name>: etc a/b tz c/d tz_colon e/f tz_empty g/h`, each `-O0/-O2`.
# A mutant nothing can see prints 0 everywhere, and the plan names it.
#     mutants <step>
mutants() {
  local step=$1 s name old new d u line
  local units="system_zone_etc system_zone_tz system_zone_tz_colon system_zone_tz_empty"
  mkdir -p "$A/legs"
  while IFS=$'\t' read -r s name old new; do
    case "$s" in ''|'#'*) continue;; esac
    [ "$s" = "$step" ] || continue
    d="$A/mut/$name"; rm -rf "${d:?}"; mkdir -p "$d"
    if [ "$step" = 1 ]; then
      mkdir -p "$d/harness"; cp "$REPO"/harness/*.py "$d/harness/"
      swap "$d/harness/checks.py" "$old" "$new" || { echo "$name: not applied"; continue; }
      line=$(python3 -B - "$d" <<'PY'
import os, sys
d = sys.argv[1]
sys.path.insert(0, os.path.join(d, "harness"))
import selfcheck
base = os.path.join(d, "work")
os.makedirs(base)
probs = selfcheck.part_b(None, base) + selfcheck.part_b_view_exempt(None, base)
kinds = sorted(set(" ".join(p.split()[:5]) for p in probs))
print("%d problem(s)%s" % (len(probs), (" -- " + "; ".join(kinds)) if kinds else ""))
PY
)
      echo "$name: $line" | cut -c1-200
    else
      mkdir -p "$d/tests/unit"; cp -r "$REPO/src" "$d/src"
      for u in $units; do cp "$REPO/tests/unit/$u.npk" "$d/tests/unit/"; done
      swap "$d/src/host/host.npk" "$old" "$new" || { echo "$name: not applied"; continue; }
      line="$name:"
      for u in $units; do line="$line ${u#system_zone_} $(legs2 "$d/tests/unit" "$u")"; done
      echo "$line"
    fi
    rm -rf "${d:?}"
  done < "$T/mutants.tsv"
  rm -rf "${A:?}/mut" "${A:?}/legs"
}
