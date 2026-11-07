"""Build the detailed review workbook (xlsx; uploaded and converted to a Google Sheet)."""
import argparse
import json
from collections import Counter, defaultdict

import yaml
from openpyxl import Workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from common import BUILD, DATA, HERE

WORKBOOK = BUILD / "Gravity-STU3.1-Glossary-Alignment-Detailed.xlsx"
FINDING_COLUMNS = [  # (header, row key, width) — all locked
    ("ID", "id", 10), ("Theme", "theme", 20), ("Terms", "terms", 20), ("Type", "type", 11),
    ("Rule", "rule", 15), ("Page / artifact", "page", 24), ("Section", "section", 24),
    ("Source file", "file", 28), ("Line @3.0.0", "line", 7), ("Occurrence #", "occurrence", 7),
    ("Published link", "url", 26), ("Context (as read)", "context", 60), ("Issue", "issue", 40),
    ("Source find (exact)", "find", 30), ("Suggested replace", "replace", 30),
    ("Change class", "change_class", 12), ("Apply method", "apply_method", 15),
    ("Confidence", "confidence", 10), ("Status", "status", 13), ("Depends on", "decision", 9),
    ("Under recommended option", "recommended", 14),
]
REVIEW_COLUMNS = [("Review", 12), ("Reviewer's replace", 34), ("Reviewer notes", 34)]
REVIEW_CHOICES = ["Accept", "Modify", "Reject", "Defer"]
RECOMMENDED_LABELS = {None: "", "": "", "change": "still changes", "keep": "left as written"}
COLUMN_HELP = {
    "Context (as read)": "The sentence as readers see it on hl7.org (markup removed).",
    "Source find (exact)": "The exact source text that will be replaced. Don't edit.",
    "Suggested replace": "What Accept will put in place of 'Source find'.",
    "Line @3.0.0": "Line in the published 3.0.0 source (edits locate by text, not line).",
    "Occurrence #": "Which occurrence of 'Source find' in the file this row means.",
    "Change class": "Prose / Artifact text / Diagram are editable; Identifier / External / Historical are locked.",
    "Apply method": "Text replace / Diagram source + re-render / Glossary entry edit are applied automatically; Manual is reported only.",
    "Status": "Ready, or Pending D-n — waits on that team decision (Decisions tab).",
    "Depends on": "The team decision (D-n) this row waits on; blank for Ready rows. Filter here to see one decision's rows.",
    "Under recommended option": "For pending rows: 'still changes' if the edit is still needed under the recommended "
                                "option, 'left as written' if that option keeps the text as it is.",
    "Review": "Accept · Modify · Reject · Defer (dropdown).",
    "Reviewer's replace": "Required for Modify: your text replaces the whole 'Source find'.",
}
GREY = PatternFill("solid", fgColor="EEEEEE")
YELLOW = PatternFill("solid", fgColor="FFF4CC")
RED = PatternFill("solid", fgColor="F4B6B6")
BOLD = Font(bold=True)
WRAP = Alignment(wrap_text=True, vertical="top")
REVIEW_COL = get_column_letter(len(FINDING_COLUMNS) + 1)
REPLACE_COL = get_column_letter(len(FINDING_COLUMNS) + 2)


def locked_value(row, key):
    """The text a locked column shows for a row (the round-trip check compares against the same function)."""
    if key == "recommended":
        if row["recommended"] not in RECOMMENDED_LABELS:
            raise ValueError(f"{row['id']}: unknown recommended value {row['recommended']!r}")
        return RECOMMENDED_LABELS[row["recommended"]]
    return row[key]


def set_text(cell, value):
    """Write a value; strings stay strings even when they start with = + - @."""
    cell.value = "" if value is None else value
    if isinstance(cell.value, str):
        cell.data_type = "s"


def header(ws, names, fills):
    for c, (name, fill) in enumerate(zip(names, fills), 1):
        cell = ws.cell(row=1, column=c, value=name)
        cell.font, cell.fill = BOLD, fill
    ws.freeze_panes = "A2"


