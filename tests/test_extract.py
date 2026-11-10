import textwrap

import pytest

import extract as gx
from common import ARTIFACT, DIAGRAM, EXTERNAL, HISTORICAL, IDENTIFIER, PROSE

IG = {"published_base": "https://hl7.org/fhir/us/sdoh-clinicalcare/en/",
      "canonical": "http://hl7.org/fhir/us/sdoh-clinicalcare",
      "artifact_prefixes": ["SDOHCC"],
      "glossary_page": "input/pagecontent/glossary.md",
      "historical_pages": ["changehistory.md"]}
BASE = IG["published_base"]
MARKERS = [IG["canonical"]] + IG["artifact_prefixes"]


def test_mask_keeps_length_and_newlines():
    raw = "a <!-- hidden\nstill hidden --> b"
    vis = gx.mask_markdown(raw)
    assert len(vis) == len(raw)
    assert vis.count("\n") == 1
    assert "hidden" not in vis
    assert vis.strip().startswith("a") and vis.strip().endswith("b")


def test_markdown_link_text_visible_url_masked():
    vis = gx.mask_markdown("See [referral target](glossary.html#referral-target) now")
    assert "referral target" in vis
    assert "glossary.html" not in vis


def test_img_include_keeps_only_caption():
    raw = '{% include img.html img="Flow.svg" caption="Figure 1: Referral Flow" %}'
    assert gx.mask_markdown(raw).strip() == "Figure 1: Referral Flow"


def test_liquid_kramdown_html_and_separator_rows_masked():
    raw = '{% include foo.md %}\n{:.grid}\n<div class="stu-note">\n| --- | --- |\n### Title {#anchor}'
    vis = gx.mask_markdown(raw)
    for gone in ("include", "grid", "div", "---", "anchor"):
        assert gone not in vis
    assert "### Title" in vis


def test_page_segments_track_sections_lines_and_fields():
    raw = "# Top\n\nIntro text.\n\n### Sub A\n\n| Term | Def |\n| --- | --- |\n| x | y |\n\n## Next\n- item one\n"
    segs = {s["text"]: s for s in gx.extract_page("input/pagecontent/p.md", raw, url="u")}
    assert segs["Intro text."]["section"] == "Top"
    assert segs["Intro text."]["line"] == 3
    assert segs["| x | y |"]["field"] == "table-row"
    assert segs["| x | y |"]["section"] == "Top › Sub A"
    assert segs["- item one"]["section"] == "Top › Next"
    assert segs["- item one"]["field"] == "list-item"
    assert all(s["change_class"] == PROSE for s in segs.values())


def test_segment_offsets_point_into_raw():
    raw = "Para one.\n\nThe [CP](glossary.html) relays data.\n"
    seg = gx.extract_page("p.md", raw)[1]
    assert raw[seg["start"]:seg["end"]] == seg["raw"]
    assert seg["raw"].startswith("The [CP]")
    assert seg["text"] == "The CP relays data."
    assert seg["seg_id"] == "p.md:3:1"


def test_page_url_maps_intro_pages_to_artifact_page():
    assert gx.page_url("StructureDefinition-SDOHCC-Goal-intro.md", BASE).endswith("/en/StructureDefinition-SDOHCC-Goal.html")
    assert gx.page_url("referral_workflow.md", BASE).endswith("/en/referral_workflow.html")


