"""Extract every reader-visible piece of text from an IG snapshot.

Each source file is "masked": everything a reader never sees (comments, Liquid,
link URLs, FSH code, diagram directives) is overwritten with spaces, keeping
newlines, so the masked text has the same length as the source. Visible runs
become segments whose offsets point straight back into the raw file.
"""
import argparse
import json
import re
from bisect import bisect_right
from collections import Counter
from pathlib import Path

import yaml

import config
from common import (ARTIFACT, DIAGRAM, EXTERNAL, HISTORICAL, IDENTIFIER, PROSE, write_jsonl)

HEADING = re.compile(r"^(#{1,6})")


def blank(s):
    return re.sub(r"[^\n]", " ", s)


def collapse(s):
    return re.sub(r"\s+", " ", s).strip()


def mask(text, pattern, flags=0, keep=()):
    """Blank every match of pattern, leaving the numbered groups in keep visible."""
    def repl(m):
        out = list(blank(m.group(0)))
        for g in keep:
            if m.group(g) is not None:
                out[m.start(g) - m.start():m.end(g) - m.start()] = m.group(g)
        return "".join(out)
    return re.compile(pattern, flags).sub(repl, text)


class LineIndex:
    def __init__(self, text):
        self.starts = [0] + [m.end() for m in re.finditer("\n", text)]

    def line_col(self, offset):
        i = bisect_right(self.starts, offset) - 1
        return i + 1, offset - self.starts[i] + 1


def segment(rel, kind, change_class, field, section, artifact, url, raw, visible, start, end, idx, text=None):
    line, col = idx.line_col(start)
    vis = visible[start:end]
    return {"seg_id": f"{rel}:{line}:{col}", "file": rel, "kind": kind,
            "change_class": change_class, "field": field, "section": section,
            "artifact": artifact, "url": url, "line": line, "col": col,
            "start": start, "end": end, "raw": raw[start:end], "visible": vis,
            "text": collapse(vis) if text is None else text}


MD_MASKS = [
    (r"<!--.*?-->", re.S, ()),
    (r"^```.*?^```[^\n]*$", re.S | re.M, ()),
    (r"\{%-?\s*include\s+img[^%]*?caption=\"([^\"]*)\"[^%]*%\}", 0, (1,)),
    (r"\{%.*?%\}", re.S, ()),
    (r"\{\{.*?\}\}", re.S, ()),
    (r"\{[:#][^}\n]*\}", 0, ()),
    (r"!\[[^\]\n]*\]\([^)\n]*\)", 0, ()),
    (r"\[([^\]]*)\]\([^)\n]*\)", 0, (1,)),
    (r"\[([^\]\n]+)\]\[[^\]\n]*\]", 0, (1,)),
    (r"^[ \t]*\[[^\]\n]+\]:[^\n]*$", re.M, ()),
    (r"</?[A-Za-z][^>\n]*>", 0, ()),
    (r"https?://[^\s)|>\]\"]+", 0, ()),
    (r"^[ \t]*\|?[ \t]*:?-{3,}[-|: \t]*$", re.M, ()),
]


def mask_markdown(text):
    for pattern, flags, keep in MD_MASKS:
        text = mask(text, pattern, flags, keep)
    return text


def line_regions(raw, visible):
    """Yield (start, end, line_no) for each line whose visible run has a letter."""
    pos = 0
    for no, (rline, vline) in enumerate(zip(raw.split("\n"), visible.split("\n")), 1):
        if re.search(r"[A-Za-z]", vline):
            lead = len(vline) - len(vline.lstrip())
            yield pos + lead, pos + len(vline.rstrip()), no
        pos += len(rline) + 1


def md_field(raw_line):
    s = raw_line.lstrip()
    if s.startswith("#"):
        return "heading"
    if "include img" in s:
        return "caption"
    if s.startswith("|"):
        return "table-row"
    if re.match(r"([-*+]|\d+\.)\s", s):
        return "list-item"
    return "paragraph"