def readme_sheet(wb, rows, meta):
    ws = wb.active
    ws.title = "README"
    last = len(rows) + 1
    lines = [
        ("Gravity SDOH Clinical Care IG — glossary alignment, detailed findings", ""),
        ("Snapshot", f"IG tag {meta['snapshot']} — the published STU 3 guide"),
        ("Findings", len(rows)),
        ("Unreviewed rows", f"=COUNTBLANK(Findings!{REVIEW_COL}2:{REVIEW_COL}{last})"),
        ("Modify rows missing a replacement",
         f'=COUNTIFS(Findings!{REVIEW_COL}2:{REVIEW_COL}{last},"Modify",Findings!{REPLACE_COL}2:{REPLACE_COL}{last},"")'),
        ("", ""),
        ("How to review", ""),
        ("1", "Work in the Findings tab. Edit ONLY the three yellow columns: Review, Reviewer's replace, Reviewer notes."),
        ("2", "Accept = apply the Suggested replace as written. Modify = apply YOUR text from Reviewer's replace "
              "instead; it replaces the whole Source find. Reject = no change. Defer = decide later."),
        ("3", "Grey columns are locked. The workbook is checked against the master copy when it comes back, so "
              "don't edit them. Sorting and filtering are fine; don't delete rows (use Reject)."),
        ("4", "Rows with Status 'Pending D-n' depend on a team decision listed on the Decisions tab. Filter the "
              "'Depends on' column to see one decision's rows. Their suggestions follow the glossary strictly; "
              "'Under recommended option' says whether the edit survives the recommended option. The Decision x "
              "theme tab shows which themes each decision touches."),
        ("5", "Use Published link to see the text in context on hl7.org."),
        ("6", "Spotted something the analysis missed? Add it on the Reviewer additions tab."),
        ("", ""),
        ("Columns", ""),
    ] + [(name, COLUMN_HELP.get(name, "")) for name, _, _ in FINDING_COLUMNS + [(n, None, None) for n, _ in REVIEW_COLUMNS]]
    for r, (a, b) in enumerate(lines, 1):
        ws.cell(row=r, column=1, value=a).font = BOLD
        ws.cell(row=r, column=2, value=b).alignment = WRAP
    ws.column_dimensions["A"].width, ws.column_dimensions["B"].width = 34, 110


def findings_sheet(wb, rows):
    ws = wb.create_sheet("Findings")
    names = [h for h, _, _ in FINDING_COLUMNS] + [h for h, _ in REVIEW_COLUMNS]
    header(ws, names, [GREY] * len(FINDING_COLUMNS) + [YELLOW] * len(REVIEW_COLUMNS))
    for r, row in enumerate(rows, 2):
        for c, (_, key, _) in enumerate(FINDING_COLUMNS, 1):
            cell = ws.cell(row=r, column=c)
            set_text(cell, locked_value(row, key))
            cell.fill, cell.alignment = GREY, WRAP
            if key == "url" and row[key]:
                cell.hyperlink = row[key]
        for c in range(len(FINDING_COLUMNS) + 1, len(names) + 1):
            cell = ws.cell(row=r, column=c)
            cell.fill, cell.alignment = YELLOW, WRAP
    for c, width in enumerate([w for _, _, w in FINDING_COLUMNS] + [w for _, w in REVIEW_COLUMNS], 1):
        ws.column_dimensions[get_column_letter(c)].width = width
    last = len(rows) + 1
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(names))}{last}"
    dv = DataValidation(type="list", formula1='"' + ",".join(REVIEW_CHOICES) + '"', allow_blank=True,
                        showErrorMessage=True, errorTitle="Review", error="Choose Accept, Modify, Reject or Defer.")
    ws.add_data_validation(dv)
    dv.add(f"{REVIEW_COL}2:{REVIEW_COL}{last}")
    ws.conditional_formatting.add(f"{REPLACE_COL}2:{REPLACE_COL}{last}", FormulaRule(
        formula=[f'AND(${REVIEW_COL}2="Modify",LEN(${REPLACE_COL}2)=0)'], fill=RED))


