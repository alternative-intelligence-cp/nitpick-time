#!/usr/bin/env python3
"""The spike's two supporting instrument sets, so the transcript regenerates
whole rather than half.  THROWAWAY with the rest of the spike (P-28).

  * the ROW-WIDTH probes -- one program per row type whose exit code IS
    `#size_of` of that type, so the width is read off a process rather than
    off a comment or a field-width sum;
  * the two NEGATIVE CONTROLS -- the emitted small table with one row's clock
    wound backwards, and with one zone's `trans_count` understated by three.
    An instrument that was never made to fail has not been commissioned.

    python3 probes.py <dir> <small.npk>
"""
import os, re, sys

FAILSAFE = """
func:failsafe = int32(Error:e) {
    pick (e) {
        (HeapBadRequest) { exit 91i32; },
        (HeapOom)        { exit 92i32; },
        (IntOverflow)    { exit 93i32; },
        (OutOfBounds)    { exit 94i32; },
        (Unreachable)    { exit 95i32; },
        (WildLeak)       { exit 96i32; },
        (*)              { exit 99i32; }
    }
    exit 9i32;
};
"""

STRUCTS = """
struct:ZoneTransition = { int64:at_utc; int32:type_index; };
struct:ZoneType       = { int32:offset_secs; uint8:is_dst; uint16:abbr_offset; };
struct:ZoneEntry      = {
    uint32:name_offset; uint16:name_len;
    uint32:trans_first; uint16:trans_count;
    uint32:type_first;  uint16:type_count;
    int32:posix_rule;
};
struct:PosixRule = {
    int32:std_offset_secs;  int32:dst_offset_secs;
    uint16:std_abbr_offset; uint16:dst_abbr_offset;
    uint8:start_month;  uint8:start_week;  uint8:start_dow;  int32:start_secs;
    uint8:end_month;    uint8:end_week;    uint8:end_dow;    int32:end_secs;
    uint8:has_dst;
};
"""


def sizes(d):
    for name in ("ZoneTransition", "ZoneType", "ZoneEntry", "PosixRule"):
        stem = "size_" + name
        open(os.path.join(d, stem + ".npk"), "w").write(
            "// THE EXIT CODE IS THE MEASUREMENT: exit(#size_of<%s>()).\n"
            "// Every candidate is far under 255, so the one-byte exit status\n"
            "// is wide enough to carry it (`../../../../PLAYBOOK.md` §6: an\n"
            "// expectation above 255 is silently wrong).\n"
            "mod:%s;\n%s\nfunc:main = int32(cstring[]:_~argv) {\n"
            "    exit (#size_of<%s>() =>! int32);\n};\n%s"
            % (name, stem, STRUCTS, name, FAILSAFE))


def negatives(d, small):
    src = open(small).read()
    lines = src.split("\n")
    n = 0
    hit = False
    for i, l in enumerate(lines):
        if l.strip().startswith("ZoneTransition{"):
            n += 1
            if n == 50:
                lines[i] = re.sub(r"at_utc: -?\d+i64", "at_utc: -9999999999i64", l)
                hit = True
                break
    assert hit, "no 50th transition row to wind backwards"
    open(os.path.join(d, "neg_unsorted.npk"), "w").write(
        "\n".join(lines).replace("mod:tz_small;", "mod:neg_unsorted;"))

    lines = src.split("\n")
    hit = False
    for i, l in enumerate(lines):
        m = re.search(r"trans_count: (\d+)u16", l)
        if m and int(m.group(1)) > 5:
            lines[i] = l.replace("trans_count: %su16" % m.group(1),
                                 "trans_count: %du16" % (int(m.group(1)) - 3))
            hit = True
            break
    assert hit, "no zone with more than five transitions to understate"
    open(os.path.join(d, "neg_shortsweep.npk"), "w").write(
        "\n".join(lines).replace("mod:tz_small;", "mod:neg_shortsweep;"))


if __name__ == "__main__":
    d, small = sys.argv[1], sys.argv[2]
    os.makedirs(d, exist_ok=True)
    sizes(d)
    negatives(d, small)
    print("wrote 4 row-width probes and 2 negative controls into %s" % d)
