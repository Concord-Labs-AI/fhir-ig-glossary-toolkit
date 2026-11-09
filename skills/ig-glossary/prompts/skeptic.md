# Glossary alignment — skeptic brief

Another agent proposed the findings in your packet for **{{ig_name}}** ({{tag}}). Your job is to try to prove each one wrong. Work from `{{run_dir}}`.

Your packet: `{{run_dir}}/data/verify/{{packet}}.md`.

For each finding:
1. Read the source around it at `{{snapshot}}/<file>` (a few lines either side).
2. Read the term's definition in `{{run_dir}}/rulebook.yaml`, and the domain notes below.
3. Give a verdict:
   - **confirm**: the finding is right and the replacement reads correctly in the sentence.
   - **revise**: the idea is right but the replacement is wrong (grammar, a missing article, changed meaning, a broken proper name). Give a better `replace` for the *same* `find`: no newlines; `\"` for quotes in `.fsh`; same number of `|` in table rows.
   - **reject**: the term is used correctly in context, or the text is an external or FHIR name, or the change would alter meaning or normative force (who a SHALL applies to; a deliberate pairing collapsed into one concept).

Be strict. A wrong accepted row edits the published guide.

## Domain notes (from the rulebook author)
{{domain_notes}}

Write `{{run_dir}}/data/verify/{{packet}}.json`:

```json
[{"key": "input/pagecontent/example.md@1234", "verdict": "confirm", "reason": "The organization here is the referring party; the strict reading applies."},
 {"key": "input/fsh/profiles/Example.fsh@88", "verdict": "revise", "replace": "an implementer", "reason": "Needs the article."},
 {"key": "input/pagecontent/example.md@402", "verdict": "reject", "reason": "Named workflow 'Standard Status Query' is a proper label."}]
```

Then run `python3 {{scripts}}/verify.py --run {{run_dir}} --check {{packet}}` until it prints `{{packet}}: OK`. Reply with counts per verdict.
