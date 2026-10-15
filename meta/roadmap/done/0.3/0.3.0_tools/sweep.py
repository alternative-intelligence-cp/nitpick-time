#!/usr/bin/env python3
"""0.3.0 -- the omission sweeps, blocks 1b's and 5b's (`0.2.4b_tools/sweep.py`, its
pathspec this plan's): a comparator proves the run equals the rehearsal and
cannot see a hunk the rehearsal never wrote, so this reads the committed tree
for statements of what the steps moved. TWO READINGS of every pattern,
because one line-based reading cannot see a phrase a line break splits (0.2.0's
record: "The three" / "modules in `support/`"), and the joined reading
cannot point at a line by itself:

  line    -- `git grep -n -I -i -E` at HEAD, line by line, case-insensitive
  joined  -- each tracked file read whole, each line's leading comment marker
             (`//`, `#`, `*`, `>`) stripped, the lines joined with spaces, and the
             pattern matched across them, case-insensitive; a hit is reported at
             the line it starts on

    python3 -B sweep.py <repo> <out-file> <pattern-file>

The pattern file holds one ERE per line (`#` lines are comments). The pathspec
is fixed below: the live tree, history excluded. It prints one line per
pattern -- `<n> line hits, <m> joined hits, <k> joined-only` -- and writes every
hit to <out-file> as `<pattern#> <reading> <path>:<line>: <text>`, which the
worker READS, every line. Only the counts are compared; the reading is the check.
"""
import bisect
import os
import re
import subprocess
import sys

PATHSPEC = [".", ":!meta/roadmap/done", ":!meta/audits", ":!meta/DECISIONS.md",
            ":!meta/roadmap/0.3/0.3.0.md", ":!meta/roadmap/0.3/0.3.0_tools",
            ":!meta/scratch", ":!*TRANSCRIPT.txt"]
_MARK = re.compile(r"^\s*(?://+|#+|\*|>)?\s?")


def git(root, *args):
    return subprocess.run(["git", "-C", root, *args], capture_output=True,
                          text=True, errors="replace").stdout


def main(argv):
    if len(argv) != 4:
        print(__doc__)
        return 2
    root, out, patfile = os.path.realpath(argv[1]), argv[2], argv[3]
    pats = [l.rstrip("\n") for l in open(patfile, encoding="utf-8")
            if l.strip() and not l.startswith("#")]
    files = [f for f in git(root, "ls-files", "-z", "--", *PATHSPEC).split("\0") if f]
    texts = {}
    for f in files:
        raw = open(os.path.join(root, f), "rb").read()
        if b"\0" in raw:
            continue
        texts[f] = raw.decode("utf-8", "replace").split("\n")
    with open(out, "w", encoding="utf-8") as fh:
        for k, pat in enumerate(pats, 1):
            line_hits = set()
            for row in git(root, "grep", "-n", "-I", "-i", "-E", pat, "HEAD", "--",
                           *PATHSPEC).splitlines():
                path, ln, text = row.split(":", 3)[1:]
                line_hits.add((path, int(ln)))
                fh.write("%d line %s:%s: %s\n" % (k, path, ln, text.strip()[:200]))
            rx = re.compile(pat, re.I)
            joined_hits, only = set(), 0
            for f, lines in sorted(texts.items()):
                clean = [_MARK.sub("", l) for l in lines]
                starts, pos = [], 0
                for l in clean:
                    starts.append(pos)
                    pos += len(l) + 1
                text = " ".join(clean)
                for m in rx.finditer(text):
                    ln = bisect.bisect_right(starts, m.start())
                    if (f, ln) in joined_hits:
                        continue
                    joined_hits.add((f, ln))
                    if (f, ln) not in line_hits:
                        only += 1
                        fh.write("%d joined %s:%d: %s\n"
                                 % (k, f, ln, text[m.start():m.end()][:200]))
            print("%d. %s: %d line hits, %d joined hits, %d joined-only"
                  % (k, pat, len(line_hits), len(joined_hits), only))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
