# Currency — the facts outside the compiler this plan rests on

One row per standard, data release, algorithm reference and reference
implementation the plan names, with the version pinned and the date it was
last checked (the workbench research skill, §7). **A row unchecked for six
months is stale, and a cycle whose rows are unchecked is not ready to start.**
Facts about the language are never rows here: they are read in the compiler's
tree at the pinned commit.

| Depends on | Pinned | Checked | Source | Decision |
|---|---|---|---|---|
| Howard Hinnant, *chrono-Compatible Low-Level Date Algorithms* — `days_from_civil`, `civil_from_days`; the digest is [`hinnant-date-algorithms.md`](hinnant-date-algorithms.md) | the page as it dates itself, 2021-09-01 | 2026-09-25 | howardhinnant.github.io/date_algorithms.html | TM-016 |
| tzdata | 2026c | 2026-09-05 — the release installed on the workbench, measured by the 0.0.5 spike ([`tzdb-size.md`](tzdb-size.md)). **Whether it is still IANA's latest is not checked here**: cycle 0.1 reads no zone data, and TM-100 pins *"the latest release at cycle 0.5"*, which re-checks it | iana.org/time-zones | TM-100 |
| Python `datetime` — the independent source of `meta/roadmap/0.1/0.1.1.md` §4a's vectors for years ≥ 1, and cycle 0.1.4's cross-oracle, and `meta/roadmap/0.1/0.1.2.md` §2's recomputation of the sweeps' domains | 3.12.3, the workbench's interpreter | 2026-09-25 | docs.python.org/3/library/datetime.html | C-18 |
