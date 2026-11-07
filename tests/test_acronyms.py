import extract as gx
import findings as gf
from acronyms import acronym_findings

PAGE = "# About CBO\n\nCBOs deliver services. The CP relays data.\n\nA community-based organization (CBO) appears.\n"
PAGE2 = "Each coordination platform (CP) is a system. The CP relays.\n"


def test_first_body_use_is_spelled_out_once_per_page(tmp_path):
    for name, text in (("a.md", PAGE), ("b.md", PAGE2)):
        p = tmp_path / "input/pagecontent" / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    segs = gx.extract_page("input/pagecontent/a.md", PAGE) + gx.extract_page("input/pagecontent/b.md", PAGE2)
    out = acronym_findings(segs, gf.Corpus(tmp_path, segs))
    got = {(r["file"].split("/")[-1], r["find"], r["replace"]) for r in out}
    assert got == {("a.md", "CBOs", "Community-based organizations (CBOs)"),
                   ("a.md", "CP", "coordination platform (CP)")}
    cp = [r for r in out if r["find"] == "CP"][0]
    assert PAGE[cp["start"]:cp["end"]] == "CP" and cp["line"] == 3 and cp["type"] == "Form"


def test_names_and_hyphenated_compounds_are_skipped(tmp_path):
    page = ("The SDOH Clinical Care IG uses SDOH Category codes for SDOH-related data, a CBO's data, "
            "services tagged “SDOH”, and SDOH matters. CBOs too.\n")
    p = tmp_path / "input/pagecontent/c.md"
    p.parent.mkdir(parents=True)
    p.write_text(page)
    segs = gx.extract_page("input/pagecontent/c.md", page)
    out = acronym_findings(segs, gf.Corpus(tmp_path, segs))
    assert [(r["find"], page[r["start"]:r["start"] + 13]) for r in out] == [("CBOs", "CBOs too.\n"),
                                                                          ("SDOH", "SDOH matters.")]


def test_an_before_a_consonant_expansion_becomes_a(tmp_path):
    page = "An SDOH referral goes to an EHR.\n"
    p = tmp_path / "input/pagecontent/d.md"
    p.parent.mkdir(parents=True)
    p.write_text(page)
    segs = gx.extract_page("input/pagecontent/d.md", page)
    out = {r["find"]: r for r in acronym_findings(segs, gf.Corpus(tmp_path, segs))}
    assert out["An SDOH"]["replace"] == "A social determinants of health (SDOH)" and out["An SDOH"]["start"] == 0
    assert out["EHR"]["replace"] == "electronic health record (EHR)"


def test_sentence_start_is_capitalized(tmp_path):
    page = "### Purpose\nSDOH data is sensitive. CBOs hold it.\n"
    p = tmp_path / "input/pagecontent/e.md"
    p.parent.mkdir(parents=True)
    p.write_text(page)
    segs = gx.extract_page("input/pagecontent/e.md", page)
    out = {r["find"]: r["replace"] for r in acronym_findings(segs, gf.Corpus(tmp_path, segs))}
    assert out == {"SDOH": "Social determinants of health (SDOH)", "CBOs": "Community-based organizations (CBOs)"}


def test_the_glossary_term_sdoh_domain_is_not_spelled_out(tmp_path):
    page = "Bindings to SDOH domain-specific value sets and SDOH domains exist. Then SDOH matters.\n"
    p = tmp_path / "input/pagecontent/e.md"
    p.parent.mkdir(parents=True)
    p.write_text(page)
    segs = gx.extract_page("input/pagecontent/e.md", page)
    out = acronym_findings(segs, gf.Corpus(tmp_path, segs))
    assert [(r["find"], page[r["start"]:r["start"] + 13]) for r in out] == [("SDOH", "SDOH matters.")]