def page_url(name, base):
    stem = name[:-3]
    for suffix in ("-intro", "-notes"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
    return base + stem + ".html"


def extract_page(rel, raw, change_class=PROSE, kind="page", url=None):
    visible = mask_markdown(raw)
    idx = LineIndex(raw)
    lines = raw.split("\n")
    stack, segs = [], []
    for start, end, no in line_regions(raw, visible):
        field = md_field(lines[no - 1])
        if field == "heading":
            level = len(HEADING.match(lines[no - 1].lstrip()).group(1))
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, collapse(visible[start:end]).lstrip("#").strip()))
        section = " › ".join(t for _, t in stack)
        segs.append(segment(rel, kind, change_class, field, section, Path(rel).name, url,
                            raw, visible, start, end, idx))
    return segs


# ---- FSH -------------------------------------------------------------------
ENTITY = re.compile(r"^(Profile|Extension|Logical|Resource|ValueSet|CodeSystem|Instance|"
                    r"Invariant|RuleSet|Mapping|Alias)\s*:\s*(\S+)", re.M)
META = re.compile(r"^(Id|InstanceOf|Usage)\s*:\s*(\S+)", re.M)
NAMED_KINDS = {"Profile", "Extension", "Logical", "Resource", "ValueSet", "CodeSystem", "Instance"}
CARET_TEXT = {"short", "definition", "comment", "requirements", "description", "purpose",
              "title", "label", "meaningWhenMissing", "orderMeaning", "human", "copyright"}
INSTANCE_TEXT = {"documentation", "description", "title", "purpose", "text", "div",
                 "valueString", "valueMarkdown", "comment", "display", "name"}
KEYWORD_TEXT = re.compile(r"^\s*(Title|Description)\s*:\s*$")
CARET = re.compile(r"\^((?:\[[^\]]*\]|[^\s=\[])+)\s*=\s*$")
CODE_DISPLAY_THEN_DEF = re.compile(r"#[\w.-]+\s+\"(?:[^\"\\]|\\.)*\"\s*$")
CODE_THEN_DISPLAY = re.compile(r"(\S*)#[\w.-]+\s*$")
ASSIGN = re.compile(r"^\s*\*\s+((?:\[[^\]]*\]|[^=\s\[])(?:\[[^\]]*\]|[^=\[])*?)\s*=\s*$")
ELEMENT = re.compile(r"^\s*\*\s+(.*?)\s*\^")
HTML_TAG = r"</?[A-Za-z][^>]*>"
URL = r"https?://[^\s)|>\]\"\\]+"


def fsh_scan(src):
    """Return (strings, comments) as (start, end, quote_len) / (start, end) spans.

    A // or /* only opens a comment at the start of a token, so unquoted URLs
    such as http://loinc.org#123 are not mistaken for comments."""
    strings, comments = [], []
    i, n = 0, len(src)
    while i < n:
        token_start = i == 0 or src[i - 1] in " \t\r\n"
        if token_start and src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j < 0 else j
            comments.append((i, j))
            i = j
        elif token_start and src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            comments.append((i, j))
            i = j
        elif src.startswith('"""', i):
            j = src.find('"""', i + 3)
            j = n if j < 0 else j
            strings.append((i + 3, j, 3))
            i = j + 3
        elif src[i] == '"':
            j = i + 1
            while j < n and src[j] != '"':
                j += 2 if src[j] == "\\" else 1
            strings.append((i + 1, j, 1))
            i = j + 1
        else:
            i += 1
    return strings, comments


def fsh_entities(code):
    ents = [(m.start(), {"kind": m.group(1), "name": m.group(2), "name_span": m.span(2),
                         "id": None, "id_span": None, "instance_of": None})
            for m in ENTITY.finditer(code)]
    offsets = [o for o, _ in ents]
    for m in META.finditer(code):
        i = bisect_right(offsets, m.start()) - 1
        if i >= 0:
            ent = ents[i][1]
            if m.group(1) == "Id":
                ent["id"], ent["id_span"] = m.group(2), m.span(2)
            elif m.group(1) == "InstanceOf":
                ent["instance_of"] = m.group(2)
    return ents


def last_segment(path):
    return re.sub(r"\[[^\]]*\]", "", path).split(".")[-1]