def decisions_sheet(wb, rows, book):
    ws = wb.create_sheet("Decisions")
    names = ["ID", "Decision", "Question", "Options", "Recommendation", "Rows",
             "Still change under the recommendation", "Left as written under it", "Team decision", "Team notes"]
    header(ws, names, [GREY] * 8 + [YELLOW] * 2)
    gated = Counter(r["decision"] for r in rows if r["decision"])
    change = Counter(r["decision"] for r in rows if r["decision"] and r["recommended"] == "change")
    for r, d in enumerate(book["decisions"], 2):
        n = gated[d["id"]]
        values = [d["id"], d.get("title", ""), d.get("question", ""), "\n".join(d.get("options", [])),
                  d.get("recommendation", ""), n, change[d["id"]], n - change[d["id"]]]
        for c, v in enumerate(values, 1):
            cell = ws.cell(row=r, column=c)
            set_text(cell, v)
            cell.fill, cell.alignment = GREY, WRAP
        for c in (9, 10):
            ws.cell(row=r, column=c).fill = YELLOW
    dv = DataValidation(type="list", formula1='"A,B,C,Other"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"I2:I{len(book['decisions']) + 1}")
    for c, width in enumerate([7, 26, 60, 60, 50, 7, 12, 12, 12, 40], 1):
        ws.column_dimensions[get_column_letter(c)].width = width


def decision_theme_sheet(wb, rows, book):
    """Which themes each decision touches, so a decision's owner knows whose pages it settles."""
    ws = wb.create_sheet("Decision x theme")
    themes = list(dict.fromkeys(r["theme"] for r in rows))
    header(ws, ["Decision"] + themes + ["Total"], [GREY] * (len(themes) + 2))
    grid = defaultdict(Counter)
    for r in rows:
        if r["decision"]:
            grid[r["decision"]][r["theme"]] += 1
    for i, d in enumerate([d["id"] for d in book["decisions"] if d["id"] in grid], 2):
        values = [d] + [grid[d][t] for t in themes] + [sum(grid[d].values())]
        for c, v in enumerate(values, 1):
            set_text(ws.cell(row=i, column=c), v)
    ws.column_dimensions["A"].width = 10


def coverage_sheet(wb, rows, book, counts):
    ws = wb.create_sheet("Term coverage")
    names = ["Glossary term", "Uses in editable text", "Missed uses", "Misuses", "Form", "Locked mentions",
             "Pages with findings"]
    header(ws, names, [GREY] * len(names))
    by_term, pages = defaultdict(Counter), defaultdict(set)
    for r in rows:
        for t in r["terms"].split("; "):
            by_term[t][r["type"]] += 1
            pages[t].add(r["page"])
    r = 2
    for t in book["terms"]:
        name = t.get("glossary_term")
        if not name:
            continue
        mine = [c for c in counts.values() if c["term_id"] == t["id"]]
        uses = sum(c["editable"] for c in mine if c["type"] == "canonical")
        locked = sum(c["total"] - c["editable"] for c in mine)
        b = by_term[name]
        for c, v in enumerate([name, uses, b["Missed use"], b["Misuse"], b["Form"], locked, len(pages[name])], 1):
            set_text(ws.cell(row=r, column=c), v)
        r += 1
    ws.column_dimensions["A"].width = 44


def page_theme_sheet(wb, rows):
    ws = wb.create_sheet("Page x theme")
    themes = list(dict.fromkeys(r["theme"] for r in rows))
    header(ws, ["Page / artifact"] + themes + ["Total"], [GREY] * (len(themes) + 2))
    grid = defaultdict(Counter)
    for r in rows:
        grid[r["page"]][r["theme"]] += 1
    ordered = sorted(grid, key=lambda p: -sum(grid[p].values()))
    for i, page in enumerate(ordered, 2):
        values = [page] + [grid[page][t] for t in themes] + [sum(grid[page].values())]
        for c, v in enumerate(values, 1):
            set_text(ws.cell(row=i, column=c), v)
    ws.column_dimensions["A"].width = 44


def additions_sheet(wb):
    ws = wb.create_sheet("Reviewer additions")
    names = ["Page or link", "Current text", "Proposed text", "Notes", "Added by"]
    header(ws, names, [YELLOW] * len(names))
    for c, width in enumerate([40, 50, 50, 40, 16], 1):
        ws.column_dimensions[get_column_letter(c)].width = width


def meta_sheet(wb, meta):
    ws = wb.create_sheet("_meta")
    for r, (k, v) in enumerate([("snapshot", meta["snapshot"]), ("rulebook", meta["rulebook"]),
                                ("generated", meta["generated"]), ("rows", meta["rows"]),
                                ("findings_sha256", meta["sha256"])], 1):
        ws.cell(row=r, column=1, value=k)
        set_text(ws.cell(row=r, column=2), v)
    ws.sheet_state = "hidden"


def build(doc, book, counts):
    wb = Workbook()
    rows = doc["rows"]
    readme_sheet(wb, rows, doc["meta"])
    findings_sheet(wb, rows)
    decisions_sheet(wb, rows, book)
    decision_theme_sheet(wb, rows, book)
    coverage_sheet(wb, rows, book, counts)
    page_theme_sheet(wb, rows)
    additions_sheet(wb)
    meta_sheet(wb, doc["meta"])
    return wb


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args(argv)
    doc = json.loads((DATA / "findings.json").read_text(encoding="utf-8"))
    book = yaml.safe_load((HERE / "rulebook.yaml").read_text(encoding="utf-8"))
    counts = json.loads((DATA / "counts.json").read_text(encoding="utf-8"))
    BUILD.mkdir(exist_ok=True)
    build(doc, book, counts).save(WORKBOOK)
    print(f"{WORKBOOK} — {len(doc['rows'])} findings")


if __name__ == "__main__":
    main()
