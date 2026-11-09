# Glossary alignment — write the rulebook

You are writing `{{run_dir}}/rulebook.yaml` for **{{ig_name}}** ({{tag}}). Read the glossary page `{{snapshot}}/{{glossary_page}}` in full, then skim the guide's main narrative pages under `{{snapshot}}/input/pagecontent/` to see how the terms are actually used. Use the example rulebooks in `{{examples}}/` (one directory per worked example) as the model for shape and tone; copy its structure, not its content.

For **every glossary term**, write an entry:

```yaml
- id: T-SHORT                      # stable id, used by findings and themes
  glossary_term: Exact headword as the glossary writes it
  definition: The glossary's definition, verbatim or lightly trimmed
  decision: D-n                    # only if every rule for the term waits on a decision
  rules:
  - id: R-SHORT-CANON
    type: canonical                # correct use; counted, never flagged
    pattern: \bexact\s+term\b
  - id: R-SHORT-OLD
    type: missed-use               # a variant that should become the term
    pattern: \bold\s+wording\b
    suggest: exact term
    note: One line a reviewer understands.
  - id: R-SHORT-CASE
    type: form                     # right term, wrong form (case, hyphenation)
    case_sensitive: true
    pattern: (?<=[a-z,;)]\s)Exact Term\b
    suggest: exact term
    skip_fields: [heading, page title, menu label, Title, caption, entity name, Id, concept display, diagram line, svg text, transcribed text, artifact group name, IG title]
```

Rule types: `canonical`, `missed-use`, `misuse-signal` (a pattern that often marks a use against the definition), `form`. Favor **recall**: patterns flag candidates; agents judge each in context. Every pattern must compile as a Python regex.

**Decisions register.** Wherever the glossary and the guide's actual usage pull apart (two words for one concept, a term the guide uses in a sense the definition excludes, a defined name the guide never uses), write a decision instead of guessing:

```yaml
decisions:
- id: D-1
  title: Short name
  question: What the team must choose, with the counts you observed.
  options: ['A: …', 'B: …', 'C: …']
  recommendation: A — one sentence of reasoning.
```

Rules whose outcome depends on a decision carry `decision: D-n`. If some artifact names or ids embed retired wording, add a decision about renaming them and set the top-level `identifier_decision: D-n`.

**Domain notes.** Add a top-level `domain_notes:` block (plain text, a few paragraphs) with the judgement rules a reader agent needs that the glossary alone doesn't give: which FHIR element names must be left alone, which actors may perform "system" actions, which ambiguous words usually name a FHIR role rather than a glossary concept.

Set `version: draft-1 (<today>)`. Then run `python3 {{scripts}}/check_rulebook.py --run {{run_dir}}` and fix every problem until it prints `rulebook: OK`. Ignore any `acronyms.table` lines; the orchestrator fixes config.yaml. Reply with the counts: terms, rules by type, decisions, and anything you could not resolve.
