---
name: ig-glossary
description: Use when asked to check a FHIR Implementation Guide's wording against its glossary, run a glossary alignment analysis, or when the user invokes /fhir-ig-glossary-toolkit:ig-glossary with a path to an IG checkout. Produces a findings workbook (xlsx) and a summary report (html).
---

# Glossary alignment for a FHIR IG

You orchestrate a pipeline of scripts and agents. The scripts are deterministic and tested; your job is to run them in order, dispatch the agents with the rendered prompts, and stop at the four checkpoints where a human decides. Never edit the IG snapshot, never hand-edit the outputs — fixes go into the data (verdicts, Q-packets, config, rulebook, themes) and the outputs are regenerated.

**Paths.** `SKILL_DIR` is this skill's base directory (announced when the skill loads). `SCRIPTS=$SKILL_DIR/scripts`. The **run directory** is the current working directory, the folder Claude Code was started in; every script takes `--run <dir>` if you need to be explicit. The usual layout keeps the IG checkout inside it (`<run>/<checkout>/`), so the agents need no access outside the folder. Never run inside the checkout: config.yaml and data/ would be written into it. If the working directory is the checkout or inside it, stop and ask the user to start Claude Code from the folder that contains the checkout. The **snapshot** is the IG checkout `config.yaml` points at.

**Resume.** Scripted steps are cheap and deterministic: re-run them each time. The exceptions are `verify.py --packets`, which runs once (skip it if `data/verify/V01.keys.json` exists), and the Step 8 copy. Agent work is skipped per packet once its output validates. Step 5 dispatches only packets without `data/agent/validated/Bnn.json`, and Step 6 only V packets without `data/verify/Vnn.json`. After each checkpoint approval, append its name (`config`, `rulebook`, `themes`, `hand-over`) to `checkpoints.txt` in the run directory. On resume, re-ask any checkpoint that isn't recorded, even if its file exists.

**When a script fails**, show the user its output and stop. Don't patch scripts or hand-edit data to get past it.

**Agents.** Dispatch with the Agent tool (`subagent_type: general-purpose`), one per packet, all packets in one message. Pass the exact text printed by `prompt.py` as the prompt. Model per role: see "Which model" in the toolkit README (reader: Opus 5.5 or Fable 5.1; every other role: the strongest available). After each agent returns, write `data/agent/<Bnn>.meta.json` (reader), `data/verify/<Vnn>.meta.json` (skeptic or consistency) or `data/qa/<Qnn>.meta.json` (QA) with `{"model": "...", "tokens": N, "seconds": N}`: write the model you requested, and take tokens and seconds from the agent result, so the run's cost is recorded.

## Step 0 — Preflight

- `python3 -c "import yaml, openpyxl"`; if it fails, tell the user the exact command `python3 -m pip install pyyaml openpyxl` and offer to run it. If it is refused with externally-managed-environment, use `python3 -m pip install --user --break-system-packages pyyaml openpyxl`, or a virtual environment.
- The argument to `/fhir-ig-glossary-toolkit:ig-glossary` is the IG checkout. If it is a repository URL instead, clone it into the run directory with `git clone --depth 1 --branch <tag> <url>` (ask for the tag under review if none was given) and use the clone. Confirm `<ig>/sushi-config.yaml` exists. If not, ask for the right path.
- `git -C <ig> status --porcelain`: if non-empty, warn that the snapshot should be a clean checkout at the tag under review (untracked build artifacts are fine; modified source files are not), and ask whether to continue.
- If `<ig>/fsh-generated/resources/` is absent, mention that running `sushi build` in the checkout first gives instance pages their published URLs; optional.
- Check the working directory is not the checkout or inside it (see Paths).

## Step 1 — Config  ✋ CHECKPOINT 1

Outputs: `config.yaml`.

