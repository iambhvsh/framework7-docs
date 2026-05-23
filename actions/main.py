#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()
import asyncio, hashlib, json, re
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
    "knowledge.json", "manifest.json", "search-index.json",
    "metadata.json", "kv-bulk.json",
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

# ── Type validation ───────────────────────────────────────────────────────────

_TS_TYPE_RE = re.compile(
    r"^([A-Za-z_][A-Za-z0-9_.<>[\], ]*"
    r"|\([^)]*\)\s*=>\s*[A-Za-z_][A-Za-z0-9_.<>[\], ]*)"
    r"(\s*(\||&)\s*"
    r"([A-Za-z_][A-Za-z0-9_.<>[\], ]*"
    r"|\([^)]*\)\s*=>\s*[A-Za-z_][A-Za-z0-9_.<>[\], ]*))*$"
)

def is_valid_ts_type(ts_type: str) -> bool:
    t = (ts_type or "").strip()
    return bool(t and _TS_TYPE_RE.match(t))

# ── Pydantic models ───────────────────────────────────────────────────────────

class Prop(BaseModel):
    name: str
    ts_type: str
    default: Optional[str]
    required: bool
    description: str
    source_table_header: Optional[str] = None
    inference_method: str = "table"
    confidence: str = "high"

    @field_validator("name")
    @classmethod
    def name_ok(cls, v: str) -> str:
        val = (v or "").strip()
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_:-]*$", val):
            raise ValueError(f"Bad prop name: {v!r}")
        return val

    @field_validator("ts_type")
    @classmethod
    def type_ok(cls, v: str) -> str:
        val = (v or "").strip()
        if not is_valid_ts_type(val):
            raise ValueError(f"Bad TS type: {v!r}")
        return val

    @field_validator("description")
    @classmethod
    def desc_ok(cls, v: str) -> str:
        return (v or "").strip() or "No description provided."

class EventEntry(BaseModel):
    name: str
    ts_type: str
    description: str
    source_table_header: Optional[str] = None
    inference_method: str = "table"
    confidence: str = "high"

    @field_validator("ts_type")
    @classmethod
    def type_ok(cls, v: str) -> str:
        val = (v or "").strip()
        if not is_valid_ts_type(val):
            raise ValueError(f"Bad event TS type: {v!r}")
        return val

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
    examples: list[str] = []
    tsx_example: str
    notes: list[str]

    @field_validator("description")
    @classmethod
    def desc_ok(cls, v: str) -> str:
        val = (v or "").strip()
        if len(val) < 10:
            raise ValueError("Description too short.")
        return val

# ── Fetch (Playwright-only, no urllib fallback for CF-protected site) ─────────

MIN_USEFUL_HTML = 50_000  # bytes — shell-only pages are ~21 bytes or ~30KB

def cache_key(url: str) -> Path:
    return CACHE_DIR / (hashlib.md5(url.encode()).hexdigest() + ".html")

def cache_valid(path: Path) -> bool:
    if not path.exists():
        return False
    content = path.read_text(encoding="utf-8", errors="replace")
    # Reject stale shells: must contain a <table and a <td to be a real page
    return len(content) >= MIN_USEFUL_HTML and "<table" in content and "<td" in content

async def fetch_html(url: str, page) -> str:
    ck = cache_key(url)
    if cache_valid(ck):
        return ck.read_text(encoding="utf-8")

    if page is None:
        raise RuntimeError("Playwright required (site blocks plain HTTP)")

    await page.goto(url, wait_until="networkidle", timeout=60_000)
    # Wait until at least one <table> with <td> cells is in the DOM
    try:
        await page.wait_for_selector("table td", timeout=15_000)
    except Exception:
        pass  # page may genuinely have no tables (intro pages)
    await page.wait_for_timeout(500)

    html = await page.content()
    ck.write_text(html, encoding="utf-8")
    await asyncio.sleep(0.3)
    return html

# ── Type normalisation ────────────────────────────────────────────────────────

