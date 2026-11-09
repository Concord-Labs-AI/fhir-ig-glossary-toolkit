import pytest

import summary as gsu

THEMES = [{"id": "TH-ACTORS", "title": "Referral actors and roles", "terms": ["T-RT"],
           "glossary_says": "Roles <defined>.", "alignment_work": "Rename the role.",
           "work_package": "WP-1 Actors", "size": "M", "depends_on": []}]
COVERAGE = {"files_extracted": 215, "files_excluded": 127, "segments": 4918}


def test_summary_sections_numbers_and_pending_not_counted_as_ready(sample_doc, sample_book, sample_counts, cfg):
    out = gsu.build_html(sample_doc, sample_book, THEMES, sample_counts, COVERAGE, cfg)
    for heading in ("Headline numbers", "Decisions needed first", "Referral actors and roles",
                    "Work packages", "Names kept as they are", "Method and limits"):
        assert heading in out
    ready = sum(r["status"] == "Ready" for r in sample_doc["rows"])
    assert f"<td>Ready to review now</td><td>{ready}</td>" in out


def test_summary_escapes_source_text(sample_doc, sample_book, sample_counts, cfg):
    doc = {**sample_doc, "rows": [{**sample_doc["rows"][0], "find": "<div>x</div>"}] + sample_doc["rows"][1:]}
    out = gsu.build_html(doc, sample_book, THEMES, sample_counts, COVERAGE, cfg)
    assert "<div>x</div>" not in out and "&lt;div&gt;x&lt;/div&gt;" in out
    assert "Roles &lt;defined&gt;." in out


def test_size_follows_the_rule_when_a_theme_leaves_it_blank():
    rows = lambda n, files: [{"file": f"f{i % files}"} for i in range(n)]
    assert [gsu.size_for(rows(10, 2)), gsu.size_for(rows(10, 5)), gsu.size_for(rows(60, 3)),
            gsu.size_for(rows(140, 40))] == ["S", "M", "M", "L"]


def test_decision_table_spells_out_the_recommended_option_and_its_reason(sample_doc, sample_book, sample_counts, cfg):
    book = {**sample_book, "decisions": [{**sample_book["decisions"][0], "options": ["A: Rename <all>", "B: Keep"],
                                          "recommendation": "A — it completes the pivot."}]}
    out = gsu.build_html(sample_doc, book, THEMES, sample_counts, COVERAGE, cfg)
    assert "<p><b>A: Rename &lt;all&gt;</b></p><p>B: Keep</p><p><i>Recommended: A — it completes the pivot.</i></p>" in out


def test_recommendation_naming_no_option_fails_loudly(sample_doc, sample_book, sample_counts, cfg):
    book = {**sample_book, "decisions": [{**sample_book["decisions"][0], "recommendation": "D — typo"}]}
    with pytest.raises(ValueError, match="D-6"):
        gsu.build_html(sample_doc, book, THEMES, sample_counts, COVERAGE, cfg)


def test_table_can_fix_column_widths_for_the_doc_conversion():
    out = gsu.table(["A", "B"], [(1, 2)], widths=["10%", "90%"])
    assert "<th style='width:10%'>A</th><th style='width:90%'>B</th>" in out
    assert gsu.table(["A"], [(1,)]) == "<table border='1' cellpadding='4'><tr><th>A</th></tr><tr><td>1</td></tr></table>"


def test_report_has_a_legend_an_ask_and_one_row_per_work_package(sample_doc, sample_book, sample_counts, cfg):
    themes = THEMES + [{**THEMES[0], "id": "TH-X", "title": "Other theme", "work_package": "WP-1 Actors"}]
    doc = {**sample_doc, "rows": sample_doc["rows"] + [{**sample_doc["rows"][0], "id": "GA-9999", "theme_id": "TH-X", "theme": "Other theme", "key": "kx"}]}
    out = gsu.build_html(doc, sample_book, themes, sample_counts, COVERAGE, cfg)
    for heading in ("How to read this report", "What we need from you", "Work packages"):
        assert heading in out
    assert out.count("<td>WP-1 Actors</td>") == 1  # one row per package, themes joined
    assert "Q6" in out  # the decision's question is shown, not only the recommendation