def classify_fsh(entity, prefix, value, markers):
    """(change_class, field) for a string literal, or None when it isn't reader prose."""
    kind = entity["kind"] if entity else None
    m = KEYWORD_TEXT.match(prefix)
    if m:
        return ARTIFACT, m.group(1)
    m = CARET.search(prefix)
    if m:
        return (ARTIFACT, "^" + m.group(1)) if last_segment(m.group(1)) in CARET_TEXT else None
    if CODE_DISPLAY_THEN_DEF.search(prefix):
        return (ARTIFACT, "concept definition") if kind == "CodeSystem" else None
    m = CODE_THEN_DISPLAY.search(prefix)
    if m:
        if kind == "CodeSystem":
            return ARTIFACT, "concept display"
        local = any(mk in m.group(1) for mk in markers)
        return (ARTIFACT, "code display (local)") if local else (EXTERNAL, "code display")
    m = ASSIGN.match(prefix)
    if m:
        path = m.group(1)
        last = last_segment(path)
        if last not in INSTANCE_TEXT or (last == "name" and path != "name"):
            return None
        if path.startswith("item") and "questionnaire" in ((entity or {}).get("instance_of") or "").lower():
            return EXTERNAL, path
        if path == "name" and not re.search(r"\s", value):
            return IDENTIFIER, path
        return ARTIFACT, path
    return None


def decamel(name):
    s = re.sub(r"[-_.]+", " ", name)
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", s)
    s = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", s)
    return collapse(s)


def local_markers(ig):
    """Substrings that mark a code system as this IG's own: its canonical URL and its FSH id prefixes."""
    return [ig["canonical"]] + list(ig["artifact_prefixes"])


def fsh_url(entity, id_types, base):
    if not entity or entity["kind"] not in NAMED_KINDS:
        return None
    ident = entity["id"] or entity["name"]
    if entity["kind"] in ("Profile", "Extension", "Logical", "Resource"):
        return f"{base}StructureDefinition-{ident}.html"
    if entity["kind"] in ("ValueSet", "CodeSystem"):
        return f"{base}{entity['kind']}-{ident}.html"
    rtype = id_types.get(ident)
    return f"{base}{rtype}-{ident}.html" if rtype else None


def extract_fsh(rel, raw, id_types, base, markers):
    """Return (segments, skipped_string_count)."""
    strings, comments = fsh_scan(raw)
    code = list(raw)
    for s, e in comments:
        code[s:e] = blank(raw[s:e])
    code = "".join(code)
    ents = fsh_entities(code)
    offsets = [o for o, _ in ents]
    visible = list(blank(raw))
    keep, skipped = [], 0
    for s, e, q in strings:
        line_start = raw.rfind("\n", 0, s - q) + 1
        prefix = code[line_start:s - q]
        i = bisect_right(offsets, s) - 1
        entity = ents[i][1] if i >= 0 else None
        cls = classify_fsh(entity, prefix, raw[s:e], markers)
        if cls is None:
            skipped += 1
            continue
        vis = raw[s:e]
        if cls[1].endswith("div"):
            vis = mask(vis, HTML_TAG)
        visible[s:e] = mask(vis, URL)
        el = ELEMENT.match(prefix)
        section = f"{el.group(1)} {cls[1]}" if el else cls[1]
        keep.append((s, e, cls, section, entity))
    visible = "".join(visible)
    idx = LineIndex(raw)
    segs = []
    for _, ent in ents:
        if ent["kind"] not in NAMED_KINDS:
            continue
        for field, span in (("entity name", ent["name_span"]), ("Id", ent["id_span"])):
            if span:
                segs.append(segment(rel, "fsh", IDENTIFIER, field, ent["kind"], ent["name"],
                                    fsh_url(ent, id_types, base), raw, raw, span[0], span[1], idx,
                                    text=decamel(raw[span[0]:span[1]])))
    for s, e, (change_class, field), section, entity in keep:
        text = collapse(visible[s:e].replace("\\n", " ").replace("\\r", " ").replace('\\"', '"'))
        if change_class == IDENTIFIER:
            text = decamel(raw[s:e])
        segs.append(segment(rel, "fsh", change_class, field, section,
                            entity["name"] if entity else None, fsh_url(entity, id_types, base),
                            raw, visible, s, e, idx, text=text))
    segs.sort(key=lambda g: g["start"])
    return segs, skipped


