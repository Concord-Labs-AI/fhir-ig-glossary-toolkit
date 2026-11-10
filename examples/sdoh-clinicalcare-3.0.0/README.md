# Example: HL7 SDOH Clinical Care IG, tag 3.0.0

The reference run this toolkit was built from, the [Gravity Project](https://thegravityproject.net)'s glossary alignment of this guide: 31 glossary terms, 844 findings, 13 decisions.

- `config.yaml` — the run's configuration, including the twelve hand-tuned packet overrides used in the reference run (an unconfigured run would partition automatically).
- `rulebook.yaml` — the authored term rules and decisions register. The `rulebook-author` prompt points at this file as its exemplar.
- `themes.yaml` — the authored theme narratives for the summary.
- `figure_transcripts.yaml` — text read off raster figures by eye.
- `*-findings.xlsx`, `*-summary.html` — the two outputs, built by this toolkit from the reference run's merged findings (added by the reproduction check).

To reproduce, copy these four YAML files into an empty folder, clone the guide into it, and start Claude Code there:

```bash
git clone --depth 1 --branch 3.0.0 https://github.com/HL7/fhir-sdoh-clinicalcare
claude
```

Then type `/fhir-ig-glossary-toolkit:ig-glossary fhir-sdoh-clinicalcare`. Because the rulebook and themes are already there, the run skips the agents that would write them.
