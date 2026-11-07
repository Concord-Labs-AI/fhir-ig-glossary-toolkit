import pytest

import apply as ga
import batches as gb


def row(id, find, occ, total, replace="NEW", method="Text replace", file="a.md"):
    return {"id": id, "file": file, "find": find, "occurrence": occ, "occurrences_total": total,
            "replace": replace, "apply_method": method}


def test_applies_exact_occurrences_and_reports(tmp_path):
    (tmp_path / "a.md").write_text("CBO one, CBO two, referral recipient.")
    rows = [row("GA-1", "CBO", 2, 2, "social service organization"),
            row("GA-2", "referral recipient", 1, 1, "referral target"),
            row("GA-3", "one", 1, 1, method="Manual")]
    rep = ga.apply_rows(rows, tmp_path, lambda r: r["replace"])
    assert (tmp_path / "a.md").read_text() == "CBO one, social service organization two, referral target."
    assert sorted(rep["applied"]) == ["GA-1", "GA-2"] and rep["skipped"] == ["GA-3"] and rep["drifted"] == []


def test_drift_is_reported_not_guessed(tmp_path):
    (tmp_path / "a.md").write_text("CBO and CBO and CBO")
    rep = ga.apply_rows([row("GA-1", "CBO", 1, 2)], tmp_path, lambda r: r["replace"])
    assert rep["applied"] == [] and rep["drifted"][0]["id"] == "GA-1"
    assert (tmp_path / "a.md").read_text() == "CBO and CBO and CBO"


def test_overlapping_rows_raise(tmp_path):
    (tmp_path / "a.md").write_text("referral recipient")
    with pytest.raises(ValueError, match="overlap"):
        ga.apply_rows([row("GA-1", "referral recipient", 1, 1), row("GA-2", "recipient", 1, 1)],
                      tmp_path, lambda r: r["replace"])


def test_residuals_separate_explained_from_unexplained():
    before = [{"rule_id": "R-1", "type": "missed-use", "locked": False, "seg_id": "s", "start": i, "match": "x"}
              for i in range(3)]
    after = [{"rule_id": "R-1", "type": "missed-use", "locked": False}] * 2
    res = ga.residuals(before, after, {gb.hit_id(before[0])})
    assert res["R-1"] == {"before": 3, "after": 2, "explained": 1, "unexplained": 1}


def test_explained_hits_cover_manual_rows_dismissals_and_skeptic_rejections(tmp_path):
    (tmp_path / "agent" / "validated").mkdir(parents=True)
    (tmp_path / "agent" / "validated" / "B01.json").write_text('{"dismissed": [{"hit": "H-d"}]}')
    (tmp_path / "rejected.json").write_text('[{"hits": ["H-r"]}]')
    rows = [{"apply_method": "Manual", "hits": ["H-m"]}, {"apply_method": "Text replace", "hits": ["H-applied"]}]
    assert ga.explained_hits(rows, tmp_path) == {"H-m", "H-d", "H-r"}
