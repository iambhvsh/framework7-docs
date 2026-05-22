import type { SearchItem } from "./types";

function scoreItem(item: SearchItem, q: string): number {
  const qn = q.toLowerCase();
  let score = 0;

  if (item.id.toLowerCase() === qn) score += 250;
  if (item.slug.toLowerCase() === qn) score += 220;
  if (item.title.toLowerCase() === qn) score += 210;

  if (item.slug.toLowerCase().includes(qn)) score += 120;
  if (item.title.toLowerCase().includes(qn)) score += 100;

  for (const a of item.aliases ?? []) {
    const x = a.toLowerCase();
    if (x === qn) score += 160;
    else if (x.includes(qn)) score += 70;
  }

  for (const k of item.keywords ?? []) {
    const x = k.toLowerCase();
    if (x === qn) score += 65;
    else if (x.includes(qn)) score += 25;
  }

  if ((item.summary || "").toLowerCase().includes(qn)) score += 15;
  if ((item.retrieval_text || "").toLowerCase().includes(qn)) score += 20;
  const boost = Number.isFinite(item.boost) ? Number(item.boost) : 1.0;
  return score * Math.max(0.1, boost);
}

export function searchDocs(items: SearchItem[], query: string, limit: number): SearchItem[] {
  const q = query.trim().toLowerCase();
  if (!q) return [];

  const scored = items
    .map((item) => ({ item, score: scoreItem(item, q) }))
    .filter((x) => x.score > 0)
    .sort((a, b) => b.score - a.score || a.item.slug.localeCompare(b.item.slug));

  return scored.slice(0, limit).map((x) => x.item);
}

export function searchDocsWithScores(
  items: SearchItem[],
  query: string,
  limit: number,
): Array<{ item: SearchItem; score: number }> {
  const q = query.trim().toLowerCase();
  if (!q) return [];

  const scored = items
    .map((item) => ({ item, score: scoreItem(item, q) }))
    .filter((x) => x.score > 0)
    .sort((a, b) => b.score - a.score || a.item.slug.localeCompare(b.item.slug))
    .slice(0, limit);

  const max = scored.length > 0 ? scored[0].score : 1;
  return scored.map((x) => ({ item: x.item, score: Number((x.score / max).toFixed(4)) }));
}