# ---- diagrams, figures, config -----------------------------------------------
PUML_HIDE = re.compile(r"^\s*(@start|@end|skinparam\b|!|hide\b|show\b|autonumber\b|activate\b|"
                       r"deactivate\b|scale\b|left to right|top to bottom|end(\s+\w+)?\s*$|[{}]\s*$)", re.I)


def mask_plantuml(raw):
    raw2 = mask(raw, r"/'.*?'/", re.S)
    raw2 = mask(raw2, r"^\s*skinparam\s+\w+\s*\{.*?^\s*\}", re.S | re.M)
    raw2 = mask(raw2, r"<style>.*?</style>", re.S)
    return "\n".join(blank(ln) if (ln.strip().startswith("'") or PUML_HIDE.match(ln)) else ln
                     for ln in raw2.split("\n"))


def extract_plantuml(rel, raw, url=None):
    visible = mask_plantuml(raw)
    m = re.search(r"^\s*title\s+(.+?)\s*$", visible, re.M)
    section = m.group(1) if m else Path(rel).stem
    idx = LineIndex(raw)
    return [segment(rel, "diagram", DIAGRAM, "diagram line", section, Path(rel).name, url,
                    raw, visible, s, e, idx) for s, e, _ in line_regions(raw, visible)]


def extract_svg(rel, raw, url=None):
    visible = mask(raw, r"<[^>]*>", re.S)
    idx = LineIndex(raw)
    segs = []
    for m in re.finditer(r"<(text|foreignObject)\b[^>]*>(.*?)</\1>", raw, re.S):
        s, e = m.span(2)
        if re.search(r"[A-Za-z]", visible[s:e]):
            segs.append(segment(rel, "figure", DIAGRAM, "svg text", Path(rel).name, Path(rel).name,
                                url, raw, visible, s, e, idx))
    return segs


def kept_segments(rel, raw, spans, kind, change_class, artifact, url=None):
    idx = LineIndex(raw)
    return [segment(rel, kind, change_class, f, sec, artifact, url, raw, raw, s, e, idx)
            for s, e, f, sec in spans]


def extract_sushi_config(rel, raw):
    spans, block, page, pos = [], None, None, 0
    for line in raw.split("\n"):
        top = re.match(r"^([A-Za-z]\w*):", line)
        if top:
            block = top.group(1)
        m = field = sec = None
        if top and block in ("title", "description"):
            m, field, sec = re.match(r"^\w+:\s*\"?(.*?)\"?\s*$", line), "IG " + block, block
        elif block == "pages" and not top:
            p = re.match(r"^\s+(\S+\.(?:md|html|xml)):\s*$", line)
            if p:
                page = p.group(1)
            m, field, sec = re.match(r"^\s+title:\s*\"?(.*?)\"?\s*$", line), "page title", page
        elif block == "menu" and not top:
            m, field, sec = re.match(r"^\s+\"?([^:\"]+?)\"?:", line), "menu label", "menu"
        if m and m.group(1).strip():
            spans.append((pos + m.start(1), pos + m.end(1), field, sec))
        pos += len(line) + 1
    return kept_segments(rel, raw, spans, "config", PROSE, "sushi-config.yaml")


def extract_ig_yml(rel, raw):
    spans, pos = [], 0
    for line in raw.split("\n"):
        m = re.match(r"^\s+(name|description):\s*\"?(.*?)\"?\s*$", line)
        if m and m.group(2):
            spans.append((pos + m.start(2), pos + m.end(2), "artifact group " + m.group(1), "artifact list"))
        pos += len(line) + 1
    return kept_segments(rel, raw, spans, "config", PROSE, "ig.yml")


