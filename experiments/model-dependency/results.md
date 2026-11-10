# Model-dependency experiment — results (2026-11-10)

Protocol: `protocol.md`. Scores: `runs/<run>/data/scores/*.json`. Baseline: the reference run's own Fable 5.1 reader outputs scored the same way.

**Changes from the protocol:**
- Opus 5.5 readers were added on the same three packets.
- A second Sonnet skeptic run on B03 was added after the skeptic brief was fixed (see the skeptic section).
- The spot check covered every unmatched finding: 10, 15 and 7 per model, not a sample of 20.

Each model read each packet once, so run-to-run variation is not measured.

**What recall means here.** Recall is agreement with the rows the Fable readers proposed and the Fable skeptics kept. It is not agreement with the truth.

**Terms used here:**
- **Packet:** the part of the guide one agent reads.
  - B03: the self-referral, enrollment and app-connection pages.
  - B12: one FHIR Shorthand (FSH) CapabilityStatement file.
  - B10: the diagrams, figure transcripts and navigation.
- **Key:** one finding's id (`file@offset`).
- **Kept rows:** reference findings the skeptics did not reject.
- **Held row:** a finding that depends on an open team decision (D-n, in the rulebook's decisions register). It is written with the replacement that applies the glossary as written (the *strict reading*) and marked Pending until the team decides.
  - D-2: patient vs person / individual / client.
  - D-6: community-based organization (CBO) vs social service organization.
  - D-8: provider as person or organization.
- **Pending violation:** a reader finding on a held hit that is not marked with its decision.
- **Consistency pass:** one agent that checks all findings together for the same text treated differently.

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

The Fable rows score the reference readers against their own kept rows, so their recall is 100% by definition. Their precision proxy is the share of their proposals the skeptics kept.

Spot check of each model's unmatched findings, one Fable 5.1 skeptic pass per model:

| Model | Confirm | Revise | Reject | Total |
|---|---|---|---|---|
| Opus | 5 | 0 | 2 | 7 |
| Sonnet | 0 | 0 | 10 | 10 |
| Haiku | 0 | 0 | 15 | 15 |

*Reading:* Every model wrote edits that validate: no invalid `find`, no overlaps, no pending violations. The models differ in what they find.

**Opus:**
- Its recall stayed within a point of the Fable readers on every packet.
- Its seven extra findings lower its precision proxy. Five of them were confirmed in the spot check: two provider wordings, "Patient/Client", a diagram typo and a bare "recipient" that names the referral target. So the proxy understates its precision: counting the confirmed ones, 140 of 143, 39 of 40 and 35 of 38 of its findings hold up.

**Sonnet** lost 8 to 32 points of recall, on every packet.
- On B10 it caught the "CBO" acronym in all 11 diagrams but missed the spelled-out "Community-Based Organization" label in every one of them. These are held rows under D-6.

**Haiku** lost 11 to 22 points on B03 and B12 and matched Fable on B10.
- On the self-referral page it missed 18 of the 19 rows renaming "Community Resource Platform" to the glossary's term.
- On the app-connection page it changed "referral platform" to "coordination platform" eight times. There the phrase means any referral server, and the spot check rejected all eight.
- It used more tokens than Sonnet on every packet.

Both cheaper models proposed patient wording for FHIR elements whose author or requester is usually a practitioner or organization.

**Treat the spot check as indicative only:**
- It is one skeptic pass per model, and it was not consistent. The same edit on the same sentence of the referral-source FSH file (bare "the recipient is" → "the referral target is") was confirmed in Opus's pass and rejected in Sonnet's and Haiku's. So the contrast between Opus's 5 of 7 and the cheaper models' 0 of 25 is partly noise between passes.
- The spot-check briefs were rendered before the skeptic fix described below. Three of Sonnet's and two of Haiku's rejected rows cite D-2. Each also gives a reason that holds on the strict reading: the edit would make a role definition circular, or the text means the person represented.

## Skeptic role (Sonnet vs the reference verdicts, V01–V07)

| Packet | Brief | Compared | Agreement | Same outcome | confirm/confirm | reject/reject | revise/revise | Disagreements (ref→Sonnet) |
|---|---|---|---|---|---|---|---|---|
| B03 | original | 66 | 40.9% | 40.9% | 25 | 1 | 1 (same text) | confirm→reject 36, confirm→revise 2, revise→reject 1 |
| B03 | fixed | 66 | 93.9% | 92.4% | 61 | 0 | 1 (different text) | confirm→reject 2, reject→confirm 1, revise→confirm 1 |
| B12 | original | 4 | 75.0% | 75.0% | 3 | 0 | 0 | confirm→reject 1 |

*Agreement* counts matching verdicts. *Same outcome* also requires a revise to give the same replacement text.

*Reading:* The first run exposed a gap in the toolkit's skeptic brief: it did not say how to judge a held row. Sonnet rejected 36 rows the reference confirmed. 34 of them were held D-2 rows, rejected because the decision's recommended option keeps the text. The reference skeptics' brief had the same gap, yet they judged those rows on the strict reading as intended. The brief now says so (`skills/ig-glossary/prompts/skeptic.md`, "Pending decisions").

With the fixed brief, Sonnet reached the same outcome as the reference on 61 of 66 keys. Each of the other five is doubtful for Sonnet:
- **Accepted text the reference changed or rejected (two keys).**
  - It confirmed an edit inside quoted example note text, which the reference rejected.
  - It confirmed a self-referral replacement the reference had narrowed so the row holds whichever way D-2 is decided.
- **Rejected two "Community Resource Platform" renames (two keys).** Its reason was that renaming only some of the page's mentions would split its vocabulary. But the reference renames 19 of the page's 20 mentions. Sonnet's packet held only 3 of those rows, so rejecting two would itself create the split.
- **Revised with different wording (one key).**

On B12 (original brief), its one disagreement rejected an "SDOH needs" → "social risks" edit as a change of meaning.

The sample is small: one packet re-run, 70 keys in all. The consistency pass was not tested. On this evidence Sonnet as a skeptic is unproven, not shown to be safe.

## Recommendation

| Role | Recommended model | Why |
|---|---|---|
| Rulebook author, themes author | strongest available | authored inputs; untested here, and every later stage depends on them |
| Reader | Opus 5.5 or Fable 5.1 | Opus's recall matched the Fable readers within a point. Sonnet lost 8–32 points on every packet, and Haiku lost 11–22 on two of three, missing whole patterns |
| Skeptic | strongest available | Sonnet with the fixed brief reached the reference's outcome on 61 of 66 keys, but its departures lean toward accepting or splitting, and it was tested on one packet |
| Consistency pass | strongest available | untested here |
| QA review | strongest available | untested here; it is the last place a wrong edit is caught |

**Cost note.** All of the reference run's agents ran on Fable 5.1 and their token counts were not recorded, so this experiment cannot state a Fable-versus-Opus saving. Measured reader cost per packet:

| Model | Tokens | Minutes |
|---|---|---|
| Opus | 183k–193k | 3–12 |
| Sonnet | 78k–120k | 1–3.4 |
| Haiku | 158k–186k | 2–6.3 |

Prices differ by model, so token counts are not cost. On this evidence, dropping the readers to Sonnet to save money gives up about 8 points of recall on prose, 10 on FSH and a third of the diagram findings.
