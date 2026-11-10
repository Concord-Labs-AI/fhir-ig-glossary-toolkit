# FHIR IG glossary toolkit

Checks every sentence of a FHIR Implementation Guide against the guide's own glossary. It gives the team two files:

- **A findings workbook** (xlsx). Every place the guide departs from its glossary is written as an exact edit, which a reviewer can accept, modify, reject or defer.
- **A summary report** (html). It goes theme by theme: what the glossary says, what the guide does, the work needed to align them, and which decisions the team must take first.

It is a Claude Code plugin. The method comes from the [Gravity Project](https://thegravityproject.net)'s glossary alignment of the HL7 SDOH Clinical Care IG 3.0.0 (31 terms, 844 findings). That run ships here as the worked example in `examples/`.

## Quick start

You need:
- [Claude Code](https://code.claude.com/docs/en/quickstart) 2.1.275 or later, signed in;
- Python 3.9 or later;
- git.

Make a folder for the run and start Claude Code in it:

```bash
mkdir sdoh-glossary && cd sdoh-glossary
claude
```

In Claude Code, install the toolkit (once per machine), then run it on a guide:

```
/plugin install fhir-ig-glossary-toolkit --marketplace Concord-Labs-AI/fhir-ig-glossary-toolkit
/fhir-ig-glossary-toolkit:ig-glossary https://github.com/HL7/fhir-sdoh-clinicalcare at tag 3.0.0
```

If the install says to run `/reload-plugins`, do that before the second line.

Claude then:
1. clones the guide into the folder;
2. installs the two Python packages it needs, `pyyaml` and `openpyxl`, if they are missing (it asks first);
3. shows you the settings it read from the guide.

Say yes, and the analysis is under way. It stops three more times for you (see [During a run](#during-a-run)).

**Your own guide.** Give its repository URL and tag, or the path to a checkout inside the run folder. The guide must be a SUSHI project (it has a `sushi-config.yaml`) with a glossary page.

**Fewer permission prompts.** In auto mode, Claude Code runs the toolkit without asking. Otherwise it asks before each script. To approve the toolkit's own scripts once for the whole run, start Claude Code like this instead:

```bash
claude --permission-mode acceptEdits --allowedTools "Bash(python3 */skills/ig-glossary/scripts/*)"
```

This lets Claude, and the agents it starts, run the toolkit's scripts and write files inside the run folder without asking. Anything else still asks.

### Or let an AI agent set it up

Open Claude Code, or another coding agent, in an empty folder and paste:

> Set up the FHIR IG glossary toolkit by following "Setup steps for AI agents" in https://github.com/Concord-Labs-AI/fhir-ig-glossary-toolkit, then run it on https://github.com/HL7/fhir-sdoh-clinicalcare at tag 3.0.0.

## Setup steps for AI agents

A user has asked you to install or run this toolkit. Work in their current folder, which becomes the run folder. Ask before each install.

1. Run `claude --version`. If `claude` is missing, send the user to https://code.claude.com/docs/en/quickstart and stop.
2. Install the plugin. A message that it is already installed is fine.
   ```bash
   claude plugin marketplace add Concord-Labs-AI/fhir-ig-glossary-toolkit
   claude plugin install fhir-ig-glossary-toolkit@fhir-ig-glossary-toolkit
   ```
3. Check Python: `python3 -c "import yaml, openpyxl"`. If that fails:
   - run `python3 -m pip install pyyaml openpyxl`;
   - if pip refuses with `externally-managed-environment`, run `python3 -m pip install --user --break-system-packages pyyaml openpyxl`.
4. Get the guide: `git clone --depth 1 --branch <tag> <repository-url>` in the current folder. Ask the user for the repository and tag if they did not give them. Check that `<clone>/sushi-config.yaml` exists.
5. Hand over:
   - **If you are Claude Code:** ask the user to type `/reload-plugins`, then `/fhir-ig-glossary-toolkit:ig-glossary <clone>`.
   - **Otherwise:** tell them to run `claude` in this folder and type that second command.

   Mention the permission tip under Quick start.

## During a run

Claude runs the pipeline and stops four times for you:

1. **Config.** It shows what it inferred from the IG's `sushi-config.yaml` (name, canonical, published URL, artifact prefixes, glossary page) and the acronym table it read off the glossary. Say yes or correct it.
2. **Rulebook.** An agent writes `rulebook.yaml`. It holds:
   - a definition and search rules for each glossary term;
   - domain notes for the reading agents;
   - a *decisions register*: every place the glossary and the guide's usage disagree, with options and a recommendation.

   You approve or edit it. This is the step worth your attention, because everything downstream follows the rulebook.
3. **Themes.** After the findings exist, an agent writes `themes.yaml`, the narrative that groups findings in the report. You approve or edit it.
4. **Hand-over.** The workbook and report are in `_build/`.

Everything else is scripted or delegated to agents:

- extraction of every reader-visible text segment, a pattern scan, and splitting the guide into packets;
- one reading agent per packet, and validation of every proposed edit;
- skeptic agents that try to disprove the findings, then a consistency pass;
- merge, and a dry-run apply to a scratch copy of the guide;
- workbook and report generation;
- a review pass whose fixes go into the data, after which the outputs are regenerated.

An interrupted run resumes where it stopped: start Claude Code in the same folder and type the same command.

Running `sushi build` in the checkout first is optional. It gives instance pages their published URLs.

## What you get

- `_build/<ig>-<tag>-glossary-alignment-findings.xlsx` has these tabs:
  - **README:** how to review.
  - **Findings:** one row per edit. It gives the context as read, the exact source text, the suggested replacement, confidence, status (Ready, or Pending D-n), the published link, and reviewer columns with a dropdown.
  - **Decisions**, **Decision x theme**, **Term coverage**, **Page x theme** and **Reviewer additions**.
- `_build/<ig>-<tag>-glossary-alignment-summary.html` has:
  - the headline numbers;
  - the decisions needed first, and what the team needs to supply;
  - one section per theme with examples;
  - work packages, and names kept as they are;
  - the method and its limits.

  It opens in a browser and converts cleanly to a Google Doc.

See the example outputs in `examples/sdoh-clinicalcare-3.0.0/`.

## Time and cost

The reference IG (207 files with text, 31 terms) split into 12 reading packets, 6 skeptic packets and 1 consistency pass, followed by a review pass. Measured per agent in the model experiment:

| Agent | Model | Tokens | Minutes |
|---|---|---|---|
| Reader, one packet | Opus 5.5 | 183k–193k | 3–12 |
| Skeptic, one packet | Sonnet | 55k–98k | under 2 |

For a guide that size, reading alone comes to about 2.3 million tokens (12 packets at about 190k each), so use a plan or API budget with room for that. Smaller guides need fewer packets. The optional IG build (`skills/ig-glossary/reference/ig-build.md`) adds 20–40 minutes per build.

## Which model

To measure this, the same packets were re-run with the same prompts on other models. They were scored against the reference run, which used Fable 5.1 throughout. Details are in `experiments/model-dependency/results.md`.

| Role | Recommended | Evidence |
|---|---|---|
| Rulebook and themes authoring | strongest available | not tested on cheaper models; every later stage depends on these |
| Reading agents | Opus 5.5 or Fable 5.1 | Opus kept recall within a point of Fable on all three packets. Sonnet lost 8–32 points on every packet. Haiku lost 11–22 on two of three, missing whole patterns |
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

`skills/ig-glossary/reference/google-conversion.md` covers:
- how to upload and convert the outputs;
- what to check;
- how to run the round-trip checker on the workbook when it comes back.

## Updating

Run `claude plugin update fhir-ig-glossary-toolkit@fhir-ig-glossary-toolkit`, then `/reload-plugins` in any open session.

## Working on the toolkit

```bash
git clone https://github.com/Concord-Labs-AI/fhir-ig-glossary-toolkit
claude --plugin-dir ./fhir-ig-glossary-toolkit      # load your local copy instead of the installed one
cd fhir-ig-glossary-toolkit && python3 -m pytest -q # the tests need pytest as well
```

```
.claude-plugin/plugin.json        the plugin manifest
.claude-plugin/marketplace.json   lets /plugin install find it on GitHub
skills/ig-glossary/SKILL.md       the runbook Claude follows
skills/ig-glossary/scripts/       the pipeline (python3, tested)
skills/ig-glossary/prompts/       the agent briefs (templates)
skills/ig-glossary/reference/     method, optional IG build, Google appendix
examples/sdoh-clinicalcare-3.0.0/ the reference run's inputs and outputs
experiments/model-dependency/     protocol, scores, results
tests/                            python3 -m pytest -q
```

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE). Copyright 2026 Clay Street Group, LLC.

---

Method and tooling by Corey Smith, Concord Labs AI (corey@claystreetgroup.com).
