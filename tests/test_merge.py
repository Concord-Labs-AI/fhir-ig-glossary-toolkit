import pytest
import extract as gx
import findings as gf
import merge as gm

THEMES = [{"id": "TH-ACTORS", "title": "Referral actors and roles", "terms": ["T-RT"]}]
BOOK = {"version": "t", "terms": [{"id": "T-RT", "glossary_term": "Referral target"},
                                  {"id": "T-CBO", "glossary_term": "Community-based organization (CBO)"}]}


def rec(key, start, end, source="agent", **kw):
    r = {"key": key, "file": "a.md", "line": 1, "start": start, "end": end, "occurrence": 1, "occurrences_total": 1,
         "find": "x", "replace": "y", "terms": ["T-RT"], "type": "Missed use", "rule": "R", "issue": "i",
         "confidence": "High", "decision": None, "recommended": None, "hits": [], "source": source,
         "seg_id": "a.md:1:1", "change_class": "Prose", "kind": "page", "field": "paragraph", "section": "S",
         "artifact": "a.md", "url": "u", "context": "ctx", "apply_method": "Text replace"}
    r.update(kw)
    return r


def test_verdicts_reject_and_revise():
    kept, rejected = gm.apply_verdicts([rec("k1", 0, 1), rec("k2", 5, 6)],
                                       [{"key": "k1", "verdict": "reject", "reason": "fine as is"},
                                        {"key": "k2", "verdict": "revise", "replace": "z", "reason": "grammar"}])
    assert [r["key"] for r in rejected] == ["k1"]
    assert kept[0]["replace"] == "z" and kept[0]["revision_note"] == "grammar" and kept[0]["issue"] == "i"


def test_agent_findings_win_overlaps_and_agent_clashes_are_errors():
    out, errors = gm.resolve_overlaps([rec("a", 10, 20), rec("s", 12, 14, source="script"),
                                       rec("s2", 30, 32, source="script")])
    assert sorted(r["key"] for r in out) == ["a", "s2"] and errors == []
    _, errors = gm.resolve_overlaps([rec("a", 10, 20), rec("b", 15, 25)])
    assert errors


def test_finalize_assigns_ids_themes_and_status():
    rows = gm.finalize([rec("k2", 50, 51, type="Form"),
                        rec("k1", 5, 6, decision="D-6", recommended="change", terms=["T-CBO"]),
                        rec("k0", 1, 2)], THEMES, BOOK)
    assert [r["id"] for r in rows] == ["GA-0001", "GA-0002", "GA-0003"]
    assert [r["theme"] for r in rows] == ["Referral actors and roles", "Form & presentation", "Other"]
    assert rows[2]["status"] == "Pending D-6" and rows[2]["terms"] == "Community-based organization (CBO)"
    assert rows[0]["status"] == "Ready"


def test_identifier_rows_one_per_artifact_and_rule(tmp_path):
    fsh = "Instance: SDOHCC-ReferralRecipientLight\nInstanceOf: CapabilityStatement\n"
    (tmp_path / "x.fsh").write_text(fsh)
    segs, _ = gx.extract_fsh("x.fsh", fsh, {}, "https://example.org/", ["SDOHCC"])
    hit = {"change_class": "Identifier", "type": "missed-use", "seg_id": segs[0]["seg_id"], "rule_id": "R-RT-RECIP",
           "term_id": "T-RT", "match": "Referral Recipient"}
    rows = gm.identifier_rows([hit, dict(hit), {**hit, "type": "canonical"}], segs,
                              {"R-RT-RECIP": {"note": "n"}}, gf.Corpus(tmp_path, segs), "D-10")
    assert len(rows) == 1 and rows[0]["apply_method"] == "Manual" and rows[0]["decision"] == "D-10"


def test_identifier_rows_carry_the_rulebook_decision():
    seg = {"seg_id": "f.fsh:1:10", "file": "f.fsh", "kind": "fsh", "change_class": "Identifier", "field": "Id",
           "section": "Profile", "artifact": "XRecipient", "url": None, "line": 1, "start": 9, "end": 19,
           "raw": "XRecipient", "visible": "XRecipient", "text": "X Recipient"}
    hit = {"change_class": "Identifier", "type": "missed-use", "seg_id": seg["seg_id"], "rule_id": "R-1",
           "term_id": "T-RT", "match": "Recipient"}

    class C:
        def text(self, f):
            return "Profile: XRecipient\n"
    rows = gm.identifier_rows([hit], [seg], {"R-1": {"note": "n"}}, C(), "D-7")
    assert rows[0]["decision"] == "D-7" and rows[0]["recommended"] == "keep"


