"""Deterministic findings: spell an acronym out at its first body use on each page."""
import re
from collections import defaultdict

from findings import make_record, positions

ACRONYMS = {"CBO": ("community-based organization", "T-CBO"),
            "CP": ("coordination platform", "T-CP"),
            "EHR": ("electronic health record", "T-EHR"),
            "SCN": ("social care network", "T-SCN"),
            "SDOH": ("social determinants of health", "T-SDOH")}
BODY_FIELDS = {"paragraph", "list-item", "table-row"}
# An acronym inside a name ("SDOH Clinical Care", the "SDOH Category" value set, the term "SDOH domain"), a hyphenated compound
# ("SDOH-related"), a quoted code value or a possessive isn't spelled out; the first standalone use is.
NOT_STANDALONE = r"(?![-\u2010\u2011”\"']|’|\s+(?:Clinical Care|Category|[Dd]omains?)\b)"
NOT_QUOTED = r"(?<![“\"'‘])"
AN_BEFORE = re.compile(r"\b([Aa]n) $")
SENTENCE_START = re.compile(r"(?:^|[.!?]\s+|^\s*(?:[-*+]|\d+\.)\s+)$")


def acronym_findings(segments, corpus):
    pages = defaultdict(list)
    for s in segments:
        if s["kind"] == "page" and s["change_class"] == "Prose":
            pages[s["file"]].append(s)
    out = []
    for file in sorted(pages):
        segs = sorted(pages[file], key=lambda s: s["start"])
        raw = corpus.text(file)
        for acr, (long, term) in ACRONYMS.items():
            acr_rx = re.compile(rf"{NOT_QUOTED}\b{acr}s?\b{NOT_STANDALONE}")
            long_rx = re.compile(r"[\s-]+".join(map(re.escape, re.split(r"[\s-]", long))), re.I)
            for s in segs:
                a, spelled = acr_rx.search(s["visible"]), long_rx.search(s["visible"])
                if spelled and (not a or spelled.start() < a.start()):
                    break
                if not a or s["field"] not in BODY_FIELDS:
                    continue
                find = a.group(0)
                start = s["start"] + a.start()
                replace = f"{long}s ({find})" if find != acr else f"{long} ({acr})"
                an = AN_BEFORE.search(s["visible"], 0, a.start())
                if an and long[0] not in "aeiou":  # "an SDOH" -> "a social determinants of health (SDOH)"
                    find, start = f"{an.group(1)} {find}", start - len(an.group(0))
                    replace = f"{an.group(1)[0]} {replace}"
                elif SENTENCE_START.search(s["visible"], 0, a.start()):
                    replace = replace[0].upper() + replace[1:]
                pos = positions(raw, find)
                out.append(make_record(s, s["line"], start, start + len(find), find, replace,
                                       pos.index(start) + 1, len(pos), terms=[term], type="Form",
                                       rule=f"R-ACRONYM-{acr}", issue=f"First use of {acr} on this page; spell it out.",
                                       confidence="High", decision=None, recommended=None, hits=[], source="script"))
                break
    return out