FSH = textwrap.dedent('''\
    Alias: $loinc = http://loinc.org
    Profile: SDOHCCServiceRequest
    Parent: http://hl7.org/fhir/us/core/StructureDefinition/us-core-servicerequest|7.0.0
    Id: SDOHCC-ServiceRequest
    Title: "SDOHCC ServiceRequest"
    Description: "Profile for referral recipient requests."
    * . ^short = "A request for a service"
    * category ^slicing.discriminator.path = "$this"
    // * status ^comment = "commented out intermediary"
    * basedOn ^requirements = "Allows an intermediary to create a request." // trailing comment
    /* * code ^short = "block commented"
    */

    Instance: ExampleOrg
    InstanceOf: Organization
    * name = "ABC Coordination Platform"
    * url = "http://example.org/x"
    * type = http://terminology.hl7.org/CodeSystem/organization-type#cg "Community Group"

    Instance: SDOHCC-ReferralRecipientLight
    InstanceOf: CapabilityStatement
    * name = "SDOHCCReferralRecipientLight"
    * rest[=].documentation = "The referral recipient needs access."
    * rest[=].resource[=].searchParam[=].name = "_id"
    * text.div = "<div xmlns=\\"http://www.w3.org/1999/xhtml\\">A referral recipient</div>"

    Instance: PrapareQ
    InstanceOf: Questionnaire
    * item.text = "What is your housing situation today?"
    * item.answerOption[0].valueCoding = $loinc#LA1-1 "I have housing"

    Instance: SelfReported
    InstanceOf: Observation
    * method = $SDOHCC-CodeSystemTemporaryCodes#self-reported "Self Reported"

    CodeSystem: SDOHCCCodeSystemTemporaryCodes
    * #sdoh-category-unspecified "SDOH Category Unspecified" "Category for unspecified social risk"
    ''')


@pytest.fixture(scope="module")
def fsh_result():
    return gx.extract_fsh("input/fsh/x.fsh", FSH, {"ExampleOrg": "Organization"}, BASE, MARKERS)


def _by_raw(segs):
    return {s["raw"]: s for s in segs}


def test_fsh_keeps_prose_fields(fsh_result):
    segs = _by_raw(fsh_result[0])
    assert segs["SDOHCC ServiceRequest"]["field"] == "Title"
    assert segs["Profile for referral recipient requests."]["change_class"] == ARTIFACT
    assert segs["A request for a service"]["section"] == ". ^short"
    assert segs["Allows an intermediary to create a request."]["field"] == "^requirements"
    assert segs["The referral recipient needs access."]["field"] == "rest[=].documentation"
    assert segs["ABC Coordination Platform"]["change_class"] == ARTIFACT


def test_fsh_skips_non_prose_and_comments(fsh_result):
    segs, skipped = fsh_result
    raws = {s["raw"] for s in segs}
    for gone in ("$this", "http://example.org/x", "_id", "commented out intermediary", "block commented"):
        assert gone not in raws
    assert skipped >= 3


def test_fsh_div_text_has_markup_masked(fsh_result):
    div = [s for s in fsh_result[0] if s["field"] == "text.div"][0]
    assert div["text"] == "A referral recipient"


def test_fsh_classifies_codes_identifiers_and_external_text(fsh_result):
    segs = _by_raw(fsh_result[0])
    assert segs["Community Group"]["change_class"] == EXTERNAL
    assert segs["I have housing"]["change_class"] == EXTERNAL
    assert segs["What is your housing situation today?"]["change_class"] == EXTERNAL
    assert segs["Self Reported"]["change_class"] == ARTIFACT
    assert segs["SDOH Category Unspecified"]["field"] == "concept display"
    assert segs["Category for unspecified social risk"]["field"] == "concept definition"
    assert segs["SDOHCCReferralRecipientLight"]["change_class"] == IDENTIFIER


def test_fsh_identifier_segments_are_decamelized(fsh_result):
    texts = {s["text"] for s in fsh_result[0] if s["field"] in ("entity name", "Id")}
    assert "SDOHCC Referral Recipient Light" in texts
    assert "SDOHCC Service Request" in texts


def test_fsh_urls(fsh_result):
    segs = _by_raw(fsh_result[0])
    assert segs["SDOHCC ServiceRequest"]["url"].endswith("/en/StructureDefinition-SDOHCC-ServiceRequest.html")
    assert segs["ABC Coordination Platform"]["url"].endswith("/en/Organization-ExampleOrg.html")
    assert segs["The referral recipient needs access."]["url"] is None


def test_plantuml_keeps_labels_drops_directives():
    raw = ("@startuml\nskinparam monochrome true\n' a comment\ntitle Indirect Referral\n"
           'participant "Referral Source" as RS\nRS -> CP: send referral\nend\n@enduml\n')
    segs = gx.extract_plantuml("input/images-source/Flow.plantuml", raw, url="u")
    assert [s["text"] for s in segs] == ["title Indirect Referral",
                                         'participant "Referral Source" as RS',
                                         "RS -> CP: send referral"]
    assert all(s["change_class"] == DIAGRAM and s["section"] == "Indirect Referral" for s in segs)


