#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()

import asyncio, hashlib, html, json, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.request import Request, urlopen

from pydantic import BaseModel, field_validator

DATA_DIR = Path("actions/data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACT_FILES = [
    "knowledge.json", "manifest.json", "search-index.json",
    "metadata.json", "kv-bulk.json",
]

RAW_BASE = "https://raw.githubusercontent.com/framework7io/framework7-website/master/src/pug/react"

# (slug, pug_filename, category)
# core pages live in docs/, components in react/
PAGES = [
    ("introduction",               "https://raw.githubusercontent.com/framework7io/framework7-website/master/src/pug/docs/introduction.pug", "core"),
    ("package",                    f"{RAW_BASE}/package.pug",                    "core"),
    ("app-layout",                 f"{RAW_BASE}/app-layout.pug",                 "core"),
    ("init-app",                   f"{RAW_BASE}/init-app.pug",                   "core"),
    ("react-component-extensions", f"{RAW_BASE}/react-component-extensions.pug", "core"),
    ("navigation-router",          f"{RAW_BASE}/navigation-router.pug",          "core"),
    ("colors",                     f"{RAW_BASE}/colors.pug",                     "core"),
    ("store",                      f"{RAW_BASE}/store.pug",                      "core"),
    ("app",                        f"{RAW_BASE}/app.pug",                        "component"),
    ("accordion",                  f"{RAW_BASE}/accordion.pug",                  "component"),
    ("action-sheet",               f"{RAW_BASE}/action-sheet.pug",               "component"),
    ("area-chart",                 f"{RAW_BASE}/area-chart.pug",                 "component"),
    ("autocomplete",               f"{RAW_BASE}/autocomplete.pug",               "component"),
    ("badge",                      f"{RAW_BASE}/badge.pug",                      "component"),
    ("block",                      f"{RAW_BASE}/block.pug",                      "component"),
    ("breadcrumbs",                f"{RAW_BASE}/breadcrumbs.pug",                "component"),
    ("button",                     f"{RAW_BASE}/button.pug",                     "component"),
    ("calendar",                   f"{RAW_BASE}/calendar.pug",                   "component"),
    ("cards",                      f"{RAW_BASE}/cards.pug",                      "component"),
    ("checkbox",                   f"{RAW_BASE}/checkbox.pug",                   "component"),
    ("chips",                      f"{RAW_BASE}/chips.pug",                      "component"),
    ("color-picker",               f"{RAW_BASE}/color-picker.pug",               "component"),
    ("contacts-list",              f"{RAW_BASE}/contacts-list.pug",              "component"),
    ("data-table",                 f"{RAW_BASE}/data-table.pug",                 "component"),
    ("dialog",                     f"{RAW_BASE}/dialog.pug",                     "component"),
    ("floating-action-button",     f"{RAW_BASE}/floating-action-button.pug",     "component"),
    ("form",                       f"{RAW_BASE}/form.pug",                       "component"),
    ("gauge",                      f"{RAW_BASE}/gauge.pug",                      "component"),
    ("grid",                       f"{RAW_BASE}/grid.pug",                       "component"),
    ("icon",                       f"{RAW_BASE}/icon.pug",                       "component"),
    ("infinite-scroll",            f"{RAW_BASE}/infinite-scroll.pug",            "component"),
    ("inputs",                     f"{RAW_BASE}/inputs.pug",                     "component"),
    ("link",                       f"{RAW_BASE}/link.pug",                       "component"),
    ("list-view",                  f"{RAW_BASE}/list-view.pug",                  "component"),
    ("list-button",                f"{RAW_BASE}/list-button.pug",                "component"),
    ("list-index",                 f"{RAW_BASE}/list-index.pug",                 "component"),
    ("list-item",                  f"{RAW_BASE}/list-item.pug",                  "component"),
    ("login-screen",               f"{RAW_BASE}/login-screen.pug",               "component"),
    ("menu-list",                  f"{RAW_BASE}/menu-list.pug",                  "component"),
    ("messagebar",                 f"{RAW_BASE}/messagebar.pug",                 "component"),
    ("messages",                   f"{RAW_BASE}/messages.pug",                   "component"),
    ("navbar",                     f"{RAW_BASE}/navbar.pug",                     "component"),
    ("notification",               f"{RAW_BASE}/notification.pug",               "component"),
    ("page",                       f"{RAW_BASE}/page.pug",                       "component"),
    ("panel",                      f"{RAW_BASE}/panel.pug",                      "component"),
    ("photo-browser",              f"{RAW_BASE}/photo-browser.pug",              "component"),
    ("picker",                     f"{RAW_BASE}/picker.pug",                     "component"),
    ("pie-chart",                  f"{RAW_BASE}/pie-chart.pug",                  "component"),
    ("popover",                    f"{RAW_BASE}/popover.pug",                    "component"),
    ("popup",                      f"{RAW_BASE}/popup.pug",                      "component"),
    ("preloader",                  f"{RAW_BASE}/preloader.pug",                  "component"),
    ("progressbar",                f"{RAW_BASE}/progressbar.pug",                "component"),
    ("pull-to-refresh",            f"{RAW_BASE}/pull-to-refresh.pug",            "component"),
    ("radio",                      f"{RAW_BASE}/radio.pug",                      "component"),
    ("range-slider",               f"{RAW_BASE}/range-slider.pug",               "component"),
    ("searchbar",                  f"{RAW_BASE}/searchbar.pug",                  "component"),
    ("segmented",                  f"{RAW_BASE}/segmented.pug",                  "component"),
    ("sheet-modal",                f"{RAW_BASE}/sheet-modal.pug",                "component"),
    ("skeleton",                   f"{RAW_BASE}/skeleton.pug",                   "component"),
    ("smart-select",               f"{RAW_BASE}/smart-select.pug",               "component"),
    ("sortable",                   f"{RAW_BASE}/sortable.pug",                   "component"),
    ("stepper",                    f"{RAW_BASE}/stepper.pug",                    "component"),
    ("subnavbar",                  f"{RAW_BASE}/subnavbar.pug",                  "component"),
    ("swipeout",                   f"{RAW_BASE}/swipeout.pug",                   "component"),
    ("swiper",                     f"{RAW_BASE}/swiper.pug",                     "component"),
    ("tabs",                       f"{RAW_BASE}/tabs.pug",                       "component"),
    ("text-editor",                f"{RAW_BASE}/text-editor.pug",                "component"),
    ("timeline",                   f"{RAW_BASE}/timeline.pug",                   "component"),
    ("toast",                      f"{RAW_BASE}/toast.pug",                      "component"),
    ("toggle",                     f"{RAW_BASE}/toggle.pug",                     "component"),
    ("toolbar-tabbar",             f"{RAW_BASE}/toolbar-tabbar.pug",             "component"),
    ("tooltip",                    f"{RAW_BASE}/tooltip.pug",                    "component"),
    ("treeview",                   f"{RAW_BASE}/treeview.pug",                   "component"),
    ("view",                       f"{RAW_BASE}/view.pug",                       "component"),
    ("virtual-list",               f"{RAW_BASE}/virtual-list.pug",               "component"),
]

