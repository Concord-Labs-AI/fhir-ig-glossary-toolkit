# Glossary alignment — deliverable review

You are a first-time reader of two deliverables for **{{ig_name}}** ({{tag}}): the summary report `{{summary}}` and the findings workbook `{{workbook}}` (read it with Python and openpyxl: `load_workbook(path, data_only=True)`; tabs README, Findings, Decisions). The source is at `{{snapshot}}`; the rulebook and themes are in `{{run_dir}}`.

Review as the team that has to act on these will: can they understand each theme without the glossary open? Is every number consistent between the report and the workbook? Do the examples make the case? Spot-check **twenty Findings rows** chosen across themes and confidence levels: open the source line, confirm `Source find` is there exactly once at the stated occurrence, and judge whether the `Suggested replace` reads correctly and whether the row's Status/decision tag is right.

Do **not** edit either deliverable. Write `{{run_dir}}/data/qa/review-{{packet}}.md` as a table:

| # | Where | Issue | Proposed fix |
|---|---|---|---|

"Proposed fix" names the data that should change: a **verdict** (`reject` / `revise` / `retag` with the row's `key` and a reason), a **new finding** the analysis missed (file, line, find, replace, terms, issue), a **themes.yaml** wording change, or a **config.summary** note. Rows you checked and found correct go in a final "Checked, no issue" list with their ids. Reply with the count of issues by kind.