def extract_structuremap(rel, raw, base):
    m_id = re.search(r'<id value="([^"]+)"', raw)
    url = f"{base}StructureMap-{m_id.group(1)}.html" if m_id else None
    spans = [(m.start(2), m.end(2), m.group(1), m.group(1))
             for m in re.finditer(r'<(description|title|documentation) value="([^"]*)"', raw)
             if m.group(2).strip()]
    return kept_segments(rel, raw, spans, "resource", ARTIFACT, Path(rel).stem, url)


# ---- whole snapshot ------------------------------------------------------------
IMG_REF = re.compile(r'img="([^"]+)"|!\[[^\]]*\]\(([^)\s]+)\)|<img[^>]*src="([^"]+)"')


def published_pages(config):
    """Page names under sushi-config's pages:, or None when it has no pages: block (every page file is then published)."""
    if not config.get("pages"):
        return None
    names = set()

    def walk(d):
        for k, v in (d or {}).items():
            if re.search(r"\.(md|xml|html)$", str(k)):
                names.add(re.sub(r"\.(xml|html)$", ".md", str(k)))
            if isinstance(v, dict):
                walk(v)
    walk(config.get("pages"))
    return names


def is_published(name, published):
    return published is None or name in published or name.endswith(("-intro.md", "-notes.md"))


def image_refs(pages):
    refs = {}
    for page, raw in pages.items():
        for m in IMG_REF.finditer(raw):
            ref = next(g for g in m.groups() if g)
            refs.setdefault(Path(ref).name, set()).add(page)
    return refs


def first_page_url(pages, base):
    return page_url(sorted(pages)[0], base) if pages else None


def classify_file(rel, published, refs, stems, includes, transcripts, glossary_name, historical):
    """Return (extractor, None) or (None, exclusion reason)."""
    parts = Path(rel).parts
    name = parts[-1]
    top = parts[1] if len(parts) > 2 else None
    if rel == "sushi-config.yaml":
        return "sushi-config", None
    if rel == "input/data/ig.yml":
        return "ig-yml", None
    if rel == "input/ignoreWarnings.txt":
        return None, "publisher QA configuration (not reader-visible)"
    if top == "pagecontent" and name.endswith(".md"):
        if name == glossary_name:
            return "glossary", None
        if name in historical:
            return "historical", None
        if is_published(name, published):
            return "page", None
        return None, "not published (absent from sushi-config pages; 404 on hl7.org)"
    if top == "fsh" and name.endswith(".fsh"):
        return "fsh", None
    if rel == "input/fsh/index.txt":
        return None, "SUSHI-generated FSH index (not reader-visible)"
    if top == "images-source" and name.endswith(".plantuml"):
        return "plantuml", None
    if top == "resources" and name.endswith(".xml"):
        return "structuremap", None
    if top == "includes":
        if name.endswith(".html"):
            return None, "layout template (no prose)"
        if name == "markdown-link-references.md":
            return None, "link reference definitions only"
        if name.endswith(".md"):
            return ("include", None) if name in includes else (None, "not included by any published page")
        if name.endswith(".orig"):
            return None, "unused backup file"
    if top == "images":
        if Path(name).stem in stems:
            return None, "rendered from plantuml source (analyzed via images-source)"
        if name not in refs:
            return None, "image not referenced by a published page"
        if name.endswith(".svg"):
            return "svg", None
        if rel in transcripts:
            return "transcript", None
        return None, f"raster image — needs visual read (referenced by {', '.join(sorted(refs[name]))})"
    return None, "unrecognized file type — review"


