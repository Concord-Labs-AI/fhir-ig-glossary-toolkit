from openpyxl import load_workbook

import sheet as gs


def test_workbook_tabs_headers_and_meta(sample_doc, sample_book, sample_counts):
    wb = gs.build(sample_doc, sample_book, sample_counts)
    assert wb.sheetnames == ["README", "Findings", "Decisions", "Decision x theme", "Term coverage",
                             "Page x theme", "Reviewer additions", "_meta"]
    ws = wb["Findings"]
    headers = [c.value for c in ws[1]]
    assert headers[:3] == ["ID", "Theme", "Terms"]
    assert headers[-3:] == ["Review", "Reviewer's replace", "Reviewer notes"]
    assert headers[-5:-3] == ["Depends on", "Under recommended option"]
    assert ws.max_row == len(sample_doc["rows"]) + 1
    assert wb["_meta"].sheet_state == "hidden"
    meta = {r[0].value: r[1].value for r in wb["_meta"].iter_rows()}
    assert meta["findings_sha256"] == sample_doc["meta"]["sha256"]


def test_formula_looking_text_stays_text_after_save(tmp_path, sample_doc, sample_book, sample_counts):
    path = tmp_path / "w.xlsx"
    gs.build(sample_doc, sample_book, sample_counts).save(path)
    ws = load_workbook(path)["Findings"]
    finds = [ws.cell(row=r, column=14).value for r in range(2, ws.max_row + 1)]
    assert "= formula-looking text" in finds
    assert all(ws.cell(row=r, column=14).data_type == "s" for r in range(2, ws.max_row + 1))


def test_decision_dropdown_and_missing_text_highlight(sample_doc, sample_book, sample_counts):
    ws = gs.build(sample_doc, sample_book, sample_counts)["Findings"]
    assert any(dv.formula1 == '"Accept,Modify,Reject,Defer"' and "V2" in str(dv.sqref)
               for dv in ws.data_validations.dataValidation)
    assert any('$V2="Modify"' in rule.formula[0] for cf in ws.conditional_formatting for rule in cf.rules)


def test_readme_counts_undecided_rows(sample_doc, sample_book, sample_counts):
    ws = gs.build(sample_doc, sample_book, sample_counts)["README"]
    values = [c.value for row in ws.iter_rows() for c in row if isinstance(c.value, str)]
    assert any(v.startswith("=COUNTBLANK(Findings!V2:V") for v in values)


def test_pending_rows_show_their_decision_and_what_the_recommendation_does(sample_doc, sample_book, sample_counts):
    wb = gs.build(sample_doc, sample_book, sample_counts)
    ws = wb["Findings"]
    headers = [c.value for c in ws[1]]
    dep, rec = headers.index("Depends on") + 1, headers.index("Under recommended option") + 1
    by_id = {ws.cell(row=r, column=1).value: (ws.cell(row=r, column=dep).value, ws.cell(row=r, column=rec).value)
             for r in range(2, ws.max_row + 1)}
    pending = {r["id"]: r for r in sample_doc["rows"] if r["decision"]}
    ready = [r["id"] for r in sample_doc["rows"] if not r["decision"]]
    assert all(by_id[i] == ("", "") for i in ready)
    for i, r in pending.items():
        assert by_id[i] == (r["decision"], {"change": "still changes", "keep": "left as written"}[r["recommended"]])
    dec = wb["Decisions"]
    assert [c.value for c in dec[1]][:7] == ["ID", "Decision", "Question", "Options", "Recommendation", "Rows",
                                             "Still change under the recommendation"]
    assert wb.sheetnames[3] == "Decision x theme"


def test_unknown_recommended_value_is_an_error():
    import pytest
    with pytest.raises(ValueError, match="k1"):
        gs.locked_value({"id": "k1", "recommended": "maybe", "decision": "D-1"}, "recommended")