Skip init.py if config.yaml exists. Otherwise run `python3 $SCRIPTS/init.py <ig>`. Show the user the printed config and ask them to confirm or correct: name, short, tag, canonical, published_base (where the guide is published — for HL7 guides the inferred `/en/` form is right; for other publishers check it), artifact_prefixes, glossary_page. If `glossary_page` is blank, init found no glossary page file under `input/pagecontent/` or `input/pages/`: ask the user for its path. Then read the glossary page yourself and propose the **acronym table**: every acronym the glossary defines, its spelled-out form, its term id (you will assign ids in Step 3 — use `T-<ACRONYM>`), and any multi-word names starting with the acronym that must not be spelled out (`not_standalone`; each name matches as spelled with an optional plural s, so list every capitalisation the guide uses, e.g. both `SDOH domain` and `SDOH Domain`). Write them into `config.yaml` under `acronyms:`; each table entry has the shape `ACR: {long: spelled-out form, term: T-ID}`. Write the long form in lower case unless it is a proper name (`electronic health record`, not `Electronic Health Record`): it is inserted mid-sentence as written, and capitalised only at the start of a sentence. Show the result; proceed on yes.

## Step 2 — Extract

Outputs: `data/segments.jsonl`, `data/coverage.json`, `data/figures.json`.

