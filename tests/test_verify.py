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