# ── Pydantic models ───────────────────────────────────────────────────────────

_TS_TYPE_RE = re.compile(
    r"^([A-Za-z_][A-Za-z0-9_.<>[\], ]*"
    r"|\([^)]*\)\s*=>\s*[A-Za-z_][A-Za-z0-9_.<>[\], ]*)"
    r"(\s*(\||&)\s*"
    r"([A-Za-z_][A-Za-z0-9_.<>[\], ]*"
    r"|\([^)]*\)\s*=>\s*[A-Za-z_][A-Za-z0-9_.<>[\], ]*))*$"
)

def is_valid_ts_type(v: str) -> bool:
    v = (v or "").strip()
    return bool(v and _TS_TYPE_RE.match(v))

class Prop(BaseModel):
    name: str
    ts_type: str
    default: Optional[str]
    required: bool
    description: str
    source_table_header: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_ok(cls, v: str) -> str:
        v = (v or "").strip()
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_:-]*$", v):
            raise ValueError(f"Bad prop name: {v!r}")
        return v

    @field_validator("ts_type")
    @classmethod
    def type_ok(cls, v: str) -> str:
        v = (v or "").strip()
        if not is_valid_ts_type(v):
            raise ValueError(f"Bad TS type: {v!r}")
        return v

    @field_validator("description")
    @classmethod
    def desc_ok(cls, v: str) -> str:
        return (v or "").strip() or "No description provided."

