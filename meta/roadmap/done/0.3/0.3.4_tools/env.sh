# meta/roadmap/0.3/0.3.4_tools/env.sh -- sourced at the top of EVERY command block of `0.3.4.md`, because a Bash
# call keeps no variables and no functions from the call before it. Set REPO first, to the dispatch's REPO line.
# BEFORE the archive's step 3 these tools are at `meta/roadmap/0.3/0.3.4_tools/`, and AFTER it at
# `meta/roadmap/done/0.3/0.3.4_tools/`:
#
#     REPO=<the dispatch's REPO>; . "$REPO/meta/roadmap/0.3/0.3.4_tools/env.sh"        # blocks 0a ... 3
#     REPO=<the dispatch's REPO>; . "$REPO/meta/roadmap/done/0.3/0.3.4_tools/env.sh"   # blocks 4 ... 6b
#
# `T` is this file's own directory, so every helper finds the tools wherever the archive has put them
# (`done/0.2/0.2.4_tools/env.sh`'s rule).
#
# ONE PIN, `7e91730`, UNDER THE MACHINE'S LLVM 20.1.8 (the compiler's D-349; TM-259) -- `tools` prints what `llc`,
# `opt` and `ld.lld` report on PATH, and any other release is a toolchain mismatch, a stop. `MAIN_SEEN` is the
# compiler's `main` when this plan was written, landing 111: READ for the hand-on cycle 0.4's README carries, and
# never pinned.
#
# The paths are the CHECKOUT's: `WB` is the directory above it, `NPK_TREE` the compiler beside that, and `CHECK` the
# workbench's own `skills/check/scripts` -- so a block run in a relocated copy finds another workbench or none: run
# the blocks in the checkout the dispatch names (the workbench `PLAYBOOK.md` §12). `$NPK_TREE` is read with `git`
# read commands only -- `show`, `rev-parse`, `cat-file` -- never written, built or fetched in. Every `rm` names its
# target through `${VAR:?}`. Nothing prints a path above the repository, so no output carries a home directory into
# a record. Workbench scripts run under `python3 -B`. TMPDIR is left as the session has it.
#
# THE RUN IS DATED ONCE (the workbench `PLAYBOOK.md` §12): the first block that sources this file writes today's
# date to `$A/run_date`, and `apply.py` writes that date for every `@@DATE034@@` of every step, whatever day each
# runs.
#
# NO LOCK IS TAKEN HERE. On a machine whose seats share one harness at a time, run the blocks that run one -- 0a, 1,
# 2, 3, 4, 4b and 6 -- each under the machine's lock; this file names no path outside the checkout and the
# workbench beside it.
: "${REPO:?set REPO to the REPO line of the dispatch, first}"
REPO=$(realpath "$REPO")
WB=$(realpath "$REPO/..")
NPK_TREE=$(realpath "$WB/../nitpick")
PIN=7e91730                                   # the pin, landings 83 ... 103
PIN_FULL=7e91730d19cffd35fcff25c36893cfaa2c01509e
MAIN_SEEN=e50eaf4                             # the compiler's main at planning, landing 111: read, never pinned
T=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)   # these tools, wherever the archive has put them
A=$REPO/.internal/w034                         # gitignored scratch
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

# The full harness over the checkout, under `python3 -B`, its log kept as `$A/<label>.log` and its summary printed:
# the exit, the self-check's lines and every FAIL, the manifest, the toolchain, the header sweep, the five checks
# this close reads -- `check_purity` and `check_host_isolation` (the gate's), `check_layering`, `check_denominators`
# and `check_specs_current`, whose `0 unresolved` says no text cites a decision or a rule a later step declares (the
# workbench's lesson) -- the parse stage, the library's emission, each stage's tally, and the verdict. Then what the
# run left of bytecode: `harness/__pycache__/` is cleared BEFORE the run, so the count after it is this run's.
#     harness <label>
harness() {
  free -g | awk '/^Mem:/ {print "available GiB:", $7}'
  rm -rf "${REPO:?}/harness/__pycache__"
  ( cd "$REPO" && python3 -B harness/run.py ) > "$A/$1.log" 2>&1
  echo "harness exit $?"
  grep -E '^\[1/9\] self-check -- [0-9]|^  FAIL  |^  ok    the tree checks|^\[2/9\]|^\[3/9\]|^\[4/9\]|of the [0-9]+ under tests/|exemption verdicts|^  ok    check_(purity|host_isolation|layering|denominators|specs_current) |parse cleanly|^  ok    npkc |^      (probe|unit|sweep|conformance|golden): |^(GREEN|RED) -- ' \
    "$A/$1.log" | cut -c1-170
  echo "harness/__pycache__ after the run: $(ls "$REPO/harness/__pycache__" 2>/dev/null | wc -l) file(s)"
}

# The close's dry run, in a throwaway clone of HEAD: steps 1 and 2's patches, the move, the plain mentions and step
# 4's patch, in that order, each staged by the tool that makes it -- the check that the tree is the one they were cut
# from, before any is applied here. `--shared`, so it costs no object copy.
#     dryclose
dryclose() {
  local d="$A/dry"
  rm -rf "${d:?}"; git clone -q --shared "$REPO" "$d"
  ( python3 -B "$T/apply.py" 1 "$d"
    python3 -B "$T/apply.py" 2 "$d"
    REPO="$d" python3 -B "$T/archive.py" move | tail -1
    REPO="$d" python3 -B "$T/archive.py" mentions | tail -1
    python3 -B "$T/apply.py" 4 "$d" ) | sed 's/^/dry run: /'
  rm -rf "${d:?}"
}

# The cycle README's two plants -- 0.3.1's boxes: a `mono_now()` in `src/cal/` and a `host_now_utc()` in `src/fmt/`,
# each by 0.3.1's own text (`0.3.1.md` block 2c) -- in a throwaway clone of HEAD, its own harness run with the suite
# filtered to nothing: the checks run in full, and the run is RED by each plant's name or the gate's "seen to fail"
# is not met. `--only` concludes nothing, and says so: the verdict read here is the RED and its lines. Block 4b's,
# after the commit whose texts say the gate was read again: a clone of HEAD is that commit.
#     plants
plants() {
  local d="$A/plants"
  rm -rf "${d:?}"; git clone -q --shared "$REPO" "$d"
  printf '%s\n' 'func:planted = int64() never fails {' '    pass mono_now();' '};' >> "$d/src/cal/cal.npk"
  printf '%s\n' 'use "../host/host.npk".host_now_utc;' 'func:planted = int64() {' \
    '    pass (relay host_now_utc()).secs;' '};' >> "$d/src/fmt/fmt.npk"
  free -g | awk '/^Mem:/ {print "available GiB:", $7}'
  ( cd "$d" && python3 -B harness/run.py --only no-unit-is-named-this ) > "$A/plants.log" 2>&1
  echo "harness exit $?"
  grep -E '^  FAIL  |^(GREEN|RED) -- |^        (src/(cal|fmt)/[a-z]+\.npk[: ]|`npk\.cal\.planted`|meta/specs/SAFETY\.md:[0-9]+ says)' \
    "$A/plants.log" | cut -c1-150
  rm -rf "${d:?}"
}
