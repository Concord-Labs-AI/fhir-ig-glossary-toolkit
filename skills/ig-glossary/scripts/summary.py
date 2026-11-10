"""Build the thematic summary report as HTML."""
import argparse
import html
import json
from collections import Counter, defaultdict

import config
from common import ATTRIBUTION, read_jsonl
from merge import THEME_FORM

SIZE_RULE = "S: a short session (under 25 edits in up to 3 files); M: up to about 100 edits or 10 files; L: larger, best done in bulk by rule."


def form_theme(legend_examples):
    examples = f" (for example {', '.join(repr(x) for x in legend_examples)})" if legend_examples else ""
    return {"id": THEME_FORM, "title": "Form & presentation",
            "convention": f"The glossary fixes each term's case, hyphenation and acronym{examples}. This theme "
                          "applies that form wherever the guide's running text uses a glossary term, and spells each "
                          "acronym out at its first use on a page. Headings, titles and table headers keep the "
                          "guide's own capitalisation.",
            "alignment_work": "Mechanical, low-risk edits that can be accepted by rule. Rows that repeat the same "
                              "edit can be accepted or declined together.",
            "work_package": "WP-Form Mechanical consistency pass", "size": "", "depends_on": []}


def e(s):
    return html.escape(str(s))


def count(n, word):
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


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


