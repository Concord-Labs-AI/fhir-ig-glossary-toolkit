"""Build the thematic summary as HTML (uploaded to Drive, which converts it to a Google Doc)."""
import argparse
import html
import json
from collections import Counter, defaultdict

import yaml

from common import BUILD, DATA, HERE, read_jsonl
from merge import THEME_FORM

SUMMARY = BUILD / "glossary-alignment-summary.html"
FORM_THEME = {"id": THEME_FORM, "title": "Form & presentation",
              "convention": "The glossary writes each term in sentence case with its hyphenation and acronym fixed "
                            "(for example 'Community-based organization (CBO)', 'Social determinants of health (SDOH)'). "
                            "This theme applies that form wherever the guide's running text uses a glossary term, and "
                            "spells each acronym out at its first use on a page. Headings, titles and table headers keep "
                            "the guide's Title Case.",
              "alignment_work": "Mechanical, low-risk edits that can be accepted by rule. One group is a single style "
                                "decision rather than many: the bold actor labels on the capacity and workflow pages "
                                "('**Referral Source**' → '**referral source**', 16 rows) should be accepted or declined "
                                "together, since the same pages' role tables and step titles stay in Title Case.",
              "work_package": "WP-Form Mechanical consistency pass", "size": "", "depends_on": []}
SIZE_RULE = "S: a short session (under 25 edits in up to 3 files); M: up to about 100 edits or 10 files; L: larger, best done in bulk by rule."
# Things the review found that no workbook row can express: they need a hand edit or their own ticket.
OUTSIDE_WORKBOOK = [
    ("sushi-config.yaml, lines 87–88", "The guide's description wraps 'Social Determinants / of Health' over two lines, so its Title Case "
     "cannot be fixed as a single edit; change it by hand in the same pass."),
    ("index.md, the note box at lines 16–21", "Under D-6 option A the whole note needs a rewrite (it currently defers broader "
     "adoption of 'social service organization' to a future version); only its first sentence has a row."),
    ("Subtask examples (Task.owner)", "Both subreferral example Tasks say the Task passes to a community organization, but each "
     "Task.owner points at 'Better Health Clinic'. An example-data bug, not a glossary issue; worth its own ticket."),
    ("SDOHCC-ReferralRecipient CapabilityStatement, purpose text", "The \"'Light' Referral Recipients\" link points at the regular "
     "Referral Recipient CapabilityStatement instead of the Light one (pre-existing)."),
    ("self_referral.md, conformance box 'refer-7'", "The box's summary attribute says 'Community Resource Platform'; it is not "
     "reader-visible text, so it has no row, but it should follow the page's rename."),
    ("self_referral.md, 'closed, open, and hybrid systems'", "The bold cross-reference has no link; "
     "'capacity.html#system-environments' would resolve it."),
]


def e(s):
    return html.escape(str(s))


def size_for(rows):
    """S: under 25 rows in 1-3 files; M: 25-100 rows or 4-10 files; L: anything larger."""
    n, files = len(rows), len({r["file"] for r in rows})
    if n < 25 and files <= 3:
        return "S"
    return "M" if n <= 100 or files <= 10 else "L"


class Markup(str):
    """A table cell that is already HTML, so table() doesn't escape it."""


def table(headers, rows, widths=None):
    """widths: optional per-column CSS widths; Docs keeps them on import, so long text columns can be made wide."""
    head = "".join(f"<th style='width:{w}'>{e(h)}</th>" if w else f"<th>{e(h)}</th>"
                   for h, w in zip(headers, widths or [None] * len(headers)))
    body = "".join("<tr>" + "".join(f"<td>{c if isinstance(c, Markup) else e(c)}</td>" for c in r) + "</tr>"
                   for r in rows)
    return f"<table border='1' cellpadding='4'><tr>{head}</tr>{body}</table>"


def options(d):
    """Every option as its own paragraph (Docs drops <br> inside cells), the recommended one in bold."""
    letter = d.get("recommendation", "").partition(" — ")[0].strip()
    if letter and letter not in {o.split(":", 1)[0].strip() for o in d.get("options", [])}:
        raise ValueError(f"{d['id']}: recommendation {letter!r} names none of its options")
    out = []
    for o in d.get("options", []):
        lab, _, text = o.partition(":")
        cell = f"{e(lab.strip())}: {e(text.strip())}"
        out.append(f"<p><b>{cell}</b></p>" if lab.strip() == letter else f"<p>{cell}</p>")
    why = d.get("recommendation", "").partition(" — ")[2].strip()
    return Markup("".join(out) + (f"<p><i>Recommended: {e(letter)} — {e(why)}</i></p>" if why else ""))


