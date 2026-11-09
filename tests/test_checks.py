import copy

import check_rulebook as cr
import check_themes as ct
import config


def test_fixture_rulebook_and_themes_are_clean(cfg):
    book, themes = config.rulebook(cfg), config.themes(cfg)
    assert cr.problems(book, glossary_terms=["Referral target", "Social service organization",
                                             "Social determinants of health"]) == []
    assert ct.problems(themes, book) == []


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
    assert any("T-SDOH" in p and "no theme" in p for p in probs) is False   # SDOH has only a canonical rule
