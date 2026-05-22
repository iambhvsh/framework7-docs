from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from extractors.framework7_loader import load_framework7_source
from processors.normalize import (
    build_aliases,
    build_keywords,
    build_retrieval_text,
    build_summary,
    category_from_slug,
    extract_plaintext,
    normalize_component_name,
    search_boost,
)


@dataclass
class GeneratedDoc:
    id: str
    slug: str
    title: str
    category: str
    url: str
    summary: str
    keywords: list[str]
    aliases: list[str]
    content: str
    tsx_example: str
    props: list[dict[str, Any]]
    events: list[dict[str, Any]]
    notes: list[str]


def stable_id(slug: str, category: str) -> str:
    raw = f"{category}:{slug}".encode("utf-8")
    digest = hashlib.sha1(raw).hexdigest()[:12]
    return f"f7-{digest}"


def related_doc_ids(
    current_id: str,
    current_category: str,
    current_keywords: list[str],
    by_id: dict[str, dict[str, Any]],
    limit: int = 3,
) -> list[str]:
    base = set(current_keywords[:32])
    if not base:
        return []
    scored: list[tuple[str, int]] = []
    for other_id, payload in by_id.items():
        if other_id == current_id:
            continue
        if payload.get("category") != current_category:
            continue
        other_kw = set((payload.get("keywords") or [])[:32])
        overlap = len(base.intersection(other_kw))
        if overlap > 0:
            scored.append((other_id, overlap))
    scored.sort(key=lambda x: (-x[1], x[0]))
    return [doc_id for doc_id, _score in scored[:limit]]


def collect_docs(source: dict[str, Any]) -> list[GeneratedDoc]:
    out: list[GeneratedDoc] = []
    for section_name in ("core_docs", "components"):
        docs = source.get(section_name, {})
        for slug, doc in docs.items():
            if not isinstance(doc, dict):
                continue
            if "error" in doc:
                continue

            category = category_from_slug(slug, section_name)
            title = normalize_component_name(doc.get("component") or slug)
            summary = build_summary(doc.get("description") or "", title)
            content = extract_plaintext(doc)
            keywords = build_keywords(slug=slug, title=title, category=category, doc=doc)
            aliases = build_aliases(slug=slug, title=title, doc=doc)

            out.append(
                GeneratedDoc(
                    id=stable_id(slug, category),
                    slug=slug,
                    title=title,
                    category=category,
                    url=str(doc.get("url") or ""),
                    summary=summary,
                    keywords=keywords,
                    aliases=aliases,
                    content=content,
                    tsx_example=str(doc.get("tsx_example") or ""),
                    props=list(doc.get("props") or []),
                    events=list(doc.get("events") or []),
                    notes=list(doc.get("notes") or []),
                )
            )
    out.sort(key=lambda d: (d.category, d.slug))
    return out


