import verify as gv


def rec(key, **kw):
    r = {"key": key, "file": "a.md", "start": 1, "type": "Missed use", "confidence": "High",
         "kind": "page", "field": "paragraph", "find": "x", "replace": "y"}
    r.update(kw)
    return r


def test_packets_hold_misuse_and_medium_findings_grouped_by_file():
    recs = [rec("k1", type="Misuse"), rec("k2", confidence="Medium", file="b.md"), rec("k3"),
            rec("k4", type="Misuse", file="b.md")]
    keys = [[r["key"] for r in p] for p in gv.build_packets(recs, n=3)]
    assert sorted(k for p in keys for k in p) == ["k1", "k2", "k4"]
    assert any(set(p) == {"k2", "k4"} for p in keys)


def test_verdict_validation():
    keys = {"k1": rec("k1"), "k2": rec("k2", kind="fsh")}
    errs = gv.validate_verdicts([{"key": "k1", "verdict": "maybe", "reason": "r"},
                                 {"key": "k2", "verdict": "revise", "reason": "r", "replace": 'a "b"'},
                                 {"key": "k9", "verdict": "confirm", "reason": "r"}], keys)
    assert any("k1: verdict" in e for e in errs)
    assert any("k2" in e and "escape" in e for e in errs)
    assert any("unknown key k9" in e for e in errs)
    assert gv.validate_verdicts([{"key": "k1", "verdict": "confirm", "reason": "ok"}], {"k1": rec("k1")}) == []


def test_load_records_can_be_limited_to_files(tmp_path):
    import json
    d = tmp_path / "agent" / "validated"
    d.mkdir(parents=True)
    (d / "B01.json").write_text(json.dumps({"records": [{"key": "a.md@1", "file": "a.md"}, {"key": "b.md@1", "file": "b.md"}]}))
    assert [r["key"] for r in gv.load_records(tmp_path)] == ["a.md@1", "b.md@1"]
    assert [r["key"] for r in gv.load_records(tmp_path, files={"b.md"})] == ["b.md@1"]


def test_partial_verdicts_skip_the_completeness_check():
    keys = {"k1": {"find": "x", "kind": "page", "field": "paragraph"}, "k2": {"find": "y", "kind": "page", "field": "paragraph"}}
    verdicts = [{"key": "k1", "verdict": "reject", "reason": "r"}]
    assert gv.validate_verdicts(verdicts, keys) == ["no verdict for k2"]
    assert gv.validate_verdicts(verdicts, keys, partial=True) == []
