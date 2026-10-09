#!/usr/bin/env python3
"""0.3.2a -- the library's two emissions at each named pin, and every check of <tree>'s that reads them or reads
the source beside them: what the pin moves in `npkc`'s output, and what that moves in the checks.

    python3 -B emissions.py <tree> <pin> [<pin> ...]

<tree> is a COPY (`env.sh`'s `ctl`): each pin's two emissions are written into its `build/`, where `run.py`'s
step 7 writes them -- the umbrella's `build/ntime.ll`, and the instances' `build/generic_instances.ll` from
`tests/unit/generic_instances.npk` -- by that pin's `npkc`, and then read by <tree>'s own `checks.py`:
`check_call_edges` and `check_wide_types`, which read the emissions, and `check_purity`, which reads the source and
is asked as the control. For each pin it prints the two sizes; the functions the umbrella defines; the drop and
vacant glue's type ids, which name a type by the id the compiler interned it at; the site table's length; the calls
of a `string`'s drop (`npk.drop.3`); the three checks' headlines; and a digest of the runtime symbols every function
of `src/`'s modules reaches, by the check's own walk -- the same digest at two pins is the same reach for every
function. `$WB` names the workbench (`env.sh`).
"""
import hashlib
import os
import re
import subprocess
import sys


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    tree, pins = os.path.realpath(argv[1]), argv[2:]
    sys.path.insert(0, os.path.join(tree, "harness"))
    import checks
    os.makedirs(os.path.join(tree, "build"), exist_ok=True)
    for pin in pins:
        npkc = os.path.join(os.environ["WB"], ".internal", "toolchain", pin, "npkc")
        lib = os.path.join(tree, checks.EMISSION)
        inst = os.path.join(tree, checks.INSTANCES)
        for f in (lib, inst):
            if os.path.exists(f):
                os.remove(f)
        r1 = subprocess.run([npkc, "lib.npk", "-o", lib], cwd=os.path.join(tree, "src"), capture_output=True, text=True)
        r2 = subprocess.run([npkc, checks.INSTANCES_ROOT, "-o", inst], cwd=tree, capture_output=True, text=True)
        if r1.returncode or r2.returncode:
            print("at %s: npkc refused %s" % (pin, "the umbrella" if r1.returncode else "the instances"))
            continue
        text = open(lib, encoding="utf-8").read()
        defines, declares, globs = checks.read_emission(lib)
        glue = sorted({int(m) for m in re.findall(r"@\"?npk\.(?:drop|vacant)\.(\d+)", text)})
        sites = re.search(r"^@npk\.site\.lines = internal constant \[(\d+) x i32\]", text, re.M)
        print("at %s: the umbrella %d B, %d function(s) defined; the instances %d B" % (
            pin, os.path.getsize(lib), len(defines), os.path.getsize(inst)))
        print("  the drop and vacant glue's type ids: %s" % " ".join(str(g) for g in glue))
        print("  the site table: %s entries; a `string`'s drop called %d time(s)" % (
            sites.group(1) if sites else "no", len(re.findall(r"call void @\"?npk\.drop\.3\"?\(", text))))
        for name in ("check_call_edges", "check_wide_types", "check_purity"):
            res = getattr(checks, name)(tree)
            print("  %s: %d finding(s) -- %s" % (name, len(res.problems), res.headline[:120]))
        mods, _host = checks._src_modules(tree)
        reach = []
        for path in (lib, inst):
            d, dec, g = checks.read_emission(path)
            for n in sorted(d):
                if checks._ir_module(n) in mods:
                    syms, _src, odd = checks._reach(n, d, dec, g, mods)
                    reach.append("%s %s|%s" % (n, ",".join(sorted(syms)), ",".join(sorted(o[1] for o in odd))))
        print("  the runtime symbols each of %d function(s) of src/'s modules reaches: %s" % (
            len(reach), hashlib.sha256("\n".join(reach).encode()).hexdigest()[:16]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
