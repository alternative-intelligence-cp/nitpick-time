# `tzdb_spike` — THROWAWAY. This is not the generator.

**Cycle 0.0.5's size spike (P-28).** It exists to answer one question — *how
many bytes does the compiled tzdb actually cost* — and **0.0.6's checklist
deletes it.** The real generator is `tools/gen_tzdb.py`, written at cycle 0.5,
and it does not exist yet.

If you are looking for the generator, it is not this. This code is correct
about **shape and volume** and deliberately not about content: it does not
parse `ZONE_MODEL.md` Z-12's POSIX footer, it does not resolve links (Z-10), it
does not sort the zone index (Z-9), and its `PosixRule` rows are placeholders
emitted at the real cardinality so that the table's *width* is measured. Every
one of those is 0.5's work and none of it changes a byte count.

## What is kept

**The number, and what it means for TM-007** — TM-135, `ZONE_MODEL.md` §3 and
`meta/research/tzdb-size.md`. Nothing else. `TRANSCRIPT.txt` is the evidence
those three cite.

## The files

| File | What it is |
|---|---|
| `tzif.py` | a minimal RFC 8536 reader: the v1 header, the v2+ 64-bit block, the type block, the abbreviation pool, and the footer captured but not parsed |
| `emit.py` | emits one `.npk` of `pub fixed` tables — `--zones N` truncates, `--with-posix` adds `POSIX_RULES` |
| `probes.py` | the four row-width probes (the exit code *is* `#size_of`) and the two negative controls |
| `transcript.py` | regenerates `TRANSCRIPT.txt`; every status is captured on its own line and printed beside the artefact it should have produced, and there is no pipeline anywhere in it |
| `TRANSCRIPT.txt` | the evidence |

## Running it

```
NPKC=<pinned npkc> NPKRT=<pinned npkrt.o> \
    python3 meta/scratch/tzdb_spike/transcript.py > TRANSCRIPT.txt
```

It writes its emitted `.npk` and every build artefact under `.internal/` —
gitignored, and in `harness/run.py`'s `WALK_SKIP`. **That is deliberate.** A
two-megabyte generated `.npk` under `meta/scratch/` would be swept by the
`expect-` header check and rooted by the `parse` stage on every run, which
would make a throwaway file a permanent cost. The generator is committed; its
output is not, and is reproducible from the pinned release name.

## What it measured

477.8 KiB for the whole database including `POSIX_RULES`, against a 348 KiB
estimate — inside the budget `../../roadmap/done/0.0/0.0.5.md` §3 fixed in advance,
with 4.4% to spare. TM-135 has the arithmetic, the controls and the four
independent ways the estimate was wrong.
