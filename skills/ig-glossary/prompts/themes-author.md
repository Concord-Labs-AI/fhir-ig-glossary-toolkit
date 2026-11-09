# Glossary alignment — write the themes

The findings for **{{ig_name}}** ({{tag}}) are merged in `{{run_dir}}/data/findings.json` (rows with `theme_id`, `terms`, `type`, `status`, `decision`, `find`, `replace`, `issue`). Write `{{run_dir}}/themes.yaml`, which groups findings for the summary report. Use the example in this toolkit's `examples/` directory as the model for shape and tone.

```yaml
themes:
- id: TH-SHORT
  title: Plain-language title
  terms: [T-A, T-B]                # rulebook term ids; a finding goes to the first theme listing its first term
  glossary_says: What the glossary says about these terms, two or three sentences, no jargon.
  alignment_work: What the alignment work is, which pages carry most of it, what is ready now versus waiting on a decision, and anything a reviewer should know before accepting rows in bulk.
  work_package: WP-1 Short name
  size: S | M | L                  # S: under 25 edits in up to 3 files; M: up to ~100 edits or 10 files; L: larger
  depends_on: [D-1]
```

Every non-Form term with findings must belong to exactly one theme; Form findings go to a built-in theme. Read the actual rows for each theme before writing `alignment_work` — state the Ready/Pending split with numbers, and say when many rows are the same edit. Write for a reader who has never opened the rulebook.

Run `python3 {{scripts}}/check_themes.py --run {{run_dir}}` until it prints `themes: OK`. Reply with the theme list and sizes.
