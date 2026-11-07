import json

import pytest

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


def seed(run, records):
    d = run / "data" / "agent" / "validated"
    d.mkdir(parents=True)
    (d / "B01.json").write_text(json.dumps({"records": records}))
    (run / "data" / "batches").mkdir()
    (run / "data" / "batches" / "manifest.json").write_text(json.dumps({"B01": {"title": "t", "files": ["a.md"], "hits": []}}))


REC = {"key": "a.md@1", "file": "a.md", "line": 1, "start": 1, "end": 2, "type": "Misuse", "confidence": "High",
       "terms": ["T-RT"], "decision": None, "recommended": None, "issue": "i", "find": "x", "replace": "y",
       "change_class": "Prose", "field": "paragraph", "kind": "page", "context": "c"}


def test_packets_number_after_the_highest_existing_verdict_file(run, capsys):
    seed(run, [REC])
    v = run / "data" / "verify"; v.mkdir(parents=True)
    (v / "V04.json").write_text("[]")              # a consistency-pass file with no keys file
    gv.main(["--run", str(run), "--packets", "--n", "1"])
    assert (v / "V05.keys.json").exists() and (v / "V04.json").read_text() == "[]"


def test_check_without_keys_file_requires_partial(run):
    seed(run, [REC])
    v = run / "data" / "verify"; v.mkdir(parents=True)
    (v / "V09.json").write_text(json.dumps([{"key": "a.md@1", "verdict": "reject", "reason": "r"}]))
    with pytest.raises(SystemExit, match="V09.keys.json"):
        gv.main(["--run", str(run), "--check", "V09"])
    with pytest.raises(SystemExit) as e:
        gv.main(["--run", str(run), "--check", "V09", "--partial"])
    assert e.value.code == 0


def test_mistyped_files_value_is_an_error(run):
    seed(run, [REC])
    with pytest.raises(SystemExit, match="B3"):
        gv.main(["--run", str(run), "--packets", "--files", "B3"])
