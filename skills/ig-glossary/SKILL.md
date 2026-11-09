---
name: ig-glossary
description: Use when asked to check a FHIR Implementation Guide's wording against its glossary, run a glossary alignment analysis, or when the user invokes /ig-glossary with a path to an IG checkout. Produces a findings workbook (xlsx) and a summary report (html).
---

# Glossary alignment for a FHIR IG

You orchestrate a pipeline of scripts and agents. The scripts are deterministic and tested; your job is to run them in order, dispatch the agents with the rendered prompts, and stop at the four checkpoints where a human decides. Never edit the IG snapshot, never hand-edit the outputs — fixes go into the data (verdicts, Q-packets, config, rulebook, themes) and the outputs are regenerated.

**Paths.** `SKILL_DIR` is this skill's base directory (announced when the skill loads). `SCRIPTS=$SKILL_DIR/scripts`. The **run directory** is the current working directory; every script takes `--run <dir>` if you need to be explicit. The **snapshot** is the IG checkout `config.yaml` points at.

**Resume rule.** Before each step, check whether its outputs already exist (listed per step). If they do, skip the step. A run can be interrupted at any point and continued.

**Agents.** Dispatch with the Agent tool (`subagent_type: general-purpose`), one per packet, all packets in one message. Pass the exact text printed by `prompt.py` as the prompt. Model per role: see "Which model" in the toolkit README; if the README has no table yet, use the strongest available model for every role. After each agent returns, write `data/agent/<Bnn>.meta.json` (or `data/verify/<Vnn>.meta.json`) with `{"model": "...", "tokens": N, "seconds": N}` from the agent result, so the run's cost is recorded.

## Step 0 — Preflight

- `python3 -c "import yaml, openpyxl"`; if it fails, tell the user the exact command `pip3 install pyyaml openpyxl` and offer to run it.
- The argument to `/ig-glossary` is the IG checkout. Confirm `<ig>/sushi-config.yaml` exists. If not, ask for the right path.
- `git -C <ig> status --porcelain`: if non-empty, warn that the snapshot should be a clean checkout at the tag under review (untracked build artifacts are fine; modified source files are not), and ask whether to continue.
- If `<ig>/fsh-generated/resources/` is absent, mention that running `sushi build` in the checkout first gives instance pages their published URLs; optional.

## Step 1 — Config  ✋ CHECKPOINT 1

Outputs: `config.yaml`.

Run `python3 $SCRIPTS/init.py <ig>`. Show the user the printed config and ask them to confirm or correct: name, short, tag, canonical, published_base (where the guide is published — for HL7 guides the inferred `/en/` form is right; for other publishers check it), artifact_prefixes, glossary_page. If `glossary_page` is blank, init found no glossary page file under `input/pagecontent/` or `input/pages/`: ask the user for its path. Then read the glossary page yourself and propose the **acronym table**: every acronym the glossary defines, its spelled-out form, its term id (you will assign ids in Step 3 — use `T-<ACRONYM>`), and any multi-word names starting with the acronym that must not be spelled out (`not_standalone`; each name matches as spelled with an optional plural s, so list every capitalisation the guide uses, e.g. both `SDOH domain` and `SDOH Domain`). Write them into `config.yaml` under `acronyms:`. Show the result; proceed on yes.

## Step 2 — Extract

Outputs: `data/segments.jsonl`, `data/coverage.json`, `data/figures.json`.

`python3 $SCRIPTS/extract.py`. Report the printed line. If `figures.json` lists raster images, tell the user: those images' text is only analysed if transcribed into `figure_transcripts.yaml` (shape: see `$SKILL_DIR/../../examples/*/figure_transcripts.yaml`). Offer to transcribe them yourself by reading the images; if the user agrees, write the file and re-run extract.

## Step 3 — Rulebook  ✋ CHECKPOINT 2

Outputs: `rulebook.yaml`.

Render `python3 $SCRIPTS/prompt.py rulebook-author` and dispatch **one agent** with it. When it returns, run `python3 $SCRIPTS/check_rulebook.py` yourself; if it lists problems, send them back to the same agent (SendMessage) until it prints `rulebook: OK`. Then show the user: the term count, each decision's title/question/recommendation, and the domain notes. The user approves, edits the file, or asks for changes (which you relay to the agent). Proceed on approval.

## Step 4 — Scan and batch

Outputs: `data/hits.jsonl`, `data/counts.json`, `data/rulebook-review.md`, `data/batches/manifest.json`, `data/batches/B*.md`.

