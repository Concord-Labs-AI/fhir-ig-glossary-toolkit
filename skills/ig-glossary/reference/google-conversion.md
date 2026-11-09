# Appendix: review in Google Sheets / Docs

The toolkit produces an `.xlsx` and an `.html`. Teams that review in Google Workspace convert them; the round-trip checker makes sure the conversion did not alter the analysis columns.

## Upload and convert
1. Drive → New → File upload → the `.xlsx` from `_build/`. Open it → File → **Save as Google Sheets**. Trash the uploaded `.xlsx` copy (the run directory holds the canonical build).
2. Drive → New → File upload → the `.html` from `_build/`. Open with Google Docs (right-click → Open with → Google Docs). Tables, headings and widths survive; re-check the Decisions table widths.

## Check the conversion (three minutes)
- Findings tab: the Review column shows a dropdown with Accept / Modify / Reject / Defer.
- Set a row to Modify with "Reviewer's replace" empty → the cell turns red → undo.
- README tab: "Unreviewed rows" equals the row count; "Modify rows missing a replacement" is 0.
- Findings column "Source find (exact)": rows starting with `=`, `+` or `-` show as text, not `#ERROR!`.
- The `_meta` tab is hidden.

## Optional: warn on edits to locked columns (Extensions → Apps Script → paste → Run)
```javascript
function protectLockedColumns() {
  const sh = SpreadsheetApp.getActive().getSheetByName('Findings');
  sh.getRange(1, 1, sh.getMaxRows(), 21).protect()
    .setDescription('Analysis columns (A–U) — edit only Review, Reviewer\'s replace, Reviewer notes')
    .setWarningOnly(true);
}
```

## Verify the round trip
File → Download → Microsoft Excel (.xlsx), then from the run directory:
```bash
python3 $SCRIPTS/roundtrip.py <downloaded>.xlsx
```
Expected: `OK: every locked column matches findings.json`. Run the same command on the workbook the reviewers hand back; it also validates their Review values and flags Modify rows without replacement text.