class EventEntry(BaseModel):
    name: str
    ts_type: str
    description: str
    source_table_header: Optional[str] = None

    @field_validator("ts_type")
    @classmethod
    def type_ok(cls, v: str) -> str:
        v = (v or "").strip()
        if not is_valid_ts_type(v):
            raise ValueError(f"Bad event TS type: {v!r}")
        return v

    @field_validator("description")
    @classmethod
    def desc_ok(cls, v: str) -> str:
        return (v or "").strip() or "No description provided."

class ComponentDoc(BaseModel):
    slug: str
    url: str
    component: str
    category: str
    description: str
    import_statement: str
    props: list[Prop]
    events: list[EventEntry]
    methods: list[str] = []
    slots: list[str] = []
    tsx_example: str
    notes: list[str]

    @field_validator("description")
    @classmethod
    def desc_ok(cls, v: str) -> str:
        return (v or "").strip() or "No description provided."

# ── Fetch ─────────────────────────────────────────────────────────────────────

def fetch_raw(url: str) -> str:
    req = Request(url, headers={"User-Agent": "framework7-docs-builder/1.0"})
    with urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")

# ── Pug text helpers ──────────────────────────────────────────────────────────

def pug_text(raw: str) -> str:
    """Strip inline HTML tags and decode HTML entities from a pug cell value."""
    # Remove inline tags: <br>, <a ...>, <span ...>, <code>, <strong>, <b>, etc.
    t = re.sub(r"<[^>]+>", " ", raw)
    t = html.unescape(t)
    # Collapse whitespace
    t = re.sub(r"\s+", " ", t).strip()
    # Strip backtick code markers
    t = t.replace("`", "")
    return t

def pug_type(raw: str) -> str:
    """
    Convert pug type cell to TypeScript union type.
    Pug uses <br> as delimiter: 'string<br>boolean' → 'string | boolean'
    """
    # Split on <br> (various forms)
    parts = re.split(r"<br\s*/?>", raw, flags=re.I)
    ts_parts = []
    for p in parts:
        clean = pug_text(p).strip().lower()
        ts_parts.append(_map_type(clean))
    ts_parts = list(dict.fromkeys(p for p in ts_parts if p))
    return " | ".join(ts_parts) if ts_parts else "unknown"

_TYPE_MAP = {
    "boolean": "boolean", "bool": "boolean",
    "string": "string", "str": "string",
    "number": "number", "integer": "number", "int": "number", "float": "number",
    "function": "() => void", "func": "() => void",
    "object": "Record<string, unknown>",
    "array": "unknown[]",
    "any": "unknown", "mixed": "unknown",
    "reactnode": "React.ReactNode", "node": "React.ReactNode",
    "element": "React.ReactElement",
    "": "unknown",
}

def _map_type(t: str) -> str:
    if not t:
        return "unknown"
    if t.endswith("[]"):
        return _map_type(t[:-2]) + "[]"
    if t.startswith("array of "):
        return _map_type(t[len("array of "):]) + "[]"
    return _TYPE_MAP.get(t, t)

def infer_event_type(name: str) -> str:
    n = name.lower()
    if n in ("onclick", "ontap", "click"):       return "(e: React.MouseEvent) => void"
    if n in ("onchange", "change"):               return "(value: unknown) => void"
    if n in ("oninput", "onkeydown", "onkeyup"): return "(e: React.KeyboardEvent) => void"
    if n in ("onfocus", "onblur"):                return "(e: React.FocusEvent) => void"
    if n == "onsubmit":                           return "(e: React.FormEvent) => void"
    return "() => void"

# ── Pug parser ────────────────────────────────────────────────────────────────

def indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))