def test_trim_context_and_digest():
    out = gm.trim_context("a" * 500 + " needle " + "b" * 500, "needle", width=50)
    assert "needle" in out and out.startswith("…") and out.endswith("…") and len(out) < 200
    assert gm.digest([{"a": 1}]) != gm.digest([{"a": 2}])


def test_retag_verdict_moves_a_row_between_decisions_or_to_ready():
    kept, rejected = gm.apply_verdicts(
        [rec("k1", 0, 1, decision="D-1", recommended="change"), rec("k2", 5, 6, decision="D-1", recommended="change")],
        [{"key": "k1", "verdict": "retag", "decision": None, "recommended": None, "reason": "same edit under every option"},
         {"key": "k2", "verdict": "retag", "decision": "D-8", "recommended": "keep", "reason": "provider wording"}])
    assert rejected == []
    assert (kept[0]["decision"], kept[0]["recommended"]) == (None, None)
    assert (kept[1]["decision"], kept[1]["recommended"]) == ("D-8", "keep")


def test_retag_to_a_decision_without_recommended_is_an_error():
    with pytest.raises(ValueError, match="k1"):
        gm.apply_verdicts([rec("k1", 0, 1, decision="D-1", recommended="change")],
                          [{"key": "k1", "verdict": "retag", "decision": "D-8", "recommended": None, "reason": "x"}])


def test_a_later_retag_keeps_an_earlier_revision_on_the_same_row():
    kept, _ = gm.apply_verdicts([rec("k1", 0, 1, decision="D-1", recommended="change")],
                                [{"key": "k1", "verdict": "revise", "replace": "z", "reason": "grammar"},
                                 {"key": "k1", "verdict": "retag", "decision": None, "recommended": None, "reason": "r"}])
    assert kept[0]["replace"] == "z" and kept[0]["decision"] is None


class FakeCorpus:
    def text(self, file):
        return "Alpha a referral requester want to send. Beta a referral requester want more.\n"


def test_revise_can_widen_the_span_and_keeps_the_issue_clean():
    r = rec("k1", 6, 26, find="a referral requester", replace="a referral source", issue="Retired term.")
    kept, _ = gm.apply_verdicts([r], [{"key": "k1", "verdict": "revise", "find": "a referral requester want",
                                       "replace": "a referral source wants", "reason": "fix the verb too"}],
                                FakeCorpus())
    k = kept[0]
    assert (k["find"], k["replace"], k["start"], k["end"]) == ("a referral requester want", "a referral source wants", 6, 31)
    assert (k["occurrence"], k["occurrences_total"]) == (1, 2)
    assert k["issue"] == "Retired term." and k["revision_note"] == "fix the verb too"


def test_widened_find_must_cover_the_original_span_exactly_once():
    r = rec("k1", 6, 26, find="a referral requester", replace="a referral source")
    with pytest.raises(ValueError, match="k1"):
        gm.apply_verdicts([r], [{"key": "k1", "verdict": "revise", "find": "Beta a referral requester",
                                 "replace": "x", "reason": "wrong place"}], FakeCorpus())


def test_revise_may_change_only_the_issue_text():
    kept, _ = gm.apply_verdicts([rec("k1", 0, 1, issue="old")],
                                [{"key": "k1", "verdict": "revise", "issue": "new", "reason": "clearer"}])
    assert (kept[0]["issue"], kept[0]["replace"], kept[0]["revision_note"]) == ("new", "y", "clearer")


def test_finalize_without_themes_puts_non_form_rows_in_the_catch_all():
    rows = gm.finalize([rec("k1", 5, 6), rec("k2", 50, 51, type="Form")], [], BOOK)
    assert {r["theme_id"] for r in rows} == {gm.THEME_OTHER, gm.THEME_FORM}


def test_merge_main_runs_before_themes_yaml_exists(run):
    (run / "themes.yaml").unlink()
    (run / "data").mkdir(exist_ok=True)
    for name in ("segments.jsonl", "hits.jsonl"):
        (run / "data" / name).write_text("")
    gm.main(["--run", str(run)])
    assert (run / "data" / "findings.json").exists()
