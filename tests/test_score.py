import json

import pytest

import batches as gb
import extract as gx
import scan as gs
import score as sc
import config
from common import write_jsonl


def build_run(run):
    """extract + scan + batches on the fixture run, like the skill's steps 2 and 4."""
    cfg = config.load(run)
    result = gx.extract(cfg["snapshot"], cfg["ig"])
    write_jsonl(cfg["data"] / "segments.jsonl", result["segments"])
    book = config.rulebook(cfg)
    hits = gs.scan(result["segments"], gs.load_rules(book))
    write_jsonl(cfg["data"] / "hits.jsonl", hits)
    plan = gb.plan_batches(gb.file_sizes(result["segments"], cfg["snapshot"]), 10**6, [])
    manifest = gb.build_manifest(result["segments"], hits, plan)
    (cfg["data"] / "batches").mkdir()
    (cfg["data"] / "batches" / "manifest.json").write_text(json.dumps(manifest))
    return cfg, manifest


def finding(file, line, find, replace, hits=(), decision=None, recommended=None):
    f = {"file": file, "line": line, "find": find, "replace": replace, "terms": ["T-RT"], "type": "Missed use",
         "rule": "R-RT-RECIP", "issue": "Retired term.", "confidence": "High", "hits": list(hits)}
    if decision:
        f["decision"] = decision
    if recommended:
        f["recommended"] = recommended
    return f


def test_reader_scores_validity_recall_and_precision(run):
    cfg, manifest = build_run(run)
    bid = next(b for b, e in manifest.items() if "input/pagecontent/index.md" in e["files"])
    entry = manifest[bid]
    recip = [h for h in entry["hits"] if h["rule_id"] == "R-RT-RECIP" and h["file"].endswith("index.md")]
    cbo = [h for h in entry["hits"] if h["rule_id"] == "R-SSO-CBO"]
    # Reference: one kept row (the recipient edit) and one rejected row (a CBO edit the skeptic threw out).
    kept = [{"key": f"input/pagecontent/index.md@{recip[0]['start']}", "file": "input/pagecontent/index.md",
             "start": recip[0]["start"], "end": recip[0]["end"], "source": "agent"}]
    rejected = [{"key": f"input/pagecontent/index.md@{cbo[0]['start']}", "file": "input/pagecontent/index.md",
                 "start": cbo[0]["start"], "end": cbo[0]["end"], "hits": [cbo[0]["hit_id"]]}]
    candidate = {"batch": bid, "findings": [
        finding("input/pagecontent/index.md", 3, "referral recipient", "referral target", [recip[0]["hit_id"]]),
        # The CBO hit carries D-1. Validation infers the decision and needs `recommended`, so this finding is
        # valid — but the agent never wrote `decision`, which is the pending-rule violation the scorer counts.
        finding("input/pagecontent/index.md", 3, "CBO", "social service organization", [cbo[0]["hit_id"]], recommended="change"),
        finding("input/pagecontent/index.md", 4, "SDOH matter", "social determinants of health matter"),      # unmatched
        finding("input/pagecontent/index.md", 99, "nowhere", "x")],                                           # invalid line
        "dismissed": [{"hit": h["hit_id"], "reason": "test"} for h in entry["hits"] if h["hit_id"] not in (recip[0]["hit_id"], cbo[0]["hit_id"])]}
    s, unmatched = sc.score_reader(candidate, entry, cfg, kept, rejected)
    assert s["proposed"] == 4 and s["valid"] == 3 and s["validity"] == 0.75
    assert s["reference_kept"] == 1 and s["recall"] == 1.0
    assert s["matches_rejected"] == 1 and s["unmatched"] == 1 and s["precision_proxy"] == pytest.approx(1 / 3)
    assert s["pending_violations"] == 1
    assert [u["find"] for u in unmatched] == ["SDOH matter"]


def packet_dir(tmp_path, keys, verdicts):
    d = tmp_path / "cand"
    d.mkdir()
    (d / "V01.keys.json").write_text(json.dumps(keys))
    (d / "V01.json").write_text(json.dumps(verdicts))
    return d / "V01.json"


REF = [[{"key": "a", "verdict": "confirm", "reason": "r"}, {"key": "b", "verdict": "reject", "reason": "r"}],
       [{"key": "b", "verdict": "revise", "replace": "x", "reason": "later pass wins"},
        {"key": "c", "verdict": "revise", "replace": "y", "reason": "r"}]]


