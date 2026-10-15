# meta/roadmap/0.3/0.3.2a_tools/env.sh -- sourced at the top of EVERY command block of `0.3.2a.md`, because a
# Bash call keeps no variables and no functions from the call before it. Set REPO first, to the dispatch's REPO line:
#
#     REPO=<the dispatch's REPO>; . "$REPO/meta/roadmap/0.3/0.3.2a_tools/env.sh"
#
# TWO PINS, EACH UNDER ITS OWN LLVM, AND ONLY INSIDE A HELPER. Each pin is held to its own exact release (the
# compiler's D-204): the unchanged tree's manifest says 20.1.2, the release this repository pinned with `5fbaf4a`,
# and the adopted tree's says 20.1.8, the compiler's since its D-349 and `7e91730`'s -- and `harness/toolchain.py`
# refuses any other. The machine's own `llc`, `opt` and `ld.lld` are 20.1.8 since 2026-10-08, so the NEW pin runs
# under PATH as the shell has it, and the OLD pin under the libraries' private 20.1.2 copy put first on PATH --
# inside the helper's own subshell (`leg`), so no other command of a block ever sees it. `tools <pin>` prints what
# each of the three reports under that pin's PATH; a release other than the pin's is a toolchain mismatch, a stop.
# (`0.3.2_tools/env.sh` put the private copy first for the whole block; one pin then needed one PATH.)
#
# The paths are the CHECKOUT's: `WB` is the directory above it and `NPK_TREE` the compiler beside that, so a block
# run in a relocated copy finds another workbench or none -- run the blocks in the checkout the dispatch names (the
# workbench `PLAYBOOK.md` §12). `$NPK_TREE` is read with `git` read commands only -- `show`, `diff`, `rev-parse`,
# `merge-base`, `cat-file` -- never written, built or fetched in. Every `rm` names its target through `${VAR:?}`.
# Nothing prints a path above the repository, so no output carries a home directory into a record. TMPDIR is left
# as the session has it, as `0.3.2_tools/env.sh` left it.
#
# THE RUN IS DATED ONCE (the workbench `PLAYBOOK.md` §12): the first block that sources this file writes today's
# date to `$A/run_date`, and `apply.py` and `facts.sh` write that date for every `@@DATE032A@@` of every step,
# whatever day each runs.
: "${REPO:?set REPO to the REPO line of the dispatch, first}"
REPO=$(realpath "$REPO")
WB=$(realpath "$REPO/..")
NPK_TREE=$(realpath "$WB/../nitpick")
PIN=7e91730                                   # the pin this subcycle adopts
PIN_FULL=7e91730d19cffd35fcff25c36893cfaa2c01509e
OLD=5fbaf4a                                   # the pin it leaves, kept for the old pin's runs and the controls
OLD_FULL=5fbaf4a40a2f6b213754cd71b6c69700f8aa2c87
OLD_LLVM=$WB/.internal/toolchain/llvm-20.1.2/root/usr/lib/llvm-20/bin   # the old pin's LLVM, the private copy
T=$REPO/meta/roadmap/0.3/0.3.2a_tools         # these tools
A=$REPO/.internal/w032a                        # gitignored scratch
CHECK=$HOME/.claude/skills/npk/skills/check/scripts
mkdir -p "$A"
[ -s "$A/run_date" ] || date +%F > "$A/run_date"
NTIME_RUN_DATE=$(cat "$A/run_date")
export REPO WB A T PIN OLD NTIME_RUN_DATE

# Inside the CALLER'S subshell: the compiler and the LLVM of <pin>. Prints nothing.
#     ( leg <pin>; ... )
leg() {
  NPKC=$WB/.internal/toolchain/$1/npkc
  NPKRT=$WB/.internal/toolchain/$1/npkrt.o
  case "$1" in "$OLD") PATH=$OLD_LLVM:$PATH ;; esac
  export NPKC NPKRT PATH
}