def parse_pug(source: str, slug: str) -> dict:
    lines = source.splitlines()

    component = "".join(w.capitalize() for w in slug.split("-"))
    description = ""
    props: list[dict] = []
    events: list[dict] = []
    methods: list[str] = []
    slots: list[str] = []
    notes: list[str] = []
    example_lines: list[str] = []

    # Extract h1 component name
    for line in lines:
        m = re.search(r"\bh1\s+(.+)", line)
        if m:
            raw = m.group(1).strip()
            # strip HTML
            raw = re.sub(r"<[^>]+>", "", raw)
            raw = html.unescape(raw)
            # strip "React Component" suffix
            raw = re.sub(r"\s*react\s+component.*", "", raw, flags=re.I).strip()
            # strip " / Side Panel" alternates
            raw = re.split(r"\s*/\s*", raw)[0].strip()
            component = "".join(w.capitalize() for w in re.split(r"[\s\-_]+", raw) if w)
            break

    # Extract first description paragraph (p tag after h1, before first h2)
    found_h1 = False
    for line in lines:
        stripped = line.strip()
        if re.match(r"h1\b", stripped):
            found_h1 = True
            continue
        if found_h1:
            if re.match(r"h2\b", stripped):
                break
            m = re.match(r"p\s+(.+)", stripped)
            if m:
                txt = pug_text(m.group(1))
                if len(txt) > 20:
                    description = txt[:400]
                    break

    # Extract important-note blocks
    in_note = False
    note_indent = 0
    note_buf: list[str] = []
    for line in lines:
        stripped = line.strip()
        ind = indent(line)
        if ".important-note" in stripped or "blockquote" in stripped:
            in_note = True
            note_indent = ind
            note_buf = []
            continue
        if in_note:
            if stripped and ind <= note_indent and not stripped.startswith("p "):
                if note_buf:
                    notes.append(pug_text(" ".join(note_buf))[:300])
                in_note = False
                note_buf = []
            elif stripped.startswith("p "):
                note_buf.append(stripped[2:])

    # ── Table parsing ─────────────────────────────────────────────────────────
    # State machine over lines to extract tables
    # Tables: params-table (props), events-table (events), methods-table (methods)

    TABLE_NONE    = 0
    TABLE_PARAMS  = 1
    TABLE_EVENTS  = 2
    TABLE_METHODS = 3
    TABLE_SLOTS   = 4

    table_state = TABLE_NONE
    table_indent = 0
    in_tbody = False
    current_section = ""   # tracks <Component> label for multi-component tables
    row_cells: list[str] = []
    col_count = 0          # detected from thead

    def flush_row():
        nonlocal row_cells
        if not row_cells:
            return
        cells = row_cells[:]
        row_cells = []
        if table_state == TABLE_PARAMS:
            _process_prop_row(cells, current_section)
        elif table_state == TABLE_EVENTS:
            _process_event_row(cells, current_section)
        elif table_state == TABLE_METHODS:
            _process_method_row(cells)

    def _process_prop_row(cells: list[str], section: str):
        if len(cells) < 2:
            return
        raw_name = cells[0].strip().rstrip("*")
        if not raw_name or raw_name.lower() in ("prop", "name", "parameter"):
            return
        # Split merged names
        names = [raw_name]
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_:-]*$", raw_name):
            parts = re.split(r"\s+", raw_name)
            if all(re.match(r"^[A-Za-z_][A-Za-z0-9_:-]*$", p) for p in parts if p):
                names = [p for p in parts if p]
        raw_type = cells[1] if len(cells) > 1 else ""
        default  = pug_text(cells[2]) if len(cells) > 2 else ""
        desc     = pug_text(cells[3]) if len(cells) > 3 else ""
        if default in ("-", "—", "undefined", "null", ""):
            default = None  # type: ignore[assignment]
        required = cells[0].strip().endswith("*") or "required" in desc.lower()
        ts_type  = pug_type(raw_type)
        if not is_valid_ts_type(ts_type):
            ts_type = "unknown"
        for name in names:
            if not re.match(r"^[A-Za-z_][A-Za-z0-9_:-]*$", name):
                continue
            props.append({
                "name": name, "ts_type": ts_type, "default": default,
                "required": required, "description": desc,
                "source_table_header": section,
            })

    def _process_event_row(cells: list[str], section: str):
        if len(cells) < 1:
            return
        # event cells: [name, description]  (name may have <br> for aliases)
        raw_name = cells[0]
        desc = pug_text(cells[1]) if len(cells) > 1 else ""
        # Split on <br> to get aliases, use first as primary
        names = [pug_text(n) for n in re.split(r"<br\s*/?>", raw_name, flags=re.I)]
        names = [n for n in names if n and re.match(r"^[A-Za-z_][A-Za-z0-9_:-]*$", n)]
        if not names:
            return
        primary = names[0]
        if primary.lower() in ("event", "name"):
            return
        events.append({
            "name": primary, "ts_type": infer_event_type(primary),
            "description": desc, "source_table_header": section,
        })

    def _process_method_row(cells: list[str]):
        if cells:
            m = pug_text(cells[0])
            if m and m.lower() not in ("method", "name"):
                methods.append(m)

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        ind = indent(line)

        # Detect table start
        if re.match(r"table\.(params|events|methods|slots)-table", stripped):
            flush_row()
            if "params" in stripped:
                table_state = TABLE_PARAMS
            elif "events" in stripped:
                table_state = TABLE_EVENTS
            elif "methods" in stripped:
                table_state = TABLE_METHODS
            elif "slots" in stripped:
                table_state = TABLE_SLOTS
            table_indent = ind
            in_tbody = False
            row_cells = []
            i += 1
            continue

        # Exit table when we return to same or lesser indent with non-table content
        if table_state != TABLE_NONE and stripped and ind <= table_indent and not re.match(r"(thead|tbody|tr|td|th)\b", stripped):
            flush_row()
            table_state = TABLE_NONE
            in_tbody = False

        if table_state == TABLE_NONE:
            # Slots extraction from ul after "h2 * Slots"
            if re.match(r"h2\s+.*Slots", stripped):
                j = i + 1
                while j < len(lines) and not re.match(r"\s*h2\b", lines[j]):
                    s = lines[j].strip()
                    m = re.match(r"li\s+`([^`]+)`\s*[-–—]?\s*(.*)", s)
                    if m:
                        slots.append(f"`{m.group(1)}` - {pug_text(m.group(2))}")
                    j += 1

            # Example code blocks (indented lines after +examplePreview or h4)
            if stripped.startswith("+examplePreview") or re.match(r"h4\s+", stripped):
                # Collect following indented lines as code
                j = i + 1
                code_buf: list[str] = []
                base_ind = ind + 2
                while j < len(lines):
                    l = lines[j]
                    if l.strip() == "" or indent(l) >= base_ind:
                        code_buf.append(l.rstrip())
                        j += 1
                    else:
                        break
                if code_buf:
                    example_lines.extend(code_buf)

            i += 1
            continue

        # Inside a table
        if stripped.startswith("tbody"):
            in_tbody = True
            i += 1
            continue
        if stripped.startswith("thead"):
            in_tbody = False
            i += 1
            continue

        # Section header row: th(colspan="N") <Component> properties/events
        m = re.match(r'th\(colspan=["\']?\d+["\']?\)\s*(.*)', stripped)
        if m:
            flush_row()
            label = html.unescape(m.group(1))
            label = re.sub(r"<[^>]+>", "", label).strip()
            current_section = label
            i += 1
            continue

        # New row
        if stripped == "tr" or stripped.startswith("tr "):
            flush_row()
            i += 1
            continue

        # Cell: td or th without colspan
        if re.match(r"td\b|th\b(?!\(colspan)", stripped):
            # Cell value may be on same line or on next indented lines
            m = re.match(r"(td|th)\s+(.*)", stripped)
            cell_val = m.group(2).strip() if m else ""

            # Collect continuation lines (deeper indent)
            cell_ind = ind
            j = i + 1
            while j < len(lines):
                nxt = lines[j]
                nxt_stripped = nxt.strip()
                if not nxt_stripped:
                    j += 1
                    continue
                if indent(nxt) > cell_ind and not re.match(r"(tr|td|th|thead|tbody)\b", nxt_stripped):
                    cell_val = cell_val + " " + nxt_stripped
                    j += 1
                else:
                    break
            i = j
            row_cells.append(cell_val)
            continue

        i += 1

    flush_row()

    # Dedupe props and events
    props_out  = _dedupe(props)
    events_out = _dedupe(events)

    # Build TSX example from collected inline code
    raw_code = "\n".join(example_lines).strip()
    tsx_example = _jsx_to_tsx(raw_code, component, props_out) if raw_code else (
        f"import React from 'react';\n"
        f"import {{ {component} }} from 'framework7-react';\n\n"
        f"interface {component}Props {{}}\n\n"
        f"const Example: React.FC = () => (\n  <{component} />\n);\n\n"
        f"export default Example;"
    )

    return {
        "component": component,
        "description": description or f"Framework7 React {component} component.",
        "props": props_out,
        "events": events_out,
        "methods": list(dict.fromkeys(methods))[:10],
        "slots": list(dict.fromkeys(slots))[:10],
        "tsx_example": tsx_example,
        "notes": list(dict.fromkeys(notes))[:5],
    }

