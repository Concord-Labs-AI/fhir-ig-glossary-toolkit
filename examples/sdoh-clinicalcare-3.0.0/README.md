# Example: HL7 SDOH Clinical Care IG, tag 3.0.0

The reference run this toolkit was built from: 31 glossary terms, 844 findings, 13 decisions.

- `config.yaml` — the run's configuration, including the twelve hand-tuned packet overrides used in the reference run (an unconfigured run would partition automatically).
- `rulebook.yaml` — the authored term rules and decisions register. The `rulebook-author` prompt points at this file as its exemplar.
- `themes.yaml` — the authored theme narratives for the summary.
- `figure_transcripts.yaml` — text read off raster figures by eye.
- `*-findings.xlsx`, `*-summary.html` — the two outputs, built by this toolkit from the reference run's merged findings (added by the reproduction check).

To reproduce: check out `github.com/HL7/fhir-sdoh-clinicalcare` at tag `3.0.0` next to this directory, copy these four YAML files into an empty run directory, adjust `ig.snapshot`, and run `/ig-glossary-toolkit:ig-glossary`.
