import roundtrip as gr
import sheet as gs


def saved(tmp_path, doc, book, counts, edit=None):
    wb = gs.build(doc, book, counts)
    if edit:
        edit(wb["Findings"])
    path = tmp_path / "w.xlsx"
    wb.save(path)
    return path


def test_untouched_workbook_round_trips_clean(tmp_path, sample_doc, sample_book, sample_counts):
    meta, rows = gr.read_workbook(saved(tmp_path, sample_doc, sample_book, sample_counts))
    assert gr.check(sample_doc, meta, rows) == []


def test_reviewer_edits_pass_but_locked_edits_and_bad_values_are_flagged(tmp_path, sample_doc, sample_book, sample_counts):
    def edit(ws):
        ws["V2"] = "Accept"
        ws["V3"] = "Modify"
        ws["W3"] = "my text"
        ws["O4"] = "changed suggestion"   # locked column
        ws["V5"] = "Maybe"                # not a decision
    meta, rows = gr.read_workbook(saved(tmp_path, sample_doc, sample_book, sample_counts, edit))
    problems = gr.check(sample_doc, meta, rows)
    assert any("GA-0003" in p and "Suggested replace" in p for p in problems)
    assert any("GA-0004" in p and "Maybe" in p for p in problems)
    assert not any("GA-0001" in p or "GA-0002" in p for p in problems)


def test_deleted_rows_modify_without_text_and_wrong_build_are_flagged(tmp_path, sample_doc, sample_book, sample_counts):
    def edit(ws):
        ws["V2"] = "Modify"
        ws.delete_rows(3)
    meta, rows = gr.read_workbook(saved(tmp_path, sample_doc, sample_book, sample_counts, edit))
    problems = gr.check({**sample_doc, "meta": {**sample_doc["meta"], "sha256": "other"}}, meta, rows)
    assert any("GA-0001: Modify without" in p for p in problems)
    assert any("GA-0002: row missing" in p for p in problems)
    assert any("different findings.json" in p for p in problems)
