import pytest

import batches as gb
from common import HISTORICAL, IDENTIFIER, PROSE


def test_packs_a_directory_up_to_the_budget_then_starts_a_new_packet():
    s = {"input/pagecontent/a.md": 400, "input/pagecontent/b.md": 400, "input/pagecontent/c.md": 400}
    plan = gb.plan_batches(s, target_chars=1000, overrides=[])
    assert [e["files"] for e in plan.values()] == [["input/pagecontent/a.md", "input/pagecontent/b.md"],
                                                   ["input/pagecontent/c.md"]]
    assert list(plan) == ["B01", "B02"]


def test_directories_never_share_a_packet_and_follow_a_fixed_order():
    s = {"input/fsh/profiles/p.fsh": 10, "input/pagecontent/a.md": 10, "input/images-source/d.plantuml": 10}
    plan = gb.plan_batches(s, target_chars=1000, overrides=[])
    assert [e["files"] for e in plan.values()] == [["input/pagecontent/a.md"], ["input/fsh/profiles/p.fsh"],
                                                   ["input/images-source/d.plantuml"]]


def test_input_pages_and_intro_notes_get_packets_after_pagecontent_not_other():
    s = {"misc/z.md": 10, "input/intro-notes/X-intro.md": 10, "input/pages/a.md": 10, "input/pagecontent/b.md": 10}
    plan = gb.plan_batches(s, target_chars=1000, overrides=[])
    assert [e["title"] for e in plan.values()] == ["input/pagecontent: b.md", "input/pages: a.md",
                                                   "input/intro-notes: X-intro.md", "other: z.md"]


def test_oversize_file_gets_a_packet_of_its_own():
    s = {"input/fsh/instances/small.fsh": 100, "input/fsh/instances/huge.fsh": 5000, "input/fsh/instances/tiny.fsh": 50}
    plan = gb.plan_batches(s, target_chars=1000, overrides=[])
    assert [e["files"] for e in plan.values()] == [["input/fsh/instances/huge.fsh"],
                                                   ["input/fsh/instances/small.fsh", "input/fsh/instances/tiny.fsh"]]


def test_overrides_win_and_keep_their_ids():
    s = {"input/pagecontent/a.md": 10, "input/pagecontent/b.md": 10, "input/fsh/x.fsh": 10}
    plan = gb.plan_batches(s, 1000, overrides=[{"id": "B07", "title": "Profiles", "globs": ["input/fsh/*"]}])
    assert plan["B07"] == {"title": "Profiles", "files": ["input/fsh/x.fsh"]}
    assert plan["B01"]["files"] == ["input/pagecontent/a.md", "input/pagecontent/b.md"]


def test_auto_ids_skip_an_override_that_took_a_low_id():
    s = {"input/pagecontent/a.md": 10, "input/fsh/profiles/p.fsh": 10, "input/fsh/instances/i.fsh": 10}
    plan = gb.plan_batches(s, 1000, overrides=[{"id": "B01", "title": "Pages", "globs": ["input/pagecontent/*"]}])
    assert list(plan) == ["B01", "B02", "B03"]
    assert plan["B01"]["files"] == ["input/pagecontent/a.md"]
    assert plan["B02"]["files"] == ["input/fsh/profiles/p.fsh"] and plan["B03"]["files"] == ["input/fsh/instances/i.fsh"]


def test_override_matching_nothing_and_empty_corpus_are_errors():
    with pytest.raises(ValueError, match="B09"):
        gb.plan_batches({"a.md": 1}, 1000, overrides=[{"id": "B09", "title": "x", "globs": ["nope/*"]}])
    with pytest.raises(ValueError, match="no editable files"):
        gb.plan_batches({}, 1000, overrides=[])


def test_file_sizes_use_text_length_for_files_and_label_length_for_figures(tmp_path):
    (tmp_path / "a.md").write_text("twelve chars")
    segs = [{"file": "a.md", "change_class": PROSE, "start": 0, "text": "twelve chars"},
            {"file": "a.md", "change_class": IDENTIFIER, "start": 3, "text": "x"},
            {"file": "img.png", "change_class": "Diagram", "start": None, "text": "Label one"},
            {"file": "img.png", "change_class": "Diagram", "start": None, "text": "Two"},
            {"file": "hist.md", "change_class": HISTORICAL, "start": 0, "text": "locked only"}]
    assert gb.file_sizes(segs, tmp_path) == {"a.md": 12, "img.png": 12}


def test_hit_id_is_stable_and_position_sensitive():
    h = {"rule_id": "R-X", "seg_id": "p.md:1:1", "start": 5, "match": "CBO"}
    assert gb.hit_id(h) == gb.hit_id(dict(h))
    assert gb.hit_id(h) != gb.hit_id({**h, "start": 9})
    assert gb.hit_id(h).startswith("H-") and len(gb.hit_id(h)) == 10


def test_manifest_skips_locked_files_canonical_and_locked_hits():
    plan = {"B01": {"title": "Pages", "files": ["input/pagecontent/referral_workflow.md"]}}
    segs = [{"file": "input/pagecontent/referral_workflow.md", "change_class": PROSE},
            {"file": "input/pagecontent/changehistory.md", "change_class": HISTORICAL}]
    base = {"seg_id": "s", "file": "input/pagecontent/referral_workflow.md", "line": 3, "start": 10,
            "match": "x", "decision": None, "context": "a | b"}
    hits = [{**base, "rule_id": "R-1", "type": "missed-use", "locked": False},
            {**base, "rule_id": "R-2", "type": "canonical", "locked": False},
            {**base, "rule_id": "R-3", "type": "form", "locked": True}]
    m = gb.build_manifest(segs, hits, plan)
    assert list(m) == ["B01"]
    assert m["B01"]["files"] == ["input/pagecontent/referral_workflow.md"]
    assert [h["rule_id"] for h in m["B01"]["hits"]] == ["R-1"]
    md = gb.packet_md("B01", m["B01"])
    assert m["B01"]["hits"][0]["hit_id"] in md and "a \\| b" in md
