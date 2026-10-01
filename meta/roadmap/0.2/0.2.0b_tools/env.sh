# meta/roadmap/0.2/0.2.0b_tools/env.sh -- sourced at the top of EVERY command block of
# `0.2.0b.md`, because a Bash call keeps no variables and no functions from the call
# before it. Set REPO first, to the dispatch's REPO line:
#
#     REPO=<the dispatch's REPO>; . "$REPO/meta/roadmap/0.2/0.2.0b_tools/env.sh"
#
# `0.2.0a_tools/env.sh`'s helpers -- `codes`, `harness`, `ctl` -- and four of
# `nitpick-regex`'s `0.1.1b_tools/env.sh`, ported: `bound` (the type's bound written
# into a copy), `moved` (every tracked `.npk`'s verdict in two trees), `irsame` (the
# IR of every file that compiles in both), and `dryrun` (the patches applied, in
# order, to a throwaway clone). `$NPK_TREE` is read with `git` read commands only --
# never written, built or fetched in. Every `rm` names its target through `${VAR:?}`.
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
T=$REPO/meta/roadmap/0.2/0.2.0b_tools         # these tools
A=$REPO/.internal/w020b                        # gitignored scratch
export NPKC NPKRT                              # the harness reads them from the ENVIRONMENT
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
  grep -E '^\[1/9\] self-check|^  ok    target|^  FAIL  |^  ok    npkc .*B of IR$|^\[4/9\]|parse cleanly|^(GREEN|RED) -- ' \
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

# The type's bound written into a tree's `vec.npk` and nothing else: `struct:Vec<T:
# Copy>`, and with `all`, every `pub func:vec_*<T>` too. No line moves.
#     bound <tree> [all]
bound() {
  sed -i 's/^pub struct:Vec<T> = {/pub struct:Vec<T: Copy> = {/' "$1/src/core/vec.npk"
  [ "$2" = all ] && sed -i -E 's/^(pub func:vec_[a-z_]+)<T> = /\1<T: Copy> = /' "$1/src/core/vec.npk"
  return 0
}

# Every `.npk` in the repository's HEAD -- its tree, not the index, so a file a step
# deletes is counted -- its verdict in HEAD's tree and in
# <tree> -- each a list of codes with their site counts, or `compiles`, or `absent`
# -- printed where the two differ, then the count. The IR of every file that
# compiles in both is kept for `irsame`.        moved <tree>
moved() {
  local t=$1 h="$A/mv/head" f k a b n=0 m=0
  rm -rf "${A:?}/mv"; mkdir -p "$h" "$A/mv/x" "$A/mv/y"
  git -C "$REPO" archive HEAD | tar -x -C "$h"
  for f in $(git -C "$REPO" ls-tree -r --name-only HEAD | grep '\.npk$' | sort); do
    k=$(echo "$f" | tr '/' '_'); n=$((n + 1))
    a=$(_verdict "$h/$f" "$A/mv/x/$k.ll"); b=$(_verdict "$t/$f" "$A/mv/y/$k.ll")
    [ "$a" = "$b" ] && { m=$((m + 1)); continue; }
    echo "$(basename "$f"): $a -> $b"
  done
  echo "verdicts: $m of $n unchanged"
}
_verdict() {
  local out
  [ -f "$1" ] || { echo absent; return; }
  out=$(cd "$(dirname "$1")" && "$NPKC" "$(basename "$1")" -o "$2" 2>&1)
  [ -z "$out" ] && { echo compiles; return; }
  rm -f "$2"
  echo "$out" | grep -oE '^NITPICK-[A-Z]+-[0-9]+' | sort | uniq -c | awk '{printf "%s x%s ", $2, $1}' | sed 's/ $//'
}

# The IR `moved` kept for every file that compiles in both trees, compared byte for
# byte and then with ONE mask: the module's `@npk.site.lines` table, which a comment
# line moves. Any other difference is named.        irsame
irsame() {
  local x k n=0 raw=0 masked=0 diff=""
  for x in "$A"/mv/x/*.ll; do
    k=$(basename "$x"); [ -f "$A/mv/y/$k" ] || continue
    n=$((n + 1))
    cmp -s "$x" "$A/mv/y/$k" && raw=$((raw + 1))
    if cmp -s <(grep -v '^@npk\.site\.lines = ' "$x") <(grep -v '^@npk\.site\.lines = ' "$A/mv/y/$k"); then
      masked=$((masked + 1)); else diff="$diff ${k%.ll}"; fi
  done
  echo "IR: $raw of $n identical byte for byte, $masked of $n with the site-line table masked${diff:+; differs:$diff}"
}

# Every patch of these tools, applied in order to a throwaway clone of HEAD -- the
# check that the tree is the one they were cut from, before any is applied here.
#     dryrun <first> <last>
dryrun() {
  local d="$A/dry" n
  rm -rf "${d:?}"; git clone -q --shared "$REPO" "$d"
  for n in $(seq "$1" "$2"); do python3 -B "$T/apply.py" "$n" "$d" | sed 's/^/dry run: /'; done
}