def test_summary_is_free_of_the_reference_run_and_carries_the_attribution(sample_doc, sample_book, sample_counts, cfg):
    from common import ATTRIBUTION
    out = gsu.build_html(sample_doc, sample_book, THEMES, sample_counts, COVERAGE, cfg)
    assert "<title>Glossary alignment: Example IG 1.0.0</title>" in out
    assert ATTRIBUTION in out
    for leak in ("Gravity", "STU 3", "D-1 to D-13", "thirteen", "LOINC", "Screening Response"):
        assert leak not in out, leak        # (the sample rows themselves name an SDOHCC artifact, which is data, not a leak)
    assert "2 decisions" in out                       # computed from the rulebook
    assert "Outside the workbook" not in out            # blank list → section omitted


def test_optional_summary_prose_appears_when_configured(sample_doc, sample_book, sample_counts, cfg):
    cfg["summary"].update(intro="Custom intro.", outside_workbook=[{"where": "index.md", "what": "Hand edit."}],
                          names_kept_note="One profile keeps its name.", build_note="The copy built clean.",
                          locked_examples="LOINC displays")
    out = gsu.build_html(sample_doc, sample_book, THEMES, sample_counts, COVERAGE, cfg)
    for s in ("Custom intro.", "Outside the workbook", "<b>index.md.</b> Hand edit.", "One profile keeps its name.",
              "The copy built clean.", "LOINC displays"):
        assert s in out


def test_identifier_paragraph_cites_the_rulebook_decision_or_none(sample_doc, sample_book, sample_counts, cfg):
    out = gsu.build_html(sample_doc, sample_book, THEMES, sample_counts, COVERAGE, cfg)
    assert "because renaming breaks implementers:" in out
    book = {**sample_book, "identifier_decision": "D-10"}
    out = gsu.build_html(sample_doc, book, THEMES, sample_counts, COVERAGE, cfg)
    assert "because renaming breaks implementers (decision D-10):" in out


def test_form_theme_lists_legend_examples_only_when_configured(sample_doc, sample_book, sample_counts, cfg):
    cfg["summary"]["legend_examples"] = ["Foo-bar"]
    assert "Foo-bar" in gsu.build_html(sample_doc, sample_book, THEMES, sample_counts, COVERAGE, cfg)
    cfg["summary"]["legend_examples"] = []
    assert "(for example" not in gsu.build_html(sample_doc, sample_book, THEMES, sample_counts, COVERAGE, cfg)


def test_configured_intro_is_escaped(sample_doc, sample_book, sample_counts, cfg):
    cfg["summary"]["intro"] = "<b>x</b>"
    out = gsu.build_html(sample_doc, sample_book, THEMES, sample_counts, COVERAGE, cfg)
    assert "&lt;b&gt;x&lt;/b&gt;" in out and "<b>x</b>" not in out


def test_no_decisions_means_no_decisions_section(sample_doc, sample_book, sample_counts, cfg):
    out = gsu.build_html(sample_doc, {**sample_book, "decisions": []}, THEMES, sample_counts, COVERAGE, cfg)
    assert "Decisions needed first" not in out and "0 decision" not in out
    assert "Review the Ready rows" in out
    assert "[Owners and dates: who reviews which themes, and by when.]" in out


def test_one_decision_reads_in_the_singular(sample_doc, sample_book, sample_counts, cfg):
    book = {**sample_book, "decisions": sample_book["decisions"][:1]}  # the D-10 row's decision is no longer in the book
    out = gsu.build_html(sample_doc, book, THEMES, sample_counts, COVERAGE, cfg)
    assert "1 decision" in out and "1 decisions" not in out
