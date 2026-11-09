# Glossary alignment — deliverable review

You are a first-time reader of two deliverables for **{{ig_name}}** ({{tag}}): the summary report `{{summary}}` and the findings workbook `{{workbook}}` (read it with Python and openpyxl: `load_workbook(path, data_only=True)`; tabs README, Findings, Decisions). The source is at `{{snapshot}}`; the rulebook and themes are in `{{run_dir}}`.

Review as the team that has to act on these will: can they understand each theme without the glossary open? Is every number consistent between the report and the workbook? Do the examples make the case? Spot-check **twenty Findings rows** chosen across themes and confidence levels: open the source line, confirm `Source find` is there exactly once at the stated occurrence, and judge whether the `Suggested replace` reads correctly and whether the row's Status/decision tag is right.

Each workbook row's ID (e.g. GA-0001) is looked up in `{{run_dir}}/data/findings.json`, where the row's stable `key` and its full record live. Use that `key` in every verdict.

Do **not** edit either deliverable. Write `{{run_dir}}/data/qa/review-{{packet}}.md` as a table:

| # | Where | Issue | Proposed fix |
|---|---|---|---|

"Proposed fix" names the data that should change, and each kind needs these fields:
- **reject:** `key` + reason.
- **revise:** `key` + `replace` + reason.
- **retag:** `key` + the target decision (a D-id that is still open, or null to move the row to Ready) + `recommended` (change or keep) when it is a D-id + reason.
- **new finding** the analysis missed: file, line, find, replace, terms, type (Missed use / Misuse / Form), confidence (High / Medium), issue.
- **themes.yaml** wording change, or a **config.summary** note.

Rows you checked and found correct go in a final "Checked, no issue" list with their ids. Reply with the count of issues by kind.
