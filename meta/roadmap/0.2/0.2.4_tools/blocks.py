#!/usr/bin/env python3
"""0.2.4 -- run the plan's command blocks, and COMPARE each one's output with the
plan's expected output. The workbench `PLAYBOOK.md` §12: "the durable form of
'quote a command's whole output' is a COMPARATOR" -- care drops lines; this does not.
`0.2.3_tools/blocks.py`, pointed at this plan -- found beside these tools, so it is found after the archive moves both.

    python3 -B blocks.py list    "$REPO"             # the blocks, in order
    python3 -B blocks.py run     "$REPO" <id> [...]  # run blocks, save outputs
    python3 -B blocks.py compare "$REPO" <id> [...]  # diff saved outputs vs Expect

A BLOCK is a fenced `bash` block in `0.2.4.md` whose first line is `# block <id>`;
it is run by a fresh `bash -c` with only `REPO=<the repository>` before it --
exactly the worker's situation, where no variable or function survives from one
call to the next. Its output (stdout and stderr) goes to
`$REPO/.internal/w024/blocks/<id>.out`.

Its EXPECTED output is the fenced `text` block whose first line is
`# expect <id>`. The comparison masks what legitimately varies from run to run --
a harness's seconds (`, 169.5 s.`), the machine's free memory (`available GiB:`),
a date -- and nothing else; a line the plan marks `# (any)` matches any one line.
It prints `SAME <id>` or the differing lines, and exits 1 if any block differs.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PLAN = os.path.join(HERE, "..", "0.2.4.md")          # beside these tools, wherever the archive puts them
FENCE = re.compile(r"^```(bash|text)\n(.*?)^```", re.S | re.M)
_MASKS = [
    (re.compile(r"\b\d+\.\d+ s\b"), "<s> s"),
    (re.compile(r"available GiB: \d+"), "available GiB: <n>"),
    (re.compile(r"\b\d{4}-\d{2}-\d{2}\b"), "<date>"),
]


def blocks(root):
    with open(PLAN, encoding="utf-8") as fh:
        text = fh.read()
    runs, expects = {}, {}
    order = []
    for m in FENCE.finditer(text):
        kind, body = m.group(1), m.group(2)
        first = body.split("\n", 1)[0].strip()
        if kind == "bash" and first.startswith("# block "):
            bid = first.split()[2]
            runs[bid] = body
            order.append(bid)
        elif kind == "text" and first.startswith("# expect "):
            expects[first.split()[2]] = body.split("\n", 1)[1] if "\n" in body else ""
    return order, runs, expects


def mask(line):
    for pat, rep in _MASKS:
        line = pat.sub(rep, line)
    return line.rstrip()


def compare_one(got, want):
    g = [mask(x) for x in got.rstrip("\n").split("\n")] if got.strip() else []
    w = [mask(x) for x in want.rstrip("\n").split("\n")] if want.strip() else []
    diffs = []
    for i in range(max(len(g), len(w))):
        a = g[i] if i < len(g) else "<missing>"
        b = w[i] if i < len(w) else "<missing>"
        if b.strip() == "# (any)" and a != "<missing>":
            continue
        if a != b:
            diffs.append(f"    line {i + 1}: got  {a}\n    line {i + 1}: want {b}")
    return diffs


def main(argv):
    if len(argv) < 3 or argv[1] not in ("list", "run", "compare"):
        print(__doc__)
        return 2
    cmd, root = argv[1], os.path.realpath(argv[2])
    order, runs, expects = blocks(root)
    ids = argv[3:] or order
    outdir = os.path.join(root, ".internal", "w024", "blocks")
    os.makedirs(outdir, exist_ok=True)
    if cmd == "list":
        for b in order:
            print(f"{b:6} expect={'yes' if b in expects else 'NO'}")
        return 0
    bad = 0
    for b in ids:
        if b not in runs:
            print(f"NO BLOCK {b}")
            bad += 1
            continue
        path = os.path.join(outdir, f"{b}.out")
        if cmd == "run":
            r = subprocess.run(["bash", "-c", f"REPO={root!r}\n" + runs[b]],
                               capture_output=True, text=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(r.stdout + r.stderr)
            print(f"RAN  {b}: bash exit {r.returncode}, {len((r.stdout + r.stderr).splitlines())} lines")
        else:
            if b not in expects:
                print(f"NO EXPECT {b}")
                bad += 1
                continue
            got = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
            d = compare_one(got, expects[b])
            if d:
                bad += 1
                print(f"DIFF {b}")
                print("\n".join(d))
            else:
                print(f"SAME {b}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
