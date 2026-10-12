#!/usr/bin/env python3
"""0.3.3 -- the transcript's every line, re-derived with Python's `datetime`
and integer arithmetic, from the sequence `tests/golden/double_transcript.npk`
states -- never from its output (the plan's §1).

    python3 -B oracle.py            # the transcript, on stdout

The sequence, as the member's `transcript` drives the double: the realtime
clock set to 1 760 270 400 s (2025-10-12 12:00 UTC), both instants at the
double's start, 0 ns; the start, asked twice; 1.5 s passing on every clock;
`TZ` set to `Europe/Kyiv`; the realtime set to 1 760 266 801.5 s; the boot
clock set 60 s ahead of itself; 0.25 s passing; the realtime set to the
range's last nanosecond, 253 402 300 799.999 999 999; and 1 ns passing.
"""
import datetime

SECS_MAX = 253402300799                      # `NTIME_SECS_MAX`, 9999-12-31 23:59:59
SECS_MIN = -377705116800                     # `NTIME_SECS_MIN`


def civil(secs, nanos):
    if secs > SECS_MAX or secs < SECS_MIN or not 0 <= nanos < 10 ** 9:
        return "the wall clock refused: outside the calendar's range"
    t = datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds=secs)
    return "%04d-%02d-%02d %02d:%02d:%02d.%09d UTC" % (
        t.year, t.month, t.day, t.hour, t.minute, t.second, nanos)


def span(ns):
    sign = "-" if ns < 0 else "+"
    ns = abs(ns)
    return "%s%d.%09d s" % (sign, ns // 10 ** 9, ns % 10 ** 9)


def main():
    utc = [1760270400, 0]                    # seconds, nanoseconds
    mono = boot = 0
    start = (mono, boot)
    zone = None
    out = []

    def stamp(label):
        z = "no zone" if zone is None else "zone %s (%s)" % zone
        out.append("%s: %s | monotonic %s | boot %s | %s" % (
            label, civil(*utc), span(mono - start[0]), span(boot - start[1]), z))

    def advance(ns):
        nonlocal mono, boot
        mono += ns
        boot += ns
        total = utc[0] * 10 ** 9 + utc[1] + ns
        utc[0], utc[1] = divmod(total, 10 ** 9)

    stamp("start")
    stamp("again")
    advance(1500000000)
    stamp("1.5 s on")
    zone = ("Europe/Kyiv", "TzEnvironment")
    stamp("TZ set")
    utc[:] = [1760266801, 500000000]
    stamp("the wall clock stepped back an hour")
    boot += 60 * 10 ** 9
    stamp("a suspend of a minute")
    advance(250000000)
    stamp("0.25 s on")
    utc[:] = [SECS_MAX, 999999999]
    stamp("the range's last nanosecond")
    advance(1)
    stamp("one nanosecond past it")
    print("\n".join(out))


if __name__ == "__main__":
    main()