def validate_docs(docs: list[GeneratedDoc]) -> None:
    ids = set()
    for d in docs:
        if not d.id or d.id in ids:
            raise ValueError(f"Duplicate/missing id: {d.id}")
        ids.add(d.id)
        if not d.url:
            raise ValueError(f"Missing url for slug={d.slug}")
        if not d.summary:
            raise ValueError(f"Missing summary for slug={d.slug}")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Framework7 AI knowledge artifacts")
    parser.add_argument("--source", default="framework7_react_docs_tsx.json")
    parser.add_argument("--fallback-source", default="data/knowledge.json")
    parser.add_argument("--output", default="data")
    parser.add_argument("--version", default=None)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    source_path = (repo_root / args.source).resolve()
    fallback_path = (repo_root / args.fallback_source).resolve()
    data_dir = (repo_root / args.output).resolve()

    if source_path.exists():
        source = load_framework7_source(source_path)
    elif fallback_path.exists():
        existing = json.loads(fallback_path.read_text(encoding="utf-8"))
        docs = existing.get("docs", [])
        source = {"core_docs": {}, "components": {}}
        for d in docs:
            slug = d.get("slug")
            if not slug:
                continue
            section = "core_docs" if d.get("category") == "core" else "components"
            source[section][slug] = {
                "url": d.get("url", ""),
                "component": d.get("title", slug),
                "description": d.get("summary", ""),
                "props": d.get("props", []),
                "events": d.get("events", []),
                "notes": d.get("notes", []),
                "tsx_example": d.get("tsx_example", ""),
            }
    else:
        raise FileNotFoundError(
            f"Neither source file exists: {source_path} nor fallback: {fallback_path}"
        )
    docs = collect_docs(source)
    validate_docs(docs)
    inferred_version = (args.version or source.get("meta", {}).get("framework7_version") or "v9").strip()

    knowledge_docs: list[dict[str, Any]] = []
    manifest_items = []
    search_items = []
    category_stats: dict[str, int] = {}

    for d in docs:
        category_stats[d.category] = category_stats.get(d.category, 0) + 1

        knowledge_docs.append(
            {
                "id": d.id,
                "slug": d.slug,
                "title": d.title,
                "category": d.category,
                "url": d.url,
                "summary": d.summary,
                "keywords": d.keywords,
                "aliases": d.aliases,
                "props": d.props,
                "events": d.events,
                "notes": d.notes,
                "tsx_example": d.tsx_example,
                "content": d.content,
            }
        )

        manifest_items.append(
            {
                "id": d.id,
                "slug": d.slug,
                "title": d.title,
                "category": d.category,
                "summary": d.summary,
                "keywords": d.keywords[:8],
            }
        )

        search_items.append(
            {
                "id": d.id,
                "slug": d.slug,
                "title": d.title,
                "category": d.category,
                "summary": d.summary,
                "keywords": d.keywords,
                "aliases": d.aliases,
                "url": d.url,
                "retrieval_text": build_retrieval_text(d.title, {
                    "description": d.content,
                    "props": d.props,
                    "events": d.events,
                    "notes": d.notes,
                }),
                "boost": search_boost(d.slug),
            }
        )

    by_id = {d["id"]: d for d in knowledge_docs}
    for d in knowledge_docs:
        d["related"] = related_doc_ids(
            current_id=d["id"],
            current_category=d["category"],
            current_keywords=d.get("keywords", []),
            by_id=by_id,
            limit=3,
        )

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    build_id = datetime.now(timezone.utc).strftime("%Y%m%d")
    component_count = sum(1 for d in knowledge_docs if d.get("category") != "core")
    core_count = sum(1 for d in knowledge_docs if d.get("category") == "core")
    knowledge = {
        "version": inferred_version,
        "generatedAt": now,
        "count": len(knowledge_docs),
        "docs": knowledge_docs,
    }
    manifest = {
        "version": inferred_version,
        "generatedAt": now,
        "documentCount": len(manifest_items),
        "componentCount": component_count,
        "coreCount": core_count,
        "count": len(manifest_items),
        "items": manifest_items,
    }
    search_index = {
        "version": inferred_version,
        "generatedAt": now,
        "count": len(search_items),
        "items": search_items,
    }

    blob = json.dumps(knowledge, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    checksum = hashlib.sha256(blob).hexdigest()
    metadata = {
        "version": inferred_version,
        "generatedAt": now,
        "documentCount": len(knowledge_docs),
        "checksum": checksum,
        "buildId": build_id,
        "sourceFile": str(source_path),
        "stats": {
            "documents": len(knowledge_docs),
            "categories": category_stats,
            "total_props": sum(len(d.get("props", [])) for d in knowledge_docs),
            "total_events": sum(len(d.get("events", [])) for d in knowledge_docs),
        },
        "checksums": {
            "knowledge_sha256": checksum,
        },
    }

    write_json(data_dir / "knowledge.json", knowledge)
    write_json(data_dir / "manifest.json", manifest)
    write_json(data_dir / "search-index.json", search_index)
    write_json(data_dir / "metadata.json", metadata)
    # Optional helper payload for `wrangler kv bulk put`.
    kv_bulk = [
        {"key": "knowledge.json", "value": json.dumps(knowledge, ensure_ascii=False)},
        {"key": "manifest.json", "value": json.dumps(manifest, ensure_ascii=False)},
        {"key": "search-index.json", "value": json.dumps(search_index, ensure_ascii=False)},
        {"key": "metadata.json", "value": json.dumps(metadata, ensure_ascii=False)},
    ]
    for d in knowledge_docs:
        kv_bulk.append({"key": f"knowledge:{d['id']}", "value": json.dumps(d, ensure_ascii=False)})
    write_json(data_dir / "kv-bulk.json", kv_bulk)

    print(f"Generated {len(knowledge_docs)} docs into {data_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
