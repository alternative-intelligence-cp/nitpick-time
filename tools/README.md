# `tools/` — generators and instruments

**Here today:** `gen_civil_oracle.py` (cycle 0.1.4), which writes the civil
cross-oracle's corpus, `tests/fixtures/civil/civil_oracle.npk`, from Python's
`datetime` (`meta/specs/TESTING.md` V-6); and `ir_alloc_scan.py`, an
instrument rather than a generator, here since cycle 0.0.4. **Planned:**
`gen_tzdb.py` (the time-zone transition tables, cycle 0.5),
`gen_zone_oracle.py` (the zone cross-oracle's corpus, cycle 0.6) and
`fuzz_parse.py` (the parsers' fuzzer, `TESTING.md` V-9). *(Until cycle 0.1.4
this paragraph named the four planned tools, as though present, and not the
one that was.)*

Everything a generator emits is **committed as source** and checked by
regeneration — a hand-edited generated file is the failure that prevents.
Until `check_tables_regenerate` goes live at cycle 0.5.3, *checked by
regeneration* means that the subcycle which changes a generator regenerates
its output and compares it byte for byte; the civil corpus's regeneration
takes about 11 s (TM-183). The
raw IANA tzdata release the generator reads is an input, not source, and is
gitignored.