def _dedupe(entries: list[dict]) -> list[dict]:
    seen: dict[str, dict] = {}
    order: list[str] = []
    for e in entries:
        name = e.get("name", "").strip()
        if not name:
            continue
        if name not in seen:
            seen[name] = e
            order.append(name)
        else:
            cur = seen[name]
            if len(e.get("description", "")) > len(cur.get("description", "")):
                cur["description"] = e["description"]
            if not cur.get("default") and e.get("default"):
                cur["default"] = e["default"]
    return [seen[n] for n in order]

# ── JSX → TSX ─────────────────────────────────────────────────────────────────

def _jsx_to_tsx(code: str, component: str, props: list[dict]) -> str:
    if not code or len(code) < 10:
        return code
    for pat, repl in [
        (r"[A-Za-z]+\.propTypes\s*=\s*\{[^}]*\}", ""),
        (r"[A-Za-z]+\.defaultProps\s*=\s*\{[^}]*\}", ""),
    ]:
        code = re.sub(pat, repl, code, flags=re.DOTALL)
    code = re.sub(
        rf"(const\s+{component})\s*=\s*\((.*?)\)\s*=>",
        rf"\1: React.FC<{component}Props> = (\2) =>",
        code, flags=re.DOTALL,
    )
    code = re.sub(
        rf"(function\s+{component})\s*\((.*?)\)\s*\{{",
        rf"\1(\2: {component}Props): JSX.Element {{",
        code, flags=re.DOTALL,
    )
    if props and f"interface {component}Props" not in code:
        lines = [f"  {p['name']}{'?' if not p.get('required') else ''}: {p['ts_type']};" for p in props[:15]]
        code = f"interface {component}Props {{\n" + "\n".join(lines) + "\n}\n\n" + code
    if "import React" not in code and "from 'react'" not in code:
        code = "import React from 'react';\n" + code
    code = code.replace(".jsx", ".tsx")
    code = re.sub(r"useState\(\)", "useState<unknown>()", code)
    code = re.sub(r"useState\(null\)", "useState<unknown>(null)", code)
    return re.sub(r"\n{3,}", "\n\n", code).strip()

