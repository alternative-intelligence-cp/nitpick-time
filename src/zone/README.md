# `src/zone/` — time zones

The **generated** IANA transition tables, committed as Nitpick source
(TM-007), plus the offset lookup and the four resolution modes. A build needs
the compiler and nothing else: no Python, no network, and never
`/usr/share/zoneinfo`.

`version.npk` holds the pinned release name — one file, one fact. Governed by
`meta/specs/ZONE_MODEL.md`. Built in cycles 0.5 (the table) and 0.6 (the
lookup and the edges).