def id_types_from(gen_dir):
    out = {}
    for p in Path(gen_dir).glob("*.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        if "id" in d and "resourceType" in d:
            out[d["id"]] = d["resourceType"]
    return out


def extract(snapshot, ig, id_types=None, transcripts=None):
    snapshot = Path(snapshot)
    base, markers = ig["published_base"], local_markers(ig)
    glossary_name, historical = Path(ig["glossary_page"]).name, set(ig.get("historical_pages") or [])
    id_types = id_types or {}
    transcripts = {t["image"]: t for t in (transcripts or [])}
    published = published_pages(yaml.safe_load((snapshot / "sushi-config.yaml").read_text(encoding="utf-8")))
    pages = {p.name: p.read_text(encoding="utf-8")
             for p in (snapshot / "input" / "pagecontent").glob("*.md") if is_published(p.name, published)}
    refs = image_refs(pages)
    stems = {p.stem for p in (snapshot / "input" / "images-source").glob("*.plantuml")}
    includes = {n: pg for pg, raw in sorted(pages.items())
                for n in re.findall(r"\{%-?\s*include\s+([\w.-]+\.md)", raw)}
    files = sorted(p.relative_to(snapshot).as_posix() for p in (snapshot / "input").rglob("*") if p.is_file())
    files.append("sushi-config.yaml")

    segments, coverage, figures = [], {}, []
    for rel in files:
        how, reason = classify_file(rel, published, refs, stems, includes, transcripts, glossary_name, historical)
        name = Path(rel).name
        if how is None:
            coverage[rel] = {"status": "excluded", "reason": reason}
            if reason.startswith("raster image"):
                figures.append({"image": rel, "pages": sorted(refs[name])})
            continue
        skipped = 0
        if how == "transcript":
            t = transcripts[rel]
            url = first_page_url(refs.get(name), base)
            segs = [{"seg_id": f"{rel}#{n}", "file": rel, "kind": "figure",
                     "change_class": t.get("change_class", DIAGRAM), "field": "transcribed text",
                     "section": name, "artifact": name, "url": url, "line": None, "col": None,
                     "start": None, "end": None, "raw": text, "visible": text, "text": text}
                    for n, text in enumerate(t["text"], 1)]
        else:
            raw = (snapshot / rel).read_text(encoding="utf-8")
            if how in ("page", "glossary", "historical"):
                segs = extract_page(rel, raw, HISTORICAL if how == "historical" else PROSE,
                                    "glossary" if how == "glossary" else "page", page_url(name, base))
            elif how == "include":
                segs = extract_page(rel, raw, url=page_url(includes[name], base))
            elif how == "fsh":
                segs, skipped = extract_fsh(rel, raw, id_types, base, markers)
            elif how == "plantuml":
                stem = Path(rel).stem
                segs = extract_plantuml(rel, raw, first_page_url(refs.get(stem + ".svg", set()) | refs.get(stem + ".png", set()), base))
            elif how == "svg":
                segs = extract_svg(rel, raw, first_page_url(refs.get(name), base))
            elif how == "sushi-config":
                segs = extract_sushi_config(rel, raw)
            elif how == "ig-yml":
                segs = extract_ig_yml(rel, raw)
            else:
                segs = extract_structuremap(rel, raw, base)
        segments += segs
        coverage[rel] = {"status": "extracted", "segments": len(segs), "skipped_strings": skipped}
    return {"segments": segments, "coverage": coverage, "figures": figures}


def main(argv=None):
    ap = config.add_run_arg(argparse.ArgumentParser(description=__doc__))
    ap.add_argument("--fsh-generated", type=Path, help="SUSHI fsh-generated/resources dir (default: inside the snapshot if present)")
    args = ap.parse_args(argv)
    cfg = config.load(args.run)
    gen = args.fsh_generated or cfg["snapshot"] / "fsh-generated" / "resources"
    id_types = id_types_from(gen) if gen.exists() else {}
    tpath = cfg["run_dir"] / "figure_transcripts.yaml"
    transcripts = yaml.safe_load(tpath.read_text(encoding="utf-8")) if tpath.exists() else []
    result = extract(cfg["snapshot"], cfg["ig"], id_types=id_types, transcripts=transcripts or [])
    out = cfg["data"]
    write_jsonl(out / "segments.jsonl", result["segments"])
    (out / "coverage.json").write_text(json.dumps(result["coverage"], indent=1, sort_keys=True) + "\n")
    (out / "figures.json").write_text(json.dumps(result["figures"], indent=1) + "\n")
    excluded = sum(c["status"] == "excluded" for c in result["coverage"].values())
    print(f"{len(result['segments'])} segments from {len(result['coverage']) - excluded} files "
          f"({excluded} excluded); by class {dict(Counter(s['change_class'] for s in result['segments']))}; "
          f"{len(result['figures'])} figures need a visual read")


if __name__ == "__main__":
    main()