def build_import(component: str, slug: str) -> str:
    names = {component}
    for p in slug.replace("-", " ").title().split():
        names.add(p)
    return f"import {{ {', '.join(sorted(names))} }} from 'framework7-react';"

def page_url(slug: str, category: str) -> str:
    if slug == "introduction":
        return "https://framework7.io/docs/introduction.html"
    return f"https://framework7.io/react/{slug}.html"

# ── Artifact writers ──────────────────────────────────────────────────────────

def to_id(category: str, slug: str) -> str:
    return f"{'core' if category == 'core' else 'component'}:{slug}"

def doc_to_manifest_item(slug: str, category: str, doc: dict) -> dict:
    title   = doc.get("component", "".join(w.capitalize() for w in slug.split("-")))
    summary = (doc.get("description") or "").strip() or f"Framework7 React {title} documentation."
    prop_names = [p.get("name", "") for p in doc.get("props", []) if isinstance(p, dict)]
    keywords = sorted(set([slug, title, "framework7", "react", "typescript", "tsx"] + prop_names))
    return {
        "id": to_id(category, slug), "slug": slug, "title": title,
        "category": category, "summary": summary,
        "keywords": [k for k in keywords if k],
        "aliases": [slug.replace("-", ""), title.lower()],
        "url": doc.get("url", page_url(slug, category)),
        "retrieval_text": "\n".join(filter(None, [
            summary,
            "Props: "  + ", ".join(prop_names[:30]),
            "Events: " + ", ".join(e.get("name", "") for e in doc.get("events", [])[:30] if isinstance(e, dict)),
        ])).strip(),
    }