def test_skeptic_scores_whole_packet_with_default_confirm(tmp_path):
    keys = ["a", "b", "c", "d", "e"]          # d and e have no reference verdict: confirmed by default
    cand = [{"key": "a", "verdict": "confirm"}, {"key": "b", "verdict": "revise", "replace": "x"},
            {"key": "c", "verdict": "revise", "replace": "z"}, {"key": "d", "verdict": "reject"}]  # e missing
    path = packet_dir(tmp_path, keys, cand)
    s = sc.score_skeptic(sc.load_candidate(path), REF, sc.load_keys(path))
    assert s["compared"] == 5 and s["agreement"] == pytest.approx(3 / 5)
    assert s["agreement_explicit"] == pytest.approx(3 / 3)
    assert s["confusion"]["confirm→reject"] == 1 and s["confusion"]["confirm→missing"] == 1
    assert s["revise_same_replace"] == 1 and s["revise_different_replace"] == 1


def test_skeptic_rejecting_default_confirmed_key_is_a_disagreement(tmp_path):
    path = packet_dir(tmp_path, ["d"], [{"key": "d", "verdict": "reject"}])
    s = sc.score_skeptic(sc.load_candidate(path), [], sc.load_keys(path))
    assert s["agreement"] == 0.0 and s["confusion"] == {"confirm→reject": 1}


def test_skeptic_missing_keys_file_is_named(tmp_path):
    (tmp_path / "V01.json").write_text("[]")
    with pytest.raises(SystemExit, match=r"V01\.keys\.json"):
        sc.load_keys(tmp_path / "V01.json")


def test_reader_duplicate_findings_lower_validity(run):
    cfg, manifest = build_run(run)
    bid = next(b for b, e in manifest.items() if "input/pagecontent/index.md" in e["files"])
    entry = manifest[bid]
    recip = [h for h in entry["hits"] if h["rule_id"] == "R-RT-RECIP" and h["file"].endswith("index.md")][0]
    kept = [{"key": f"input/pagecontent/index.md@{recip['start']}", "file": "input/pagecontent/index.md",
             "start": recip["start"], "end": recip["end"], "source": "agent"}]
    f = finding("input/pagecontent/index.md", 3, "referral recipient", "referral target", [recip["hit_id"]])
    rest = [{"hit": h["hit_id"], "reason": "t"} for h in entry["hits"] if h["hit_id"] != recip["hit_id"]]
    one, _ = sc.score_reader({"batch": bid, "findings": [f], "dismissed": rest}, entry, cfg, kept, [])
    assert one["validity"] == 1.0 and one["errors"] == 0
    two, _ = sc.score_reader({"batch": bid, "findings": [f, dict(f)], "dismissed": rest}, entry, cfg, kept, [])
    assert two["proposed"] == 2 and two["valid"] == 0 and two["validity"] == 0.0 and two["errors"] >= 1


def test_reader_matching_is_one_to_one():
    kept = [{"key": "f@10", "file": "f", "start": 10, "end": 20}, {"key": "f@30", "file": "f", "start": 30, "end": 40}]
    wide = [{"key": "f@5", "file": "f", "start": 5, "end": 45}]
    matched, rest = sc.match_one_to_one(kept, wide)
    assert len(matched) == 1 and rest == []
    exact = [{"key": "f@30", "file": "f", "start": 30, "end": 40}, {"key": "f@5", "file": "f", "start": 5, "end": 45}]
    matched, rest = sc.match_one_to_one(kept, exact)
    assert len(matched) == 2 and rest == []


def test_reader_missing_or_malformed_output_scores_zero(tmp_path):
    for name, body, status in [("none.json", None, "did not complete"), ("list.json", "[]", "malformed"),
                               ("bad.json", "{not json", "malformed")]:
        p = tmp_path / name
        if body is not None:
            p.write_text(body)
        cand, why = sc.read_reader_candidate(p)
        assert cand is None and why == status
        r = sc.incomplete_result(why, 5)
        assert r["status"] == status and r["proposed"] == 0 and r["valid"] == 0
        assert r["validity"] == 0.0 and r["recall"] == 0.0 and r["reference_kept"] == 5


def test_malformed_candidate_is_an_error(run, tmp_path):
    cfg, manifest = build_run(run)
    bad = tmp_path / "B01.json"
    bad.write_text("{not json")
    with pytest.raises(SystemExit, match="B01.json"):
        sc.load_candidate(bad)