# What `llc`, `opt` and `ld.lld` report under <pin>'s PATH, and where each was found -- relative to the workbench
# when it is the private copy.
#     tools <pin>
tools() {
  ( leg "$1"
    for t in llc opt ld.lld; do
      w=$(command -v "$t"); case "$w" in "$WB"/*) w=${w#"$WB"/} ;; *) w="the machine's" ;; esac
      echo "$1 $t: $w -- $("$t" --version | grep -oE '(LLVM version|LLD) [0-9.]+' | head -1)"
    done )
}

# Compile each file as a root from its own directory with <pin>'s compiler, and print `<file> at <pin>:` and each
# diagnostic's code and site -- `L:C` in the file itself, `<name>:L:C` in another -- or `compiles`.
#     codes <pin> <file>...     (a relative file is the repository's)
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

# The full harness at <pin>, under its LLVM, over a tree -- the checkout by default -- with that tree's own harness,
# its log kept as `$A/<label>.log`, and its summary printed: the exit, the self-check's line and every FAIL, the
# toolchain held, the parse stage, the library's two emissions and the two readings of them, the objects, every
# heap figure a header bounds, and the verdict; then part E's third half, the literal reader against the compiler
# (TM-231), and `check_call_edges`' count of the functions `src/` declares found in the emissions -- two clauses its
# own lines carry past the summary's width.
#     harness <label> <pin> [<tree>]
harness() {
  free -g | awk '/^Mem:/ {print "available GiB:", $7}'
  ( leg "$2"; cd "${3:-$REPO}" && python3 -B harness/run.py ) > "$A/$1.log" 2>&1
  echo "harness exit $?"
  grep -E '^\[1/9\] self-check -- [0-9]|^  FAIL  |^\[3/9\]|^  ok    (llc|opt|ld\.lld) |^  ok    target|^  ok    the (tree checks|reader)|^\[5/9\]|parse cleanly|^  ok    npkc |^  ok    check_(call_edges|wide_types)|^  ok    (llc|opt -O2) \+ scan|heap peak_live|^(GREEN|RED) -- ' \
    "$A/$1.log" | sed -E 's/ exit [0-9]+, both legs, [0-9.]+ s, / /' | cut -c1-150
  grep -m1 -oE 'E3: [^;]*' "$A/$1.log" | sed 's/^/        part E, /'
  grep -m1 -oE "[0-9]+ of [0-9]+ non-generic function\(s\) src/ declares in the umbrella's, [0-9]+ of [0-9]+ generic in the instances'" \
    "$A/$1.log" | sed 's/^/        check_call_edges, /'
}

# A copy of the working tree AS IT STANDS -- tracked and new files, not the ignored -- at $A/ctl/<name>, for a
# control or a measurement to change one thing in. Prints nothing.
#     ctl <name>
ctl() {
  local d="$A/ctl/$1"
  rm -rf "${d:?}"; mkdir -p "$d"
  ( cd "$REPO" && git ls-files -co --exclude-standard -z | xargs -0 tar -cf - ) | tar -xf - -C "$d"
}

# Every tracked `.npk` of <tree> compiled as a root at <pin> -- `census.py` -- into $A/<out>.tsv, and its summary.
#     census <pin> <tree> <out>
census() {
  python3 -B "$T/census.py" run "$1" "$2" "$A/$3.tsv"
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

# Every slot <step> re-spells, undone ALONE in a copy, its file compiled as a root at both pins -- `slots.py`.
#     slots <step>
slots() {
  python3 -B "$T/slots.py" "$REPO" "$1"
}

# The named mutants of `$T/vmutants.tsv` whose step is <step>, each in a copy, its roots compiled at both pins.
#     vmut <step>
vmut() {
  python3 -B "$T/vmut.py" "$REPO" "$1"
}

# The runner's own judge of every refusal -- `stages.refusal`, D-332's count with B-7's sets and every
# `expect-error-at` -- over <tree>'s files with <tree>'s harness, at each pin: `refusals.py`.
#     refusals <tree> <pin>...
refusals() {
  python3 -B "$T/refusals.py" "$@"
}

# The library's two emissions at <pin> into <tree>/build/ -- the umbrella's `ntime.ll` and the instances'
# `generic_instances.ll`, as `run.py`'s step 7 writes them -- and the three checks that read them or the source
# beside them, with <tree>'s checks: `emissions.py`.
#     emissions <tree> <pin>...
emissions() {
  python3 -B "$T/emissions.py" "$@"
}
