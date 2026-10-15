# Format standards — research digest

**As of 2026-10-15.** Question: what is the current status of RFC 3339 (date and time on the Internet), RFC 5322 (the Internet message format's date-time), RFC 9110 §5.6.7 (HTTP-date, with its two obsolete forms) and ISO 8601-1:2019 with Amd 1:2022 (its date and time representations, the expanded year among them)? For each: its errata, every RFC that updates or obsoletes it, and the edition in force. And does any change the grammar or the meaning of an offset, a fraction or a year range?

*(Requested by cycle 0.3's close, `meta/roadmap/done/0.3/0.3.4.md` step 5a, of the workbench's researcher agent, which writes no file; filed by the 0.3.4 worker as returned. It feeds `FORMAT_MODEL.md` F-2, F-3, F-9, F-12 and F-14, cycle 0.4's 0.4.1 … 0.4.4 boxes, and four rows of [`CURRENCY.md`](CURRENCY.md).)*

## Answer

All four editions are still in force. One offset's meaning has changed. No RFC changes the grammar of an offset, a fraction or a year. ISO's amendment changes the year text and restates the fraction rule.

**RFC 3339** (July 2002, Proposed Standard) is obsoleted by nothing.

- **RFC 9557** (April 2024) is the only RFC that updates it. It rewrites §4.3:
  - **`Z` now means what `-00:00` meant**: "the time in UTC is known, but the offset to local time is unknown".
  - **`Z` differs from `+00:00`**, which still implies "UTC is the preferred reference point".
  - `-00:00` is not formally deprecated, but "`Z` should now be used in its place".
- 9557 imports `date-time` and `time-numoffset` from 3339 §5.6 unchanged. It also states that ISO 8601:2000 and later "do not actually allow -00:00".
- 3339 has seven errata: 4 verified, 3 held. None is on `time-offset`, `time-secfrac` or `date-fullyear`.
  - The verified ones concern the informational Appendix A grammar (4110: a fraction below unity is preceded by "00"; 293: hour 24; 1584), §5.1's wording, and a URL.
  - Held 5783 says §5.6's NOTE allowing a space separator conflicts with the ABNF. It proposes no fix.

**RFC 5322** (October 2008, Draft Standard) is obsoleted by nothing and updated by RFC 6854 alone.

- It has 31 errata: 8 verified, 10 held, 13 rejected.
- One verified erratum changes date-time grammar: **6639, `zone = (FWS ( "+" / "-" ) 4DIGIT) / [FWS] obs-zone`**. It allows whitespace before an obsolete zone name.
- No erratum touches the numeric offset, `-0000`, the year, the day or month names, or §4.3.
- Held 2726 ("Universal Time" becomes "UTC") and held 5905 (time-of-day on a zone-transition day) are not normative.
- Its successor, draft-ietf-emailcore-rfc5322bis, was found in the RFC Editor queue but not opened.

**RFC 9110** (2022, Internet Standard, STD 97) is neither updated nor obsoleted. HTTP-date — IMF-fixdate plus the obsolete rfc850-date and asctime-date — stands as published.

- It has 14 errata: 6 verified, 2 reported, 6 rejected. None is on §5.6.7 or §6.6.1.
- The only one that names §5.6.7's rules is 9164, reported 2026-09-07 and unverified. It says Appendix A writes `%s"GMT"` as `%x47.4D.54` and `SP 1DIGIT` as `SP DIGIT` — the same grammar either way.

**ISO 8601-1** is still the 2019 first edition with **Amd 1:2022** ("Technical corrections", 2022-10). No other amendment is listed. ISO publishes no errata; corrections come as amendments. Its successor, **ISO/CD 8601-1, is still at stage 30.60** (close of comment period, since 2026-07-25): not a DIS, and not published. Amd 1 was read in full:

- **Year (4.3.2):** a minus sign may mark "a year preceding year zero", and a year may have more than four digits "in the case of expanded representation".
- **Fraction (5.3.1.4):** the rule is restated. Below one, the decimal sign is "preceded by two zeros". The decimal sign itself (4.5) is untouched.
- **Offset (5.5.1):** the meaning changes only inside a time interval. A time shift on the start applies to the end unless the end has its own.
- It touches neither the time shift's form nor `Z`.

## Evidence

- https://www.rfc-editor.org/info/rfc3339 — retrieved 2026-10-15 — "Date and Time on the Internet: Timestamps", "July 2002", "Proposed Standard". The page's one notice is "This RFC was updated, see" RFC 9557. It has no obsoleted notice.
- https://www.rfc-editor.org/rfc/rfc9557.html — retrieved 2026-10-15 — "Updates: 3339", "Published: April 2024".
  - §2.2: "This specification updates Section 4.3 of [RFC3339], aligning it with the actual practice of interpreting the offset Z to mean the same as -00:00: "the time in UTC is known, but the offset to local time is unknown"."
  - Revised §4.3: "If the time in UTC is known, but the offset to local time is unknown, this can be represented with an offset of "Z"." … "This differs semantically from an offset of `+00:00`, which implies that UTC is the preferred reference point for the specified time."
  - §2.3: "Note that the semantics of the local offset `+00:00` is not updated" … "the present specification does not formally deprecate this syntax. With the update to [RFC3339], the local offset `Z` should now be used in its place."
  - §2.1: "[ISO8601:2000] and later versions do not actually allow -00:00."
  - ABNF: "`date-time` and `time-numoffset` are imported from Section 5.6 of [RFC3339]".
- https://errata.rfc-editor.org/rfc3339 (redirected from www.rfc-editor.org/errata/rfc3339) — retrieved 2026-10-15 — seven errata.
  - Verified: 4110 (Technical, Appendix A), 293 (Editorial, §5.1 and Appendix A), 1584 (Editorial, Appendix A), 3710 (Editorial, §6, a URL).
  - Held: 5783 (Technical, §5.6), 5624 (Editorial, §5.6), 6533 (Editorial, table of contents).
  - 4110 corrected: "ISO 8601/Cor1:1991 also requires (in section 5.3.1.3) that a decimal fraction be proceeded by "00" if less than unity."
  - 5783: original "date-time = full-date "T" full-time"; no correction proposed. The reporter says the ABNF "allows only "T"/"t" as the separator".
- https://www.rfc-editor.org/info/rfc5322 — retrieved 2026-10-15 — "Internet Message Format", "October 2008", "Draft Standard", "Obsoletes: 2822", "Updates: 4021", "This RFC was updated, see" RFC 6854. It has no obsoleted notice.
- https://errata.rfc-editor.org/rfc5322 — retrieved 2026-10-15 — 31 errata: 8 verified, 10 held, 13 rejected, 0 reported.
  - 6639, Verified 2024-05-15, Technical, §3.3: "zone = (FWS ( "+" / "-" ) 4DIGIT) / obs-zone" becomes "zone = (FWS ( "+" / "-" ) 4DIGIT) / [FWS] obs-zone".
  - 2726, Held, §3.3: "The form "+0000" SHOULD be used to indicate a time zone at Universal Time." becomes "… at UTC."
  - 5905, Held, §3.3: time-of-day counted "since the nominal midnight of the zone now in effect".
  - 3979 (Verified) and 5867 (Held) concern the Received: field's grammar around `date-time`. 3088 and 5035 were rejected.
  - None concerns §4.3, `obs-year`, the military zones or §3.6.1.
- https://www.rfc-editor.org/info/rfc9110 — retrieved 2026-10-15 — "STD 97: HTTP Semantics", "Internet Standard", "This document updates RFC 3864 and obsoletes RFCs 2818, 7231, 7232, 7233, 7235, 7538, 7615, 7694, and portions of 7230." It has no updated or obsoleted notice.
- https://errata.rfc-editor.org/rfc9110 — retrieved 2026-10-15 — 14 errata (6 verified, 2 reported, 6 rejected, 0 held). None is on §5.6.7 or §6.6.1. 9164 (Reported 2026-09-07, Appendix A): "The collected rules are otherwise a normalised rendering of the rules defined in the body: … case-sensitive strings may be written in hexadecimal notation, and repetition bounds may be written in their shortest equivalent form."
- https://iss.rs/en/project/show/iso:proj:90784 — retrieved 2026-10-15 — this is the Institute for Standardization of Serbia, the source the existing row reads. It shows "ISO/CD 8601-1", current stage 30.60 "Close of voting/ comment period", "Jul 25, 2026". Previously published: ISO 8601-1:2019 and ISO 8601-1:2019/Amd 1:2022. ISO/TC 154. No publication date.
- https://cdn.standards.iteh.ai/samples/81801/f527872a9fe34281ae3a4af8e730f3f8/ISO-8601-1-2019-Amd-1-2022.pdf — retrieved 2026-10-15; ten pages, body pages 1–6, read whole.
  - Title page: "First edition 2019-02 AMENDMENT 1 2022-10 … AMENDMENT 1: Technical corrections … Reference number ISO 8601-1:2019/Amd.1:2022(E)".
  - Instructions, in order: 3.1.1.24, 3.1.2.15, 4.2.2 (twice), 4.2.3, 4.3.2 (twice), 4.3.11, 4.3.12, 5.3.1.4, 5.3.2 (title and text), 5.5.1 (paragraph and EXAMPLE 2), 5.5.2.2.
  - 4.3.2: "The year number may be preceded by a minus sign to indicate a year preceding year zero."
  - 4.3.2, third paragraph replaced: "The number of digits may exceed 4 in the case of expanded representation."
  - 5.3.1.4: "A decimal fraction of hour, minute or second may be included in a representation. If included, lower order time scale components (if any) shall be omitted and the decimal fraction shall be divided from the integer part by the decimal sign. If the magnitude of the number is less than one, the decimal sign shall be preceded by two zeros in accordance with 4.5."
  - 5.5.1: "Representations of the time shift between the local time scale and UTC included with the component preceding the separator shall be assumed to apply to the component following the separator, unless a corresponding alternative is included."
- Found by search, not opened (budget): https://datatracker.ietf.org/doc/draft-ietf-emailcore-rfc5322bis/ — the search tool's summary gives revision -12, IESG state "RFC Ed Queue", RFC Editor state blocked ("Reference First Edit Incomplete"), intended status Internet Standard. This is a lead, not evidence.

## What would change this

- **An RFC updates RFC 3339 — triggered at planning, and confirmed.** RFC 9557 is the only one, and nothing obsoletes 3339. It needs a row of its own. Before 0.4.1, two rules need a re-read:
  - F-2: `to_rfc3339`'s `Z` and a zero offset written `+00:00` now say different things.
  - The `Parsed` record (`has_offset`, `offset_secs`) cannot tell `Z` and `-00:00` apart from `+00:00`.
  - Also, by 9557's statement, ISO refuses `-00:00`, which RFC 3339's grammar accepts.
- **RFC 9110's HTTP-date obsoleted, or its obsolete forms withdrawn — not triggered.** There is no update, no obsoletion and no erratum on §5.6.7.
- **ISO 8601-1's successor published — not triggered.** It is still at the CD stage, 30.60. The existing row's re-check stands: at DIS, and at cycle 0.8 at the latest.
- **Found, not in the trigger list:**
  - Amd 1's year text (minus sign; more than four digits when expanded) bears on F-3's expanded ISO year.
  - RFC 5322 erratum 6639 is the one date-time grammar change now in force. It matters wherever `parse_rfc5322` accepts obsolete zone names.
  - If rfc5322bis is published, it obsoletes RFC 5322, and §3.3 and §4.3 need a re-read.

## Confidence and gaps

**High:** the status, updates and obsoletion of every RFC (rfc-editor.org's own pages); RFC 9557's text; the errata counts and quotes; the whole of Amd 1; the successor's stage. The errata and info-page quotes came through the fetch tool's extraction. RFC 9110's "no update" rests on the top of a page the tool cut off at 100 000 characters; the update notices for 3339 and 5322 were seen in the same place.

**Gaps at the budget:**
- RFC 6854's subject was not opened. From memory it is group syntax in the From: and Sender: fields, not date-time.
- RFC 9557's own errata were not checked.
- RFC 9110 §5.6.7's text was not re-quoted. Nothing found changes it.
- RFC 5322 §3.3's own year rule was not re-read. From memory it is `4*DIGIT`, "1900 or later"; F-3 names only RFC 3339's range.
- The rfc5322bis draft's date-time changes are unread.
- The 2019 clauses on expanded representation, the time shift and the decimal sign lie past the free preview. That includes the "mutual agreement" F-3 cites.
- iso.org was not tried; it answered 403 on 2026-09-25.

**Lead for F-14, unverified:** erratum 5783's reporter reads 3339's ABNF as accepting "t". If 3339 §5.6 also admits lowercase "t" and "z", F-14 wrongly counts lowercase as a lenient departure. Re-read §5.6 before 0.4.1.

**Noticed for F-13 / C-9** (outside the request): Amd 1 5.3.2 lets 24:00:00 carry an all-zero fraction ("T240000.000"), and says it "should be interpreted as the beginning instant of the next calendar day". 3.1.1.24 makes [23:59:58Z] the last second of a minute that has a negative leap second.

**Budget:** 12 of 12 fetches and 1 search. Three of the fetches were rfc-editor.org errata URLs that only redirected (no content); each redirect was then followed with a fetch of its own. The fetch tool could not extract the Amd 1 PDF's text, so it was read as page images from the tool's saved copy.
