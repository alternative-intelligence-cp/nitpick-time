# meta/roadmap/0.4/0.4.0a_tools/facts.sh -- `0.4.0a.md` §1: re-derive what this plan rests on, at both pins, in
# scratch copies of the tree, never in it. Sourced after `env.sh`, in one Bash call -- block 0b of the plan, run
# BEFORE step 1:
#
#     . "$REPO/meta/roadmap/0.4/0.4.0a_tools/env.sh"; . "$T/facts.sh"
#
# `head` is the working tree as it stands; `s1` is it with step 1 applied and `s2` with steps 1 and 2, each by GNU
# `patch` into the copy alone (`git apply` run inside this checkout would resolve the paths against the checkout),
# dated as `apply.py` dates them. A program that imports the library sits in a copy's `tests/zz/`, and one that does
# not in `$F/p`; each is built and run at the pin it is asked of (`legs`). A check is asked of its OWN tree's
# harness. The unchanged tree's censuses are kept as `$A/head_old.tsv` and `$A/head_new.tsv` for blocks 1 … 3;
# everything else here is removed at the end. One network read: GitHub's record of the LLVM asset CI installs.
: "${REPO:?}" "${A:?}" "${T:?}" "${PIN:?}" "${OLD:?}" "${NTIME_RUN_DATE:?}"
F=$A/facts
MID=c9baa9e                                   # the pin between, landing 118, which this repository never took
fresh() {   # fresh <name> [<step>...]: the working tree as it stands at $F/<name>, then each step's patch
  local d=$1 n; shift
  mkdir -p "$F/$d"
  ( cd "$REPO" && git ls-files -co --exclude-standard -z | xargs -0 tar -cf - ) | tar -xf - -C "$F/$d"
  for n in "$@"; do
    sed "s/@@DATE040A@@/$NTIME_RUN_DATE/g" "$T/step$n.patch" | patch -p1 -s --no-backup-if-mismatch -d "$F/$d" \
      || echo "STOP: step$n does not apply to a copy of the tree"
  done
}
FS=$(sed -n '/^func:failsafe/,$p' "$REPO/tests/unit/bytes_view_lifetime.npk")   # twelve arms and the catch-all
prog() {    # prog <dir> <name> <body of main>, declarations on stdin: a program in <dir>
  { printf 'mod:%s;\n\n' "$2"; cat; printf 'func:main = int32(cstring[]:_~argv) {\n%s\n};\n\n%s\n' "$3" "$FS"; } > "$1/$2.npk"
}

rm -rf "${F:?}"; mkdir -p "$F/p"
fresh head; fresh s1 1; fresh s2 1 2

# ---- §1.1 the pins: the landings between, and the landings past
landings() { git -C "$NPK_TREE" log --format=%s "$1" | sed -nE 's/^[0-9.a-z]+, landing ([0-9]+):.*/\1/p' | sort -n; }
echo "§1.1 $OLD..$PIN on the compiler's history: $(git -C "$NPK_TREE" rev-list --count $OLD..$PIN) commit(s), $(landings $OLD..$PIN | wc -l) of them landings, $(landings $OLD..$PIN | head -1) ... $(landings $OLD..$PIN | tail -1); $MID between them: $(git -C "$NPK_TREE" merge-base --is-ancestor $OLD $MID && git -C "$NPK_TREE" merge-base --is-ancestor $MID $PIN && echo yes)"
echo "§1.1 past $PIN, to 6370cae (the compiler's main at planning): $(git -C "$NPK_TREE" log --format='%h %s' $PIN..6370cae | cut -c1-90)"
echo "§1.1 the compiler's main past 6370cae: $(git -C "$NPK_TREE" rev-list --count 6370cae..main 2>/dev/null) commit(s)"
python3 -B "$T/nested.py" "$REPO" | sed 's/^/§1.1 landing 141 (DEF-268), this tree: /'