`python3 $SCRIPTS/scan.py` then `python3 $SCRIPTS/batches.py`. Show the batch table (id, files, hits, title). If a packet looks wrong to you (one file that clearly belongs with another), add an entry to `config.yaml` `batches.overrides` and re-run `batches.py`; otherwise continue without asking.

## Step 5 — Read

Outputs: `data/agent/B*.json`, one per packet in the manifest.

For every packet id in `data/batches/manifest.json`: `python3 $SCRIPTS/prompt.py reader --packet Bnn` → dispatch one agent. All in one message. When all return, run `python3 $SCRIPTS/findings.py` (validates every packet). Any packet that fails validation or whose file is missing: re-dispatch that packet alone with the same prompt plus the validator's output.

## Step 6 — Verify

Outputs: `data/verify/V*.json` (skeptic packets), plus one consistency verdict file.

`python3 $SCRIPTS/verify.py --packets --n 3` (use `--n 4` or more if any packet has over ~120 findings). For each `Vnn`: `python3 $SCRIPTS/prompt.py skeptic --packet Vnn` → dispatch one agent; all in one message. Then the consistency pass: the next free id is `V<n+1>`; render `python3 $SCRIPTS/prompt.py consistency --packet V<n+1>` and dispatch one agent. Check each returned file with `python3 $SCRIPTS/verify.py --check Vnn` (add `--partial` for the consistency file).

## Step 7 — Merge

Outputs: `data/findings.json`, `data/rejected.json`.

`python3 $SCRIPTS/merge.py`. Report the printed counts. If it reports overlapping agent findings, open the two keys it names, decide which stands, and record a `reject` verdict for the other in a new `V<next>.json` (reason "overlap: …"); re-run.

## Step 8 — Dry run

Outputs: `data/dryrun/apply-report.json`.

Create a scratch copy of the snapshot (`git -C <ig> worktree add --detach <ig>-dryrun <tag>`, or `cp -R` if it is not a git checkout). `python3 $SCRIPTS/apply.py --root <ig>-dryrun`. Expected: `drifted 0`. Any drift means a finding's text does not match the snapshot; report it to the user — it is a bug in the data, not something to patch. Optional IG build: `reference/ig-build.md`.

## Step 9 — Themes  ✋ CHECKPOINT 3

Outputs: `themes.yaml`.

Render `python3 $SCRIPTS/prompt.py themes-author`, dispatch one agent, run `python3 $SCRIPTS/check_themes.py` until `themes: OK`. Show the user the theme titles, sizes and the `alignment_work` paragraphs. Proceed on approval.

## Step 10 — Outputs

Outputs: `data/findings.json`, `_build/<short>-<tag>-glossary-alignment-findings.xlsx`, `_build/<short>-<tag>-glossary-alignment-summary.html`.

The Step 7 merge ran before `themes.yaml` existed, so every row sits in a catch-all theme. Run `python3 $SCRIPTS/merge.py` again so rows pick up the approved themes, then `python3 $SCRIPTS/sheet.py` and `python3 $SCRIPTS/summary.py`.

## Step 11 — Quality review

Outputs: `data/qa/review-Q*.md`; fixes as `data/verify/V<next>.json` and `data/agent/Q*.json`.

Render `python3 $SCRIPTS/prompt.py qa-review --packet Q01` (and `Q02`, `Q03` for independent readers) and dispatch. Read the review tables. For each issue, land the fix in the data:
- a wrong or weak row → verdict (`reject` / `revise` / `retag`) in `data/verify/V<next>.json`, reason prefixed "QA: "; each QA verdict file is checked with `python3 $SCRIPTS/verify.py --check V<next> --partial` until it prints `V<next>: OK`; a `retag` verdict carries `"decision"` (an open D-id, or null to move the row to Ready) and `"recommended": "change" | "keep"`, which is required when decision is a D-id;
- a missed finding → an entry in `data/agent/Q01.json` (reader output format, `"hits": []`), validated with `python3 $SCRIPTS/findings.py --batch Q01`;
- a narrative problem → edit `themes.yaml` or `config.yaml` `summary:`.
Then re-run Steps 7 and 10. Repeat once if the second review still finds substantive issues; otherwise stop.

## Step 12 — Hand over  ✋ CHECKPOINT 4

Tell the user where the two files are and what they contain, in three or four sentences. Point them to `reference/google-conversion.md` if the review will happen in Google Sheets, and to `python3 $SCRIPTS/roundtrip.py <returned.xlsx>` for when the reviewed workbook comes back (expected: `OK: every locked column matches findings.json`). Done.
