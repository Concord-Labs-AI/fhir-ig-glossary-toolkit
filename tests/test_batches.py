import batches as gb
from common import HISTORICAL, PROSE


def test_assign_routes_files_to_batches():
    assert gb.assign("input/pagecontent/StructureDefinition-SDOHCC-Goal-intro.md") == "B06"
    assert gb.assign("input/pagecontent/referral_workflow.md") == "B01"
    assert gb.assign("input/pagecontent/privacy_and_security.md") == "B05"
    assert gb.assign("input/fsh/instances/SDOHCC-ReferralRecipientLight.fsh") == "B08"
    assert gb.assign("input/fsh/instances/SDOHCC-CoordinationPlatform.fsh") == "B11"
    assert gb.assign("input/fsh/instances/SDOHCC-ReferralSource.fsh") == "B12"
    assert gb.assign("input/fsh/instances/SDOHCC-GoalExample.fsh") == "B09"
    assert gb.assign("input/fsh/profiles/SDOHCCGoal.fsh") == "B07"
    assert gb.assign("input/images-source/Flow.plantuml") == "B10"
    assert gb.assign("somewhere/else.txt") is None


def test_hit_id_is_stable_and_position_sensitive():
    h = {"rule_id": "R-X", "seg_id": "p.md:1:1", "start": 5, "match": "CBO"}
    assert gb.hit_id(h) == gb.hit_id(dict(h))
    assert gb.hit_id(h) != gb.hit_id({**h, "start": 9})
    assert gb.hit_id(h).startswith("H-") and len(gb.hit_id(h)) == 10


def test_manifest_skips_locked_files_canonical_and_locked_hits():
    segs = [{"file": "input/pagecontent/referral_workflow.md", "change_class": PROSE},
            {"file": "input/pagecontent/changehistory.md", "change_class": HISTORICAL}]
    base = {"seg_id": "s", "file": "input/pagecontent/referral_workflow.md", "line": 3, "start": 10,
            "match": "x", "decision": None, "context": "a | b"}
    hits = [{**base, "rule_id": "R-1", "type": "missed-use", "locked": False},
            {**base, "rule_id": "R-2", "type": "canonical", "locked": False},
            {**base, "rule_id": "R-3", "type": "form", "locked": True}]
    m = gb.build_manifest(segs, hits)
    assert list(m) == ["B01"]
    assert m["B01"]["files"] == ["input/pagecontent/referral_workflow.md"]
    assert [h["rule_id"] for h in m["B01"]["hits"]] == ["R-1"]
    md = gb.packet_md("B01", m["B01"])
    assert m["B01"]["hits"][0]["hit_id"] in md and "a \\| b" in md
