"""The toolchain, asked its version and held to the pin. Step 2, P-12.

THE TOOLCHAIN IS A BUILD INPUT (D-204). `nitpick.toml` pins `llvm` to an exact
patch release because a patch release can change instruction selection, so a
mismatch is an ASSERTION that fails here rather than a difference discovered
three cycles later in a golden file.

ASK THE TOOLS, NOT `llvm-config`. Cycle 0.0.1's floor asked `llvm-config
--version`, which is the one binary in the set the build does not use: it ships
in the `-dev` package, so a machine can have a perfectly good `llc`, `opt` and
`ld.lld` and no `llvm-config` at all, and the floor would refuse it for a tool
it never invokes. Worse, the reverse: `llvm-config` could report the version of
a DIFFERENT installation from the one on `PATH`. The three tools this harness
actually runs are the three it asks.

The version strings, measured at the pin:

    llc --version      "Ubuntu LLVM version 20.1.2"
    opt --version      "Ubuntu LLVM version 20.1.2"
    ld.lld --version   "Ubuntu LLD 20.1.2 (compatible with GNU linkers)"

-- three different shapes, one of them not containing "LLVM" at all, so the
match is on the dotted number and not on the surrounding words.
"""

import re
import subprocess

TOOLS = ("llc", "opt", "ld.lld")

_VERSION = re.compile(r"\b(\d+\.\d+\.\d+)\b")


class ToolchainError(Exception):
    """A tool missing, unaskable, or at the wrong version."""


def _ask(tool):
    """Run `<tool> --version` with NO shell and NO pipeline.

    The status captured is the process's own. A `subprocess.check_output(...,
    shell=True)` through a `| head` would report the filter's status, which is
    how a measurement session in this repository once recorded thirty programs
    as `exit=0` when two had refused and written nothing.
    """
    try:
        p = subprocess.run([tool, "--version"], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
    except FileNotFoundError:
        raise ToolchainError(
            "%s: not on PATH. `nitpick.toml` [toolchain] names it and this "
            "harness invokes it; a missing tool fails loudly rather than "
            "skipping a leg (B-3)." % tool)
    out = p.stdout.decode("utf-8", "replace")
    if p.returncode != 0:
        raise ToolchainError("%s --version exited %d:\n%s"
                             % (tool, p.returncode, out.rstrip()))
    first = out.splitlines()[0] if out.splitlines() else ""
    m = _VERSION.search(first)
    if not m:
        raise ToolchainError(
            "%s --version printed a first line with no dotted version in it, "
            "so the pin cannot be checked: %r" % (tool, first))
    return m.group(1), first.strip()


def check(manifest):
    """Assert every tool matches `[toolchain] llvm` exactly.

    Returns `[(tool, version, banner), ...]` for the run log. Raises naming
    EVERY mismatch, not the first: a machine with a half-upgraded LLVM should
    be told once.
    """
    want = manifest["toolchain"]["llvm"]
    seen, bad = [], []
    for tool in TOOLS:
        version, banner = _ask(tool)
        seen.append((tool, version, banner))
        if version != want:
            bad.append("%s reports %s; nitpick.toml [toolchain] llvm pins %s "
                       "exactly (%s)" % (tool, version, want, banner))
    if bad:
        raise ToolchainError(
            "the toolchain does not match the pin -- %d mismatch(es):\n  - %s\n"
            "The pin is an exact patch release on purpose (D-204): a patch "
            "release can change instruction selection, so this is an assertion "
            "and not a report." % (len(bad), "\n  - ".join(bad)))
    return seen
