# `tools/` — generators and instruments

`gen_tzdb.py` (the time-zone transition tables), `gen_civil_oracle.py` and
`gen_zone_oracle.py` (the committed cross-oracle corpora), `fuzz_parse.py`.

Everything a generator emits is **committed as source** and checked by
regeneration — a hand-edited generated file is the failure that prevents. The
raw IANA tzdata release the generator reads is an input, not source, and is
gitignored.
