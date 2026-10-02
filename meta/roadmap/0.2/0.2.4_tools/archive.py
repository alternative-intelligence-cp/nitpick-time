#!/usr/bin/env python3
"""0.2.4 -- ARCHIVE CYCLE 0.2: `git mv meta/roadmap/0.2 meta/roadmap/done/0.2`, and
re-point what navigates to it, by the line `nitpick-regex`'s RX-140 drew and this
repository's 0.0.6 and 0.1.5 followed: LIVE NAVIGATION IS CORRECTED, HISTORICAL
CLAIMS ARE NOT. `0.1.5.md` §8.4's `archive.py`, in the two halves its second half
ran as two scripts (the workbench `PLAYBOOK.md`: "move in one commit and rewrite
in the next" meets "`check_refs` clean or no commit" in a move commit that
carries only the links the move breaks):

    archive.py check      -- report what each half would do; write nothing
    archive.py move       -- `git mv`, then every markdown LINK the move breaks:
                             one inside the folder that leaves it gains a `../`,
                             and one outside it that enters it is re-pointed
    archive.py mentions   -- every other mention of the folder outside it -- a
                             plain path, in any tracked text file -- re-pointed

OUTSIDE the folder, the records are left as written: `meta/DECISIONS.md` (a settled
decision's text is never rewritten), the earlier archives `meta/roadmap/done/0.0/`
and `done/0.1/`, and the transcripts. INSIDE it, a plain path is left: it says
where a file was when its note was written. Reads and writes with `newline=""`,
so no byte it was not asked to change moves. Stops if the folder is already gone
(`move`), if `done/0.2` exists (`move`), if the folder is not gone (`mentions`),
or if a live mention is left after `mentions`.
"""
import os, re, subprocess, sys

REPO = os.environ["REPO"]
OLD, NEW = "meta/roadmap/0.2", "meta/roadmap/done/0.2"
RECORDS = re.compile(r"^meta/DECISIONS\.md$|^meta/roadmap/done/0\.[01]/|TRANSCRIPT\.txt$")
# A mention of the folder: a repository path (`meta/roadmap/0.2/`, and the
# relative `roadmap/0.2/` the specifications and the questions use), a
# sibling-relative one (`../0.2/`), or `0.2/` before one of its files, not
# preceded by a path character.
MENTION = re.compile(r"(?<![A-Za-z0-9_./-])((?:\.\./)*(?:meta/)?roadmap/)0\.2/"
                     r"|(?<![A-Za-z0-9_./-])((?:\.\./)+)0\.2/"
                     r"|(?<![A-Za-z0-9_./-])0\.2/(?=0\.2\.|README\.md)")
LINK = re.compile(r"\]\(([^)#\s]+)(#[^)]*)?\)")


