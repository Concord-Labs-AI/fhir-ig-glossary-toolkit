import pytest

import scan as gs
from common import HISTORICAL, IDENTIFIER, PROSE


def seg(text, cls=PROSE, start=100, line=10, field="paragraph", seg_id="p.md:10:1"):
    return {"seg_id": seg_id, "file": "p.md", "change_class": cls, "field": field, "line": line,
            "start": start, "end": None if start is None else start + len(text),
            "visible": text, "text": " ".join(text.split())}


BOOK = {"decisions": [{"id": "D-1"}],
        "terms": [{"id": "T-RT", "glossary_term": "Referral target", "rules": [
            {"id": "R-RT-CANON", "type": "canonical", "pattern": r"\breferral targets?\b"},
            {"id": "R-RT-RECIP", "type": "missed-use", "pattern": r"\breferral[\s-]+recipients?\b",
             "suggest": "referral target"},
            {"id": "R-RT-CASE", "type": "form", "case_sensitive": True, "pattern": r"\bReferral Target\b",
             "skip_fields": ["heading"]},
            {"id": "R-RT-PEND", "type": "missed-use", "pattern": r"\brecipient\b", "decision": "D-1"}]}]}


def test_load_rules_rejects_bad_rulebooks():
    for bad, msg in [
        ({"terms": [{"id": "T", "rules": [{"id": "R", "type": "nope", "pattern": "x"}]}]}, "unknown rule type"),
        ({"terms": [{"id": "T", "rules": [{"id": "R", "type": "form", "pattern": "("}]}]}, "bad pattern"),
        ({"terms": [{"id": "T", "rules": [{"id": "R", "type": "form", "pattern": "x"},
                                          {"id": "R", "type": "form", "pattern": "y"}]}]}, "duplicate"),
        ({"decisions": [], "terms": [{"id": "T", "rules": [{"id": "R", "type": "form", "pattern": "x",
                                                            "decision": "D-9"}]}]}, "unknown decision"),
    ]:
        with pytest.raises(ValueError, match=msg):
            gs.load_rules(bad)


def test_scan_offsets_lines_and_case():
    rules = gs.load_rules(BOOK)
    hits = gs.scan([seg("Line one.\nSend to the Referral-Recipient and referral targets.")], rules)
    recip = [h for h in hits if h["rule_id"] == "R-RT-RECIP"][0]
    assert recip["match"] == "Referral-Recipient"
    assert recip["line"] == 11
    assert recip["start"] == 100 + len("Line one.\nSend to the ")
    assert [h["match"] for h in hits if h["rule_id"] == "R-RT-CANON"] == ["referral targets"]
    assert not [h for h in hits if h["rule_id"] == "R-RT-CASE"]
    assert recip["context"].startswith("Line one. Send to the [[Referral-Recipient]]")


def test_scan_marks_locked_classes_skips_fields_and_carries_decisions():
    rules = gs.load_rules(BOOK)
    hits = gs.scan([seg("Old referral recipient wording.", cls=HISTORICAL),
                    seg("About the Referral Target", field="heading", seg_id="p.md:1:1")], rules)
    assert all(h["locked"] for h in hits if h["seg_id"] == "p.md:10:1")
    assert not [h for h in hits if h["rule_id"] == "R-RT-CASE"]
    assert [h for h in hits if h["rule_id"] == "R-RT-PEND"][0]["decision"] == "D-1"


def test_scan_identifiers_use_decamelized_text():
    hits = gs.scan([seg("SDOHCC Referral Recipient Light", cls=IDENTIFIER, start=None)], gs.load_rules(BOOK))
    h = [h for h in hits if h["rule_id"] == "R-RT-RECIP"][0]
    assert h["start"] is None and h["locked"]


def test_summarize_counts_editable_and_locked():
    rules = gs.load_rules(BOOK)
    hits = gs.scan([seg("a referral recipient"), seg("b referral recipient", cls=HISTORICAL, seg_id="q")], rules)
    s = gs.summarize(hits, rules)["R-RT-RECIP"]
    assert (s["total"], s["editable"], s["by_class"]) == (2, 1, {PROSE: 1, HISTORICAL: 1})
