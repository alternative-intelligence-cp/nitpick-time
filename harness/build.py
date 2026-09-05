"""The build pipeline. Steps 4 and 2 of `BUILD.md`, every argv from the manifest.

    root.npk ─► npkc ─► x.ll ─► llc  ─► x.o  ─► symbol scan ─► ld.lld ─► run
                          └──► opt -O2 ─► x.opt.ll ─► llc -O2 ─► x.opt.o ─► …

THERE IS NO SEPARATE COMPILATION, AND THE PLAN SAID THERE WAS. `0.0.2.md` §2
drew `ld.lld(p.o, ntime.o, npkrt.o)` and P-16 said *"the library compiles once
to an object; each test program compiles and links against it"*. Measured at pin
`0dfddac`: `npkc`'s usage line is `npkc <root.npk> [-o out.ll]` and it emits the
WHOLE reachable module graph -- the prelude included, ~610 `define`s in the
smallest program here -- into every root's output. Linking a program object
beside a library object built from the same graph is `ld.lld` exit 1 with 121
lines of `duplicate symbol`, starting at `npk.prelude.int8:ToString.to_string`.
That is TM-117, and it is why the pipeline below links `p.o` with `npkrt.o` and
nothing else.

WHAT SURVIVES OF P-16. Its REASON was cost -- "the difference between a
two-minute suite and a forty-minute one". The remedy is unavailable, so the cost
is paid and measured rather than assumed: every program carries the prelude, and
the suite's wall time is printed by `run.py` so the day it becomes a problem is
a number rather than a feeling. The library is still built exactly once per run,
not per test -- but as a CHECK of its own (it emits, assembles and scans), not
as an input to anything.

EVERY `npkc` EXIT 0 IS PAIRED WITH THE ARTEFACT IT SHOULD HAVE PRODUCED. Carried
over from the 0.0.1 floor deliberately: a status that disagrees with an artefact
is the tell, and it is how this repository has caught its own measurement bugs
twice.
"""

import os
import re
import subprocess

import elf


class BuildError(Exception):
    """A step of the pipeline that did not do what it was asked.

    `step` is the tool or check; `detail` is its own output, verbatim. Never a
    summary -- a summary is not evidence, and this repository was once failed by
    its own verifier for offering one.
    """

    def __init__(self, step, detail):
        super().__init__("%s: %s" % (step, detail))
        self.step = step
        self.detail = detail


