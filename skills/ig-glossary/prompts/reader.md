# Glossary alignment — reading brief

You are reviewing part of **{{ig_name}}**, tag {{tag}}, against its glossary. The glossary is the yardstick. Find every place a glossary term is used against its definition, and every place a glossary term should be used but isn't. Each finding becomes a row a reviewer accepts or edits, and accepted rows are applied **automatically**. So every finding must be an exact, drop-in text edit.

Work from `{{run_dir}}`.

## Inputs
- **Your packet:** `{{run_dir}}/data/batches/{{packet}}.md`. It lists the files you own and the candidate hits you must give a disposition.
- **The rulebook:** `{{run_dir}}/rulebook.yaml`. It has each glossary term's definition (`terms[].definition`), the rules, and the decisions register (each D-n has a recommended option).
- **The source:** `{{snapshot}}/<path>`. Read every file in your packet **in full** with the Read tool, which shows line numbers. Never edit these files.
  - Files over ~2,000 lines: read them in consecutive chunks with `offset`/`limit` until you reach the end. Their documentation strings often repeat; judge each distinct string once, then give every occurrence its own finding.
  - `input/resources/*.xml`: only `description`, `title` and `documentation` attributes are reader-visible. Find them with Grep and read the lines around them; the rest is code.

## Domain notes (from the rulebook author)
{{domain_notes}}

## What to produce
1. **A disposition for every hit in the packet.** Either a finding covers it (list its id in that finding's `hits`), or it is dismissed with a one-line reason. Typical dismissal reasons: false positive, external proper name, FHIR element/resource name, deliberate correct use.
2. **Findings the patterns can't catch.** Paraphrases that should use a glossary term, and uses against a definition. Use `"hits": []` and `"rule": null`.
3. **Optional `glossary_feedback`:** places where the guide's usage exposes a problem in the glossary itself.

## Finding types
- **Missed use:** another word or phrase is used where a glossary term should be.
- **Misuse:** a glossary term is used with a meaning that conflicts with its definition.
- **Form:** the right term in the wrong form. Examples: Title Case mid-sentence; wrong hyphenation.

**Not yours:**
- Spelling out an acronym at first use (a script does this).
- Linking terms to the glossary.
- Typos or grammar unrelated to glossary terms.
- Title Case in headings, page titles, figure captions, and table header cells (house style).

## Pending decisions
Some hits show a Decision (D-n) in the packet. Read that D-n entry in the rulebook. Then, unless the hit is a plain false positive:
- Write the finding with the **strict-glossary** replacement (the option that applies the glossary as written) and set `"decision": "D-n"`.
- Set `"recommended": "change"` if the edit is still needed under the decision's **recommended** option. Set `"keep"` if that option would leave this text as it is.

If a D-n entry has a `team_decision`, apply that option directly and leave `decision` unset.

## Writing the edit
- **`line`:** the source line number as the Read tool shows it. Transcribed figures (`input/images/*.png|jpg`) have no lines: use `"line": null` and copy `find` from the label text shown in the packet.
- **`find`:** copy **exactly** from the raw source line: same characters, case, punctuation, and markdown (`**`, backticks).
  - As short as possible while still a correct drop-in. Include a neighboring word when the replacement changes it ("a CBO" → "a social service organization").
  - It must start and end on visible text. Never start or end inside a link URL `](...)`, a tag `<...>`, or a Liquid tag `{% %}`.
  - If the same text appears more than once on the line, add `"nth_in_line": N` (1-based).
- **`replace`:** the exact text that replaces the whole `find`. Keep the sentence grammatical (articles, plurals, a capital at sentence start). No newlines. In `.fsh` files you are inside a quoted string, so write a double quote as `\"`. In markdown table rows, don't add or remove `|`.
- **One finding per span.** If one span has several problems, write one finding that lists all its `terms` and describes each problem in `issue`.
- **Never edit locked text** (it isn't in your packet anyway): artifact names and ids; code displays from other terminologies; external proper names (instrument names, profile names from other guides, titles of cited documents); FHIR element and resource names; code values.
- **Normative statements (SHALL/SHOULD/MAY):** changing the actor changes who must comply. Only do it when the glossary makes the intended actor unambiguous, mark it Medium confidence, and say so in `issue`.
- **`issue`:** one plain sentence a reviewer understands without the glossary open.
- **`confidence`:** High means clear-cut by the glossary text. Medium means it needs judgment.

## Output — write `{{run_dir}}/data/agent/{{packet}}.json`

```json
{
  "batch": "{{packet}}",
  "findings": [
    {"file": "input/pagecontent/example.md", "line": 42, "find": "old wording",
     "replace": "glossary term", "terms": ["T-XX"], "type": "Missed use", "rule": "R-XX-OLD",
     "issue": "Glossary names this 'glossary term'; 'old wording' is the retired name.",
     "confidence": "High", "hits": ["H-1a2b3c4d"]},
    {"file": "input/pagecontent/example.md", "line": 57, "find": "a CBO",
     "replace": "a social service organization", "terms": ["T-SSO"], "type": "Missed use", "rule": "R-SSO-CBO",
     "decision": "D-1", "recommended": "change",
     "issue": "Generic use; the glossary's inclusive term is social service organization.",
     "confidence": "High", "hits": ["H-5e6f7a8b"]}
  ],
  "dismissed": [{"hit": "H-0badc0de", "reason": "Names an external instrument (proper name)."}],
  "glossary_feedback": [{"term": "T-XX", "observation": "…", "evidence": ["input/pagecontent/example.md:12"]}]
}
```

## Validate until clean
Run `python3 {{scripts}}/findings.py --run {{run_dir}} --batch {{packet}}`. Fix every problem it lists and re-run until it prints `{{packet}}: OK`. Then reply with a short summary: findings by type, dismissed count, and any glossary feedback, one line each.
