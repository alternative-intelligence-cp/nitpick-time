"""`repro` -- two builds of one tree must be the same bytes. Step 7, B-4, P-17.

WHAT IT COMPARES. Each root is emitted twice: once from the repository root with
a relative source path, once from a different working directory with an absolute
one. The two `.ll` files must be byte-identical (D-078, D-204, D-236). Measured
at pin `0dfddac`, they are -- `npkc` embeds no working directory and no argument
text in its output, which is what makes the check meaningful rather than
vacuous.

WHY IT IS BUILT NOW, BEFORE THERE IS ANYTHING TO GENERATE (P-17). The zone
tables will be the largest source file in the tree (`ZONE_MODEL.md` §3) and they
are GENERATED. A generator whose output varied with dictionary iteration order
would break byte-identity in a way no other check in this suite would notice:
the tables would still be sorted, the invariants would still hold, every test
would still pass, and two checkouts would differ. Building the check at 0.0.2
means 0.5 inherits it instead of inventing it under deadline.

`--between` IS WHY THIS IS A COMMAND AND NOT JUST A FUNCTION. `TESTING.md` §2's
`check_tables_regenerate` diffs the committed tables against a fresh generator
run. That is this check with a generator invoked between the two builds, so the
option exists now:

    python3 harness/repro.py --between tools/gen_tzdb.py -- src/zone/tzdb.npk

runs the generator between build A and build B and requires the emitted IR to be
unchanged. A generator that is deterministic changes nothing; one that is not
turns this check red, which is the entire point.

IT HAS BEEN SEEN TO FAIL. A check that has never failed has never been shown to
work, so this one was run once against a deliberately non-deterministic
generator -- a `fixed` table whose row order came from unsorted `set` iteration
-- and reported the first differing byte. The transcript is in
`meta/roadmap/done/0.0/0.0.2.md`.
"""

import os
import sys

from build import BuildError


def _first_difference(a, b):
    """Byte offset of the first difference, and the two lines around it."""
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            la = a.rfind(b"\n", 0, i) + 1
            lb = b.rfind(b"\n", 0, i) + 1
            return (i,
                    a[la:a.find(b"\n", i)].decode("utf-8", "replace"),
                    b[lb:b.find(b"\n", i)].decode("utf-8", "replace"))
    return (n, "<end of file>" if len(a) == n else "<longer>",
            "<end of file>" if len(b) == n else "<longer>")


def check(bld, roots, between=None, say=print):
    """Build each root twice and compare. Returns a list of problems.

    `between` is an argv run between the two builds, from the repository root.
    A non-zero status from it is itself a problem: a regeneration step that
    fails has not proved anything about determinism.
    """
    problems = []
    other_cwd = os.path.abspath(os.sep)
    for rel in roots:
        stem = os.path.basename(rel)[:-4]
        a = os.path.join(bld.out_dir, stem + ".repro-a.ll")
        b = os.path.join(bld.out_dir, stem + ".repro-b.ll")
        try:
            # A: from the repository root, relative path.
            bld.emit(rel, a, cwd=bld.root)
            if between:
                from build import run as _run
                st, out = _run(list(between), cwd=bld.root)
                if st != 0:
                    problems.append("%s: `%s` exited %d between the two "
                                    "builds:\n%s"
                                    % (rel, " ".join(between), st,
                                       out.rstrip()))
                    continue
            # B: from a different working directory, absolute path.
            bld.emit(os.path.join(bld.root, rel), b, cwd=other_cwd)
        except BuildError as err:
            problems.append("%s: %s -- %s" % (rel, err.step, err.detail))
            continue

        with open(a, "rb") as fh:
            ba = fh.read()
        with open(b, "rb") as fh:
            bb = fh.read()
        if ba == bb:
            say("  ok    %-40s %9d B, identical from two working directories"
                % (rel, len(ba)))
            continue
        off, la, lb = _first_difference(ba, bb)
        problems.append(
            "%s: the two builds differ. %d B vs %d B; first difference at byte "
            "%d.\n      A (from %s): %s\n      B (from %s): %s\n"
            "      B-4: two builds of the same tree from different working "
            "directories produce byte-identical IR. They did not."
            % (rel, len(ba), len(bb), off, bld.root, la[:160], other_cwd,
               lb[:160]))
    return problems


def main(argv):
    """`repro.py [--between CMD ARG... --] ROOT.npk ...`"""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(here, "harness"))
    import manifest as manifest_mod
    from build import Build

    between, roots, i = None, [], 0
    while i < len(argv):
        if argv[i] == "--between":
            between, i = [], i + 1
            while i < len(argv) and argv[i] != "--":
                between.append(argv[i])
                i += 1
            i += 1
            continue
        roots.append(argv[i])
        i += 1

    npkc = os.environ.get("NPKC")
    npkrt = os.environ.get("NPKRT")
    if not npkc or not npkrt:
        sys.stderr.write("repro.py: $NPKC and $NPKRT must both be set\n")
        return 2
    man = manifest_mod.load(here)
    bld = Build(here, man, npkc, npkrt, os.path.join(here, "build"))
    if not roots:
        roots = [man["build"]["entry"]]
    problems = check(bld, roots, between=between)
    for p in problems:
        sys.stdout.write("  FAIL  %s\n" % p)
    sys.stdout.write("repro: %d root(s), %d problem(s)\n"
                     % (len(roots), len(problems)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
