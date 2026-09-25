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
| Python `datetime` — the independent source of `meta/roadmap/0.1/0.1.1.md` §4a's vectors for years ≥ 1, and cycle 0.1.4's cross-oracle, and `meta/roadmap/0.1/0.1.2.md` §2's recomputation of the sweeps' domains, and `meta/roadmap/0.1/0.1.3.md` §3's first method for the 41 derived-field vectors (`weekday()`, `timetuple().tm_yday`, `isocalendar()`) | 3.12.3, the workbench's interpreter | 2026-09-25 | docs.python.org/3/library/datetime.html | C-18 |
| ISO 8601-1 — the week-date rule of `CALENDAR.md` C-14 (week 1 holds the year's first Thursday, clause 3.1.1.23); the digest is [`iso-8601-week-date.md`](iso-8601-week-date.md). **Monday = 1 … Sunday = 7 could not be quoted from the 2019 text** and rests on C-7, RFC 3339's informational appendix and Python's `isocalendar()` | 2019, first edition, with Amd 1:2022 — its successor ISO/CD 8601-1 at stage 30.60 since 2026-07-25: re-check at DIS, and at 0.8 at the latest | 2026-09-25 | iss.rs/en/project/show/iso:proj:70907 (iso.org answered 403); the text through the distributor iTeh's previews of ISO's own pages | C-14 |
