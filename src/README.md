# `src/` — the library

Nitpick source only. The package is `ntime` (TM-001) and every public symbol
carries its module's short prefix. The layering and the direction of every
dependency arrow are in `../meta/specs/BUILD.md` §6; a module may not import
one to its right, and **nothing imports `host/`** except `lib.npk` and an
application — that is `SAFETY.md` §3's purity boundary expressed as a layering
rule.

`lib.npk` is the umbrella and lists the public surface, one name per line,
because `use` is not transitive.
