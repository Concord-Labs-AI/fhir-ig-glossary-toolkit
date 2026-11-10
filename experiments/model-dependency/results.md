# Model-dependency experiment — results (2026-11-10)

Protocol: `protocol.md`. Scores: `runs/<run>/data/scores/*.json`. Baseline: the reference run's own Fable 5.1 reader outputs scored the same way.

Added after the protocol was written: Opus 5.5 readers on the same three packets, and a second Sonnet skeptic run on B03 after the skeptic brief was fixed (see the skeptic section). Each model read each packet once, so run-to-run variation is not measured.

**What recall means here.** Recall is agreement with the rows Fable's readers proposed and Fable's skeptics kept. It is not agreement with the truth. The spot check below shows Opus found five real findings the Fable readers missed.

## Reader role

| Packet | Model | Proposed | Valid | Validity | Recall of kept | Precision proxy | Pending violations | Tokens | Minutes |
|---|---|---|---|---|---|---|---|---|---|
| B03 prose | Fable 5.1 | 142 | 142 | 100% | 100% (by construction) | 97.2% | 0 | not recorded | not recorded |
| B03 prose | Opus 5.5 | 143 | 143 | 100% | 99.3% | 95.8% | 0 | 192,506 | 12.1 |
| B03 prose | Sonnet | 135 | 135 | 100% | 92.0% | 94.1% | 0 | 114,511 | 3.4 |
| B03 prose | Haiku | 123 | 123 | 100% | 78.3% | 87.8% | 0 | 185,899 | 6.3 |
| B12 FSH | Fable 5.1 | 38 | 38 | 100% | 100% (by construction) | 100% | 0 | not recorded | not recorded |
| B12 FSH | Opus 5.5 | 40 | 40 | 100% | 100% | 95.0% | 0 | 189,425 | 3.2 |
| B12 FSH | Sonnet | 40 | 40 | 100% | 89.5% | 85.0% | 0 | 78,199 | 1.3 |
| B12 FSH | Haiku | 38 | 38 | 100% | 89.5% | 89.5% | 0 | 178,067 | 2.1 |
| B10 diagrams | Fable 5.1 | 36 | 36 | 100% | 100% (by construction) | 94.4% | 0 | not recorded | not recorded |
| B10 diagrams | Opus 5.5 | 38 | 38 | 100% | 100% | 89.5% | 0 | 182,977 | 4.3 |
| B10 diagrams | Sonnet | 25 | 25 | 100% | 67.6% | 92.0% | 0 | 119,698 | 1.0 |
| B10 diagrams | Haiku | 36 | 36 | 100% | 100% | 94.4% | 0 | 158,479 | 2.4 |

The Fable rows score the reference readers against their own kept rows, so recall is 100% by definition; their precision proxy is the share of their proposals the skeptics kept.

Spot check of each model's unmatched findings (one Fable 5.1 skeptic per model): Opus 5 confirm / 0 revise / 2 reject of 7; Sonnet 0 / 0 / 10 of 10; Haiku 0 / 0 / 15 of 15.

*Reading:* Every model wrote edits that validate: no invalid `find`, no overlaps, no pending-decision violations. The models differ in what they find. Opus's recall stayed within a point of the Fable readers on every packet. Its precision proxy is up to five points lower, partly because Fable confirmed five of its seven extra findings: two provider wordings, "Patient/Client", a diagram typo, and a bare "recipient" that names the referral target. Counting those, 140 of 143, 39 of 40 and 35 of 38 of Opus's findings hold up. On these packets Opus found slightly more than the reference. Sonnet and Haiku each lost 8 to 32 points of recall on at least one packet, and none of their 25 extra findings survived the spot check. The misses follow patterns rather than being scattered. Sonnet skipped 11 of the 22 held "CBO" rows on B10, one in each of 11 diagrams (decision D-6). Haiku missed 18 of the coordination-platform alias rows on the self-referral page, and on the app-connection page it applied the same alias to "referral platform", which there means any referral server; all 8 of those were rejected. Both cheaper models proposed patient wording for FHIR elements whose author or requester is usually a practitioner or organization. Haiku did not save tokens: it used more than Sonnet on every packet.

The spot-check briefs were rendered before the skeptic fix described below. Three of Sonnet's and two of Haiku's rejected rows cite the pending decision D-2. Each also gives a reason that holds on the strict reading: the edit would make a role definition circular, or the text means the person represented.

## Skeptic role (Sonnet vs the reference verdicts, V01–V07)

| Packet | Brief | Compared | Agreement | confirm/confirm | reject/reject | revise/revise | Disagreements (ref→Sonnet) |
|---|---|---|---|---|---|---|---|
| B03 | original | 66 | 40.9% | 25 | 1 | 1 | confirm→reject 36, confirm→revise 2, revise→reject 1 |
| B03 | fixed | 66 | 93.9% | 61 | 0 | 1 | confirm→reject 2, reject→confirm 1, revise→confirm 1 |
| B12 | original | 4 | 75.0% | 3 | 0 | 0 | confirm→reject 1 |

*Reading:* The first run exposed a gap in the toolkit's skeptic brief. It did not say how to judge a row held for a team decision. Sonnet rejected 36 rows the reference confirmed. 34 of them were held D-2 rows, rejected because their recommended option keeps the text. The reference skeptics, whose brief had the same gap, judged those rows on the strict reading as intended. The brief now says so (`skills/ig-glossary/prompts/skeptic.md`, "Pending decisions"). With the fixed brief Sonnet agreed on 62 of 66 keys. Two of its four disagreements were in the safe direction: it rejected two "Community Resource Platform" renames the reference confirmed, because the label is used across that page and renaming two mentions would split it. One was in the dangerous direction: it confirmed an edit inside quoted example note text that the reference rejected. On B12 (original brief) its one disagreement was also in the safe direction: it rejected an "SDOH needs" → "social risks" edit as a change of meaning. The sample is small: one packet re-run, 70 keys in all. The consistency pass was not tested.

## Recommendation

| Role | Recommended model | Why |
|---|---|---|
| Rulebook author, themes author | strongest available | authored inputs; untested here, and every later stage depends on them |
| Reader | Opus 5.5 or Fable 5.1 | Opus's recall matched the Fable readers within a point and its extra findings mostly held up; Sonnet and Haiku missed whole patterns and none of their extras held up |
| Skeptic | strongest available; Sonnet is workable | with the fixed brief Sonnet agreed on 94% of 66 keys, but one of its four disagreements accepted a row the reference rejected, and the sample is one packet |
| Consistency pass | strongest available | untested here |
| QA review | strongest available | untested here; it is the last place a wrong edit is caught |

Cost note: the reference run's 64 agents all ran on Fable 5.1, and their token counts were not recorded, so this experiment cannot state a Fable-versus-Opus saving. Measured reader cost per packet: Opus 183k–193k tokens (3–12 minutes), Sonnet 78k–120k (1–3.4 minutes), Haiku 158k–186k (2–6.3 minutes). Prices differ by model, so token counts are not cost. A run that drops the readers to Sonnet to save money gives up about 8 points of recall on prose and a third of the diagram findings, on this evidence.
