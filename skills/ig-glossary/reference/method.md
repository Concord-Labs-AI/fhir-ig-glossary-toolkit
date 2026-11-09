# The method, on one page

**What a finding is.** One place in the guide where the wording departs from the glossary, expressed as an exact edit: a `find` string that occurs at a known offset in a known source file, and the `replace` text. Nothing vaguer is allowed, because accepted rows are applied by script.

**Why extraction comes first.** Every source file is "masked": everything a reader never sees (comments, Liquid, link URLs, FSH code, diagram directives) is overwritten with spaces, keeping newlines, so the visible text keeps the raw file's offsets. Visible runs become *segments* with a change class: Prose, Artifact text, Diagram (editable) or Identifier, External, Historical (locked). Locked text is counted but never edited.

**Rules then judgement.** The rulebook's regexes favour recall: they flag candidates, and a reading agent that has read the whole file judges each one in context, dismisses false positives with a reason, and adds the paraphrases no pattern catches. Every candidate gets a disposition, so nothing is silently dropped.

**Adversarial verification.** Misuse and Medium-confidence findings go to skeptic agents whose brief is to disprove them. A consistency pass then applies each reasoned rejection to every row of the same kind. Verdicts are applied by stable key (`file@offset`) in file order, so later passes build on earlier ones and nothing is edited in place.

**Decisions, not errors.** Where the glossary and the guide's usage pull apart, the rulebook holds a decision with options and a recommendation. Findings that depend on it are written with the strict-glossary edit, tagged Pending D-n, and marked whether the recommended option would still make the edit. The team decides once; the rows regenerate.

**Occurrence-addressed apply.** A row is applied as "the Nth occurrence of `find` in this file". If the count has changed since the snapshot, the row is reported as drifted and left alone. Nothing is guessed.

**Round trip.** The workbook's analysis columns are locked by convention and hashed; when it comes back, every locked cell is compared with the master data, so a reviewer's edits in the wrong column are caught before anything is applied.

**Fixes go into the data.** Quality review finds problems in the outputs; the fixes are verdicts, new finding packets, theme text or config — never hand edits to the workbook or report, which are regenerated.