def test_svg_text_elements_become_segments():
    raw = '<svg><text x="1">Referral Source</text><g><text><tspan>CBO</tspan></text></g><text> </text></svg>'
    segs = gx.extract_svg("input/images/Map.svg", raw, url="u")
    assert [s["text"] for s in segs] == ["Referral Source", "CBO"]
    assert all(raw[s["start"]:s["end"]] == s["raw"] for s in segs)


SUSHI = textwrap.dedent('''\
    id: hl7.fhir.us.sdoh-clinicalcare
    title: "SDOH Clinical Care"
    description: Guide for referral targets.
    pages:
      index.md:
        title: Home
        child.md:
          title: Child Page
    menu:
      Home: index.html
      Implementation Guidance:
        Referral Workflow: referral_workflow.html
      Project Home: https://confluence.hl7.org/display/GRAV
    ''')


def test_sushi_config_keeps_titles_and_menu_labels():
    got = {(s["field"], s["text"]) for s in gx.extract_sushi_config("sushi-config.yaml", SUSHI)}
    assert ("IG title", "SDOH Clinical Care") in got
    assert ("IG description", "Guide for referral targets.") in got
    assert ("page title", "Home") in got and ("page title", "Child Page") in got
    assert {("menu label", "Implementation Guidance"), ("menu label", "Referral Workflow"),
            ("menu label", "Project Home")} <= got
    assert not any("hl7.fhir" in t or "confluence" in t for _, t in got)


def test_ig_yml_and_resource_text():
    yml = "groups:\n    Profiles:\n        name: Profiles\n        description: For referral targets\n        resources:\n          - X\n"
    assert [s["text"] for s in gx.extract_ig_yml("input/data/ig.yml", yml)] == ["Profiles", "For referral targets"]
    xml = '<StructureMap><id value="SDOHCC-SM"/><description value="Transforms answers"/><url value="http://x"/></StructureMap>'
    segs = gx.extract_resource("input/resources/sm.xml", xml, BASE)
    assert [s["text"] for s in segs] == ["Transforms answers"]
    assert segs[0]["url"].endswith("/en/StructureMap-SDOHCC-SM.html")


def test_resource_link_takes_its_type_from_the_root_element():
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<!-- <StructureMap> in a comment -->\n'
           '<Library xmlns="http://hl7.org/fhir"><id value="lib-1"/><description value="Shared logic"/></Library>')
    assert gx.extract_resource("input/resources/lib.xml", xml, BASE)[0]["url"] == BASE + "Library-lib-1.html"
    no_id = '<Library xmlns="http://hl7.org/fhir"><description value="Shared logic"/></Library>'
    assert gx.extract_resource("input/resources/lib.xml", no_id, BASE)[0]["url"] is None