def build_html(doc, book, themes, counts, coverage, cfg):
    ig, sm = cfg["ig"], cfg["summary"]
    rows = doc["rows"]
    ready = [r for r in rows if r["status"] == "Ready"]
    pending = [r for r in rows if r["status"].startswith("Pending")]
    ident_rows = [r for r in rows if r["change_class"] == "Identifier"]
    rec_change = [r for r in pending if r["recommended"] == "change"]
    glossary_rows = [r for r in rows if r["apply_method"] == "Glossary entry edit"]
    decisions = book.get("decisions", [])
    ident_decision = book.get("identifier_decision")
    n_terms = sum(1 for t in book["terms"] if t.get("glossary_term"))
    by_theme = defaultdict(list)
    for r in rows:
        by_theme[r["theme_id"]].append(r)
    known = {t["id"] for t in themes} | {THEME_FORM}
    extra = [{"id": tid, "title": rs[0]["theme"], "glossary_says": "", "alignment_work": "", "work_package": "",
              "size": "", "depends_on": []} for tid, rs in by_theme.items() if tid not in known]
    all_themes = [{**t, "size": t.get("size") or size_for(by_theme[t["id"]])}
                  for t in themes + extra + [form_theme(sm["legend_examples"])] if by_theme[t["id"]]]
    snapshot = e(doc["meta"]["snapshot"])
    title = f"Glossary alignment: {ig['name']} {ig['tag']}"
    repeated = Counter((r["find"], r["replace"]) for r in rows).most_common(1)
    repeat_note = (f" ({repeated[0][1]} rows are the identical '{e(repeated[0][0][0])}' → '{e(repeated[0][0][1])}' edit)"
                   if repeated and repeated[0][1] >= 10 else "")
    intro = e(sm["intro"]) if sm["intro"] else (
        f"This report checks every sentence of the published guide (tag {snapshot}) against its {n_terms} glossary "
        "terms and shows, theme by theme, where the wording departs from the glossary and what the alignment work "
        "is. The companion workbook lists every finding as an exact edit for review.")
    p = [f"<h1>{e(title)}: findings and work plan</h1>", f"<p>{intro}</p>",
         "<h2>How to read this report</h2>",
         "<p>Each <b>finding</b> is one place in the guide where the wording differs from the glossary, with the exact "
         "text to find and the text to put in its place. Counts are occurrences: a sentence repeated in four "
         f"artifacts counts four times{repeat_note}. The review is about wording, not about whether the glossary "
         "definitions are right; where the two pull apart, that is a decision for the team (the decisions below).</p>",
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
               + [(f"Confidence: {c}", n) for c, n in Counter(r["confidence"] for r in rows).most_common()])]
    if ident_rows:
        pending = f"counted among the pending rows (decision {e(ident_decision)}) and are " if ident_decision else ""
        p.append(f"<p><i>The {len(ident_rows)} Identifier rows are artifact names; they are {pending}reported, "
                 "not edited.</i></p>")
    if decisions:
        gated = Counter(r["decision"] for r in rows if r["decision"])
        zero = [d["id"] for d in decisions if not gated[d["id"]]]
        zero_note = (f" No workbook rows wait on {count(len(zero), 'decision')} ({e(', '.join(zero))}): a decision like "
                     "that changes the glossary itself (a note, a definition, a new entry) or adds links, and the "
                     "work-package table lists it where a package depends on it." if zero else "")
        p += ["<h2>Decisions needed first</h2>",
              f"<p>The team has {count(len(decisions), 'decision')} to take; taking a decision settles all of its "
              f"pending rows at once.{zero_note} The recommended option is in bold.</p>",
              table(["ID", "Decision", "Rows", "Question", "Options"],
                    [(d["id"], d.get("title", ""), gated[d["id"]], " ".join(str(d.get("question", "")).split()), options(d))
                     for d in decisions], widths=["6%", "15%", "7%", "32%", "40%"])]
    decisions_ask = (f"<li><b>Take the {count(len(decisions), 'decision')} above.</b> A decision settles its pending "
                     "rows in one go; the rows are regenerated under the chosen option, so nobody reviews them "
                     "twice.</li>" if decisions else "")
    glossary_ask = (f"<li><b>Route the glossary edits to the glossary owner first.</b> The workbook has "
                    f"{count(len(glossary_rows), 'row')} on the glossary page itself, and the glossary owner's sign-off "
                    "comes before anything else.</li>" if glossary_rows else "")
    owners = ("who decides each decision and by when, and who reviews which themes" if decisions
              else "who reviews which themes, and by when")
    p += ["<h2>What we need from you</h2>",
          "<ol>"
          f"{decisions_ask}"
          "<li><b>Review the Ready rows in the workbook.</b> Work page by page (the workbook is sorted that way), "
          "because a page's High and Medium rows sit in the same sentences. Mark each row Accept, Modify (with your "
          "replacement text), Reject or Defer. Repeated edits can be accepted together.</li>"
          f"{glossary_ask}"
          "</ol>"
          "<p><b>What happens next.</b> Accepted rows are applied to the source by script, the guide is rebuilt, "
          "and any row whose original text has since changed is reported back for a person to look at rather than "
          f"guessed. <i>[Owners and dates: {owners}.]</i></p>",
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
          table(["Page / artifact", "Findings"], Counter(r["page"] for r in rows).most_common(12))]
    p.append("<h2>Names kept as they are</h2>")
    idents = sorted({r["page"] for r in rows if r["change_class"] == "Identifier"})
    cite = f" (decision {e(ident_decision)})" if ident_decision else ""
    p.append(f"<p>{len(idents)} artifact names or ids embed retired or non-glossary wording and are not renamed, "
             f"because renaming breaks implementers{cite}: {e(', '.join(idents)) or 'none'}."
             f"{' ' + e(sm['names_kept_note']) if sm['names_kept_note'] else ''}</p>")
    locked = Counter()
    for c in counts.values():
        if c["type"] != "canonical":
            for cls in ("External", "Historical"):
                locked[cls] += c["by_class"].get(cls, 0)
    examples_txt = e(sm["locked_examples"]) if sm["locked_examples"] else \
        "code displays from other terminologies, quoted instrument names and text inherited from dependencies"
    p.append(f"<p>Also left alone by design: external text such as {examples_txt}, and the historical change-log "
             f"pages ({locked['Historical']} pattern matches there).</p>")
    if sm["outside_workbook"]:
        p += ["<h2>Outside the workbook</h2>",
              "<p>The review also found things no workbook row can express. Each needs a hand edit in the same pass or "
              "its own ticket.</p>",
              "<ul>" + "".join(f"<li><b>{e(x['where'])}.</b> {e(x['what'])}</li>" for x in sm["outside_workbook"]) + "</ul>"]
    build_note = (" " + e(sm["build_note"])) if sm["build_note"] else ""
    p += ["<h2>Method and limits</h2>",
          f"<p>Every reader-visible piece of text in the {snapshot} source was extracted ({coverage['segments']} "
          f"text segments from {coverage['files_extracted']} files; {coverage['files_excluded']} files were excluded "
          "with recorded reasons, such as unpublished pages and unreferenced images). Pattern matching over the "
          "glossary terms flagged candidates; AI-assisted review passes judged each candidate in context and added "
          "paraphrases the patterns could not catch; a second, independent pass tried to disprove the judgment calls; "
          f"and a final editorial pass checked every ready row and the decision tagging.{build_note} The workbook "
          "review is the human check: nothing changes in the guide until a person accepts the row. "
          f"Not covered: text the publishing tool generates that is not in the source. {e(ATTRIBUTION)}</p>"]
    return (f"<html><head><meta charset='utf-8'><title>{e(title)}</title></head><body>" + "".join(p) + "</body></html>")


def main(argv=None):
    ap = config.add_run_arg(argparse.ArgumentParser(description=__doc__))
    args = ap.parse_args(argv)
    cfg = config.load(args.run)
    data = cfg["data"]
    doc = json.loads((data / "findings.json").read_text(encoding="utf-8"))
    book = config.rulebook(cfg)
    themes = config.themes(cfg)
    counts = json.loads((data / "counts.json").read_text(encoding="utf-8"))
    cov = json.loads((data / "coverage.json").read_text(encoding="utf-8"))
    coverage = {"files_extracted": sum(c["status"] == "extracted" for c in cov.values()),
                "files_excluded": sum(c["status"] == "excluded" for c in cov.values()),
                "segments": len(read_jsonl(data / "segments.jsonl"))}
    cfg["build"].mkdir(exist_ok=True)
    path = config.summary_path(cfg)
    path.write_text(build_html(doc, book, themes, counts, coverage, cfg), encoding="utf-8")
    print(f"{path} ({path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
