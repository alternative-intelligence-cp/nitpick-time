# `tests/`

| Directory | Stage | Contents |
|---|---|---|
| `probe/` | `program` | the cycle-0.0 language probes; **never deleted** |
| `conformance/` | `accept` | the public API compiles in a program that only imports it |
| `unit/` | `program` | behaviour, judged by exit code |
| `unit/sweep/` | `sweep` | the exhaustive calendar and zone sweeps |
| `golden/` | `golden` | formatted output, byte for byte |
| `rejection/` | `check` | programs the compiler must refuse, with exactly the expected codes |
| `fixtures/` | `fixture` | the committed corpora: the civil and zone cross-oracles, the format vectors, and everything the fuzzer found |

Expectations live in the test file. Governed by `../meta/specs/TESTING.md`.
