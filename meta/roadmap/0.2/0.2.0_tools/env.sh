# meta/roadmap/0.2/0.2.0_tools/env.sh -- sourced at the top of EVERY command block of
# `0.2.0.md`, because a Bash call keeps no variables and no functions from the call
# before it. Set REPO first, to the dispatch's REPO line:
#
#     REPO=<the dispatch's REPO>; . "$REPO/meta/roadmap/0.2/0.2.0_tools/env.sh"
#
# `0.2.0b_tools/env.sh`'s helpers -- `codes`, `harness`, `ctl`, `dryrun` -- and
# `0.2.0a_tools/env.sh`'s `reach` and `nitpick-regex`'s `run4` (a program built and
# run at -O0 and through `opt -O2`). `W` is the scratch directory under the name
# `facts.sh` reads (§1.8), which the plan's §0 used to write into an `env.sh` of
# the worker's own. `$NPK_TREE` is read with `git` read commands only -- never
# written, built or fetched in. Every `rm` names its target through `${VAR:?}`.
# Nothing prints a path above the repository, so no output carries a home directory
# into a record. TMPDIR is left alone: `nitpick-regex`'s harness reddened its
# reproducibility check with its scratch under the repository (the workbench
# PLAYBOOK §12), and nothing here needs it moved.
: "${REPO:?set REPO to the REPO line of the dispatch, first}"
REPO=$(realpath "$REPO")
WB=$(realpath "$REPO/..")
NPK_TREE=$(realpath "$WB/../nitpick")
PIN=5fbaf4a                                   # the pin this subcycle is planned and rehearsed at
PIN_FULL=5fbaf4a40a2f6b213754cd71b6c69700f8aa2c87
NPKC=$WB/.internal/toolchain/$PIN/npkc
NPKRT=$WB/.internal/toolchain/$PIN/npkrt.o
T=$REPO/meta/roadmap/0.2/0.2.0_tools          # these tools
A=$REPO/.internal/w020                         # gitignored scratch
W=$A                                           # facts.sh's name for it
export NPKC NPKRT                              # the harness reads them from the ENVIRONMENT
export REPO W
mkdir -p "$A"

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
  grep -E '^\[1/9\] self-check|^  ok    target|^  FAIL  |^  ok    npkc .*B of IR$|^\[4/9\]|S-6 arm generator  |exemption verdicts|parse cleanly|^\[7/9\]|^(GREEN|RED) -- ' \
    "$A/$1.log" | cut -c1-150
}

# A copy of the working tree AS IT STANDS -- tracked and new files, not the ignored --
# at $A/ctl/<name>, for a control to change one thing in. Prints nothing.
#     ctl <name>
ctl() {
  local d="$A/ctl/$1"
  rm -rf "${d:?}"; mkdir -p "$d"
  ( cd "$REPO" && git ls-files -co --exclude-standard -z | xargs -0 tar -cf - ) | tar -xf - -C "$d"
}

# The identities `NITPICK-REACH-003` names for a root with no `failsafe`.
#     reach <file>       (a relative file is the repository's)
reach() {
  local src=$1; [ "${1#/}" = "$1" ] && src="$REPO/$1"
  echo "$(basename "$src") at $PIN: $(cd "$(dirname "$src")" && "$NPKC" "$(basename "$src")" -o /dev/null 2>&1 \
    | grep -oE '[0-9]+ identities: [^-]*' | sed 's/ *$//')"
}

# Build a program and run it at -O0 and through `opt -O2`: `npkc`, `llc`, `ld.lld`, the
# binary -- all four, because `npkc` exit 0 is not well-formedness (TM-112).
#     run4 <file>...     (a relative file is the repository's)
run4() {
  local f src b o r0 r2
  mkdir -p "$A/run4"
  for f in "$@"; do
    src=$f; [ "${f#/}" = "$f" ] && src="$REPO/$f"
    b=$(basename "$src" .npk); o="$A/run4/$b"
    if ! ( cd "$(dirname "$src")" && "$NPKC" "$(basename "$src")" -o "$o.ll" ) > "$o.npkc" 2>&1; then
      echo "$b: npkc refused -- $(grep -oE '^NITPICK-[A-Z]+-[0-9]+' "$o.npkc" | sort -u | tr '\n' ' ' | sed 's/ $//')"; continue
    fi
    llc -O0 -filetype=obj -relocation-model=static "$o.ll" -o "$o.o" && ld.lld -static "$o.o" "$NPKRT" -o "$o"
    "$o" > /dev/null 2>&1; r0=$?
    opt -O2 -S "$o.ll" -o "$o.2.ll" && llc -O2 -filetype=obj -relocation-model=static "$o.2.ll" -o "$o.2.o" \
      && ld.lld -static "$o.2.o" "$NPKRT" -o "$o.2"
    "$o.2" > /dev/null 2>&1; r2=$?
    echo "$b: -O0 $r0, -O2 $r2"
  done
}

# Every patch of these tools, applied in order to a throwaway clone of HEAD -- the
# check that the tree is the one they were cut from, before any is applied here.
#     dryrun <first> <last>
dryrun() {
  local d="$A/dry" n
  rm -rf "${d:?}"; git clone -q --shared "$REPO" "$d"
  for n in $(seq "$1" "$2"); do python3 -B "$T/apply.py" "$n" "$d" | sed 's/^/dry run: /'; done
}