def is_case_or_hyphen_fix(r):
    norm = lambda s: s.lower().replace("-", " ")
    return norm(r["find"]) == norm(r["replace"])


def examples(rows, k=3):
    """Three clear rows from different files: High confidence and Ready first; for Form rows, pure case/hyphen fixes first."""
    picked, files = [], set()
    for r in sorted(rows, key=lambda r: (r["confidence"] != "High", r["status"] != "Ready",
                                         r["type"] == "Form" and not is_case_or_hyphen_fix(r), r["id"])):
        if r["file"] not in files and r["replace"]:
            picked.append(r)
            files.add(r["file"])
        if len(picked) == k:
            break
    return picked


def build_html(doc, book, themes, counts, coverage):
    rows = doc["rows"]
    ready = [r for r in rows if r["status"] == "Ready"]
    pending = [r for r in rows if r["status"].startswith("Pending")]
    manual = [r for r in rows if r["apply_method"] == "Manual"]
    rec_change = [r for r in pending if r["recommended"] == "change"]
    by_theme = defaultdict(list)
    for r in rows:
        by_theme[r["theme_id"]].append(r)
    known = {t["id"] for t in themes} | {THEME_FORM}
    extra = [{"id": tid, "title": rs[0]["theme"], "glossary_says": "", "alignment_work": "", "work_package": "",
              "size": "", "depends_on": []} for tid, rs in by_theme.items() if tid not in known]
    all_themes = [{**t, "size": t.get("size") or size_for(by_theme[t["id"]])}
                  for t in themes + extra + [FORM_THEME] if by_theme[t["id"]]]
    snapshot = e(doc["meta"]["snapshot"])
    p = ["<h1>Glossary alignment: STU 3.0 findings and the STU 3.1 work plan</h1>",
         f"<p>STU 3.0 revised the glossary and, in the note on its home page, deferred carrying the new terms through the "
         f"rest of the guide to a later version. This report checks every sentence of the published STU 3.0 guide "
         f"(tag {snapshot}) against the 31 glossary terms and shows, theme by theme, where the wording departs from the "
         "glossary and what the STU 3.1 alignment work is. The companion workbook lists every finding as an exact edit "
         "for review.</p>",
         "<h2>How to read this report</h2>",
         "<p>Each <b>finding</b> is one place in the guide where the wording differs from the glossary, with the exact "
         "text to find and the text to put in its place. Counts are occurrences: a sentence repeated in four "
         "CapabilityStatements counts four times (68 rows are the identical 'referral recipients' → 'referral targets' "
         "edit). The review is about wording, not about whether the glossary definitions are right; where the two "
         "pull apart, that is a decision for the team (D-1 to D-13 below).</p>",
         "<ul>"
         "<li><b>Type.</b> <i>Missed use</i>: the guide says something else where a glossary term applies. "
         "<i>Misuse</i>: a glossary term is used against its definition. <i>Form</i>: the right term in the wrong "
         "form (capitalization, hyphenation, an acronym not spelled out).</li>"
         "<li><b>Status.</b> <i>Ready</i>: can be reviewed now; the edit is the same whatever the team decides. "
         "<i>Pending D-n</i>: the edit depends on decision D-n; the row shows the strict-glossary edit and records "
         "whether the recommended option would still make it. Pending rows are not errors.</li>"
         "<li><b>Confidence.</b> <i>High</i>: clear-cut from the glossary text. <i>Medium</i>: needs a reviewer's "
         "judgment.</li>"
         "<li><b>Change class.</b> <i>Prose</i>: page text. <i>Artifact text</i>: descriptions and documentation "
         "inside profiles, CapabilityStatements, code systems and examples. <i>Diagram</i>: workflow-diagram source, "
         "re-rendered at build time. <i>Identifier</i>: an artifact's name or id; reported, never changed "
         "automatically.</li>"
         f"<li><b>Work-package size.</b> {e(SIZE_RULE)}</li>"
         "</ul>",
         "<h2>Headline numbers</h2>",
         table(["Measure", "Count"],
               [("Findings", len(rows)), ("Ready to review now", len(ready)),
                ("Pending a team decision", len(pending)),
                ("If the recommended option is taken on every decision: edits that go ahead", len(ready) + len(rec_change)),
                ("… and pending rows left as written", len(pending) - len(rec_change)),
                ("Pages and artifacts with findings", len({r["page"] for r in rows}))]
               + [(f"Type: {t}", n) for t, n in Counter(r["type"] for r in rows).most_common()]
               + [(f"Change class: {c}", n) for c, n in Counter(r["change_class"] for r in rows).most_common()]
               + [(f"Confidence: {c}", n) for c, n in Counter(r["confidence"] for r in rows).most_common()]),
         f"<p><i>The {len(manual)} Identifier rows are artifact names; they are counted among the pending rows "
         "(decision D-10) and are reported, not edited.</i></p>",
         "<h2>Decisions needed first</h2>"]
    gated = Counter(r["decision"] for r in rows if r["decision"])
    zero = [d["id"] for d in book["decisions"] if not gated[d["id"]]]
    p.append("<p>These choices settle the pending findings; deciding one settles all its rows at once. "
             f"{len(zero)} decisions ({e(', '.join(zero))}) gate no workbook rows: they change the glossary itself "
             "(a note, a definition, a new entry) or add links, and the work-package table lists them where a package "
             "depends on them. The recommended option is in bold.</p>")
    p.append(table(["ID", "Decision", "Rows", "Question", "Options"],
                   [(d["id"], d.get("title", ""), gated[d["id"]], " ".join(str(d.get("question", "")).split()), options(d))
                    for d in book["decisions"]], widths=["6%", "15%", "7%", "32%", "40%"]))
    p += ["<h2>What we need from you</h2>",
          "<ol>"
          "<li><b>Take the thirteen decisions above.</b> Each one settles its pending rows in one go; the rows are "
          "regenerated under the chosen option, so nobody reviews them twice.</li>"
          "<li><b>Review the Ready rows in the workbook.</b> Work page by page (the workbook is sorted that way), "
          "because a page's High and Medium rows sit in the same sentences. Mark each row Accept, Modify (with your "
          "replacement text), Reject or Defer. Repeated edits can be accepted together.</li>"
          "<li><b>Route the glossary edits to the glossary owner first.</b> Eleven rows edit the glossary page, and six "
          "decisions would change entries; those need sign-off before anything else.</li>"
          "</ol>"
          "<p><b>What happens next.</b> Accepted rows are applied to the STU 3.1 source by script, the guide is rebuilt, "
          "and any row whose original text has since changed is reported back for a person to look at rather than "
          "guessed. <i>[Owners and dates: who decides D-1 to D-13 and by when, and who reviews which themes.]</i></p>",
          "<h2>Themes</h2>"]
    for t in all_themes:
        rs = by_theme[t["id"]]
        top = ", ".join(f"{pg} ({n})" for pg, n in Counter(r["page"] for r in rs).most_common(5))
        types = ", ".join(f"{n} {ty.lower()}" for ty, n in Counter(r["type"] for r in rs).most_common())
        waits = Counter(r["decision"] for r in rs if r["decision"])
        waiting = "; ".join(f"{n} on {d}" for d, n in waits.most_common()) or "none"
        p += [f"<h3>{e(t['title'])}</h3>"]
        if t.get("glossary_says"):
            p.append(f"<p><b>What the glossary says.</b> {e(t['glossary_says'])}</p>")
        if t.get("convention"):
            p.append(f"<p><b>Convention applied.</b> {e(t['convention'])}</p>")
        p.append(f"<p><b>What the guide does.</b> {len(rs)} findings ({e(types)}): "
                 f"{sum(r['status'] == 'Ready' for r in rs)} ready now, waiting on a decision: {e(waiting)}. "
                 f"Most affected: {e(top)}.</p>")
        p.append("<ul>" + "".join(f"<li>{e(r['page'])}: “{e(r['find'])}” → “{e(r['replace'])}” — {e(r['issue'])}</li>"
                                  for r in examples(rs)) + "</ul>")
        if t.get("alignment_work"):
            deps = ", ".join(t.get("depends_on") or []) or "none"
            p.append(f"<p><b>Alignment work.</b> {e(t['alignment_work'])} "
                     f"<i>({e(t.get('work_package', ''))}; size {e(t.get('size') or '—')}; depends on {e(deps)})</i></p>")
    packages = {}
    for t in all_themes:
        wp = packages.setdefault(t.get("work_package", ""), {"themes": [], "n": 0, "size": t.get("size", ""), "deps": []})
        wp["themes"].append(t["title"])
        wp["n"] += len(by_theme[t["id"]])
        wp["deps"] += [d for d in (t.get("depends_on") or []) if d not in wp["deps"]]
    p += ["<h2>Work packages</h2>",
          f"<p>Size: {e(SIZE_RULE)}</p>",
          table(["Work package", "Themes", "Findings", "Size", "Depends on"],
                [(wp, ", ".join(v["themes"]), v["n"], v["size"], ", ".join(v["deps"])) for wp, v in packages.items()]),
          "<p>Pages and artifacts with the most findings:</p>",
          table(["Page / artifact", "Findings"], Counter(r["page"] for r in rows).most_common(12)),
          "<h2>Names kept as they are</h2>"]
    idents = sorted({r["page"] for r in rows if r["change_class"] == "Identifier"})
    p.append(f"<p>{len(idents)} artifact names or ids embed retired or non-glossary wording and are not renamed in 3.1, "
             f"because renaming breaks implementers (decision D-10): {e(', '.join(idents)) or 'none'}. The SDOHCC "
             "Observation Screening Response profile keeps its name for the same reason (its description text is in "
             "the Assessment language theme).</p>")
    locked = Counter()
    for c in counts.values():
        if c["type"] != "canonical":
            for cls in ("External", "Historical"):
                locked[cls] += c["by_class"].get(cls, 0)
    p.append(f"<p>Also left alone by design: external text such as LOINC and SNOMED displays, quoted instrument names "
             f"and text inherited from US Core, and the historical change-log pages ({locked['Historical']} pattern "
             "matches there).</p>")
    p += ["<h2>Outside the workbook</h2>",
          "<p>The review also found things no workbook row can express. Each needs a hand edit in the same pass or "
          "its own ticket.</p>",
          "<ul>" + "".join(f"<li><b>{e(where)}.</b> {e(what)}</li>" for where, what in OUTSIDE_WORKBOOK) + "</ul>",
          "<h2>Method and limits</h2>",
          f"<p>Every reader-visible piece of text in the {snapshot} source was extracted ({coverage['segments']} "
          f"text segments from {coverage['files_extracted']} files; {coverage['files_excluded']} files were excluded "
          "with recorded reasons, such as unpublished pages and unreferenced images). Pattern matching over the "
          "glossary terms flagged candidates; AI-assisted review passes judged each candidate in context and added "
          "paraphrases the patterns could not catch; a second, independent pass re-checked the judgment calls and "
          "rejected about one in eight; and a final editorial pass checked every ready row and the decision tagging. "
          "Every suggested edit was then applied to a copy of the guide, which built with no new errors and one expected "
          "new warning: a changed artifact title must be registered in HL7's artifact list, which is part of the D-10 "
          "work. The workbook review is the human check: nothing changes in the guide until a person accepts the row. "
          "Not covered: text the publishing tool generates that is not in the source.</p>"]
    return ("<html><head><meta charset='utf-8'><title>Glossary alignment: STU 3.0 findings and the STU 3.1 work plan"
            "</title></head><body>" + "".join(p) + "</body></html>")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args(argv)
    doc = json.loads((DATA / "findings.json").read_text(encoding="utf-8"))
    book = yaml.safe_load((HERE / "rulebook.yaml").read_text(encoding="utf-8"))
    themes = yaml.safe_load((HERE / "themes.yaml").read_text(encoding="utf-8"))["themes"]
    counts = json.loads((DATA / "counts.json").read_text(encoding="utf-8"))
    cov = json.loads((DATA / "coverage.json").read_text(encoding="utf-8"))
    coverage = {"files_extracted": sum(c["status"] == "extracted" for c in cov.values()),
                "files_excluded": sum(c["status"] == "excluded" for c in cov.values()),
                "segments": len(read_jsonl(DATA / "segments.jsonl"))}
    BUILD.mkdir(exist_ok=True)
    SUMMARY.write_text(build_html(doc, book, themes, counts, coverage), encoding="utf-8")
    print(f"{SUMMARY} ({SUMMARY.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
