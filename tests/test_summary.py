import pytest

import summary as gsu

THEMES = [{"id": "TH-ACTORS", "title": "Referral actors and roles", "terms": ["T-RT"],
           "glossary_says": "Roles <defined>.", "alignment_work": "Rename the role.",
           "work_package": "WP-1 Actors", "size": "M", "depends_on": []}]
COVERAGE = {"files_extracted": 215, "files_excluded": 127, "segments": 4918}


def test_summary_sections_numbers_and_pending_not_counted_as_ready(sample_doc, sample_book, sample_counts):
    out = gsu.build_html(sample_doc, sample_book, THEMES, sample_counts, COVERAGE)
    for heading in ("Headline numbers", "Decisions needed first", "Referral actors and roles",
                    "Work packages", "Names kept as they are", "Method and limits"):
        assert heading in out
    ready = sum(r["status"] == "Ready" for r in sample_doc["rows"])
    assert f"<td>Ready to review now</td><td>{ready}</td>" in out


def test_summary_escapes_source_text(sample_doc, sample_book, sample_counts):
    doc = {**sample_doc, "rows": [{**sample_doc["rows"][0], "find": "<div>x</div>"}] + sample_doc["rows"][1:]}
    out = gsu.build_html(doc, sample_book, THEMES, sample_counts, COVERAGE)
    assert "<div>x</div>" not in out and "&lt;div&gt;x&lt;/div&gt;" in out
    assert "Roles &lt;defined&gt;." in out


def test_size_follows_the_rule_when_a_theme_leaves_it_blank():
    rows = lambda n, files: [{"file": f"f{i % files}"} for i in range(n)]
    assert [gsu.size_for(rows(10, 2)), gsu.size_for(rows(10, 5)), gsu.size_for(rows(60, 3)),
            gsu.size_for(rows(140, 40))] == ["S", "M", "M", "L"]


def test_decision_table_spells_out_the_recommended_option_and_its_reason(sample_doc, sample_book, sample_counts):
    book = {**sample_book, "decisions": [{**sample_book["decisions"][0], "options": ["A: Rename <all>", "B: Keep"],
                                          "recommendation": "A — it completes the pivot."}]}
    out = gsu.build_html(sample_doc, book, THEMES, sample_counts, COVERAGE)
    assert "<p><b>A: Rename &lt;all&gt;</b></p><p>B: Keep</p><p><i>Recommended: A — it completes the pivot.</i></p>" in out


def test_recommendation_naming_no_option_fails_loudly(sample_doc, sample_book, sample_counts):
    book = {**sample_book, "decisions": [{**sample_book["decisions"][0], "recommendation": "D — typo"}]}
    with pytest.raises(ValueError, match="D-6"):
        gsu.build_html(sample_doc, book, THEMES, sample_counts, COVERAGE)


def test_table_can_fix_column_widths_for_the_doc_conversion():
    out = gsu.table(["A", "B"], [(1, 2)], widths=["10%", "90%"])
    assert "<th style='width:10%'>A</th><th style='width:90%'>B</th>" in out
    assert gsu.table(["A"], [(1,)]) == "<table border='1' cellpadding='4'><tr><th>A</th></tr><tr><td>1</td></tr></table>"


def test_report_has_a_legend_an_ask_and_one_row_per_work_package(sample_doc, sample_book, sample_counts):
    themes = THEMES + [{**THEMES[0], "id": "TH-X", "title": "Other theme", "work_package": "WP-1 Actors"}]
    doc = {**sample_doc, "rows": sample_doc["rows"] + [{**sample_doc["rows"][0], "id": "GA-9999", "theme_id": "TH-X", "theme": "Other theme", "key": "kx"}]}
    out = gsu.build_html(doc, sample_book, themes, sample_counts, COVERAGE)
    for heading in ("How to read this report", "What we need from you", "Work packages", "Outside the workbook"):
        assert heading in out
    assert out.count("<td>WP-1 Actors</td>") == 1  # one row per package, themes joined
    assert "Q6" in out  # the decision's question is shown, not only the recommendation
