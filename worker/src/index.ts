import type { Env, KnowledgeDoc } from "./types";
import { buildJSONResponse, enforceRateLimit, sanitizeQuery, withCORS } from "./cache";
import { searchDocsWithScores } from "./search";
import { getKnowledge, getKnowledgeDocById, getManifest, getMetadata, getSearchIndex } from "./storage";
import { RateLimiter } from "./rate_limiter";

function notFound(req: Request, env: Env): Response {
  return buildJSONResponse(req, env, { error: true, message: "Document not found" }, 60, 404);
}

function badRequest(req: Request, env: Env, msg: string): Response {
  return buildJSONResponse(req, env, { error: true, message: msg }, 60, 400);
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    if (req.method === "OPTIONS") {
      const headers = new Headers();
      withCORS(req, headers, env);
      return new Response(null, { status: 204, headers });
    }

    if (req.method !== "GET") {
      return buildJSONResponse(req, env, { error: true, message: "Method not allowed" }, 60, 405);
    }

    const ok = await enforceRateLimit(req, env);
    if (!ok) {
      return buildJSONResponse(req, env, { error: true, message: "Too many requests" }, 30, 429);
    }

    const url = new URL(req.url);
    const path = url.pathname.replace(/\/+$/, "") || "/";

    try {
      if (path === "/manifest") {
        const manifest = await getManifest(env);
        return buildJSONResponse(req, env, manifest, 300);
      }

      if (path === "/metadata") {
        const metadata = await getMetadata(env);
        const checksum = typeof metadata.checksum === "string"
          ? metadata.checksum
          : typeof metadata.checksums?.knowledge_sha256 === "string"
          ? metadata.checksums.knowledge_sha256
          : undefined;
        const etag = checksum ? `W/"${checksum}"` : undefined;
        return buildJSONResponse(req, env, metadata, 300, 200, etag);
      }

      if (path === "/health") {
        const metadata = await getMetadata(env);
        return buildJSONResponse(
          req,
          env,
          {
            status: "ok",
            version: metadata.version,
            buildId: metadata.buildId,
            documents: metadata.documentCount,
          },
          60,
        );
      }

      if (path === "/search") {
        const q = sanitizeQuery(url.searchParams.get("q"));
        if (!q) return badRequest(req, env, "Missing or invalid q parameter");
        const normalizedQ = q.toLowerCase();

        const rawLimit = Number(url.searchParams.get("limit") || "10");
        const limit = Math.max(1, Math.min(20, Number.isFinite(rawLimit) ? rawLimit : 10));

        const cacheUrl = new URL(req.url);
        cacheUrl.searchParams.set("q", normalizedQ);
        cacheUrl.searchParams.set("limit", String(limit));
        const cacheKey = new Request(cacheUrl.toString(), { method: "GET" });
        const cache = (caches as CacheStorage & { default: Cache }).default;
        const cached = await cache.match(cacheKey);
        if (cached) return cached;

        const index = await getSearchIndex(env);
        const matches = searchDocsWithScores(index.items, normalizedQ, limit);

        // LLM-optimized compact response.
        const response = {
          query: normalizedQ,
          count: matches.length,
          results: matches.map(({ item, score }) => ({
            id: item.id,
            title: item.title,
            slug: item.slug,
            category: item.category,
            summary: item.summary,
            score,
          })),
        };
        const out = buildJSONResponse(req, env, response, 600);
        await cache.put(cacheKey, out.clone());
        return out;
      }

      if (path.startsWith("/knowledge/")) {
        const id = decodeURIComponent(path.slice("/knowledge/".length));
        if (!/^[a-z0-9:_-]{2,120}$/i.test(id)) {
          return badRequest(req, env, "Invalid id format");
        }

        // Fast path: document stored under its own KV key.
        let doc = (await getKnowledgeDocById(env, id)) as KnowledgeDoc | null;
        // Backward-compatible fallback if per-doc keys are not uploaded yet.
        if (!doc) {
          const knowledge = await getKnowledge(env);
          doc = knowledge.docs.find((d: KnowledgeDoc) => d.id === id) ?? null;
        }
        if (!doc) return notFound(req, env);

        return buildJSONResponse(req, env, doc, 86400);
      }

      return notFound(req, env);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unexpected error";
      return buildJSONResponse(req, env, { error: true, message: "Internal error", detail: message }, 30, 500);
    }
  },
};

export { RateLimiter };
