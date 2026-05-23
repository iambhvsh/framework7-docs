#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()
import asyncio, hashlib, json, os, re, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup
try:
    from playwright.async_api import async_playwright
except Exception:
    async_playwright = None
import trafilatura
from pydantic import BaseModel, field_validator
from urllib.request import Request, urlopen

CACHE_DIR = Path.home() / ".f7_cache"
DATA_DIR  = Path("actions/data")
CACHE_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACT_FILES = [
    "knowledge.json",
    "manifest.json",
    "search-index.json",
    "metadata.json",
    "kv-bulk.json",
]

URLS = [
    ("introduction",               "https://framework7.io/docs/introduction.html",               "core"),
    ("package",                    "https://framework7.io/react/package.html",                    "core"),
    ("app-layout",                 "https://framework7.io/react/app-layout.html",                 "core"),
    ("init-app",                   "https://framework7.io/react/init-app.html",                   "core"),
    ("react-component-extensions", "https://framework7.io/react/react-component-extensions.html", "core"),
    ("navigation-router",          "https://framework7.io/react/navigation-router.html",          "core"),
    ("colors",                     "https://framework7.io/react/colors.html",                     "core"),
    ("store",                      "https://framework7.io/react/store.html",                      "core"),
    ("app",                        "https://framework7.io/react/app.html",                        "component"),
    ("accordion",                  "https://framework7.io/react/accordion.html",                  "component"),
    ("action-sheet",               "https://framework7.io/react/action-sheet.html",               "component"),
    ("area-chart",                 "https://framework7.io/react/area-chart.html",                 "component"),
    ("autocomplete",               "https://framework7.io/react/autocomplete.html",               "component"),
    ("badge",                      "https://framework7.io/react/badge.html",                      "component"),
    ("block",                      "https://framework7.io/react/block.html",                      "component"),
    ("breadcrumbs",                "https://framework7.io/react/breadcrumbs.html",                "component"),
    ("button",                     "https://framework7.io/react/button.html",                     "component"),
    ("calendar",                   "https://framework7.io/react/calendar.html",                   "component"),
    ("cards",                      "https://framework7.io/react/cards.html",                      "component"),
    ("checkbox",                   "https://framework7.io/react/checkbox.html",                   "component"),
    ("chips",                      "https://framework7.io/react/chips.html",                      "component"),
    ("color-picker",               "https://framework7.io/react/color-picker.html",               "component"),
    ("contacts-list",              "https://framework7.io/react/contacts-list.html",              "component"),
    ("data-table",                 "https://framework7.io/react/data-table.html",                 "component"),
    ("dialog",                     "https://framework7.io/react/dialog.html",                     "component"),
    ("floating-action-button",     "https://framework7.io/react/floating-action-button.html",     "component"),
    ("form",                       "https://framework7.io/react/form.html",                       "component"),
    ("gauge",                      "https://framework7.io/react/gauge.html",                      "component"),
    ("grid",                       "https://framework7.io/react/grid.html",                       "component"),
    ("icon",                       "https://framework7.io/react/icon.html",                       "component"),
    ("infinite-scroll",            "https://framework7.io/react/infinite-scroll.html",            "component"),
    ("inputs",                     "https://framework7.io/react/inputs.html",                     "component"),
    ("link",                       "https://framework7.io/react/link.html",                       "component"),
    ("list-view",                  "https://framework7.io/react/list-view.html",                  "component"),
    ("list-button",                "https://framework7.io/react/list-button.html",                "component"),
    ("list-index",                 "https://framework7.io/react/list-index.html",                 "component"),
    ("list-item",                  "https://framework7.io/react/list-item.html",                  "component"),
    ("login-screen",               "https://framework7.io/react/login-screen.html",               "component"),
    ("menu-list",                  "https://framework7.io/react/menu-list.html",                  "component"),
    ("messagebar",                 "https://framework7.io/react/messagebar.html",                 "component"),
    ("messages",                   "https://framework7.io/react/messages.html",                   "component"),
    ("navbar",                     "https://framework7.io/react/navbar.html",                     "component"),
    ("notification",               "https://framework7.io/react/notification.html",               "component"),
    ("page",                       "https://framework7.io/react/page.html",                       "component"),
    ("panel",                      "https://framework7.io/react/panel.html",                      "component"),
    ("photo-browser",              "https://framework7.io/react/photo-browser.html",              "component"),
    ("picker",                     "https://framework7.io/react/picker.html",                     "component"),
    ("pie-chart",                  "https://framework7.io/react/pie-chart.html",                  "component"),
    ("popover",                    "https://framework7.io/react/popover.html",                    "component"),
    ("popup",                      "https://framework7.io/react/popup.html",                      "component"),
    ("preloader",                  "https://framework7.io/react/preloader.html",                  "component"),
    ("progressbar",                "https://framework7.io/react/progressbar.html",                "component"),
    ("pull-to-refresh",            "https://framework7.io/react/pull-to-refresh.html",            "component"),
    ("radio",                      "https://framework7.io/react/radio.html",                      "component"),
    ("range-slider",               "https://framework7.io/react/range-slider.html",               "component"),
    ("searchbar",                  "https://framework7.io/react/searchbar.html",                  "component"),
    ("segmented",                  "https://framework7.io/react/segmented.html",                  "component"),
    ("sheet-modal",                "https://framework7.io/react/sheet-modal.html",                "component"),
    ("skeleton",                   "https://framework7.io/react/skeleton.html",                   "component"),
    ("smart-select",               "https://framework7.io/react/smart-select.html",               "component"),
    ("sortable",                   "https://framework7.io/react/sortable.html",                   "component"),
    ("stepper",                    "https://framework7.io/react/stepper.html",                    "component"),
    ("subnavbar",                  "https://framework7.io/react/subnavbar.html",                  "component"),
    ("swipeout",                   "https://framework7.io/react/swipeout.html",                   "component"),
    ("swiper",                     "https://framework7.io/react/swiper.html",                     "component"),
    ("tabs",                       "https://framework7.io/react/tabs.html",                       "component"),
    ("text-editor",                "https://framework7.io/react/text-editor.html",                "component"),
    ("timeline",                   "https://framework7.io/react/timeline.html",                   "component"),
    ("toast",                      "https://framework7.io/react/toast.html",                      "component"),
    ("toggle",                     "https://framework7.io/react/toggle.html",                     "component"),
    ("toolbar-tabbar",             "https://framework7.io/react/toolbar-tabbar.html",             "component"),
    ("tooltip",                    "https://framework7.io/react/tooltip.html",                    "component"),
    ("treeview",                   "https://framework7.io/react/treeview.html",                   "component"),
    ("view",                       "https://framework7.io/react/view.html",                       "component"),
    ("virtual-list",               "https://framework7.io/react/virtual-list.html",               "component"),
]