_TYPE_MAP: dict[str, str] = {
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

# Known two-word type phrases the docs write as "string boolean" (space-separated union)
_SPACE_UNION_RE = re.compile(
    r"^(string|number|boolean|object|array|function|any|unknown)"
    r"(\s+(string|number|boolean|object|array|function|any|unknown))+$"
)

def normalise_type(raw: str) -> str:
    if not raw:
        return "unknown"
    stripped = raw.strip()

    # Framework7 docs write "string   boolean" (multi-space) for unions — handle first
    normalised_spaces = re.sub(r"\s{2,}", "  ", stripped)  # collapse to double-space sentinel
    if "  " in normalised_spaces:
        parts = [normalise_type(p.strip()) for p in re.split(r"\s{2,}", stripped) if p.strip()]
        parts = list(dict.fromkeys(p for p in parts if p))
        return " | ".join(parts) if parts else "unknown"

    clean = stripped.lower()
    clean = re.sub(r"\b(function|func)\s*\([^)]*\)", "function", clean)
    if clean.startswith("function(") or clean.startswith("func("):
        return "() => void"

    # Pipe/slash/comma/semicolon unions
    if any(c in clean for c in ("|", "/", ",")):
        sep = "|" if "|" in clean else ("/" if "/" in clean else ",")
        parts = [normalise_type(p.strip()) for p in clean.split(sep)]
        parts = list(dict.fromkeys(p for p in parts if p))
        return " | ".join(parts) if parts else "unknown"

    clean = re.sub(r"\bor\b", "|", clean)
    if "|" in clean:
        parts = [normalise_type(p.strip()) for p in clean.split("|")]
        parts = list(dict.fromkeys(p for p in parts if p))
        return " | ".join(parts) if parts else "unknown"

    if clean.endswith("[]"):
        return normalise_type(clean[:-2]) + "[]"
    if clean.startswith("array of "):
        return normalise_type(clean[len("array of "):]) + "[]"

    # Single-word space union (e.g. "string boolean" — rare but present)
    if " " in clean and _SPACE_UNION_RE.match(clean):
        parts = list(dict.fromkeys(normalise_type(p) for p in clean.split()))
        return " | ".join(parts)

    return _TYPE_MAP.get(clean, stripped)

# ── Table parsing ─────────────────────────────────────────────────────────────

def _is_section_header_row(tr) -> bool:
    """Detect rows like <tr><th colspan="4">&lt;Button&gt; properties</th></tr>."""
    tds = tr.find_all(["th", "td"])
    if len(tds) == 1 and tds[0].get("colspan"):
        return True
    # Also catches rows where ALL cells are <th> and the first looks like a section label
    if all(td.name == "th" for td in tds):
        first = tds[0].get_text(strip=True)
        if first.startswith("<") or "properties" in first.lower() or "events" in first.lower():
            return True
    return False

def parse_prop_tables(soup: BeautifulSoup) -> tuple[list[dict], list[dict]]:
    props: list[dict] = []
    events: list[dict] = []

    for table in soup.find_all("table"):
        # ── Detect column layout from <thead> or first non-section-header <tr> ──
        thead = table.find("thead")
        header_row = None
        if thead:
            header_row = thead.find("tr")
        if not header_row:
            for tr in table.find_all("tr"):
                if not _is_section_header_row(tr):
                    header_row = tr
                    break
        if not header_row:
            continue

        headers = [th.get_text(strip=True).lower() for th in header_row.find_all(["th", "td"])]
        col: dict[str, int] = {}
        for i, h in enumerate(headers):
            if re.search(r"\b(prop|name|parameter|event)\b", h) and "name" not in col:
                col["name"] = i
            elif "type" in h and "type" not in col:
                col["type"] = i
            elif "default" in h and "default" not in col:
                col["default"] = i
            elif ("description" in h or "desc" in h) and "description" not in col:
                col["description"] = i

        if "name" not in col:
            continue

        is_event_table = any("event" in h or "callback" in h for h in headers)
        table_header = " | ".join(headers)

        for tr in table.find_all("tr"):
            if _is_section_header_row(tr):
                # Check if this section header changes event/prop context
                label = tr.get_text(strip=True).lower()
                if "event" in label:
                    is_event_table = True
                elif "propert" in label:
                    is_event_table = False
                continue

            cells = tr.find_all("td")
            if not cells or len(cells) < 2:
                continue

            def cell(key: str) -> str:
                idx = col.get(key)
                if idx is None or idx >= len(cells):
                    return ""
                return cells[idx].get_text(" ", strip=True).strip()

            raw_name = cell("name")
            if not raw_name or raw_name.lower() in ("prop", "name", "parameter", "event"):
                continue

            # Split merged names like "ptr ptrDistance ptrPreloader"
            clean_name = raw_name.rstrip("*").strip()
            name_parts = [clean_name]
            if not re.match(r"^[A-Za-z_][A-Za-z0-9_:-]*$", clean_name):
                candidates = re.split(r"\s+", clean_name)
                if all(re.match(r"^[A-Za-z_][A-Za-z0-9_:-]*$", p) for p in candidates if p):
                    name_parts = [p for p in candidates if p]

            raw_type = cell("type")
            ts_type   = normalise_type(raw_type)
            default   = cell("default") or None
            if default in ("-", "—", "undefined", "null", ""):
                default = None
            desc      = cell("description")
            required  = raw_name.endswith("*") or "required" in desc.lower()

            for name in name_parts:
                if not re.match(r"^[A-Za-z_][A-Za-z0-9_:-]*$", name):
                    continue
                entry = {
                    "name": name,
                    "ts_type": ts_type,
                    "raw_type": raw_type,
                    "default": default,
                    "required": required,
                    "description": desc,
                    "source_table_header": table_header,
                    "inference_method": "table",
                    "confidence": "high",
                }
                if is_event_table:
                    entry["ts_type"] = infer_event_type(name, raw_type)
                    entry["inference_method"] = "event_name_inference"
                    entry["confidence"] = "medium"
                    events.append(entry)
                else:
                    props.append(entry)

    return props, events

def infer_event_type(name: str, raw_type: str) -> str:
    n = name.lower()
    if n in ("onclick", "ontap"):        return "(e: React.MouseEvent) => void"
    if n == "onchange":                  return "(value: unknown) => void"
    if n in ("oninput", "onkeydown", "onkeyup", "onkeypress"):
                                         return "(e: React.KeyboardEvent) => void"
    if n in ("onfocus", "onblur"):       return "(e: React.FocusEvent) => void"
    if n == "onsubmit":                  return "(e: React.FormEvent) => void"
    return "() => void"

# ── Page extraction helpers ───────────────────────────────────────────────────

def extract_description(soup: BeautifulSoup) -> str:
    h1 = soup.find("h1")
    if h1:
        nxt = h1.find_next_sibling()
        while nxt:
            if nxt.name == "p":
                txt = nxt.get_text(" ", strip=True)
                if len(txt) > 20:
                    return txt[:400]
            if nxt.name in ("h2", "table"):
                break
            nxt = nxt.find_next_sibling()
    text = trafilatura.extract(str(soup), include_tables=False) or ""
    for s in re.split(r"(?<=[.!?])\s+", text)[:5]:
        if len(s) > 30:
            return s[:400]
    return ""

def extract_component_name(soup: BeautifulSoup, slug: str) -> str:
    h1 = soup.find("h1")
    if h1:
        txt = h1.get_text(strip=True)
        name = re.split(r"\s*/\s*|\s+(?:react\s+)?component", txt, flags=re.I)[0].strip()
        name = "".join(w.capitalize() for w in re.split(r"[\s\-_]+", name))
        if name:
            return name
    return "".join(w.capitalize() for w in slug.split("-"))

def extract_code_examples(soup: BeautifulSoup) -> list[str]:
    return [
        (pre.find("code") or pre).get_text()
        for pre in soup.find_all("pre")
        if len((pre.find("code") or pre).get_text()) > 30
    ]

def extract_structured_sections(soup: BeautifulSoup) -> dict:
    out: dict[str, list[str]] = {"methods": [], "slots": [], "examples": [], "notes": []}
    bucket_map = {"method": "methods", "slot": "slots", "example": "examples",
                  "note": "notes", "tip": "notes", "warning": "notes"}
    for heading in soup.find_all(["h2", "h3"]):
        title = heading.get_text(" ", strip=True).lower()
        bucket = next((v for k, v in bucket_map.items() if k in title), None)
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
    return {k: list(dict.fromkeys(v))[:12] for k, v in out.items()}

def dedupe(entries: list[dict]) -> list[dict]:
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
        if len(e.get("description") or "") > len(cur.get("description") or ""):
            cur["description"] = e["description"]
        if not cur.get("default") and e.get("default"):
            cur["default"] = e["default"]
        if (cur.get("ts_type") or "").lower() == "unknown" and (e.get("ts_type") or ""):
            cur["ts_type"] = e["ts_type"]
    return [by_name[n] for n in order]

# ── JSX → TSX transforms ──────────────────────────────────────────────────────

_STRIP_PATTERNS = [
    (r"[A-Za-z]+\.propTypes\s*=\s*\{[^}]*\}", ""),
    (r"[A-Za-z]+\.defaultProps\s*=\s*\{[^}]*\}", ""),
    (r"React\.createClass\(", "React.Component("),
]

def jsx_to_tsx(code: str, component_name: str, props: list[dict]) -> str:
    if not code or len(code) < 10:
        return code
    for pat, repl in _STRIP_PATTERNS:
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
        lines = [
            f"  {p['name']}{'?' if not p.get('required') else ''}: {p['ts_type']};"
            for p in props[:15]
        ]
        code = f"interface {component_name}Props {{\n" + "\n".join(lines) + "\n}\n\n" + code
    if "import React" not in code and "from 'react'" not in code:
        code = "import React from 'react';\n" + code
    code = code.replace(".jsx", ".tsx")
    code = re.sub(r"useState\(\)", "useState<unknown>()", code)
    code = re.sub(r"useState\(null\)", "useState<unknown>(null)", code)
    return re.sub(r"\n{3,}", "\n\n", code).strip()

def build_import_statement(component_name: str, slug: str) -> str:
    names = {component_name}
    for p in slug.replace("-", " ").title().split():
        names.add(p)
    return f"import {{ {', '.join(sorted(names))} }} from 'framework7-react';"

# ── Assembly ──────────────────────────────────────────────────────────────────

def assemble(slug: str, url: str, category: str, html: str) -> ComponentDoc:
    soup = BeautifulSoup(html, "lxml")
    component   = extract_component_name(soup, slug)
    description = extract_description(soup)
    props_raw, events_raw = parse_prop_tables(soup)
    code_blocks = extract_code_examples(soup)
    sections    = extract_structured_sections(soup)

    props_raw  = dedupe(props_raw)
    events_raw = dedupe(events_raw)

    best_code = next(
        (b for b in code_blocks if component in b or slug.replace("-", "") in b.lower()),
        max(code_blocks, key=len) if code_blocks else ""
    )

    tsx_example = jsx_to_tsx(best_code, component, props_raw) if best_code else (
        f"import React from 'react';\n"
        f"import {{ {component} }} from 'framework7-react';\n\n"
        f"interface {component}Props {{}}\n\n"
        f"const Example: React.FC = () => (\n  <{component} />\n);\n\n"
        f"export default Example;"
    )

    props = []
    for p in props_raw:
        try:
            props.append(Prop(**{k: v for k, v in p.items() if k != "raw_type"}))
        except Exception:
            pass

    events = []
    for e in events_raw:
        try:
            events.append(EventEntry(
                name=e["name"], ts_type=e["ts_type"], description=e["description"],
                source_table_header=e.get("source_table_header"),
                inference_method=e.get("inference_method", "table"),
                confidence=e.get("confidence", "high"),
            ))
        except Exception:
            pass

    notes = []
    for tag in soup.find_all("blockquote"):
        txt = tag.get_text(" ", strip=True)
        if 20 < len(txt) < 300:
            notes.append(txt)
    for tag in soup.select(".note, .warning, .tip, .alert, .important-note"):
        txt = tag.get_text(" ", strip=True)
        if 20 < len(txt) < 300:
            notes.append(txt)
    notes.extend(sections.get("notes", []))
    notes = list(dict.fromkeys(notes))[:5]

    return ComponentDoc(
        slug=slug, url=url, component=component, category=category,
        description=description,
        import_statement=build_import_statement(component, slug),
        props=props, events=events,
        methods=sections.get("methods", []),
        slots=sections.get("slots", []),
        examples=sections.get("examples", []),
        tsx_example=tsx_example,
        notes=notes,
    )

# ── Artifact writers ──────────────────────────────────────────────────────────

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
        "id": to_id(category, slug), "slug": slug, "title": title,
        "category": category, "summary": summary,
        "keywords": [k for k in keywords if k],
        "aliases": [slug.replace("-", ""), title.lower()],
        "url": doc.get("url"),
        "retrieval_text": "\n".join(filter(None, [
            summary,
            "Props: " + ", ".join(p.get("name", "") for p in doc.get("props", [])[:30] if isinstance(p, dict)),
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
                    "Slots: "   + ", ".join(item.get("slots", []))   if item.get("slots") else "",
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
        "version": version, "generatedAt": generated_at, "documentCount": len(docs),
        "checksum": checksum, "buildId": generated_at,
        "stats": {
            "components": manifest["componentCount"], "core": manifest["coreCount"],
            "totalProps":  sum(len(d.get("props",  [])) for d in docs),
            "totalEvents": sum(len(d.get("events", [])) for d in docs),
        },
    }
    kv_bulk = {"manifest": manifest, "searchIndex": search_index, "metadata": metadata, "knowledge": knowledge}
    payloads = {
        "knowledge.json": knowledge, "manifest.json": manifest,
        "search-index.json": search_index, "metadata.json": metadata, "kv-bulk.json": kv_bulk,
    }
    for artifact in ARTIFACT_FILES:
        (DATA_DIR / artifact).write_text(
            json.dumps(payloads[artifact], indent=2, ensure_ascii=False), encoding="utf-8"
        )

# ── Main ──────────────────────────────────────────────────────────────────────

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
        "core_docs": {}, "components": {},
    }

    write_artifacts(output)  # empty init

    if async_playwright is None:
        raise RuntimeError("Playwright is required — site is Cloudflare-protected")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            java_script_enabled=True,
        )
        await ctx.route(
            re.compile(r"\.(png|jpg|jpeg|gif|webp|svg|woff2?|ttf|eot|mp4|mp3|ico)(\?.*)?$"),
            lambda r: r.abort()
        )
        page = await ctx.new_page()
        await process_all(page, output)
        await browser.close()

    write_artifacts(output)
    print(f"\n{'─'*56}")
    print(f"Done.  core={len(output['core_docs'])}  components={len(output['components'])}")
    print(f"Output → {(DATA_DIR / 'knowledge.json').resolve()}")

if __name__ == "__main__":
    asyncio.run(main())
