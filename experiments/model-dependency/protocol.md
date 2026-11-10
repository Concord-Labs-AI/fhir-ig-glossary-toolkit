# Model-dependency experiment — protocol

**Question.** Did the reference run's quality come from running every agent on Fable 5.1, or would a cheaper model do? Per role.

**Reference.** The SDOH 3.0.0 reference run's data (kept outside this repository): reader outputs B01–B12 (all Fable 5.1, no model override), skeptic verdicts V01–V06, consistency pass V07, QA verdicts V08, merged `findings.json` (kept) and `rejected.json`.

**Base.** `runs/base/` is the toolkit's own extract/scan/batches on the same snapshot with the reference packet overrides; Task 14 confirmed it reproduces the reference counts and hit ids, so candidate agents read identical packets.

**Candidates.**

| Role | Packet | Material | Models |
|---|---|---|---|
| Reader | B03 | prose (self-referral, enrollment, app connection) | Sonnet, Haiku |
| Reader | B12 | FSH, referral-source CapabilityStatement | Sonnet, Haiku |
| Reader | B10 | diagrams, figure transcripts, navigation | Sonnet, Haiku |
| Skeptic | B03's reference findings | verdicts | Sonnet |
| Skeptic | B12's reference findings | verdicts | Sonnet |
| Spot check | 20 unmatched findings from the cheaper readers | one Fable skeptic pass | Fable 5.1 |

Identical prompts (`prompt.py`); only the Agent tool `model:` differs. Each candidate run directory is a copy of `runs/base/` so agents validate against the same segments and rulebook.

**Measures** (`score.py`): validity (share of proposed findings that validate), recall of reference kept rows (same key or overlapping span), precision proxy (share of valid findings that match a reference rejected row or no row), pending-decision violations, tokens and wall time. Skeptic: agreement with the reference verdict per key, with a reject/revise/confirm breakdown.

**Reading the result.** A role tolerates a cheaper model if validity and recall stay within a few points of Fable and the spot check confirms most of its extra findings. The README states the per-role recommendation from these numbers.