_TS_TYPE_RE = re.compile(
    r"^([A-Za-z_][A-Za-z0-9_.<>[\], ]*|\([^)]*\)\s*=>\s*[A-Za-z_][A-Za-z0-9_.<>[\], ]*)(\s*(\||&)\s*([A-Za-z_][A-Za-z0-9_.<>[\], ]*|\([^)]*\)\s*=>\s*[A-Za-z_][A-Za-z0-9_.<>[\], ]*))*$"
)

def is_valid_ts_type(ts_type: str) -> bool:
    t = (ts_type or "").strip()
    if not t:
        return False
    return _TS_TYPE_RE.match(t) is not None

class Prop(BaseModel):
    name: str
    ts_type: str
    default: Optional[str]
    required: bool
    description: str
    source_text: Optional[str] = None
    source_table_header: Optional[str] = None
    inference_method: str = "table"
    confidence: str = "high"

    @field_validator("name")
    @classmethod
    def name_must_be_identifierish(cls, v: str) -> str:
        val = (v or "").strip()
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_:-]*$", val):
            raise ValueError(f"Invalid prop name: {v}")
        return val

    @field_validator("ts_type")
    @classmethod
    def ts_type_must_be_valid(cls, v: str) -> str:
        val = (v or "").strip()
        if not is_valid_ts_type(val):
            raise ValueError(f"Invalid TypeScript type: {v}")
        return val

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        return (v or "").strip() or "No description provided."