# ---- §1.2 the unchanged tree past the self-check at the new pin -- an inner run, `--root`, the self-check skipped
( leg $PIN; cd "$F/head" && python3 -B harness/run.py --root "$F/head" ) > "$A/head_inner.log" 2>&1
echo "§1.2 the unchanged tree at $PIN past the self-check (\`--root\`): exit $?"
grep -E '^(GREEN|RED) -- ' "$A/head_inner.log" | sed -E 's/ in [0-9.]+ s//; s/^/  /' | cut -c1-170
grep -E '^  FAIL  ' "$A/head_inner.log" | sed 's/^  FAIL  /  FAIL /'
python3 -B - "$REPO/harness" "$F/p" <<'PY'
import os, sys
sys.path.insert(0, sys.argv[1])
import selfcheck
forms = list(selfcheck._NUM_FORMS)
for k, (expr, value) in enumerate(forms):
    want = "%di64" % value if value >= 0 else "(0i64 - %di64)" % -value
    open(os.path.join(sys.argv[2], "n%02d.npk" % k), "w").write(
        "mod:n%02d;\nfunc:main = int32(cstring[]:_~argv) {\n    if (%s != %s) { exit 10i32; }\n    exit 0i32;\n};\n%s"
        % (k, expr, want, selfcheck._NUM_FAILSAFE))
print("§1.2 part E's third half: %d spelling(s) in `_NUM_FORMS`, and the loop's bound beside them" % len(forms))
PY
for p in $OLD $PIN; do
  ok=0; bad=""
  for f in "$F"/p/n*.npk; do
    r=$(codes $p "$f"); case "$r" in *compiles) ok=$((ok + 1)) ;; *) bad="$bad $(sed -n 's/^    if (\([^ ]*\) .*/\1/p' "$f") ${r#*: }" ;; esac
  done
  echo "§1.2 each spelling alone at $p: $ok compile${bad:+; refused:$bad}"
done

# ---- §1.3 every file a root, at three pins
echo "§1.3 the unchanged tree, every .npk a root:"
census $OLD "$REPO" head_old | sed 's/^/  /'
census $MID "$REPO" head_mid | sed 's/^/  /'
census $PIN "$REPO" head_new | sed 's/^/  /'
echo "§1.3 $OLD against $MID:"
python3 -B "$T/census.py" compare "$A/head_old.tsv" "$A/head_mid.tsv" | sed 's/^/  /'
echo "§1.3 $OLD against $PIN:"
python3 -B "$T/census.py" compare "$A/head_old.tsv" "$A/head_new.tsv" | sed 's/^/  /' | cut -c1-230
python3 -B "$T/census.py" sites "$A/head_new.tsv" NITPICK-BORROW-015 | sed 's/^/  /'
rm -f "$A/head_mid.tsv"

# ---- §1.4 every refusal, judged by the runner's own reader, at both pins
echo "§1.4 every refusal judged by the unchanged tree's own stages.refusal:"
refusals "$REPO" $OLD $PIN | sed 's/^/  /' | cut -c1-170

# ---- §1.5 the freeze, call by call: each public call of the sink made while a view of it lives
mkdir -p "$F/s1/tests/zz"
for call in "drop bytes_push(@b, 66u8);" "drop bytes_extend(@b, string_bytes(\"xy\"));" "drop bytes_extend_str(@b, \"xy\");" \
    "drop bytes_put_uint(@b, 7u64);" "drop bytes_put_int(@b, 7i64);" "drop bytes_reserve(@b, 1i64);" "drop bytes_clear(@b);" \
    "int64:k = raw bytes_len(@b);" "int64:k = raw bytes_capacity(@b);" "uint8[]:w = raw bytes_view(@b);" \
    "string:s = raw bytes_take(@b);"; do
  n=$(echo "$call" | grep -oE 'bytes_[a-z_]+' | head -1)
  prog "$F/s1/tests/zz" "fz_$n" "    Bytes:b = raw bytes_init(64i64);
    drop bytes_push(@b, 65u8);
    uint8[]:v = raw bytes_view(@b);
    $call
    if (v[0i64] != 65u8) { exit 10i32; }
    exit 0i32;" <<'NPK'
use "../../src/core/bytes.npk".*;

