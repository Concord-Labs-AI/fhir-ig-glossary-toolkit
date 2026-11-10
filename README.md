# IG glossary toolkit

Checks every sentence of a FHIR Implementation Guide against the guide's own glossary. It gives the team two things:

- **A findings workbook.** Every place the guide departs from the glossary is written as an exact, reviewable edit, with Accept / Modify / Reject / Defer.
- **A summary report.** It goes theme by theme: what the glossary says, what the guide does, the work needed to align them, and which decisions the team must take first.

The method comes from the glossary alignment of the HL7 SDOH Clinical Care IG 3.0.0 (31 terms, 844 findings). That run ships here as the worked example in `examples/`.

## What you need

- **Claude Code.** The toolkit is a Claude Code plugin; the stages that need judgement run as Claude agents.
- **Python 3** with `pyyaml` and `openpyxl` (`pip3 install pyyaml openpyxl`), and `pytest` only to run the tests.
- **A checkout of the IG** at the tag you are reviewing. Running `sushi build` in it first is optional; it gives instance pages their published URLs.

## Run it

```bash
git clone https://github.com/Concord-Labs-AI/ig-glossary-toolkit
mkdir my-ig-glossary-run && cd my-ig-glossary-run
claude --plugin-dir ../ig-glossary-toolkit
```
Keep the run folder outside the IG checkout; the toolkit writes its data there. Then, in Claude Code:
```
/ig-glossary-toolkit:ig-glossary ../path-to-your-ig-checkout
```

Claude runs the pipeline and stops four times for you:

1. **Config.** It shows what it inferred from the IG's `sushi-config.yaml` (name, canonical, published URL, artifact prefixes, glossary page) and the acronym table it read off the glossary. Say yes or correct it.
2. **Rulebook.** An agent writes `rulebook.yaml`. It holds a definition and search rules for each glossary term, plus domain notes for the reading agents. It also has a *decisions register*: every place the glossary and the guide's usage disagree, with options and a recommendation. You approve or edit it. This is the step worth your attention, because everything downstream follows the rulebook.
3. **Themes.** After the findings exist, an agent writes `themes.yaml`, the narrative that groups findings in the report. You approve or edit it.
4. **Hand-over.** The workbook and report are in `_build/`.

Everything else is scripted or delegated to agents:

- extraction of every reader-visible text segment, a pattern scan, and splitting the guide into packets;
- one reading agent per packet, and validation of every proposed edit;
- skeptic agents that try to disprove the findings, then a consistency pass;
- merge, and a dry-run apply to a scratch copy of the guide;
- workbook and report generation;
- a review pass whose fixes go into the data, after which the outputs are regenerated.

An interrupted run resumes where it stopped.

## What you get

- `_build/<ig>-<tag>-glossary-alignment-findings.xlsx` has these tabs:
  - **README:** how to review.
  - **Findings:** one row per edit, with the context as read, the exact source text, the suggested replacement, confidence, status (Ready, or Pending D-n), the published link, and reviewer columns with a dropdown.
  - **Decisions**, **Decision x theme**, **Term coverage**, **Page x theme** and **Reviewer additions**.
- `_build/<ig>-<tag>-glossary-alignment-summary.html` has the headline numbers, the decisions needed first, what the team needs to supply, one section per theme with examples, work packages, names kept as they are, and the method and its limits. It opens in a browser and converts cleanly to a Google Doc.

See the example outputs in `examples/sdoh-clinicalcare-3.0.0/`.

## Time and cost

The reference IG (207 files with text, 31 terms) split into 12 reading packets, 6 skeptic packets and 1 consistency pass, followed by a review pass. Measured per agent in the model experiment:

| Agent | Model | Tokens | Minutes |
|---|---|---|---|
| Reader, one packet | Opus 5.5 | 183k–193k | 3–12 |
| Skeptic, one packet | Sonnet | 55k–98k | under 2 |

Smaller guides need fewer packets. The optional IG build (`skills/ig-glossary/reference/ig-build.md`) adds 20–40 minutes per build.

## Which model

To measure this, the same packets were re-run with the same prompts on other models and scored against the reference run, which used Fable 5.1 throughout. Details are in `experiments/model-dependency/results.md`.

| Role | Recommended | Evidence |
|---|---|---|
| Rulebook and themes authoring | strongest available | not tested on cheaper models; every later stage depends on these |
| Reading agents | Opus 5.5 or Fable 5.1 | Opus kept recall within a point of Fable on all three packets. Sonnet lost 8–32 points on every packet; Haiku lost 11–22 on two of three, missing whole patterns |
| Skeptic | strongest available | Sonnet reached Fable's outcome on 61 of 66 findings, but its departures lean toward accepting edits Fable changed or rejected; tested on one packet |
| Consistency pass | strongest available | not tested |
| Quality review | strongest available | not tested on cheaper models; the last place a wrong edit is caught |

## Limits

- Text inside raster images is analysed only if someone transcribes it into `figure_transcripts.yaml`. Claude offers to do this when it finds such images.
- In `sushi-config.yaml`, a title or description that wraps onto a second line is read only up to the line break.
- The model recommendation rests on one IG and one run per model per packet.

## The method in one page

See `skills/ig-glossary/reference/method.md`. In short:

- Edits are exact: each one names the text to find and its replacement.
- Rules are tuned to catch too much; an agent then judges every candidate and records a disposition for each.
- Skeptic agents try to disprove the findings.
- Disagreements between the glossary and the guide are held as *decisions*, not counted as errors.
- Edits are applied by occurrence, and the toolkit reports drift instead of guessing.
- Quality fixes go into the data, never into the outputs by hand.

## Reviewing in Google Sheets / Docs

`skills/ig-glossary/reference/google-conversion.md` covers how to upload and convert the outputs, what to check, and how to run the round-trip checker on the workbook when it comes back.

## Layout

```
.claude-plugin/plugin.json        the plugin manifest
skills/ig-glossary/SKILL.md       the runbook Claude follows
skills/ig-glossary/scripts/       the pipeline (python3, tested)
skills/ig-glossary/prompts/       the agent briefs (templates)
skills/ig-glossary/reference/     method, optional IG build, Google appendix
examples/sdoh-clinicalcare-3.0.0/ the reference run's inputs and outputs
experiments/model-dependency/     protocol, scores, results
tests/                            python3 -m pytest -q
```

---

Method and tooling by Corey Smith, Concord Labs AI (corey@claystreetgroup.com). Use it however you like.
