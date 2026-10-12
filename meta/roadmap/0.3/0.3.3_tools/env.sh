# meta/roadmap/0.3/0.3.3_tools/env.sh -- sourced at the top of EVERY command block of `0.3.3.md`, because a
# Bash call keeps no variables and no functions from the call before it. Set REPO first, to the dispatch's REPO line:
#
#     REPO=<the dispatch's REPO>; . "$REPO/meta/roadmap/0.3/0.3.3_tools/env.sh"
#
# ONE PIN, `7e91730`, UNDER THE MACHINE'S LLVM 20.1.8 (the compiler's D-349; TM-259) -- `tools` prints what `llc`,
# `opt` and `ld.lld` report on PATH, and any other release is a toolchain mismatch, a stop.
#
# The paths are the CHECKOUT's: `WB` is the directory above it, `NPK_TREE` the compiler beside that, and `CHECK` the
# workbench's own `skills/check/scripts` -- by the checkout's place, where `0.3.2a_tools/env.sh` read the plugin's
# path (that plan's dated note in §0) -- so a block run in a relocated copy finds another workbench or none: run the
# blocks in the checkout the dispatch names (the workbench `PLAYBOOK.md` §12). `$NPK_TREE` is read with `git` read
# commands only -- `show`, `rev-parse`, `cat-file` -- never written, built or fetched in. Every `rm` names its target
# through `${VAR:?}`. Nothing prints a path above the repository, so no output carries a home directory into a
# record. Workbench scripts run under `python3 -B`. TMPDIR is left as the session has it.
#
# THE RUN IS DATED ONCE (the workbench `PLAYBOOK.md` §12): the first block that sources this file writes today's
# date to `$A/run_date`, and `apply.py` and `facts.sh` write that date for every `@@DATE033@@` of every step,
# whatever day each runs.
#
# NO LOCK IS TAKEN HERE. On a machine whose seats share one harness at a time, run the blocks that run one -- 0a,
# 0b, 1, 2, 2m, 3 and 4 -- each under the machine's lock, `blocks.py run` inside `flock`; this file names no path
# outside the checkout and the workbench beside it.
: "${REPO:?set REPO to the REPO line of the dispatch, first}"
REPO=$(realpath "$REPO")
WB=$(realpath "$REPO/..")
NPK_TREE=$(realpath "$WB/../nitpick")
PIN=7e91730                                   # the pin, landings 83 ... 103
PIN_FULL=7e91730d19cffd35fcff25c36893cfaa2c01509e
T=$REPO/meta/roadmap/0.3/0.3.3_tools          # these tools
A=$REPO/.internal/w033                         # gitignored scratch
CHECK=$WB/skills/check/scripts
NPKC=$WB/.internal/toolchain/$PIN/npkc
NPKRT=$WB/.internal/toolchain/$PIN/npkrt.o
mkdir -p "$A"
[ -s "$A/run_date" ] || date +%F > "$A/run_date"
NTIME_RUN_DATE=$(cat "$A/run_date")
export REPO WB A T PIN NPKC NPKRT NTIME_RUN_DATE

# What `llc`, `opt` and `ld.lld` report on PATH.
tools() {
  local t
  for t in llc opt ld.lld; do
    echo "$t: $("$t" --version | grep -oE '(LLVM version|LLD) [0-9.]+' | head -1)"
  done
}

# The full harness over a tree -- the checkout by default -- with that tree's own harness, its log kept as
# `$A/<label>.log`, and its summary printed: the exit, the self-check's line and every FAIL, the toolchain held, the
# header sweep, `check_layering`, `check_denominators` and `check_specs_current` -- whose `0 unresolved` says no
# text cites a decision or a rule a later step declares (the workbench's lesson) -- the parse stage, the library's
# emission, the double's three tests and each stage's tally, and the verdict.
#     harness <label> [<tree>]
harness() {
  free -g | awk '/^Mem:/ {print "available GiB:", $7}'
  ( cd "${2:-$REPO}" && python3 -B harness/run.py ) > "$A/$1.log" 2>&1
  echo "harness exit $?"
  grep -E '^\[1/9\] self-check -- [0-9]|^  FAIL  |^  ok    the tree checks|^\[2/9\]|^\[3/9\]|^\[4/9\]|of the [0-9]+ under tests/|exemption verdicts|^  ok    check_layering|^  ok    check_denominators|^  ok    check_specs_current|parse cleanly|^  ok    npkc |double_|^      (probe|unit|sweep|conformance|golden): |^(GREEN|RED) -- ' \
    "$A/$1.log" | cut -c1-170
}

# The steps' patches applied in order to a throwaway clone of HEAD -- the check that the tree is the one they were
# cut from, before any is applied here. `--shared`, so it costs no object copy.
#     dryrun <step>...
dryrun() {
  local d="$A/dry" n
  rm -rf "${d:?}"; git clone -q --shared "$REPO" "$d"
  for n in "$@"; do python3 -B "$T/apply.py" "$n" "$d" | sed 's/^/dry run: /'; done
  rm -rf "${d:?}"
}

# A unit built as `run.py` builds one -- at -O0 and through `opt -O2` -- and run once a leg from its own directory
# with the harness's environment, `NTIME_HARNESS=1` and nothing else: `<file>: <exit> / <exit>`, and for a member
# with a golden whether each leg's stdout is its `.txt`, byte for byte.
#     legs <file>...     (a relative file is the repository's)
legs() {
  local f src d b o e0 e2 g
  for f in "$@"; do
    src=$f; [ "${f#/}" = "$f" ] && src="$REPO/$f"
    d=$(dirname "$src"); b=$(basename "$src" .npk); o="$A/legs/$b"; mkdir -p "$A/legs"
    if ! ( cd "$d" && "$NPKC" "$b.npk" -o "$o.ll" ) > "$o.err" 2>&1; then
      echo "$b: npkc refused -- $(grep -oE '^NITPICK-[A-Z]+-[0-9]+' "$o.err" | tr '\n' ' ')"; continue
    fi
    llc -O0 -filetype=obj -relocation-model=static "$o.ll" -o "$o.o" && ld.lld -static "$o.o" "$NPKRT" -o "$o.x0" \
      && opt -O2 -S "$o.ll" -o "$o.2.ll" && llc -O2 -filetype=obj -relocation-model=static "$o.2.ll" -o "$o.2.o" \
      && ld.lld -static "$o.2.o" "$NPKRT" -o "$o.x2"
    ( cd "$d" && env -i NTIME_HARNESS=1 "$o.x0" > "$o.out0" 2> /dev/null ); e0=$?
    ( cd "$d" && env -i NTIME_HARNESS=1 "$o.x2" > "$o.out2" 2> /dev/null ); e2=$?
    g=""
    if [ -f "$d/$b.txt" ]; then
      g=", its golden $(cmp -s "$o.out0" "$d/$b.txt" && echo same || echo DIFFERS) / $(cmp -s "$o.out2" "$d/$b.txt" && echo same || echo DIFFERS)"
    fi
    echo "$b: $e0 / $e2$g"
  done
}

# Every single-site mutant of the double (`all`), or `named.tsv`'s rows (`table`), against its three tests: `mutants.py`.
#     mutants all|table
mutants() {
  free -g | awk '/^Mem:/ {print "available GiB:", $7}'
  python3 -B "$T/mutants.py" "$1" "$REPO" "$A/mutants" -j 8
  rm -rf "${A:?}/mutants"
}
