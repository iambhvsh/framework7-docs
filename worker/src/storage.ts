import type { Env, KnowledgePayload, ManifestPayload, Metadata, SearchIndexPayload } from "./types";

const cache = new Map<string, { exp: number; value: unknown }>();
const MEM_TTL_MS = 30_000;
const MAX_MEM_ITEMS = 20;

function getMem<T>(key: string): T | null {
  const hit = cache.get(key);
  if (!hit) return null;
  if (Date.now() > hit.exp) {
    cache.delete(key);
    return null;
  }
  return hit.value as T;
}

function setMem(key: string, value: unknown): void {
  if (cache.size >= MAX_MEM_ITEMS) {
    // Prune expired first.
    const now = Date.now();
    for (const [k, v] of cache.entries()) {
      if (now > v.exp) cache.delete(k);
    }
    // If still full, evict oldest inserted entry.
    if (cache.size >= MAX_MEM_ITEMS) {
      const firstKey = cache.keys().next().value as string | undefined;
      if (firstKey) cache.delete(firstKey);
    }
  }
  cache.set(key, { exp: Date.now() + MEM_TTL_MS, value });
}

async function loadJSON<T>(env: Env, key: string): Promise<T> {
  const mem = getMem<T>(key);
  if (mem) return mem;

  const raw = await env.DOCS_KV.get(key);
  if (!raw) throw new Error(`KV key not found: ${key}`);
  const parsed = JSON.parse(raw) as T;
  setMem(key, parsed);
  return parsed;
}

export async function getManifest(env: Env): Promise<ManifestPayload> {
  return loadJSON<ManifestPayload>(env, "manifest.json");
}

export async function getSearchIndex(env: Env): Promise<SearchIndexPayload> {
  return loadJSON<SearchIndexPayload>(env, "search-index.json");
}

export async function getKnowledge(env: Env): Promise<KnowledgePayload> {
  return loadJSON<KnowledgePayload>(env, "knowledge.json");
}

export async function getKnowledgeDocById(env: Env, id: string): Promise<unknown | null> {
  const key = `knowledge:${id}`;
  const raw = await env.DOCS_KV.get(key);
  if (!raw) return null;
  return JSON.parse(raw);
}

export async function getMetadata(env: Env): Promise<Metadata> {
  return loadJSON<Metadata>(env, "metadata.json");
}
