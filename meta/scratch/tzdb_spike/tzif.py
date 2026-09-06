"""Minimal TZif v2+ reader for the 0.0.5 size spike (P-28: THROWAWAY).

Not `tools/gen_tzdb.py`.  This exists to answer ONE question -- how many bytes
does the compiled tzdb cost -- and 0.0.6's checklist deletes it.  It parses
enough of RFC 8536 to get shape and volume right and nothing more; the POSIX
footer is captured as a raw string and deliberately NOT parsed (0.0.5.md §2
step 2).
"""
import os, struct

ROOT = "/usr/share/zoneinfo"

def tzdata_version(root="/usr/share/zoneinfo"):
    """The release name, from the database itself.  `+VERSION` does not exist
    in this distribution's layout; `tzdata.zi`'s first line is `# version <R>`
    and is what `zic` writes."""
    for cand in ("+VERSION", "tzdata.zi"):
        p = os.path.join(root, cand)
        if not os.path.exists(p):
            continue
        with open(p) as fh:
            first = fh.readline().strip()
        return first.split()[-1] if first.startswith("#") else first
    return "unknown"


def _block(buf, off, timesize):
    """Parse one TZif data block.  Returns (transitions, types, abbrs, off)."""
    # header
    magic, ver = buf[off:off+4], buf[off+4:off+5]
    assert magic == b"TZif", magic
    off += 20                                        # magic+ver+15 reserved
    isutcnt, isstdcnt, leapcnt, timecnt, typecnt, charcnt = \
        struct.unpack(">6I", buf[off:off+24])
    off += 24
    tfmt = ">%d%s" % (timecnt, "q" if timesize == 8 else "i")
    times = list(struct.unpack(tfmt, buf[off:off+timecnt*timesize])) if timecnt else []
    off += timecnt * timesize
    idxs = list(buf[off:off+timecnt]); off += timecnt
    types = []
    for _ in range(typecnt):
        utoff, isdst, desig = struct.unpack(">ibB", buf[off:off+6]); off += 6
        types.append((utoff, isdst, desig))
    abbrs = buf[off:off+charcnt]; off += charcnt
    off += leapcnt * (timesize + 4)
    off += isstdcnt + isutcnt
    return times, idxs, types, abbrs, ver, off

def read(path):
    buf = open(path, "rb").read()
    times, idxs, types, abbrs, ver, off = _block(buf, 0, 4)
    footer = ""
    if ver in (b"2", b"3", b"4"):
        times, idxs, types, abbrs, _, off = _block(buf, off, 8)
        assert buf[off:off+1] == b"\n", buf[off:off+1]
        end = buf.index(b"\n", off + 1)
        footer = buf[off+1:end].decode("ascii")
    return {"transitions": list(zip(times, idxs)), "types": types,
            "abbrs": abbrs, "footer": footer, "version": ver.decode()}

def canonical_zones(root=ROOT):
    """Canonical zones only: real files, not symlinks; `posix/` and `right/`
    excluded (`right/` is the leap-second variant TM-006 says we are not on);
    non-zone metadata files excluded by name."""
    skip_top = {"posix", "right"}
    skip_name = {"tzdata.zi", "leapseconds", "iso3166.tab", "zone.tab",
                 "zone1970.tab", "leap-seconds.list", "localtime", "+VERSION"}
    # `Factory` IS a canonical zone -- a real TZif file the IANA distribution
    # ships and `zoneinfo` resolves, whose only type is the "-00" placeholder.
    # The first pass of this sweep skipped it by name and came out at 446
    # against the estimate's 447; the relation is 447 = 446 + Factory.
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        top = rel_dir.split(os.sep)[0]
        if top in skip_top:
            dirnames[:] = []
            continue
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            if os.path.islink(full):
                continue
            name = os.path.relpath(full, root)
            if name in skip_name or fn in skip_name:
                continue
            with open(full, "rb") as fh:
                if fh.read(4) != b"TZif":
                    continue
            out.append(name)
    return sorted(out)