class EventEntry(BaseModel):
    name: str
    ts_type: str
    description: str
    source_text: Optional[str] = None
    source_table_header: Optional[str] = None
    inference_method: str = "table"
    confidence: str = "high"

    @field_validator("ts_type")
    @classmethod
    def event_ts_type_must_be_valid(cls, v: str) -> str:
        val = (v or "").strip()
        if not is_valid_ts_type(val):
            raise ValueError(f"Invalid event TypeScript type: {v}")
        return val

    @field_validator("description")
    @classmethod
    def event_description_not_empty(cls, v: str) -> str:
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
    examples: list[str] = []
    tsx_example: str
    notes: list[str]

    @field_validator("description")
    @classmethod
    def component_description_not_empty(cls, v: str) -> str:
        val = (v or "").strip()
        if len(val) < 10:
            raise ValueError("Component description is too short.")
        return val

async def fetch_html(url: str, page) -> str:
    ck = CACHE_DIR / (hashlib.md5(url.encode()).hexdigest() + ".html")
    if ck.exists():
        return ck.read_text(encoding="utf-8")
    if page is not None:
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(600)
        html = await page.content()
    else:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=60) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    ck.write_text(html, encoding="utf-8")
    await asyncio.sleep(0.4)
    return html

_TYPE_MAP = {
    "boolean": "boolean", "bool": "boolean",
    "string": "string", "str": "string",
    "number": "number", "integer": "number", "int": "number", "float": "number",
    "function": "() => void", "func": "() => void",
    "object": "Record<string, unknown>",
    "array": "unknown[]",
    "any": "unknown", "mixed": "unknown",
    "reactnode": "React.ReactNode", "node": "React.ReactNode",
    "element": "React.ReactElement", "reactelement": "React.ReactElement",
    "ref": "React.Ref<unknown>",
    "": "unknown",
}

