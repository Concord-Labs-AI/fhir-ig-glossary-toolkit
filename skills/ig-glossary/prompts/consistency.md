# Glossary alignment — consistency pass

Skeptic agents have ruled on the findings for **{{ig_name}}** ({{tag}}) in separate packets. Where two packets reached different verdicts on the *same kind of text*, the stricter, reasoned verdict should apply to every row of that kind. Work from `{{run_dir}}`.

1. Read every verdict file `{{run_dir}}/data/verify/V*.json` and every validated record file `{{run_dir}}/data/agent/validated/B*.json`.
2. Group rejects and revisions by the reason given. For each reasoned reject or revise, find the records elsewhere that the same reasoning covers but that were confirmed or never sent to a skeptic (only Misuse and Medium rows were). Read each candidate's source line at `{{snapshot}}/<file>` before ruling on it.
3. Write `{{run_dir}}/data/verify/{{packet}}.json` with one entry per row you are overriding, in the skeptic format (`key`, `verdict`, `reason`, and `replace` for revise). Start each reason with the packet you are aligning with, e.g. "Consistent with V02: …". Rule only where you are sure; leave the rest alone.
4. Write `{{run_dir}}/data/verify/{{packet}}.md`: a one-paragraph note of what you aligned and why.
5. Run `python3 {{scripts}}/verify.py --run {{run_dir}} --check {{packet}} --partial` until it prints `{{packet}}: OK`.

Domain notes: {{domain_notes}}

Reply with the number of rows overridden per reason.