`python3 $SCRIPTS/extract.py`. Report the printed line, and show the user the excluded files grouped by reason (extract prints each reason with its count; `data/coverage.json` gives each file's reason). If any pages were excluded as not published, ask the user before continuing: those pages are left out of the analysis. If they should not be, stop: the fix belongs in the guide's `sushi-config.yaml` `pages:` block, not in this run. If `figures.json` lists raster images, tell the user: those images' text is only analysed if transcribed into `figure_transcripts.yaml` (shape: see `$SKILL_DIR/../../examples/*/figure_transcripts.yaml`). Offer to transcribe them yourself by reading the images; if the user agrees, write the file and re-run extract.

## Step 3 — Rulebook  ✋ CHECKPOINT 2

Outputs: `rulebook.yaml`.

If `rulebook.yaml` already exists (a resumed run, or a rulebook copied in), skip the agent, which would overwrite it: start from the `check_rulebook.py` run below, and make any fixes or changes yourself instead of relaying them. Otherwise render `python3 $SCRIPTS/prompt.py rulebook-author` and dispatch **one agent** with it. When it returns, run `python3 $SCRIPTS/check_rulebook.py` yourself; if it lists problems, send them back to the same agent (SendMessage) until it prints `rulebook: OK`. Fix any `acronyms.table…` problems yourself in config.yaml (set the term to the rulebook id of the term it spells out); send only the other problems back to the agent. Run `python3 $SCRIPTS/scan.py` and show the user: the per-rule hit counts from `data/rulebook-review.md` (a rule with zero hits or thousands of hits is worth a question), the term count, each decision's title/question/recommendation, and the domain notes. The user approves, edits the file, or asks for changes (which you relay to the agent). Proceed on approval.

## Step 4 — Scan and batch

Outputs: `data/hits.jsonl`, `data/counts.json`, `data/rulebook-review.md`, `data/batches/manifest.json`, `data/batches/B*.md`.

`python3 $SCRIPTS/scan.py` then `python3 $SCRIPTS/batches.py`. Show the batch table (id, files, hits, title). If a packet looks wrong to you (one file that clearly belongs with another), add an entry to `config.yaml` `batches.overrides` (entries are `{id: Bnn, title: ..., globs: [paths relative to the snapshot]}`) and re-run `batches.py`; otherwise continue without asking.

## Step 5 — Read

Outputs: `data/agent/B*.json`, one per packet in the manifest.

For every packet id in `data/batches/manifest.json`: `python3 $SCRIPTS/prompt.py reader --packet Bnn` → dispatch one agent. All in one message. When all return, run `python3 $SCRIPTS/findings.py` (validates every packet). Any packet that fails validation or whose file is missing: re-dispatch that packet alone with the same prompt plus the validator's output, at most twice. After that, tell the user which packet and what the validator says.

## Step 6 — Verify

Outputs: `data/verify/V*.json` (skeptic packets), plus one consistency verdict file.

`python3 $SCRIPTS/verify.py --packets --n 3` (use `--n 4` or more if any packet has over ~120 findings; to change `--n`, first delete `data/verify/V*.md` and `data/verify/V*.keys.json` (no verdicts exist yet); otherwise new packets are added after the old ones). For each `Vnn`: `python3 $SCRIPTS/prompt.py skeptic --packet Vnn` → dispatch one agent; all in one message. Then the consistency pass: its id is the next one after the last V packet `verify.py --packets` printed (the highest `data/verify/Vnn.keys.json`; empty packets are not written, so there can be fewer than `--n`); render `python3 $SCRIPTS/prompt.py consistency --packet <that id>` and dispatch one agent. Check each returned file with `python3 $SCRIPTS/verify.py --check Vnn` (add `--partial` for the consistency file).

## Step 7 — Merge

Outputs: `data/findings.json`, `data/rejected.json`.

`python3 $SCRIPTS/merge.py`. Report the printed counts. If it reports overlapping agent findings, open the two keys it names, decide which stands, and record a `reject` verdict for the other in a new `V<next>.json` (reason "overlap: …"); re-run.

## Step 8 — Dry run

Outputs: `data/dryrun/apply-report.json`.

Use absolute paths. Remove any existing `<ig>-dryrun` first (`git -C <ig> worktree remove --force <ig>-dryrun`; use `rm -rf <ig>-dryrun` only for a copy made with `cp -R`, because a worktree removed that way stays registered and the next `worktree add` fails), because re-applying onto an applied copy doubles edits. Create the copy with `git -C <ig> worktree add --detach <ig>-dryrun HEAD` (HEAD is the commit under review, and the configured tag may not be a git ref). If `git -C <ig> status --porcelain` shows modified source files, use `cp -R <ig> <ig>-dryrun` instead. Then run `python3 $SCRIPTS/apply.py --root <ig>-dryrun`. Expected: `drifted 0`. Any drift means a finding's text does not match the snapshot; report it to the user — it is a bug in the data, not something to patch.

## Step 9 — Themes  ✋ CHECKPOINT 3

Outputs: `themes.yaml`.

If `themes.yaml` already exists, skip the agent, which would overwrite it: run `python3 $SCRIPTS/check_themes.py`, fix any problems it lists yourself, and go on to the checkpoint. Otherwise render `python3 $SCRIPTS/prompt.py themes-author`, dispatch one agent, run `python3 $SCRIPTS/check_themes.py` until `themes: OK`. Either way, show the user the theme titles, sizes and the `alignment_work` paragraphs. Proceed on approval.

## Step 10 — Outputs

Outputs: `data/findings.json`, `_build/<short>-<tag>-glossary-alignment-findings.xlsx`, `_build/<short>-<tag>-glossary-alignment-summary.html`.

The Step 7 merge ran before `themes.yaml` existed, so every row sits in a catch-all theme. Run `python3 $SCRIPTS/merge.py` again so rows pick up the approved themes, then `python3 $SCRIPTS/sheet.py` and `python3 $SCRIPTS/summary.py`.

## Step 11 — Quality review

Outputs: `data/qa/review-Q*.md`; fixes as `data/verify/V<next>.json` and `data/agent/Q*.json`.

Render `python3 $SCRIPTS/prompt.py qa-review --packet Q01` (and `Q02`, `Q03` for independent readers) and dispatch. Read the review tables. For each issue, land the fix in the data:
- a wrong or weak row → verdict (`reject` / `revise` / `retag`) in `data/verify/V<next>.json`, reason prefixed "QA: "; each QA verdict file is checked with `python3 $SCRIPTS/verify.py --check V<next> --partial` until it prints `V<next>: OK`; a `retag` verdict carries `"decision"` (an open D-id, or null to move the row to Ready) and `"recommended": "change" | "keep"`, which is required when decision is a D-id;
- a missed finding → an entry in `data/agent/Q01.json` (reader output format, `"hits": []`), validated with `python3 $SCRIPTS/findings.py --batch Q01`;
- a narrative problem → edit `themes.yaml` or `config.yaml` `summary:`.
Then re-run Steps 7 and 10. Repeat once if the second review still finds substantive issues; otherwise stop. Optional: build the final dry-run copy and compare the publisher's QA (`reference/ig-build.md`).

## Step 12 — Hand over  ✋ CHECKPOINT 4

Tell the user where the two files are and what they contain, in three or four sentences. Point them to `reference/google-conversion.md` if the review will happen in Google Sheets, and tell them that when the reviewed workbook comes back they can ask Claude to run the round-trip check on it. You run `python3 $SCRIPTS/roundtrip.py --run <absolute run dir> <returned.xlsx>` (expected: `OK: every locked column matches findings.json`). Done.