def normalise_type(raw: str) -> str:
    if not raw:
        return "unknown"
    clean = raw.strip().lower()
    clean = re.sub(r"\b(function|func)\s*\([^)]*\)", "function", clean)
    if clean.startswith("function(") or clean.startswith("func("):
        return "() => void"
    clean = clean.replace(";", " ").replace(",", " | ").replace("/", " | ")
    clean = re.sub(r"\bor\b", "|", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    if "|" in clean:
        parts = [normalise_type(p.strip()) for p in clean.split("|")]
        seen, uniq = set(), []
        for p in parts:
            if p and p not in seen:
                seen.add(p)
                uniq.append(p)
        return " | ".join(uniq) if uniq else "unknown"
    if " " in clean:
        parts = [p for p in re.split(r"\s+", clean) if p]
        if len(parts) > 1:
            mapped = [m for m in (normalise_type(p) for p in parts) if m]
            return " | ".join(mapped) if mapped else "unknown"
    if clean.endswith("[]"):
        return normalise_type(clean[:-2]) + "[]"
    if clean.startswith("array of "):
        return normalise_type(clean.replace("array of ", "", 1)) + "[]"
    return _TYPE_MAP.get(clean, raw.strip())

def split_prop_names(name: str) -> list[str]:
    n = (name or "").strip().rstrip("*").strip()
    if not n:
        return []
    if re.match(r"^[A-Za-z_][A-Za-z0-9_:-]*$", n):
        return [n]
    parts = [p for p in re.split(r"\s+", n) if p]
    if len(parts) > 1 and all(re.match(r"^[A-Za-z_][A-Za-z0-9_:-]*$", p) for p in parts):
        return parts
    return []

def parse_prop_tables(soup: BeautifulSoup) -> tuple[list[dict], list[dict]]:
    props: list[dict] = []
    events: list[dict] = []

    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
        if not headers:
            first_tr = table.find("tr")
            if first_tr:
                headers = [td.get_text(strip=True).lower() for td in first_tr.find_all(["td", "th"])]

        col = {}
        for i, h in enumerate(headers):
            h_norm = h.strip().lower()
            if h_norm.startswith("<") and h_norm.endswith(">"):
                continue
            if re.search(r"\b(prop|name|parameter|event)\b", h_norm) and "name" not in col:
                col["name"] = i
            elif "type" in h_norm and "type" not in col:
                col["type"] = i
            elif "default" in h_norm and "default" not in col:
                col["default"] = i
            elif ("description" in h_norm or "desc" in h_norm) and "description" not in col:
                col["description"] = i

        if "name" not in col:
            continue

        is_event = any("event" in h or "callback" in h for h in headers)
        table_header = " | ".join(headers)

        for tr in table.find_all("tr")[1:]:
            cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
            if not cells or len(cells) < 2:
                continue

            def cell(key: str) -> str:
                idx = col.get(key)
                return cells[idx].strip() if idx is not None and idx < len(cells) else ""

            name = cell("name")
            if not name or name.lower() in ("prop", "name", "parameter"):
                continue

            raw_type = cell("type")
            ts_type  = normalise_type(raw_type)
            default  = cell("default") or None
            if default in ("-", "—", "undefined", "null", ""):
                default = None
            desc = cell("description")
            required = name.endswith("*") or "required" in desc.lower()
            names = split_prop_names(name)
            if not names:
                continue

            for one_name in names:
                entry = {
                    "name": one_name,
                    "ts_type": ts_type,
                    "raw_type": raw_type,
                    "default": default,
                    "required": required,
                    "description": desc,
                    "source_text": " | ".join(cells),
                    "source_table_header": table_header,
                    "inference_method": "table",
                    "confidence": "high",
                }
                if is_event:
                    entry["ts_type"] = infer_event_type(one_name, raw_type)
                    entry["inference_method"] = "event_name_inference"
                    entry["confidence"] = "medium"
                    events.append(entry)
                else:
                    props.append(entry)

    return props, events

def infer_event_type(name: str, raw_type: str) -> str:
    n = name.lower()
    if n in ("onclick", "ontap"):
        return "(e: React.MouseEvent) => void"
    if n == "onchange":
        return "(value: unknown) => void"
    if n in ("oninput", "onkeydown", "onkeyup", "onkeypress"):
        return "(e: React.KeyboardEvent) => void"
    if n in ("onfocus", "onblur"):
        return "(e: React.FocusEvent) => void"
    if n == "onsubmit":
        return "(e: React.FormEvent) => void"
    return "() => void"

def extract_description(soup: BeautifulSoup) -> str:
    h1 = soup.find("h1")
    if h1:
        nxt = h1.find_next_sibling()
        while nxt:
            if nxt.name == "p":
                txt = nxt.get_text(" ", strip=True)
                if len(txt) > 20:
                    return txt[:300]
            if nxt.name in ("h2", "table"):
                break
            nxt = nxt.find_next_sibling()
    text = trafilatura.extract(str(soup), include_tables=False) or ""
    for s in re.split(r"(?<=[.!?])\s+", text)[:5]:
        if len(s) > 30:
            return s[:300]
    return ""

def extract_component_name(soup: BeautifulSoup, slug: str) -> str:
    h1 = soup.find("h1")
    if h1:
        txt = h1.get_text(strip=True)
        name = re.split(r"\s*/\s*|\s+component", txt, flags=re.I)[0].strip()
        name = "".join(w.capitalize() for w in re.split(r"[\s\-_]+", name))
        if name:
            return name
    return "".join(w.capitalize() for w in slug.split("-"))

def extract_code_examples(soup: BeautifulSoup) -> list[str]:
    blocks = []
    for pre in soup.find_all("pre"):
        code = pre.find("code") or pre
        txt = code.get_text()
        if len(txt) > 30:
            blocks.append(txt)
    return blocks

def extract_structured_sections(soup: BeautifulSoup) -> dict:
    out = {"methods": [], "slots": [], "examples": [], "notes": []}
    for heading in soup.find_all(["h2", "h3"]):
        title = heading.get_text(" ", strip=True).lower()
        bucket = None
        if "method" in title:
            bucket = "methods"
        elif "slot" in title:
            bucket = "slots"
        elif "example" in title:
            bucket = "examples"
        elif "note" in title or "tip" in title or "warning" in title:
            bucket = "notes"
        if not bucket:
            continue
        node = heading.find_next_sibling()
        while node and node.name not in ("h2", "h3"):
            if node.name in ("ul", "ol"):
                for li in node.find_all("li"):
                    txt = li.get_text(" ", strip=True)
                    if 3 < len(txt) < 220:
                        out[bucket].append(txt)
            elif node.name == "p":
                txt = node.get_text(" ", strip=True)
                if 10 < len(txt) < 260:
                    out[bucket].append(txt)
            node = node.find_next_sibling()
    for k, v in out.items():
        out[k] = list(dict.fromkeys(v))[:12]
    return out

def dedupe_entries(entries: list[dict]) -> list[dict]:
    by_name: dict[str, dict] = {}
    order: list[str] = []
    for e in entries:
        name = (e.get("name") or "").strip()
        if not name:
            continue
        if name not in by_name:
            by_name[name] = e
            order.append(name)
            continue
        cur = by_name[name]
        if len((e.get("description") or "")) > len((cur.get("description") or "")):
            cur["description"] = e["description"]
        if cur.get("default") in (None, "") and e.get("default") not in (None, ""):
            cur["default"] = e["default"]
        if (cur.get("ts_type") or "").strip().lower() == "unknown" and (e.get("ts_type") or "").strip():
            cur["ts_type"] = e["ts_type"]
        by_name[name] = cur
    return [by_name[n] for n in order]

_JSX_ONLY_PATTERNS = [
    (r"[A-Za-z]+\.propTypes\s*=\s*\{[^}]*\}", ""),
    (r"[A-Za-z]+\.defaultProps\s*=\s*\{[^}]*\}", ""),
    (r"React\.createClass\(", "React.Component("),
]

def jsx_to_tsx(code: str, component_name: str, props: list[dict]) -> str:
    if not code or len(code) < 10:
        return code
    for pat, repl in _JSX_ONLY_PATTERNS:
        code = re.sub(pat, repl, code, flags=re.DOTALL)
    code = re.sub(
        rf"(const\s+{component_name})\s*=\s*\((.*?)\)\s*=>",
        rf"\1: React.FC<{component_name}Props> = (\2) =>",
        code, flags=re.DOTALL
    )
    code = re.sub(
        rf"(function\s+{component_name})\s*\((.*?)\)\s*\{{",
        rf"\1(\2: {component_name}Props): JSX.Element {{",
        code, flags=re.DOTALL
    )
    if props and f"interface {component_name}Props" not in code:
        prop_lines = []
        for p in props[:12]:
            opt = "" if p.get("required") else "?"
            prop_lines.append(f"  {p['name']}{opt}: {p['ts_type']};")
        interface = f"interface {component_name}Props {{\n" + "\n".join(prop_lines) + "\n}\n\n"
        code = interface + code
    if "import React" not in code and "from 'react'" not in code:
        code = "import React from 'react';\n" + code
    code = code.replace(".jsx", ".tsx")
    code = re.sub(r"useState\(\)", "useState<unknown>()", code)
    code = re.sub(r"useState\(null\)", "useState<unknown>(null)", code)
    code = re.sub(r"\n{3,}", "\n\n", code).strip()
    return code

def build_import_statement(component_name: str, slug: str) -> str:
    names = {component_name}
    for p in slug.replace("-", " ").title().split():
        names.add(p)
    return f"import {{ {', '.join(sorted(names))} }} from 'framework7-react';"

def assemble(slug: str, url: str, category: str, html: str) -> ComponentDoc:
    soup = BeautifulSoup(html, "lxml")
    component   = extract_component_name(soup, slug)
    description = extract_description(soup)
    props_raw, events_raw = parse_prop_tables(soup)
    code_blocks = extract_code_examples(soup)
    sections    = extract_structured_sections(soup)

    props_raw  = dedupe_entries(props_raw)
    events_raw = dedupe_entries(events_raw)

    best_code = ""
    for block in code_blocks:
        if component in block or slug.replace("-", "") in block.lower():
            best_code = block
            break
    if not best_code and code_blocks:
        best_code = max(code_blocks, key=len)

    tsx_example = jsx_to_tsx(best_code, component, props_raw) if best_code else (
        f"import React from 'react';\n"
        f"import {{ {component} }} from 'framework7-react';\n\n"
        f"interface {component}Props {{}}\n\n"
        f"const Example: React.FC = () => (\n"
        f"  <{component} />\n"
        f");\n\n"
        f"export default Example;"
    )

    props = [Prop(**{k: v for k, v in p.items() if k != "raw_type"}) for p in props_raw]
    events = [
        EventEntry(
            name=e["name"],
            ts_type=e["ts_type"],
            description=e["description"],
            source_text=e.get("source_text"),
            source_table_header=e.get("source_table_header"),
            inference_method=e.get("inference_method", "table"),
            confidence=e.get("confidence", "high"),
        )
        for e in events_raw
    ]

    notes = []
    for tag in soup.find_all("blockquote"):
        txt = tag.get_text(" ", strip=True)
        if 20 < len(txt) < 300:
            notes.append(txt)
    for tag in soup.select(".note, .warning, .tip, .alert"):
        txt = tag.get_text(" ", strip=True)
        if 20 < len(txt) < 300:
            notes.append(txt)
    notes.extend(sections.get("notes", []))
    notes = list(dict.fromkeys(notes))[:5]

    return ComponentDoc(
        slug=slug,
        url=url,
        component=component,
        category=category,
        description=description,
        import_statement=build_import_statement(component, slug),
        props=props,
        events=events,
        methods=sections.get("methods", []),
        slots=sections.get("slots", []),
        examples=sections.get("examples", []),
        tsx_example=tsx_example,
        notes=notes,
    )

def to_id(category: str, slug: str) -> str:
    return f"{'core' if category == 'core' else 'component'}:{slug}"

def doc_to_item(slug: str, category: str, doc: dict) -> dict:
    title   = doc.get("component") or "".join(w.capitalize() for w in slug.split("-"))
    summary = (doc.get("description") or "").strip() or f"Framework7 React {title} documentation."
    keywords = sorted(set(
        [slug, title, "framework7", "react", "typescript", "tsx"] +
        [p.get("name", "") for p in doc.get("props", []) if isinstance(p, dict)]
    ))
    return {
        "id": to_id(category, slug),
        "slug": slug,
        "title": title,
        "category": category,
        "summary": summary,
        "keywords": [k for k in keywords if k],
        "aliases": [slug.replace("-", ""), title.lower()],
        "url": doc.get("url"),
        "retrieval_text": "\n".join([
            summary,
            f"Props: {', '.join(p.get('name','') for p in doc.get('props', [])[:30] if isinstance(p, dict))}",
            f"Events: {', '.join(e.get('name','') for e in doc.get('events', [])[:30] if isinstance(e, dict))}",
        ]).strip(),
    }

def initialize_artifacts() -> None:
    now = datetime.now(timezone.utc).isoformat()
    write_artifacts({"meta": {"generated_at": now}, "core_docs": {}, "components": {}})

def write_artifacts(output: dict) -> None:
    generated_at = output["meta"]["generated_at"]
    version = "v9"
    docs = []
    for bucket, category in (("core_docs", "core"), ("components", "component")):
        for slug, item in output.get(bucket, {}).items():
            if not isinstance(item, dict) or "error" in item:
                continue
            doc_item = doc_to_item(slug, category, item)
            docs.append({
                **doc_item,
                "props": item.get("props", []),
                "events": item.get("events", []),
                "notes": item.get("notes", []),
                "tsx_example": item.get("tsx_example", ""),
                "content": "\n".join(filter(None, [
                    item.get("description", ""),
                    "Methods: " + ", ".join(item.get("methods", [])) if item.get("methods") else "",
                    "Slots: " + ", ".join(item.get("slots", [])) if item.get("slots") else "",
                ])).strip(),
            })
    docs.sort(key=lambda d: d["id"])
    manifest_items = [{k: d[k] for k in ("id", "slug", "title", "category", "summary", "keywords")} for d in docs]
    search_items   = [{k: d[k] for k in ("id", "slug", "title", "category", "summary", "keywords", "aliases", "url", "retrieval_text")} for d in docs]

    knowledge = {"version": version, "generatedAt": generated_at, "count": len(docs), "docs": docs}
    manifest  = {
        "version": version, "generatedAt": generated_at,
        "documentCount": len(docs),
        "componentCount": sum(1 for d in docs if d["category"] == "component"),
        "coreCount": sum(1 for d in docs if d["category"] == "core"),
        "count": len(docs), "items": manifest_items,
    }
    search_index = {"version": version, "generatedAt": generated_at, "count": len(search_items), "items": search_items}
    checksum = hashlib.sha256(json.dumps(knowledge, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    metadata = {
        "version": version, "generatedAt": generated_at,
        "documentCount": len(docs), "checksum": checksum, "buildId": generated_at,
        "stats": {
            "components": manifest["componentCount"],
            "core": manifest["coreCount"],
            "totalProps": sum(len(d.get("props", [])) for d in docs),
            "totalEvents": sum(len(d.get("events", [])) for d in docs),
        },
    }
    kv_bulk = {"manifest": manifest, "searchIndex": search_index, "metadata": metadata, "knowledge": knowledge}
    payloads = {
        "knowledge.json": knowledge,
        "manifest.json": manifest,
        "search-index.json": search_index,
        "metadata.json": metadata,
        "kv-bulk.json": kv_bulk,
    }
    for artifact in ARTIFACT_FILES:
        (DATA_DIR / artifact).write_text(
            json.dumps(payloads[artifact], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

async def process_all(page, output: dict) -> None:
    total = len(URLS)
    for i, (slug, url, category) in enumerate(URLS, 1):
        bucket = "core_docs" if category == "core" else "components"
        print(f"[{i:02d}/{total}] {slug}", end="  ", flush=True)
        try:
            html = await fetch_html(url, page)
            print(f"scraped({len(html)//1024}KB)", end="  ", flush=True)
        except Exception as e:
            print(f"SCRAPE FAIL: {e}")
            output[bucket][slug] = {"error": "scrape_failed", "url": url, "detail": str(e)}
            continue
        try:
            doc = assemble(slug, url, category, html)
            output[bucket][slug] = doc.model_dump(exclude={"slug", "category"})
            print(f"props={len(doc.props)} events={len(doc.events)}  ✓")
        except Exception as e:
            print(f"ASSEMBLE FAIL: {e}")
            output[bucket][slug] = {"error": "assemble_failed", "url": url, "detail": str(e)}
        if i % 10 == 0:
            write_artifacts(output)
            print(f"  ── checkpoint {i}/{total} ──")

async def main() -> None:
    output: dict = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "framework7.io",
            "target_stack": "React + TypeScript (TSX)",
            "total_pages": len(URLS),
        },
        "core_docs": {},
        "components": {},
    }

    initialize_artifacts()

    if async_playwright is None:
        print("Playwright unavailable, using urllib fallback")
        await process_all(None, output)
    else:
        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                ctx = await browser.new_context(
                    user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
                    java_script_enabled=True,
                )
                await ctx.route(
                    re.compile(r"\.(png|jpg|jpeg|gif|webp|svg|woff2?|ttf|eot|mp4|mp3|ico)(\?.*)?$"),
                    lambda r: r.abort()
                )
                page = await ctx.new_page()
                await process_all(page, output)
                await browser.close()
        except Exception as e:
            print(f"Playwright failed ({e}), falling back to urllib")
            await process_all(None, output)

    write_artifacts(output)
    print(f"\n{'─'*56}")
    print(f"Done.  core={len(output['core_docs'])}  components={len(output['components'])}")
    print(f"Output → {(DATA_DIR / 'knowledge.json').resolve()}")

if __name__ == "__main__":
    asyncio.run(main())
