# `tests/`

| Directory | Stage | Contents |
|---|---|---|
| `probe/` | `program` | the cycle-0.0 language probes; **never deleted** |
| `conformance/` | `compile`, `kind = "positive"` | the public API compiles in a program that only imports it — and that program links, RUNS and exits with the expected code (`../meta/specs/BUILD.md` B-4b, TM-114) |
| `unit/` | `program` | behaviour, judged by exit code |
| `unit/sweep/` | `sweep` | the exhaustive calendar and zone sweeps |
| `golden/` | `golden` | formatted output, byte for byte |
| `rejection/` | `check` | programs the compiler must refuse, with exactly the expected codes |
| `fixtures/` | `fixture` | the committed corpora: the civil and zone cross-oracles, the format vectors, and everything the fuzzer found |

Expectations live in the test file. Governed by `../meta/specs/TESTING.md`.

*(Corrected at cycle 0.1.2: the `conformance/` row gave its stage as
`accept`, which `BUILD.md` B-4b and TM-114 declined at cycle 0.0.1 — `accept`
stops at "accepted in silence", the shape a program with no `failsafe` walks
through, and `nitpick.toml`'s entry has been `compile`/`positive` since then.)*