NPK
done
verdict() {  # verdict <pin> <file>: `admitted`, or the codes it reports with their sites
  local r; r=$(codes "$1" "$2"); case "$r" in *" compiles") echo admitted ;; *) echo "${r#*: }" ;; esac
}
for p in $OLD $PIN; do
  echo "§1.5 a view held across each call, over step 1's tree, at $p:"
  for f in "$F"/s1/tests/zz/fz_*.npk; do n=$(basename "$f" .npk); echo "  ${n#fz_}: $(verdict $p "$f")"; done
done

# ---- §1.5 the stale read, as `probe10d` holds it, at both pins, over step 1's tree
prog "$F/s1/tests/zz" zz_stale "    Bytes:c = raw bytes_init(2i64);
    int64:i = 0i64;
    while (i < 2i64) decreases 2i64 - i { drop bytes_push(@c, 65u8); i = i + 1i64; }
    uint8[]:w = raw bytes_view(@c);
    if (w[0i64] != 65u8) { exit 21i32; }
    i = 0i64;
    while (i < 40i64) decreases 40i64 - i { drop bytes_push(@c, 66u8); i = i + 1i64; }
    exit (w[0i64] => int32);" <<'NPK'
use "../../src/core/bytes.npk".*;

NPK
for p in $OLD $PIN; do legs $p "$F/s1/tests/zz/zz_stale.npk" "§1.5 the stale read at $p"; done
rm -rf "${F:?}/s1/tests/zz"

# ---- §1.6 the unit as step 1 spells it, at both pins
for p in $OLD $PIN; do legs $p "$F/s1/tests/unit/bytes_view_lifetime.npk" "§1.6 bytes_view_lifetime, step 1's spelling, at $p"; echo "  $(heapline $p "$F/s1/tests/unit/bytes_view_lifetime.npk")"; done

# ---- §1.7 bytes_view's answer: a write through it, as it stands and as step 2 makes it
for t in s1 s2; do
  mkdir -p "$F/$t/tests/zz"
  slot=$([ $t = s1 ] && echo 'uint8[]' || echo 'fixed uint8[]')
  prog "$F/$t/tests/zz" zz_write "    Bytes:b = raw bytes_init(4i64);
    drop bytes_push(@b, 97u8);
    $slot:v = raw bytes_view(@b);
    v[0i64] = 65u8;
    $slot:w = raw bytes_view(@b);
    exit (w[0i64] => int32);" <<'NPK'
use "../../src/core/bytes.npk".*;

NPK
  prog "$F/$t/tests/zz" zz_plain "    Bytes:b = raw bytes_init(4i64);
    drop bytes_push(@b, 97u8);
    uint8[]:v = raw bytes_view(@b);
    exit (v[0i64] => int32);" <<'NPK'
use "../../src/core/bytes.npk".*;

NPK
done
for p in $OLD $PIN; do
  legs $p "$F/s1/tests/zz/zz_write.npk" "§1.7 a write through the answer, read back, after step 1, at $p"
  legs $p "$F/s2/tests/zz/zz_write.npk" "§1.7 the same after step 2, at $p"
  legs $p "$F/s2/tests/zz/zz_plain.npk" "§1.7 a plain slot binding the answer after step 2, at $p"
done
rm -rf "${F:?}/s1/tests/zz" "${F:?}/s2/tests/zz"

# ---- §1.8 who may claim `Copy`: in this tree, for a builtin and for the library's own type; in a tree of its own
mkdir -p "$F/s1/tests/zz" "$F/consumer"
FS19=$(sed -n '/^func:failsafe/,$p' "$REPO/tests/probe/probe19_pod_owner_refused.npk")
claim() {   # claim <dir> <name> <use lines> <impl line>
  printf 'mod:%s;\n\n%s\n\n%s\n\nfunc:main = int32(cstring[]:_~argv) {\n    exit 0i32;\n};\n\n%s\n' "$2" "$3" "$4" "$FS19" > "$1/$2.npk"
}
claim "$F/s1/tests/zz" zq_string 'use "../../src/core/vec.npk".*;' 'impl:string:Copy = { };'
claim "$F/s1/tests/zz" zq_bytes 'use "../../src/core/vec.npk".*;
use "../../src/core/bytes.npk".Bytes;' 'impl:Bytes:Copy = { };'
claim "$F/s1/tests/zz" zq_owner 'use "../../src/core/vec.npk".*;

