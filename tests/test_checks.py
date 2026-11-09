import copy

import check_rulebook as cr
import check_themes as ct
import config
import pytest


def test_fixture_rulebook_and_themes_are_clean(cfg):
    book, themes = config.rulebook(cfg), config.themes(cfg)
    assert cr.problems(book, glossary_terms=["Referral target", "Social service organization",
                                             "Social determinants of health"]) == []
    assert ct.problems(themes, book) == []


def test_acronym_term_ids_must_be_rulebook_term_ids(cfg):
    book = config.rulebook(cfg)
    assert cr.problems(book, acronyms=cfg["acronyms"]) == []
    acr = copy.deepcopy(cfg["acronyms"])
    name = next(iter(acr["table"]))
    acr["table"][name]["term"] = "T-NOPE"
    assert cr.problems(book, acronyms=acr) == [f"acronyms.table.{name}.term T-NOPE is not a rulebook term id"]


def test_rulebook_problems_are_named(cfg):
    book = copy.deepcopy(config.rulebook(cfg))
    book["terms"][0]["rules"][0]["pattern"] = "("                     # bad regex
    del book["terms"][1]["definition"]
    book["terms"][2]["rules"] = []                                       # no canonical rule
    book["decisions"][0]["recommendation"] = "Z — names no option"
    book["identifier_decision"] = "D-9"
    probs = cr.problems(book, glossary_terms=["Referral target", "Missing term"])
    assert any("bad pattern" in p for p in probs)
    assert "T-SSO: definition required" in probs
    assert "T-SDOH: no canonical rule" in probs
    assert any("D-1" in p and "Z" in p for p in probs)
    assert "identifier_decision D-9 is not a decision" in probs
    assert "glossary term has no rulebook entry: Missing term" in probs


def test_glossary_terms_are_read_from_segments():
    segs = [{"kind": "glossary", "field": "table-row", "text": "| Term | Definition |"},
            {"kind": "glossary", "field": "table-row", "text": "| Referral target | An actor. |"},
            {"kind": "page", "field": "table-row", "text": "| Not | glossary |"}]
    assert cr.glossary_terms(segs) == ["Referral target"]


def test_theme_problems_are_named(cfg):
    book, themes = config.rulebook(cfg), copy.deepcopy(config.themes(cfg))
    themes[0]["terms"].append("T-NOPE")
    del themes[1]["alignment_work"]
    themes[1]["size"] = "XL"
    themes.append({**themes[0], "id": "TH-ACTORS"})
    probs = ct.problems(themes, book)
    assert "TH-ACTORS: unknown term T-NOPE" in probs
    assert "TH-ORGS: alignment_work required" in probs
    assert "TH-ORGS: size must be S, M or L" in probs
    assert "duplicate theme id TH-ACTORS" in probs
    assert not any("T-SDOH" in p and "no theme" in p for p in probs)   # SDOH has only a canonical rule


def _row(text):
    return {"kind": "glossary", "field": "table-row", "text": text}


def test_headwords_skip_any_header_and_repeats_and_strip_markup():
    segs = [_row("| Name | Meaning |"), _row("| **Referral target** | An actor. |"),
            _row("| Name | Meaning |"), _row("| [Referral target](#rt) | x |"),
            _row('| <a name="s"></a>`SDOH` | x |'), _row("| __Bold__ | x |")]
    assert cr.glossary_terms(segs) == ["Referral target", "Referral target", "SDOH", "Bold"]


def _main(capsys, run):
    cr.main(["--run", str(run)])
    return capsys.readouterr().out


def test_coverage_note_distinguishes_missing_segments_from_empty_glossary(run, capsys):
    assert "run extract.py first" in _main(capsys, run)
    (run / "data").mkdir(exist_ok=True)
    (run / "data" / "segments.jsonl").write_text('{"kind": "page", "field": "paragraph", "text": "x"}\n')
    assert "the glossary page has no table rows" in _main(capsys, run)


def test_missing_keys_are_named_not_a_keyerror(cfg):
    book = copy.deepcopy(config.rulebook(cfg))
    del book["terms"][0]["rules"][0]["pattern"]
    book["terms"].append({"glossary_term": "No id", "definition": "x", "rules": []})
    probs = cr.problems(book)
    assert "T-RT: rule R-RT-CANON needs pattern" in probs
    assert "term without id: No id" in probs
    assert not any("KeyError" in p or "'pattern'" in p for p in probs)


def test_recommendation_without_dash_gets_format_message(cfg):
    book = copy.deepcopy(config.rulebook(cfg))
    book["decisions"][0]["recommendation"] = "A. text"
    assert ('D-1: recommendation must start with an option letter and " — " (e.g. "A — reason")'
            in cr.problems(book))


def test_form_only_term_needs_no_theme_but_missed_use_does(cfg):
    book = copy.deepcopy(config.rulebook(cfg))
    book["terms"].append({"id": "T-F", "glossary_term": "F", "definition": "d", "rules": [
        {"id": "R-F1", "type": "canonical", "pattern": "f"}, {"id": "R-F2", "type": "form", "pattern": "g"}]})
    assert not any("T-F" in p for p in ct.problems(config.themes(cfg), book))
    book["terms"][-1]["rules"].append({"id": "R-F3", "type": "missed-use", "pattern": "h"})
    assert "T-F: term has flagging rules but no theme" in ct.problems(config.themes(cfg), book)


def test_term_in_two_themes_is_reported(cfg):
    book, themes = config.rulebook(cfg), copy.deepcopy(config.themes(cfg))
    themes[1]["terms"].append("T-RT")
    assert "T-RT listed in TH-ACTORS and TH-ORGS" in ct.problems(themes, book)


def test_term_without_id_does_not_crash_themes_check(cfg):
    book = copy.deepcopy(config.rulebook(cfg))
    book["terms"].append({"glossary_term": "No id", "rules": []})
    ct.problems(config.themes(cfg), book)


def test_themes_file_without_list_is_a_named_error(run, cfg):
    (run / "themes.yaml").write_text("version: 1\n")
    with pytest.raises(config.ConfigError, match="needs a top-level themes: list"):
        config.themes(cfg)


def test_concept_term_needs_label_not_definition_or_canonical(cfg):
    book = copy.deepcopy(config.rulebook(cfg))
    book["terms"].append({"id": "N-REF", "glossary_term": None, "label": "Referral (undefined core concept)",
                          "note": "Counted for D-1.",
                          "rules": [{"id": "R-REF-MISSED", "type": "missed-use", "pattern": r"\breferral\b"}]})
    assert cr.problems(book) == []


def test_term_with_neither_glossary_term_nor_label_is_reported(cfg):
    book = copy.deepcopy(config.rulebook(cfg))
    book["terms"].append({"id": "N-BARE", "glossary_term": None,
                          "rules": [{"id": "R-BARE", "type": "missed-use", "pattern": "x"}]})
    assert cr.problems(book) == ["N-BARE: glossary_term or label required"]
