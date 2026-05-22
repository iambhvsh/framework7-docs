from __future__ import annotations

import re
from typing import Any

STOPWORDS = {
    "framework7",
    "react",
    "component",
    "default",
    "value",
    "boolean",
    "string",
    "number",
    "true",
    "false",
}
MAX_SUMMARY_LENGTH = 260
BOOSTED_WEIGHTS = {
    "router": 1.3,
    "popup": 1.3,
    "dialog": 1.2,
    "store": 1.2,
    "sheet-modal": 1.15,
    "view": 1.15,
    "page": 1.1,
}


def normalize_component_name(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        return "Unknown"
    return re.sub(r"\s+", " ", raw)


def category_from_slug(slug: str, section_name: str) -> str:
    if section_name == "core_docs":
        return "core"
    if any(x in slug for x in ("chart", "picker", "editor", "store", "router")):
        return "advanced"
    return "component"


def build_summary(description: str, title: str) -> str:
    d = (description or "").strip()
    if d:
        if len(d) <= MAX_SUMMARY_LENGTH:
            return d
        cut = d[:MAX_SUMMARY_LENGTH]
        last_period = cut.rfind(".")
        if last_period > 100:
            return cut[: last_period + 1]
        return cut.rstrip() + "..."
    return f"{title} documentation entry for Framework7 React."


def extract_plaintext(doc: dict[str, Any]) -> str:
    chunks: list[str] = []
    desc = (doc.get("description") or "").strip()
    if desc:
        chunks.append(desc)

    props = doc.get("props") or []
    if props:
        chunks.append("Properties:")
        for p in props:
            name = p.get("name") or ""
            ts_type = p.get("ts_type") or "unknown"
            pdesc = (p.get("description") or "").strip()
            chunks.append(f"- {name} ({ts_type}): {pdesc}")

    events = doc.get("events") or []
    if events:
        chunks.append("Events:")
        for e in events:
            name = e.get("name") or ""
            ts_type = e.get("ts_type") or "unknown"
            edesc = (e.get("description") or "").strip()
            chunks.append(f"- {name} ({ts_type}): {edesc}")

    notes = doc.get("notes") or []
    if notes:
        chunks.append("Notes:")
        chunks.extend(f"- {n}" for n in notes)

    return "\n".join(chunks).strip()


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]{1,30}", (text or "").lower())
    seen: set[str] = set()
    out: list[str] = []
    for w in words:
        if w in STOPWORDS or w in seen:
            continue
        seen.add(w)
        out.append(w)
    return out


def build_aliases(slug: str, title: str, doc: dict[str, Any]) -> list[str]:
    aliases = [slug, slug.replace("-", " "), title, title.lower()]
    for p in doc.get("props") or []:
        name = (p.get("name") or "").strip()
        if name:
            aliases.append(f"{slug}:{name}")
    for e in doc.get("events") or []:
        name = (e.get("name") or "").strip()
        if name:
            aliases.append(f"{slug}:{name}")
    seen: list[str] = []
    for a in aliases:
        a = a.strip()
        if a and a not in seen:
            seen.append(a)
    return seen[:50]


def build_keywords(slug: str, title: str, category: str, doc: dict[str, Any]) -> list[str]:
    text_parts = [slug, title, category, doc.get("description") or ""]
    for p in doc.get("props") or []:
        text_parts.append(p.get("name") or "")
    for e in doc.get("events") or []:
        text_parts.append(e.get("name") or "")
    for n in doc.get("notes") or []:
        text_parts.append(str(n))
    keywords = tokenize(" ".join(text_parts))
    return keywords[:64]


def build_retrieval_text(title: str, doc: dict[str, Any]) -> str:
    parts: list[str] = [title, (doc.get("description") or "").strip()]
    parts.extend((p.get("name") or "").strip() for p in (doc.get("props") or []))
    parts.extend((e.get("name") or "").strip() for e in (doc.get("events") or []))
    parts.extend(str(n).strip() for n in (doc.get("notes") or []))
    joined = "\n".join(p for p in parts if p)
    return re.sub(r"\n{3,}", "\n\n", joined).strip()


def search_boost(slug: str) -> float:
    return BOOSTED_WEIGHTS.get(slug, 1.0)
