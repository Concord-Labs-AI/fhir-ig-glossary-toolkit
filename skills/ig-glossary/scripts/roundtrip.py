"""Read a converted or reviewed workbook back and check it against findings.json."""
import argparse
import json
from collections import Counter
from pathlib import Path

from openpyxl import load_workbook

import config
from sheet import FINDING_COLUMNS, REVIEW_CHOICES, locked_value


def read_workbook(path):
    wb = load_workbook(path, data_only=True)
    meta = {r[0]: r[1] for r in wb["_meta"].iter_rows(values_only=True) if r[0]}
    values = list(wb["Findings"].iter_rows(values_only=True))
    headers = list(values[0])
    rows = [dict(zip(headers, v)) for v in values[1:] if any(x not in (None, "") for x in v)]
    return meta, rows


def norm(v):
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return str(v)


def check(doc, meta, sheet_rows):
    problems = []
    if meta.get("findings_sha256") != doc["meta"]["sha256"]:
        problems.append("workbook was built from a different findings.json")
    expected = {r["id"]: r for r in doc["rows"]}
    got = {}
    for s in sheet_rows:
        rid = norm(s.get("ID"))
        if rid in got:
            problems.append(f"{rid}: duplicated row")
        got[rid] = s
    problems += [f"{rid}: row missing (deleted?)" for rid in sorted(expected.keys() - got.keys())]
    problems += [f"{rid}: unknown row (new issues belong on Reviewer additions)" for rid in sorted(got.keys() - expected.keys())]
    for rid in sorted(expected.keys() & got.keys()):
        e, s = expected[rid], got[rid]
        for header, key, _ in FINDING_COLUMNS:
            if norm(locked_value(e, key)) != norm(s.get(header)):
                problems.append(f"{rid}: locked column '{header}' changed")
        d = norm(s.get("Review"))
        if d and d not in REVIEW_CHOICES:
            problems.append(f"{rid}: Review '{d}' is not one of {', '.join(REVIEW_CHOICES)}")
        if d == "Modify" and not norm(s.get("Reviewer's replace")):
            problems.append(f"{rid}: Modify without Reviewer's replace")
    return problems


def main(argv=None):
    ap = config.add_run_arg(argparse.ArgumentParser(description=__doc__))
    ap.add_argument("workbook", type=Path)
    args = ap.parse_args(argv)
    cfg = config.load(args.run)
    doc = json.loads((cfg["data"] / "findings.json").read_text(encoding="utf-8"))
    meta, rows = read_workbook(args.workbook)
    problems = check(doc, meta, rows)
    print(f"{len(rows)} rows; review: {dict(Counter(norm(r.get('Review')) or '(blank)' for r in rows))}")
    if problems:
        print("\n".join(f"  - {p}" for p in problems))
        raise SystemExit(1)
    print("OK: every locked column matches findings.json")


if __name__ == "__main__":
    main()
