import pytest

import extract as gx
import findings as gf

PAGE = ("# Title\n\nThe referral recipient gets it. The referral recipient replies.\n"
        "See [glossary](glossary.html#referral-recipient) for more.\n"
        "| Term | Def |\n| --- | --- |\n| CBO | A thing |\n")
FSH = 'Profile: X\nParent: Goal\nDescription: "Sent to the referral recipient."\n'
BOOK = {"decisions": [{"id": "D-6"}, {"id": "D-1", "team_decision": "C"}],
        "terms": [{"id": "T-RT", "rules": [{"id": "R-RT-RECIP"}]}, {"id": "T-SSO", "rules": [{"id": "R-SSO-CBO"}]}]}
P, F = "input/pagecontent/p.md", "input/fsh/x.fsh"
ENTRY = {"files": [P, F], "hits": [{"hit_id": "H-1", "decision": None}, {"hit_id": "H-2", "decision": "D-6"}]}


@pytest.fixture
def corpus(tmp_path):
    (tmp_path / "input/pagecontent").mkdir(parents=True)
    (tmp_path / "input/fsh").mkdir(parents=True)
    (tmp_path / P).write_text(PAGE)
    (tmp_path / F).write_text(FSH)
    return gf.Corpus(tmp_path, gx.extract_page(P, PAGE) + gx.extract_fsh(F, FSH, {})[0])


def finding(**kw):
    f = {"file": P, "line": 3, "find": "referral recipient", "nth_in_line": 2, "replace": "referral target",
         "terms": ["T-RT"], "type": "Missed use", "rule": "R-RT-RECIP", "issue": "Use the glossary term.",
         "confidence": "High", "hits": ["H-1"]}
    f.update(kw)
    return f


def run(corpus, findings, dismissed=({"hit": "H-2", "reason": "external name"},)):
    return gf.validate_batch({"findings": list(findings), "dismissed": list(dismissed)}, ENTRY, corpus, BOOK)


def test_valid_finding_becomes_a_locatable_record(corpus):
    recs, errors = run(corpus, [finding()])
    assert errors == []
    r = recs[0]
    assert PAGE[r["start"]:r["end"]] == "referral recipient"
    assert (r["occurrence"], r["occurrences_total"], r["line"]) == (2, 2, 3)
    assert r["apply_method"] == "Text replace" and r["decision"] is None


def test_location_errors(corpus):
    for f, msg in [(finding(nth_in_line=None), "give nth_in_line"),
                   (finding(line=5), "not on line"),
                   (finding(line=4, find="glossary.html", nth_in_line=None), "hidden markup"),
                   (finding(find=" referral recipient"), "whitespace")]:
        _, errors = run(corpus, [f])
        assert any(msg in e for e in errors), (msg, errors)


def test_replacement_safety(corpus):
    _, errors = run(corpus, [finding(file=F, line=3, nth_in_line=None, replace='the "target"')])
    assert any("escape double quotes" in e for e in errors)
    _, errors = run(corpus, [finding(line=7, find="CBO", nth_in_line=None, replace="CBO | org", terms=["T-SSO"],
                                     hits=[], rule=None)],
                    dismissed=[{"hit": "H-1", "reason": "x"}, {"hit": "H-2", "reason": "y"}])
    assert any("| characters" in e for e in errors)


def test_every_hit_needs_one_disposition(corpus):
    _, errors = run(corpus, [finding()], dismissed=[])
    assert any("H-2 has no disposition" in e for e in errors)
    _, errors = run(corpus, [finding()], dismissed=[{"hit": "H-2"}])
    assert any("needs a reason" in e for e in errors)


def test_overlapping_findings_are_rejected(corpus):
    second = finding(find="recipient replies", nth_in_line=None, replace="target replies", hits=[])
    _, errors = run(corpus, [finding(), second])
    assert any("overlap" in e for e in errors)


def test_pending_decisions(corpus):
    cbo = finding(line=7, find="CBO", nth_in_line=None, replace="Social service organization",
                  terms=["T-SSO"], rule="R-SSO-CBO", hits=["H-2"])
    _, errors = run(corpus, [finding(), cbo], dismissed=[])
    assert any("recommended" in e for e in errors)
    recs, errors = run(corpus, [finding(), {**cbo, "recommended": "change"}], dismissed=[])
    assert errors == [] and recs[1]["decision"] == "D-6"
    _, errors = run(corpus, [finding(decision="D-1", recommended="keep")])
    assert any("unknown or already-decided decision D-1" in e for e in errors)


def test_apply_method_by_segment():
    base = {"start": 0, "field": "paragraph", "kind": "page", "change_class": "Prose"}
    assert gf.apply_method(base) == "Text replace"
    assert gf.apply_method({**base, "change_class": "Historical"}) == "Manual"
    assert gf.apply_method({**base, "kind": "diagram", "change_class": "Diagram"}) == "Diagram source + re-render"
    assert gf.apply_method({**base, "kind": "glossary"}) == "Glossary entry edit"
    assert gf.apply_method({**base, "start": None, "kind": "figure", "change_class": "Diagram"}) == "Manual"


def test_qa_batches_get_a_synthetic_manifest_entry_from_their_own_files():
    out = {"findings": [{"file": "a.md"}, {"file": "b.md"}, {"file": "a.md"}]}
    entry = gf.batch_entry({"B01": {"files": ["z.md"], "hits": [1]}}, "Q01", out)
    assert entry == {"title": "QA additions Q01", "files": ["a.md", "b.md"], "hits": []}
    assert gf.batch_entry({"B01": {"files": ["z.md"], "hits": [1]}}, "B01", out)["files"] == ["z.md"]
    with pytest.raises(KeyError):
        gf.batch_entry({}, "B02", out)