def _write(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


@pytest.fixture
def snapshot(tmp_path):
    _write(tmp_path, "sushi-config.yaml",
           "title: T\npages:\n  index.md:\n    title: Home\n  changehistory.md:\n    title: History\n"
           "  glossary.md:\n    title: Glossary\nmenu:\n  Home: index.html\n")
    _write(tmp_path, "input/pagecontent/index.md",
           'Hello referral target.\n{% include img.html img="Flow.svg" caption="Figure 1" %}\n'
           '{% include img.html img="Model.png" caption="Figure 2" %}\n{% include img.html img="Map.svg" %}\n'
           "{% include Post_task.md %}\n")
    _write(tmp_path, "input/pagecontent/changehistory.md", "Renamed referral recipient.\n")
    _write(tmp_path, "input/pagecontent/glossary.md", "| Term | Definition |\n| --- | --- |\n| Referral target | An actor. |\n")
    _write(tmp_path, "input/pagecontent/savestuff.md", "Unpublished draft.\n")
    _write(tmp_path, "input/pagecontent/StructureDefinition-X-intro.md", "Intro.\n")
    _write(tmp_path, "input/fsh/x.fsh", 'Profile: X\nParent: Goal\nDescription: "A goal."\n')
    _write(tmp_path, "input/images-source/Flow.plantuml", "@startuml\nA -> B: refer\n@enduml\n")
    _write(tmp_path, "input/images/Model.png", "binary")
    _write(tmp_path, "input/images/Map.svg", '<svg><text x="1">Referral Source</text><text><tspan>CBO</tspan></text></svg>')
    _write(tmp_path, "input/images/Unused.png", "binary")
    _write(tmp_path, "input/includes/img.html", "<img>")
    _write(tmp_path, "input/includes/Post_task.md", "Included text.\n")
    _write(tmp_path, "input/includes/Orphan.md", "Never included.\n")
    _write(tmp_path, "input/fsh/index.txt", "Name  Type  File\n")
    _write(tmp_path, "input/weird.bin", "??")
    return tmp_path


def test_extract_accounts_for_every_file(snapshot):
    cov = gx.extract(snapshot, IG)["coverage"]
    all_files = {p.relative_to(snapshot).as_posix() for p in snapshot.rglob("*") if p.is_file()}
    assert set(cov) == all_files
    assert cov["input/pagecontent/savestuff.md"]["reason"] == \
        "not published (absent from sushi-config pages; 404 when published)"  # no publisher's host assumed
    assert cov["input/weird.bin"]["reason"].startswith("unrecognized")
    assert cov["input/fsh/index.txt"]["reason"].startswith("SUSHI-generated FSH index")
    assert cov["input/images/Unused.png"]["reason"].startswith("image not referenced")
    assert cov["input/includes/Orphan.md"]["reason"] == "not included by any published page"
    assert cov["input/includes/Post_task.md"]["status"] == "extracted"
    assert cov["input/pagecontent/StructureDefinition-X-intro.md"]["status"] == "extracted"


def test_without_a_pages_block_every_page_file_is_published(snapshot):
    sc = snapshot / "sushi-config.yaml"
    sc.write_text("title: T\nmenu:\n  Home: index.html\n")
    result = gx.extract(snapshot, IG)
    assert result["coverage"]["input/pagecontent/savestuff.md"]["status"] == "extracted"
    assert result["coverage"]["input/pagecontent/index.md"]["status"] == "extracted"
    assert result["coverage"]["input/images/Map.svg"]["status"] == "extracted"  # referenced by a published page


def test_input_pages_and_intro_notes_are_read_like_pagecontent(snapshot):
    sc = snapshot / "sushi-config.yaml"
    sc.write_text(sc.read_text().replace("menu:", "  guidance.md:\n    title: Guidance\nmenu:", 1))
    (snapshot / "input/pages").mkdir()
    (snapshot / "input/pagecontent/glossary.md").rename(snapshot / "input/pages/glossary.md")
    _write(snapshot, "input/pages/guidance.md", 'Use the referral target.\n{% include img.html img="Unused.png" %}\n')
    _write(snapshot, "input/pages/draft.md", "Unpublished draft.\n")
    _write(snapshot, "input/intro-notes/StructureDefinition-X-notes.md", "Notes on the goal.\n")
    _write(snapshot, "input/intro-notes/readme.md", "Not an intro or notes file.\n")
    result = gx.extract(snapshot, {**IG, "glossary_page": "input/pages/glossary.md"})
    cov = result["coverage"]
    assert cov["input/pages/guidance.md"]["status"] == "extracted"
    assert "not published" in cov["input/pages/draft.md"]["reason"]
    assert cov["input/intro-notes/StructureDefinition-X-notes.md"]["status"] == "extracted"
    assert cov["input/intro-notes/readme.md"]["reason"].startswith("unrecognized")
    assert "needs visual read" in cov["input/images/Unused.png"]["reason"]  # referenced from input/pages
    segs = {s["file"]: s for s in result["segments"]}
    assert segs["input/pages/glossary.md"]["kind"] == "glossary"
    assert segs["input/pages/guidance.md"]["url"] == BASE + "guidance.html"
    assert segs["input/intro-notes/StructureDefinition-X-notes.md"]["url"] == BASE + "StructureDefinition-X.html"


def test_extract_change_classes_kinds_and_urls(snapshot):
    by_file = {}
    for s in gx.extract(snapshot, IG)["segments"]:
        by_file.setdefault(s["file"], []).append(s)
    assert by_file["input/pagecontent/changehistory.md"][0]["change_class"] == HISTORICAL
    assert by_file["input/pagecontent/glossary.md"][0]["kind"] == "glossary"
    assert by_file["input/images-source/Flow.plantuml"][0]["url"].endswith("/en/index.html")
    assert by_file["input/includes/Post_task.md"][0]["url"].endswith("/en/index.html")
    assert {s["text"] for s in by_file["input/images/Map.svg"]} == {"Referral Source", "CBO"}


def test_raster_figures_queue_for_visual_read_until_transcribed(snapshot):
    result = gx.extract(snapshot, IG)
    assert [f["image"] for f in result["figures"]] == ["input/images/Model.png"]
    assert "needs visual read" in result["coverage"]["input/images/Model.png"]["reason"]

    transcripts = [{"image": "input/images/Model.png", "change_class": "Diagram",
                    "text": ["Referral Source", "Coordination Platform"]}]
    result = gx.extract(snapshot, IG, transcripts=transcripts)
    assert result["figures"] == []
    assert result["coverage"]["input/images/Model.png"]["status"] == "extracted"
    segs = [s for s in result["segments"] if s["file"] == "input/images/Model.png"]
    assert [s["text"] for s in segs] == ["Referral Source", "Coordination Platform"]
    assert segs[0]["start"] is None and segs[0]["url"].endswith("/en/index.html")


def test_link_text_wrapping_across_lines_is_still_unwrapped():
    vis = gx.mask_markdown("see [the referral\nServiceRequest](#servicerequest-topic). Next")
    assert "](#" not in vis and "servicerequest-topic" not in vis
    assert "the referral" in vis and "ServiceRequest" in vis


def test_local_code_systems_come_from_config_not_a_hard_coded_name():
    ig = {**IG, "artifact_prefixes": ["ACME"], "canonical": "http://acme.org/fhir/x"}
    markers = gx.local_markers(ig)
    assert gx.classify_fsh(None, "* code = ACME-Temp#x ", "x", markers) == (gx.ARTIFACT, "code display (local)")
    assert gx.classify_fsh(None, "* code = http://acme.org/fhir/x/CodeSystem/y#x ", "x", markers) == (gx.ARTIFACT, "code display (local)")
    assert gx.classify_fsh(None, "* code = SDOHCC-Temp#x ", "x", markers) == (gx.EXTERNAL, "code display")


def test_glossary_and_historical_pages_come_from_config(snapshot):
    ig = {**IG, "glossary_page": "input/pagecontent/index.md", "historical_pages": ["glossary.md"]}
    by_file = {}
    for s in gx.extract(snapshot, ig)["segments"]:
        by_file.setdefault(s["file"], []).append(s)
    assert by_file["input/pagecontent/index.md"][0]["kind"] == "glossary"
    assert by_file["input/pagecontent/glossary.md"][0]["change_class"] == HISTORICAL


def test_main_prints_one_line_per_exclusion_reason(run, capsys):
    gx.main(["--run", str(run)])
    assert "excluded, by reason" not in capsys.readouterr().out    # nothing excluded, nothing listed
    snap = run / "snapshot"
    for name in ("draft.md", "old.md"):
        _write(snap, f"input/pagecontent/{name}", "Unpublished.\n")
    _write(snap, "input/notes.bin", "??")
    _write(snap, "input/images/A.png", "binary")
    _write(snap, "input/images/B.png", "binary")
    _write(snap, "input/pagecontent/changehistory.md", '{% include img.html img="A.png" %}\n')
    _write(snap, "input/pagecontent/glossary.md", '{% include img.html img="B.png" %}\n| T | D |\n| --- | --- |\n')
    gx.main(["--run", str(run)])
    lines = capsys.readouterr().out.splitlines()
    assert "excluded, by reason:" in lines
    assert "     2  not published (absent from sushi-config pages; 404 when published)" in lines
    assert "     2  raster image — needs visual read" in lines     # grouped, whichever pages refer to them
    assert "     1  unrecognized file type — review" in lines