struct:Owner = { string:name; };' 'impl:Owner:Copy = { };'
claim "$F/consumer" zq_consumer 'use "../s1/src/core/vec.npk".*;
use "../s1/src/core/bytes.npk".Bytes;' 'impl:Bytes:Copy = { };'
printf '[project]\nname = "consumer"\nversion = "0.0.0"\n' > "$F/consumer/nitpick.toml"
for f in "$F/s1/tests/zz/zq_string" "$F/s1/tests/zz/zq_bytes" "$F/s1/tests/zz/zq_owner" "$F/consumer/zq_consumer"; do
  echo "§1.8 $(basename "$f"): $(codes $OLD "$f.npk" | sed 's/^[^ ]* //'); $(codes $PIN "$f.npk" | sed 's/^[^ ]* //')"
done
echo "§1.8 the judgement at $PIN: $( ( cd "$F/s1/tests/zz" && "$WB/.internal/toolchain/$PIN/npkc" zq_bytes.npk -o /dev/null 2>&1 ) | grep -oE '`Bytes` owns what it holds, so a copy of it would be a second owner')"
rm -rf "${F:?}/s1/tests/zz" "${F:?}/consumer"

# ---- §1.9 the compiler's lexer, re-read (TM-202)
echo "§1.9 the files the re-read names, $OLD to $PIN:"
git -C "$NPK_TREE" diff --stat $OLD $PIN -- src/frontend/lexer.npk src/frontend/escapes.npk src/frontend/parse_decl.npk \
  meta/specs/LEXICAL_REFERENCE.md src/frontend/numeric.npk src/frontend/num_width.npk | sed 's/^/ /'
