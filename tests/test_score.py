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


def test_skeptic_agreement_and_breakdown():
    ref = [[{"key": "a", "verdict": "confirm", "reason": "r"}, {"key": "b", "verdict": "reject", "reason": "r"}],
           [{"key": "b", "verdict": "revise", "reason": "later pass wins"}, {"key": "c", "verdict": "confirm", "reason": "r"}]]
    cand = [{"key": "a", "verdict": "confirm"}, {"key": "b", "verdict": "reject"}, {"key": "zzz", "verdict": "reject"}]
    s = sc.score_skeptic(cand, ref)
    assert s["compared"] == 2 and s["agreement"] == 0.5
    assert s["pairs"]["confirm/confirm"] == 1 and s["pairs"]["revise/reject"] == 1


def test_malformed_candidate_is_an_error(run, tmp_path):
    cfg, manifest = build_run(run)
    bad = tmp_path / "B01.json"
    bad.write_text("{not json")
    with pytest.raises(SystemExit, match="B01.json"):
        sc.load_candidate(bad)
