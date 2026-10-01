# `src/core/` — storage primitives

`Vec<T: Copy>` (an element owns nothing, since cycle 0.2.0b), `Bytes` (an
owning byte sink with an allocation-free decimal writer),
and `limits.npk` — every named bound in the library, in one file. Depends on
nothing. Governed by `meta/specs/BUILD.md` §5. Built in cycle 0.0.4.
