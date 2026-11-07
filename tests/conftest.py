import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "ig-glossary" / "scripts"))

FIXTURE_RUN = Path(__file__).resolve().parent / "fixtures" / "run"


@pytest.fixture
def run(tmp_path):
    dest = tmp_path / "run"
    shutil.copytree(FIXTURE_RUN, dest)
    return dest


@pytest.fixture
def cfg(run):
    import config
    return config.load(run)


def _row(n, **kw):
    base = {"id": f"GA-{n:04d}", "theme": "Referral actors and roles", "theme_id": "TH-ACTORS",
            "terms": "Referral target", "type": "Missed use", "rule": "R-RT-RECIP", "page": "referral_workflow.md",
            "section": "Overview", "file": "input/pagecontent/referral_workflow.md", "line": 10 + n,
            "occurrence": 1, "occurrences_total": 1,
            "url": "https://hl7.org/fhir/us/sdoh-clinicalcare/en/referral_workflow.html",
            "context": "Send to the referral recipient.", "issue": "Glossary term is referral target.",
            "find": "referral recipient", "replace": "referral target", "change_class": "Prose",
            "apply_method": "Text replace", "confidence": "High", "status": "Ready", "decision": None,
            "recommended": None, "start": 100 * n, "end": 100 * n + 18, "hits": [], "source": "agent", "key": f"k{n}"}
    base.update(kw)
    return base


@pytest.fixture
def sample_doc():
    from merge import digest
    rows = [_row(1),
            _row(2, find="= formula-looking text", replace="+ plus", type="Form", theme="Form & presentation",
                 theme_id="TH-FORM"),
            _row(3, terms="Social service organization", find="CBO", replace="social service organization",
                 status="Pending D-6", decision="D-6", recommended="change", rule="R-SSO-CBO",
                 theme="Organization types", theme_id="TH-ORGS"),
            _row(4, change_class="Identifier", apply_method="Manual", find="SDOHCC-ReferralRecipient", replace="",
                 status="Pending D-10", decision="D-10", recommended="keep", source="identifier", line=1,
                 page="SDOHCC-ReferralRecipient")]
    return {"meta": {"snapshot": "3.0.0", "rulebook": "draft-1", "generated": "2026-10-23",
                     "rows": len(rows), "sha256": digest(rows)}, "rows": rows}


@pytest.fixture
def sample_book():
    return {"version": "draft-1",
            "decisions": [{"id": "D-6", "title": "CBO vs social service organization", "question": "Q6",
                           "options": ["A: x", "B: y"], "recommendation": "A"},
                          {"id": "D-10", "title": "Identifier-level misalignments", "question": "Q10",
                           "options": ["A: keep"], "recommendation": "A"}],
            "terms": [{"id": "T-RT", "glossary_term": "Referral target", "rules": []},
                      {"id": "T-SSO", "glossary_term": "Social service organization", "rules": []}]}


@pytest.fixture
def sample_counts():
    return {"R-RT-CANON": {"term_id": "T-RT", "type": "canonical", "total": 80, "editable": 75,
                           "by_class": {"Prose": 75, "Historical": 5}, "by_file": {}},
            "R-RT-RECIP": {"term_id": "T-RT", "type": "missed-use", "total": 105, "editable": 96,
                           "by_class": {"Prose": 96, "Identifier": 9}, "by_file": {}}}
