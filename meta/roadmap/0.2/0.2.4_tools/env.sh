# 0.2.4_tools/env.sh -- sourced at the top of EVERY command block of `0.2.4.md`, because a
# Bash call keeps no variables and no functions from the call before it. Set REPO first,
# to the dispatch's REPO line. Before the archive's step 1 the tools are at
# `meta/roadmap/0.2/0.2.4_tools/`, and after it at `meta/roadmap/done/0.2/0.2.4_tools/`:
#
#     REPO=<the dispatch's REPO>; . "$REPO/meta/roadmap/0.2/0.2.4_tools/env.sh"        # steps 0 and 1
#     REPO=<the dispatch's REPO>; . "$REPO/meta/roadmap/done/0.2/0.2.4_tools/env.sh"   # after
#
# `T` is this file's own directory, so every helper finds the tools wherever the
# archive has put them. 0.2.3's `harness` and `check`, and `dryclose`, the close's
# dry run. `$NPK_TREE` is read with `git` read commands only. Every `rm` names its
# target through `${VAR:?}`. TMPDIR is left as the session has it.
: "${REPO:?set REPO to the REPO line of the dispatch, first}"
REPO=$(realpath "$REPO")
WB=$(realpath "$REPO/..")
NPK_TREE=$(realpath "$WB/../nitpick")
PIN=5fbaf4a                                   # the pin this subcycle is planned at
NPKC=$WB/.internal/toolchain/$PIN/npkc
NPKRT=$WB/.internal/toolchain/$PIN/npkrt.o
T=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)   # these tools, wherever they are
A=$REPO/.internal/w024                         # gitignored scratch
CHECK=$HOME/.claude/skills/npk/skills/check/scripts
export NPKC NPKRT REPO
mkdir -p "$A"

# The full harness at the pin, its log kept, its summary lines printed.
#     harness <label>
harness() {
  free -g | awk '/^Mem:/ {print "available GiB:", $7}'
  ( cd "$REPO" && python3 -B harness/run.py ) > "$A/$1.log" 2>&1
  echo "harness exit $?"
  grep -E '^\[1/9\] self-check|^  ok    the tree checks|^  FAIL  |^  ok    npkc .*B of IR$|^\[4/9\]|^\[5/9\]|parse cleanly|swept (7304484|44236800)|^(GREEN|RED) -- ' \
    "$A/$1.log" | cut -c1-150
}

# The close's dry run, in a throwaway clone of HEAD: the move, the S4 patch, the plain
# mentions and the texts patch, in that order, each staged as its block stages it --
# the check that the tree is the one they were cut from, before any is applied here.
#     dryclose
dryclose() {
  local d="$A/dry"
  rm -rf "${d:?}"; git clone -q --shared "$REPO" "$d"
  ( export REPO="$d"
    python3 -B "$T/archive.py" move | tail -1 | sed 's/^/dry run: /'
    git -C "$d" add -A
    python3 -B "$T/apply.py" s4 "$d" | sed 's/^/dry run: /'
    python3 -B "$T/archive.py" mentions | tail -1 | sed 's/^/dry run: /'
    git -C "$d" add -A
    python3 -B "$T/apply.py" texts "$d" | sed 's/^/dry run: /' )
}