for fn in parse_decl.npk:p_parse_import numeric.npk:num_scan num_width.npk:num_width_of; do for p in $OLD $PIN; do
  echo "§1.9 ${fn#*:} at $p: $(git -C "$NPK_TREE" show $p:src/frontend/${fn%%:*} | awk "/^(pub )?func:${fn#*:} /,/^};/" | sha256sum | cut -c1-16)"
done; done

# ---- §1.10 a local named after a keyword, at both pins
for n in uid gid pid tid fd thread cfg arena stack unit end limit in on mod fixed range error buffer raw move drop pass fail \
    relay give pick fall any as with where is is_err never fails defaults prove assert_static requires ensures acquires gives \
    invariant old result pure decreases unbounded sealed hidden Ordering ppid measure; do
  printf 'mod:rw_%s;\n\nfunc:main = int32(cstring[]:_~argv) {\n    int64:%s = 1i64;\n    exit 0i32;\n};\n\n%s\n' "$n" "$n" "$FS" > "$F/p/rw_$n.npk"
done
for p in $OLD $PIN; do
  common=$([ $p = $OLD ] && echo 'NITPICK-PARSE-002 4:5' || echo 'NITPICK-PARSE-001 4:11')
  n_common=0; others=""
  for f in "$F"/p/rw_*.npk; do
    v=$(verdict $p "$f"); w=$(basename "$f" .npk); w=${w#rw_}
    if [ "$v" = "$common" ]; then n_common=$((n_common + 1)); else others="$others $w ($v);"; fi
  done
  echo "§1.10 at $p: $n_common of $(ls "$F"/p/rw_*.npk | wc -l) words \`$common\`; the others:$others"
done

# ---- §1.10 three readings the last adoption's record calls true as written, asked again
printf 'mod:tw_asm;\n\nfunc:main = int32(cstring[]:_~argv) {\n    int64:k = asm<int64>(1i64);\n    exit 0i32;\n};\n\n%s\n' "$FS" > "$F/p/tw_asm.npk"
mkdir -p "$F/s1/tests/zz"
printf 'mod:tw_vecinit;\n\nuse "../../src/core/vec.npk".*;\n\nfunc:main = int32(cstring[]:_~argv) {\n    Vec<int64>:v = raw vec_init<int64>(2i64);\n    drop vec_free(@v);\n    exit 0i32;\n};\n\n%s\n' "$FS" > "$F/s1/tests/zz/tw_vecinit.npk"
printf 'mod:tw_taint;\n\nerror:ETake;\n\nfunc:take = int64(int64:k) {\n    if (k > 9i64) { fail ETake; }\n    pass k;\n};\n\nfunc:main = int32(cstring[]:_~argv) {\n    Result<int64>:r = take(4i64);\n    int64:v = r.value;\n    if (r.is_error) { exit 3i32; }\n    exit (v =>! int32);\n};\n\n%s\n' \
  "$(echo "$FS" | sed 's/^        (DivByZero) /        (ETake)  { exit 80i32; },\n        (DivByZero) /')" > "$F/p/tw_taint.npk"
for f in "$F/p/tw_asm.npk" "$F/s1/tests/zz/tw_vecinit.npk" "$F/p/tw_taint.npk"; do
  echo "§1.10 $(basename "$f" .npk): $(verdict $OLD "$f") at $OLD; $(verdict $PIN "$f") at $PIN"
done
rm -rf "${F:?}/s1/tests/zz"

# ---- §1.11 a module binding with no initialiser, at both pins
printf 'mod:mb_none;\n\nint64:counter;\n\nfunc:main = int32(cstring[]:_~argv) {\n    counter = 7i64;\n    exit (counter =>! int32);\n};\n\n%s\n' "$FS" > "$F/p/mb_none.npk"
for p in $OLD $PIN; do legs $p "$F/p/mb_none.npk" "§1.11 a module binding with no initialiser, written, at $p"; done

# ---- §1.12 TM-171's table: spellable at the new pin, and what it changes under the weekday mutants
for v in cast table; do for m in none D1 D2; do
  d="$F/w171/$v$m"; mkdir -p "$d"
  ( cd "$F/s2" && tar -cf - nitpick.toml src tests/unit/derived_field_vectors.npk tests/unit/sweep/every_civil_date.npk ) | tar -xf - -C "$d"
  if [ $v = table ]; then python3 -B - "$d/src/cal/cal.npk" <<'PY'
import sys
p = sys.argv[1]; t = open(p, encoding="utf-8").read()
old = "    pass ((raw weekday_index(raw date_to_days(cd))) =>! int32) =>! Weekday;\n"
anchor = "pub func:weekday = Weekday(CivilDate:cd) never fails {\n"
assert t.count(old) == 1 and t.count(anchor) == 1
t = t.replace(old, "    pass WEEKDAY_OF_INDEX[raw weekday_index(raw date_to_days(cd))];\n")
t = t.replace(anchor, "fixed Weekday[7]:WEEKDAY_OF_INDEX = [Weekday.Monday, Weekday.Tuesday, Weekday.Wednesday, Weekday.Thursday,\n"
              "                                     Weekday.Friday, Weekday.Saturday, Weekday.Sunday];\n\n" + anchor)
open(p, "w", encoding="utf-8").write(t)
PY
  fi
  case $m in
    D1) sed -i '/^    if (rem < 0i64) { rem = rem + 7i64; }$/d' "$d/src/cal/cal.npk" ;;
    D2) sed -i '/^    if (rem < 0i64) { rem = rem + 7i64; }$/d; /^    if ((rem < 0i64) || (rem > 6i64)) { #unreachable(); }$/d' "$d/src/cal/cal.npk" ;;
  esac
done; done
for p in $OLD $PIN; do echo "§1.12 the table at $p: $(verdict $p "$F/w171/tablenone/src/cal/cal.npk")"; done
for v in cast table; do for m in none D1 D2; do
  d="$F/w171/$v$m"
  echo "§1.12 $v, $m, at $PIN: $(legs $PIN "$d/tests/unit/derived_field_vectors.npk" derived_field_vectors); $(legs $PIN "$d/tests/unit/sweep/every_civil_date.npk" every_civil_date)"
done; done
rm -rf "${F:?}/w171"