def write_artifacts(output: dict) -> None:
    generated_at = output["meta"]["generated_at"]
    version = "v9"
    docs = []
    for bucket, category in (("core_docs", "core"), ("components", "component")):
        for slug, item in output.get(bucket, {}).items():
            if not isinstance(item, dict) or "error" in item:
                continue
            mi = doc_to_manifest_item(slug, category, item)
            docs.append({
                **mi,
                "props":       item.get("props", []),
                "events":      item.get("events", []),
                "notes":       item.get("notes", []),
                "tsx_example": item.get("tsx_example", ""),
                "content": "\n".join(filter(None, [
                    item.get("description", ""),
                    "Methods: " + ", ".join(item.get("methods", [])) if item.get("methods") else "",
                    "Slots: "   + ", ".join(item.get("slots",   [])) if item.get("slots")   else "",
                ])).strip(),
            })
    docs.sort(key=lambda d: d["id"])
    mkeys = ("id", "slug", "title", "category", "summary", "keywords")
    skeys = ("id", "slug", "title", "category", "summary", "keywords", "aliases", "url", "retrieval_text")
    manifest_items = [{k: d[k] for k in mkeys} for d in docs]
    search_items   = [{k: d[k] for k in skeys} for d in docs]
    knowledge = {"version": version, "generatedAt": generated_at, "count": len(docs), "docs": docs}
    manifest  = {
        "version": version, "generatedAt": generated_at,
        "documentCount": len(docs),
        "componentCount": sum(1 for d in docs if d["category"] == "component"),
        "coreCount":      sum(1 for d in docs if d["category"] == "core"),
        "count": len(docs), "items": manifest_items,
    }
    search_index = {"version": version, "generatedAt": generated_at, "count": len(search_items), "items": search_items}
    checksum = hashlib.sha256(json.dumps(knowledge, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    metadata = {
        "version": version, "generatedAt": generated_at, "documentCount": len(docs),
        "checksum": checksum, "buildId": generated_at,
        "stats": {
            "components":  manifest["componentCount"],
            "core":        manifest["coreCount"],
            "totalProps":  sum(len(d.get("props",  [])) for d in docs),
            "totalEvents": sum(len(d.get("events", [])) for d in docs),
        },
    }
    kv_bulk = {"manifest": manifest, "searchIndex": search_index, "metadata": metadata, "knowledge": knowledge}
    payloads = {
        "knowledge.json": knowledge, "manifest.json": manifest,
        "search-index.json": search_index, "metadata.json": metadata, "kv-bulk.json": kv_bulk,
    }
    for name in ARTIFACT_FILES:
        (DATA_DIR / name).write_text(
            json.dumps(payloads[name], indent=2, ensure_ascii=False), encoding="utf-8"
        )

# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    output: dict = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "github.com/framework7io/framework7-website (raw pug)",
            "target_stack": "React + TypeScript (TSX)",
            "total_pages": len(PAGES),
        },
        "core_docs": {}, "components": {},
    }

    total = len(PAGES)
    for i, (slug, raw_url, category) in enumerate(PAGES, 1):
        bucket = "core_docs" if category == "core" else "components"
        print(f"[{i:02d}/{total}] {slug}", end="  ", flush=True)
        try:
            source = fetch_raw(raw_url)
        except Exception as e:
            print(f"FETCH FAIL: {e}")
            output[bucket][slug] = {"error": "fetch_failed", "url": page_url(slug, category), "detail": str(e)}
            continue
        try:
            parsed = parse_pug(source, slug)
            # Validate through pydantic
            props  = []
            for p in parsed["props"]:
                try:
                    props.append(Prop(**p).model_dump())
                except Exception:
                    pass
            events = []
            for e in parsed["events"]:
                try:
                    events.append(EventEntry(**e).model_dump())
                except Exception:
                    pass
            url = page_url(slug, category)
            output[bucket][slug] = {
                "url": url,
                "component":        parsed["component"],
                "description":      parsed["description"],
                "import_statement": build_import(parsed["component"], slug),
                "props":   props,
                "events":  events,
                "methods": parsed["methods"],
                "slots":   parsed["slots"],
                "tsx_example": parsed["tsx_example"],
                "notes":   parsed["notes"],
            }
            print(f"props={len(props)} events={len(events)}  ✓")
        except Exception as e:
            print(f"PARSE FAIL: {e}")
            output[bucket][slug] = {"error": "parse_failed", "url": page_url(slug, category), "detail": str(e)}

        if i % 15 == 0:
            write_artifacts(output)
            print(f"  ── checkpoint {i}/{total} ──")

    write_artifacts(output)

    k = json.loads((DATA_DIR / "knowledge.json").read_text())
    total_props  = sum(len(d.get("props",  [])) for d in k["docs"])
    total_events = sum(len(d.get("events", [])) for d in k["docs"])
    print(f"\n{'─'*56}")
    print(f"Done.  docs={k['count']}  props={total_props}  events={total_events}")
    if total_props == 0:
        raise SystemExit("ERROR: zero props — check parser")

if __name__ == "__main__":
    main()