def read(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return fh.read()


def write(p, t):
    with open(p, "w", encoding="utf-8", newline="") as fh:
        fh.write(t)


def tracked():
    out = subprocess.run(["git", "-C", REPO, "ls-files"], stdout=subprocess.PIPE,
                         text=True).stdout
    return [l for l in out.split("\n") if l]


def text_of(rel):
    try:
        return read(os.path.join(REPO, rel))
    except (UnicodeDecodeError, IsADirectoryError, FileNotFoundError):
        return None


def _repoint(m):
    if m.group(1) is not None:                  # `…roadmap/0.2/`
        return m.group(1) + "done/0.2/"
    if m.group(2) is not None:                  # `../0.2/`
        return m.group(2) + "done/0.2/"
    return "done/0.2/"                          # `0.2/` beside `done/`


def outside_links(rel, text):
    """Markdown links in a file outside the folder that resolve into it."""
    count = 0
    base = os.path.dirname(rel)

    def sub(m):
        nonlocal count
        t = m.group(1)
        if t.startswith(("http://", "https://", "mailto:", "#", "/")):
            return m.group(0)
        landed = os.path.normpath(os.path.join(base, t))
        if not (landed == OLD or landed.startswith(OLD + "/")):
            return m.group(0)
        count += 1
        new = MENTION.sub(_repoint, t, count=1)
        # `]` and `(` built apart: a plan quotes this script.
        return "]" + "(" + new + (m.group(2) or "") + ")"
    return LINK.sub(sub, text), count


def inside_links(rel_new, text):
    """`rel_new` is the file's NEW path; a link resolved from its OLD directory
    that lands outside the folder gains one `../`."""
    old_dir = os.path.dirname(rel_new.replace(NEW, OLD, 1))
    count = 0

    def sub(m):
        nonlocal count
        t = m.group(1)
        if t.startswith(("http://", "https://", "mailto:", "#", "/")):
            return m.group(0)
        landed = os.path.normpath(os.path.join(old_dir, t))
        if landed == OLD or landed.startswith(OLD + "/"):
            return m.group(0)
        count += 1
        return "]" + "(" + "../" + t + (m.group(2) or "") + ")"
    return LINK.sub(sub, text), count


def plain(text):
    """Every mention of the folder that is NOT inside a markdown link's target."""
    spans = [(m.start(1), m.end(1)) for m in LINK.finditer(text)]
    hits = [m for m in MENTION.finditer(text)
            if not any(a <= m.start() < b for a, b in spans)]
    return hits


def main(mode):
    files = tracked()
    inside = [f for f in files if f.startswith(OLD + "/")]
    outside = [f for f in files if not f.startswith(OLD + "/") and not RECORDS.search(f)
               and not f.startswith(NEW + "/")]
    if mode in ("check", "move"):
        if not os.path.isdir(os.path.join(REPO, OLD)):
            sys.exit("STOP: %s is not a directory -- already archived?" % OLD)
        if os.path.exists(os.path.join(REPO, NEW)):
            sys.exit("STOP: %s exists" % NEW)
        print("the folder: %d tracked file(s)" % len(inside))
        n_out = f_out = 0
        for rel in outside:
            t = text_of(rel)
            if t is None or not rel.endswith(".md"):
                continue
            new, n = outside_links(rel, t)
            if n:
                n_out += n
                f_out += 1
                print("  link     %-58s %3d" % (rel, n))
                if mode == "move":
                    write(os.path.join(REPO, rel), new)
        print("links into the folder from outside it: %d in %d file(s)" % (n_out, f_out))
        n_in = 0
        if mode == "move":
            r = subprocess.run(["git", "-C", REPO, "mv", OLD, NEW])
            if r.returncode != 0:
                sys.exit("STOP: git mv exited %d" % r.returncode)
        for rel in inside:
            if not rel.endswith(".md"):
                continue
            rel_new = rel.replace(OLD, NEW, 1)
            p = os.path.join(REPO, rel_new if mode == "move" else rel)
            new, n = inside_links(rel_new, read(p))
            if n:
                n_in += n
                print("  inside   %-58s %3d" % (rel_new, n))
                if mode == "move":
                    write(p, new)
        print("links leaving the folder from inside it: %d" % n_in)
        n_plain = f_plain = 0
        for rel in outside:
            t = text_of(rel)
            if t is None:
                continue
            k = len(plain(t))
            if k:
                n_plain += k
                f_plain += 1
        print("plain mentions outside it, left for `mentions`: %d in %d file(s)"
              % (n_plain, f_plain))
        left = sum(len(MENTION.findall(text_of(f) or "")) for f in files
                   if f == "meta/DECISIONS.md")
        print("left as written in meta/DECISIONS.md, settled text: %d mention(s)" % left)
        if mode == "move":
            print("moved: %s -> %s" % (OLD, NEW))
        return
    # mode == "mentions"
    if os.path.exists(os.path.join(REPO, OLD)):
        sys.exit("STOP: %s still exists -- run `move` first" % OLD)
    total = nfiles = 0
    for rel in outside:
        t = text_of(rel)
        if t is None:
            continue
        hits = plain(t)
        if not hits:
            continue
        out, last = [], 0
        for m in hits:
            out.append(t[last:m.start()])
            out.append(_repoint(m))
            last = m.end()
        out.append(t[last:])
        write(os.path.join(REPO, rel), "".join(out))
        total += len(hits)
        nfiles += 1
        print("  plain    %-58s %3d" % (rel, len(hits)))
    print("plain mentions re-pointed: %d in %d live file(s)" % (total, nfiles))
    stale = [f for f in tracked() if not f.startswith(NEW + "/") and not RECORDS.search(f)
             and MENTION.search(text_of(f) or "")]
    if stale:
        sys.exit("STOP: live mentions left in: %s" % ", ".join(stale))
    print("archived: no live mention of %s left" % OLD)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("check", "move", "mentions"):
        sys.exit("usage: archive.py check|move|mentions")
    main(sys.argv[1])