# ---- §1.13 the adoption list's int128 arithmetic: the umbrella over step 2's tree, at both pins and legs
mkdir -p "$F/ir"
for p in $OLD $PIN; do
  ( leg $p; cd "$F/s2/src" && "$NPKC" lib.npk -o "$F/ir/lib.$p.ll" \
    && llc -O0 -filetype=obj -relocation-model=static "$F/ir/lib.$p.ll" -o "$F/ir/lib.$p.0.o" \
    && opt -O2 -S "$F/ir/lib.$p.ll" -o "$F/ir/lib.$p.2.ll" \
    && llc -O2 -filetype=obj -relocation-model=static "$F/ir/lib.$p.2.ll" -o "$F/ir/lib.$p.2.o"
    echo "§1.13 at $p, the umbrella declares $(grep -oE 'declare [^@]*@llvm\.s(mul|sub)\.with\.overflow\.i128' "$F/ir/lib.$p.ll" | grep -oE 'llvm\.s(mul|sub)[a-z.]*i128' | sort | tr '\n' ' ')"
    for o in 0 2; do
      echo "§1.13 at $p, its object at -O$o: $(llvm-nm -u "$F/ir/lib.$p.$o.o" | wc -l) undefined symbol(s), $(llvm-nm -u "$F/ir/lib.$p.$o.o" | awk '{print $NF}' | grep -vcE '^(npk_[a-z0-9_]+|__morestack)$') of them not the runtime's"
    done )
done

# ---- §1.14 the builtin table and the prelude, at both pins
for p in $OLD $PIN; do
  git -C "$NPK_TREE" show $p:src/frontend/builtins.npk | awk '/func:is_builtin_name /,/^};/' | grep -oE '"[a-z_0-9]+"' | sort -u > "$F/bi.$p"
  git -C "$NPK_TREE" show $p:src/prelude/prelude.npk | grep -oE '^pub (async )?func:[A-Za-z_0-9]+' | sort -u > "$F/pre.$p"
done
echo "§1.14 the builtin table's names: $(wc -l < "$F/bi.$OLD") at $OLD, $(wc -l < "$F/bi.$PIN") at $PIN, $(comm -3 "$F/bi.$OLD" "$F/bi.$PIN" | wc -l) differing"
echo "§1.14 the prelude's public functions: $(wc -l < "$F/pre.$OLD") at $OLD, $(wc -l < "$F/pre.$PIN") at $PIN, $(comm -3 "$F/pre.$OLD" "$F/pre.$PIN" | wc -l) differing; the prelude's files differ in $(git -C "$NPK_TREE" diff --name-only $OLD $PIN -- src/prelude | wc -l) file(s)"
echo "§1.14 the builtin rows that moved: $(git -C "$NPK_TREE" diff $OLD $PIN -- src/frontend/builtins.npk | grep -E '^\+ ' | grep -v '//' | sed 's/^+ *//')"

# ---- §1.15 the readings of npkc's output, over step 2's tree, which both compilers build
emissions "$F/s2" $OLD $PIN | sed 's/^/§1.15 /' | cut -c1-170
across "$F/s2" "$F/across" | sed 's/^/§1.15 /' | cut -c1-170

# ---- §1.17 CI's rows, and the LLVM asset
echo "§1.17 $PIN is $(git -C "$NPK_TREE" rev-parse $PIN); its emission row: $(grep -m1 ' npkc.ll ' "$WB/.internal/toolchain/$PIN/PIN.md" | awk '{print $2, $3}')"
echo "§1.17 the workbench's digests: $(cut -c1-16 "$WB/.internal/toolchain/$PIN/SHA256SUMS" | tr '\n' ' ')"
git -C "$NPK_TREE" diff --quiet $OLD $PIN -- bootstrap/harness/quickemit.py && echo "§1.17 bootstrap/harness/quickemit.py: the same at both pins"
git -C "$NPK_TREE" cat-file -e $PIN:npkg/main.npk && echo "§1.17 npkg/main.npk: present at $PIN"
gh api repos/llvm/llvm-project/releases/tags/llvmorg-20.1.8 --jq '"§1.17 the LLVM release: immutable \(.immutable); its asset \(.assets[] | select(.name == "LLVM-20.1.8-Linux-X64.tar.xz") | "\(.name), \(.size) B, \(.digest), updated \(.updated_at)")"' 2>&1 | head -2

rm -rf "${A:?}/head"; mv "$F/head" "$A/head"    # the unchanged tree, kept for block 1's emissions
rm -rf "${F:?}"