def run(argv, cwd=None, env=None, timeout=None):
    """Run argv with NO shell and NO pipeline. Returns `(status, output)`.

    `$?` after a pipeline is the LAST command's status, so a trailing `| head`
    reports the filter's success as the command's. There is no pipeline here and
    there never should be: the status returned is the process's own.
    """
    p = subprocess.run(argv, cwd=cwd, env=env, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=timeout)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def run_split(argv, cwd=None, env=None, timeout=None):
    """As `run`, but keeps stdout and stderr apart and returns BYTES.

    The `golden` stage needs both halves of that. A golden file asserts what a
    program WROTE, byte for byte -- so it must not have the runtime's stderr
    folded into it, and it must not be decoded and re-encoded on the way to the
    comparison. `run` above merges the streams because for a `program` unit the
    exit code is the verdict and the output is only evidence; here the output IS
    the verdict.
    """
    p = subprocess.run(argv, cwd=cwd, env=env, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


# `use "<path>".<what>;` and `pub use "<path>".<what>;` -- BUILD.md B-16: every
# import is relative until dependency roots are populated (O-N1).
_USE = re.compile(r'^\s*(?:pub\s+)?use\s+"([^"]+)"')


def imports_of(path):
    """The relative paths a single source file imports, in file order."""
    out = []
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = _USE.match(line)
            if m:
                out.append(m.group(1))
    return out


def reachable_sources(root_npk):
    """Every source `root_npk` reaches by `use`, including itself.

    The module-graph walk cycle 0.0's checklist asks for. `npkc` does its own,
    so this is not needed to BUILD -- it is needed to know which files are
    imported by something else and therefore are not programs in their own
    right, and it is what `check_layering` will walk at 0.0.3. A `use` cycle is
    legal in the language (D-086), so the walk carries a seen-set rather than
    assuming a tree.
    """
    seen, order, stack = set(), [], [os.path.abspath(root_npk)]
    while stack:
        cur = stack.pop()
        if cur in seen or not os.path.isfile(cur):
            continue
        seen.add(cur)
        order.append(cur)
        base = os.path.dirname(cur)
        for rel in imports_of(cur):
            stack.append(os.path.abspath(os.path.join(base, rel)))
    return order


class Build:
    """Everything a build needs, read once: the manifest, the pin, the allowlist."""

    def __init__(self, root, manifest, npkc, npkrt, out_dir):
        self.root = root
        self.manifest = manifest
        self.npkc = npkc
        self.npkrt = npkrt
        self.out_dir = out_dir
        tc = manifest["toolchain"]
        self.llc_flags = tc["llc-flags"]
        self.llc_opt_flags = tc["llc-opt-flags"]
        self.opt_flags = tc["opt-flags"]
        self.lld_flags = tc["lld-flags"]
        # Derived, never written (P-14 as corrected by TM-118): what the
        # object we actually link provides, plus what it requires of us.
        self.allowlist = elf.runtime_allowlist(npkrt)
        os.makedirs(out_dir, exist_ok=True)

    # -- the four tools, each at the manifest's flags and never at its own
    #    defaults (B-1: `llc` defaults to -O2 and would optimise a build the
    #    manifest declined, which cost the compiler project a measured 25x) ---

    def emit(self, src, out_ll, cwd=None):
        """`npkc src -o out_ll`. Exit 0 AND the artefact, or it did not happen."""
        if os.path.exists(out_ll):
            os.remove(out_ll)
        st, out = run([self.npkc, src, "-o", out_ll], cwd=cwd or self.root)
        if st != 0:
            raise BuildError("npkc", "exit %d\n%s" % (st, out.rstrip()))
        if not os.path.isfile(out_ll):
            raise BuildError("npkc", "exit 0 and wrote no %s. A status that "
                                     "disagrees with an artefact is the tell."
                             % out_ll)
        return out

    def emit_expecting_refusal(self, src, out_ll, cwd=None):
        """`npkc src`, for a file that MUST NOT compile. Returns `(status, output)`.

        Kept separate from `emit` on purpose: a refusal is an expected outcome
        here, and a function that sometimes raises on failure and sometimes
        returns it is a function whose callers stop checking.
        """
        if os.path.exists(out_ll):
            os.remove(out_ll)
        return run([self.npkc, src, "-o", out_ll], cwd=cwd or self.root)

    def optimise(self, in_ll, out_ll):
        """`opt -O2 -S`. B-3's check leg -- never skipped, never silent."""
        st, out = run(["opt"] + self.opt_flags + [in_ll, "-o", out_ll])
        if st != 0:
            raise BuildError("opt", "exit %d\n%s" % (st, out.rstrip()))
        if not os.path.isfile(out_ll):
            raise BuildError("opt", "exit 0 and wrote no %s" % out_ll)

    def assemble(self, ll, obj, optimised=False):
        flags = self.llc_opt_flags if optimised else self.llc_flags
        st, out = run(["llc"] + flags + [ll, "-o", obj])
        if st != 0:
            raise BuildError("llc", "exit %d\n%s" % (st, out.rstrip()))
        if not os.path.isfile(obj):
            raise BuildError("llc", "exit 0 and wrote no %s" % obj)

    def scan(self, obj):
        """B-2: a BUILD step, not a test. Any forbidden symbol fails the build.

        See `elf.py` for what this can and cannot see -- in particular it CANNOT
        see a syscall, and it is not a purity result.
        """
        bad = elf.scan(obj, self.allowlist)
        if bad:
            raise BuildError(
                "undefined-symbol scan",
                "%s needs %d symbol(s) the runtime does not define: %s\n"
                "`ntime` depends on the language, its prelude and nothing else "
                "(BUILD.md B-2/B-10). The allowlist is derived from %s."
                % (os.path.basename(obj), len(bad), ", ".join(bad),
                   self.npkrt))

    def link(self, objs, exe):
        st, out = run(["ld.lld"] + self.lld_flags + list(objs)
                      + [self.npkrt, "-o", exe])
        if st != 0:
            raise BuildError("ld.lld", "exit %d\n%s" % (st, out.rstrip()))
        if not os.path.isfile(exe):
            raise BuildError("ld.lld", "exit 0 and wrote no %s" % exe)

    # ---------------------------------------------------------------------
    # the whole chain, one leg
    # ---------------------------------------------------------------------

    def build_program(self, src, stem, optimised, require_failsafe=True):
        """Emit, optionally optimise, assemble, scan, link. Returns the exe path.

        `require_failsafe` asserts the emitted IR defines `@npk_failsafe`.
        `npkc` refuses a root with `main` and no handler since the compiler's
        DEF-5 (TM-112), so this is redundant TODAY and is kept because it is
        what catches the next stage that stops at the `.ll`: `npkc` exit 0 is
        not well-formedness, and this repository holds the reproduction.
        """
        suffix = ".opt" if optimised else ""
        ll = os.path.join(self.out_dir, stem + ".ll")
        obj = os.path.join(self.out_dir, stem + suffix + ".o")
        exe = os.path.join(self.out_dir, stem + suffix)

        if not optimised:
            self.emit(src, ll)
            if require_failsafe:
                with open(ll, "r", encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
                if text.count("\ndefine i32 @npk_failsafe") < 1:
                    raise BuildError(
                        "failsafe", "the emitted IR defines no @npk_failsafe. "
                                    "A program with no handler compiled at "
                                    "npkc exit 0 until the compiler's DEF-5 "
                                    "(O-N11, TM-112).")
        else:
            opt_ll = os.path.join(self.out_dir, stem + ".opt.ll")
            self.optimise(ll, opt_ll)
            ll = opt_ll

        self.assemble(ll, obj, optimised=optimised)
        self.scan(obj)
        self.link([obj], exe)
        return exe
