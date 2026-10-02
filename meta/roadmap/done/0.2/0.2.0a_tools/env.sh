# meta/roadmap/0.2/0.2.0a_tools/env.sh -- sourced at the top of EVERY command block of
# `0.2.0a.md`, because a Bash call keeps no variables and no functions from the call
# before it. Set REPO first, to the dispatch's REPO line:
#
#     REPO=<the dispatch's REPO>; . "$REPO/meta/roadmap/0.2/0.2.0a_tools/env.sh"
#
# `$NPK_TREE` is read with `git` read commands only -- never written, built or
# fetched in. Every `rm` names its target through `${VAR:?}`. Nothing prints a path
# above the repository, so no output carries a home directory into a record.
# `nitpick-regex`'s `0.1.0b_tools/env.sh`, ported: the same helpers, this tree's
# scratch and programs.
: "${REPO:?set REPO to the REPO line of the dispatch, first}"
REPO=$(realpath "$REPO")
WB=$(realpath "$REPO/..")
NPK_TREE=$(realpath "$WB/../nitpick")
PIN=5fbaf4a                                   # the pin this subcycle adopts
PIN_FULL=5fbaf4a40a2f6b213754cd71b6c69700f8aa2c87
OLD=c970483                                   # the pin it leaves, kept for controls
NPKC=$WB/.internal/toolchain/$PIN/npkc
NPKRT=$WB/.internal/toolchain/$PIN/npkrt.o
T=$REPO/meta/roadmap/0.2/0.2.0a_tools         # these tools
A=$REPO/.internal/w020a                        # gitignored scratch
export NPKC NPKRT                              # the harness reads them from the ENVIRONMENT
mkdir -p "$A"

# Compile each file as a root with a kept pin's compiler, from its own directory, and
# print `<file> at <pin>: CODE L:C ...` per error line, or `compiles`.
#     codes <pin> <file>...     (a relative file is the repository's)
codes() {
  local pin=$1; shift
  local cc=$WB/.internal/toolchain/$pin/npkc f src out
  for f in "$@"; do
    src=$f; [ "${f#/}" = "$f" ] && src="$REPO/$f"
    out=$(cd "$(dirname "$src")" && "$cc" "$(basename "$src")" -o /dev/null 2>&1)
    if [ -z "$out" ]; then echo "$(basename "$src") at $pin compiles"; continue; fi
    echo "$(basename "$src") at $pin: $(echo "$out" | grep -oE '^NITPICK-[A-Z]+-[0-9]+ [^ ]+:[0-9]+:[0-9]+' \
      | sed -E 's|^(NITPICK-[A-Z]+-[0-9]+) [^ ]*:([0-9]+):([0-9]+)$|\1 \2:\3|' | tr '\n' ' ' | sed 's/ $//')"
  done
}

# The identities `NITPICK-REACH-003` names for a root with no `failsafe`.
#     reach <pin> <file>
reach() {
  local cc=$WB/.internal/toolchain/$1/npkc
  echo "$(basename "$2") at $1: $(cd "$(dirname "$2")" && "$cc" "$(basename "$2")" -o /dev/null 2>&1 \
    | grep -oE '[0-9]+ identities: [^-]*' | sed 's/ *$//')"
}

# The full harness at the pin, its log kept, its summary lines printed.
#     harness <label>
harness() {
  free -g | awk '/^Mem:/ {print "available GiB:", $7}'
  ( cd "$REPO" && python3 -B harness/run.py ) > "$A/$1.log" 2>&1
  echo "harness exit $?"
  grep -E '^\[1/9\] self-check|^  ok    target|^  FAIL  |^  ok    npkc .*B of IR$|^(GREEN|RED) -- ' "$A/$1.log" | cut -c1-150
}

# A copy of the working tree AS IT STANDS -- tracked and new files, not the ignored --
# at $A/ctl/<name>, for a control to change one thing in. Prints nothing.
#     ctl <name>
ctl() {
  local d="$A/ctl/$1"
  rm -rf "${d:?}"; mkdir -p "$d"
  ( cd "$REPO" && git ls-files -co --exclude-standard -z | xargs -0 tar -cf - ) | tar -xf - -C "$d"
}

# The measurement programs of §1, written to <dir>: the owner of a live view written
# (D-325's freeze), a view of an OWNED `cstring`'s `.ptr` returned (D-328), and the
# ecosystem audit's EC3 pair -- a private identity raised and relayed, and two public
# identities declared and never raised. None is a test of this repository's.
#     programs <dir>
programs() {
  local d=$1 fs='func:failsafe = int32(Error:e) {
    pick (e) {
        (HeapBadRequest) { exit 91i32; }, (HeapOom) { exit 92i32; }, (OutOfBounds) { exit 94i32; },
        (Unreachable) { exit 95i32; }, (WildLeak) { exit 96i32; }, (StackExhausted) { exit 106i32; },
        (MachineFault) { exit 107i32; }, (*) { exit 99i32; }
    }
    exit 9i32;
};'
  mkdir -p "$d"
  printf '%s\n' 'mod:zz_root_written;' 'func:main = int32(cstring[]:_~argv) {' \
    '    string:s = string_concat("abbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "c");' \
    '    uint8[]:v = string_bytes(s);' \
    '    s = string_concat("xyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy", "z");' \
    '    exit (v[0i64] => int32);' '};' "$fs" > "$d/zz_root_written.npk"
  printf '%s\n' 'mod:zz_owned_view;' 'error:EP;' 'func:make = string() {' \
    '    cstring:s = to_cstring("TZ=Europe/Kyiv") ?! EP;' \
    '    pass string_from_bytes(s.ptr, s.len);' '};' 'func:main = int32(cstring[]:_~argv) {' \
    '    string:v = make() ?! EP;' '    exit 0i32;' '};' "${fs/pick (e) \{/pick (e) \{
        (EP) \{ exit 90i32; \},}" > "$d/zz_owned_view.npk"
  printf '%s\n' 'mod:mpriv;' 'error:EPriv;' 'pub func:f = int64(int64:x) {' \
    '    if (x < 0i64) { fail EPriv; }' '    pass x;' '};' > "$d/mpriv.npk"
  printf '%s\n' 'mod:mdecl;' 'pub error:EA;' 'pub error:EB;' \
    'pub func:g = int64(int64:x) never fails { pass x; };' > "$d/mdecl.npk"
  printf '%s\n' 'mod:cpriv;' 'use "./mpriv.npk".*;' 'error:EC;' 'func:main = int32(cstring[]:_~argv) {' \
    '    int64:v = f(1i64) ?! EC;' '    exit 0i32;' '};' > "$d/cpriv.npk"
  printf '%s\n' 'mod:cdecl;' 'use "./mdecl.npk".*;' 'func:main = int32(cstring[]:_~argv) {' \
    '    int64:v = raw g(1i64);' '    exit 0i32;' '};' > "$d/cdecl.npk"
}
