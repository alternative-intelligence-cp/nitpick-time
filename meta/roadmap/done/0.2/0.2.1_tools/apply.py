#!/usr/bin/env python3
"""0.2.1 -- apply one step's patch -- all-or-nothing -- and say which of three states the tree
was in. The plan beside this directory names the steps; `stepN.patch` is each one's
text, a `git diff` of the tree the plan was rehearsed on, and the review surface: a
worker may tighten a text, never change what it says, and amends THE PATCH, never
the tree by hand (the workbench `PLAYBOOK.md` §12).

    python3 -B apply.py <N> "$REPO"

`@@DATE@@` in a patch is replaced by today's date before anything is compared, so a
dated note carries the day the worker ran it. Then, with `git apply --index` (the
index and the working tree together, renames included):

  * the patch applies IN REVERSE  -> ALREADY: the step is in the tree; nothing written
  * the patch applies             -> APPLY: written and staged, every file of it
  * neither                       -> STOP: the tree is not the one the patch was measured
                                     on, and nothing was written; read `git status` and
                                     the message, find the drift, and amend the patch

`git apply` checks every hunk before it writes any, so a STOP writes nothing. A re-run
on the same day reports ALREADY; on a later day the dates differ and it STOPs, which
is the safe answer.
"""
import datetime
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    n, root = argv[1], os.path.realpath(argv[2])
    path = os.path.join(HERE, f"step{n}.patch")
    if not os.path.isfile(path):
        print(f"STOP step{n}: no {os.path.basename(path)} beside this tool")
        return 1
    with open(path, encoding="utf-8", newline="") as fh:
        text = fh.read().replace("@@DATE@@", datetime.date.today().isoformat())

    def git(*args):
        return subprocess.run(["git", "-C", root, "apply", "--index", *args, "-"],
                              input=text, text=True, capture_output=True)

    if git("--reverse", "--check").returncode == 0:
        print(f"ALREADY step{n}")
        return 0
    r = git("--check")
    if r.returncode == 0:
        r = git()
    if r.returncode != 0:
        print(f"STOP step{n}: " + " | ".join(r.stderr.strip().splitlines()[:6]))
        return 1
    print(f"APPLY step{n}: {text.count(chr(10) + 'diff --git') + text.startswith('diff --git')} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
