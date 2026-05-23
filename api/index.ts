import type { KnowledgeDoc } from "../src/types";
import { buildJSONResponse, sanitizeQuery, withCORS } from "../src/cache";
import { searchDocsWithScores } from "../src/search";
import {
  getKnowledge,
  getKnowledgeDocById,
  getManifest,
  getMetadata,
  getSearchIndex,
} from "../src/storage";

export const config = {
  runtime: "edge",
};

// In-memory strict rate limiting
const rateLimitCache = new Map<string, { count: number; resetTime: number }>();

async function enforceRateLimit(req: Request): Promise<boolean> {
  const ip =
    req.headers.get("x-forwarded-for") ||
    req.headers.get("x-real-ip") ||
    "anon";

  const limit = Number(process.env.RATE_LIMIT_MAX || "120");
  const windowSec = Number(process.env.RATE_LIMIT_WINDOW_SECONDS || "60");
  const now = Date.now();

  let record = rateLimitCache.get(ip);

  if (!record || now > record.resetTime) {
    record = {
      count: 1,
      resetTime: now + windowSec * 1000,
    };

    rateLimitCache.set(ip, record);
    return true;
  }

  if (record.count >= limit) {
    return false;
  }

  record.count++;
  return true;
}

function notFound(req: Request): Response {
  return buildJSONResponse(
    req,
    {
      error: true,
      message: "Document not found",
    },
    60,
    404,
  );
}

function badRequest(req: Request, msg: string): Response {
  return buildJSONResponse(
    req,
    {
      error: true,
      message: msg,
    },
    60,
    400,
  );
}

export default async function handler(req: Request): Promise<Response> {
  if (req.method === "OPTIONS") {
    const headers = new Headers();
    withCORS(req, headers);

    return new Response(null, {
      status: 204,
      headers,
    });
  }

  if (req.method !== "GET") {
    return buildJSONResponse(
      req,
      {
        error: true,
        message: "Method not allowed",
      },
      60,
      405,
    );
  }

  const ok = await enforceRateLimit(req);

  if (!ok) {
    return buildJSONResponse(
      req,
      {
        error: true,
        message: "Too many requests",
      },
      30,
      429,
    );
  }

  const url = new URL(req.url);
  const path = url.pathname.replace(/\/+$/, "") || "/";

  try {
    if (path === "/manifest") {
      const manifest = await getManifest();
      return buildJSONResponse(req, manifest, 300);
    }

    if (path === "/metadata") {
      const metadata = await getMetadata();

      const checksum =
        typeof metadata.checksum === "string"
          ? metadata.checksum
          : typeof metadata.checksums?.knowledge_sha256 === "string"
            ? metadata.checksums.knowledge_sha256
            : undefined;

      const etag = checksum ? `W/"${checksum}"` : undefined;

      return buildJSONResponse(
        req,
        metadata,
        300,
        200,
        etag,
      );
    }

    if (path === "/health") {
      const metadata = await getMetadata();

      return buildJSONResponse(
        req,
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

      if (!q) {
        return badRequest(req, "Missing or invalid q parameter");
      }

      const normalizedQ = q.toLowerCase();

      const rawLimit = Number(url.searchParams.get("limit") || "10");

      const limit = Math.max(
        1,
        Math.min(
          20,
          Number.isFinite(rawLimit) ? rawLimit : 10,
        ),
      );

      const cacheUrl = new URL(req.url);
      cacheUrl.searchParams.set("q", normalizedQ);
      cacheUrl.searchParams.set("limit", String(limit));

      const cacheKey = new Request(cacheUrl.toString(), {
        method: "GET",
      });

      let cache: Cache | undefined;

      try {
        cache =
          typeof caches !== "undefined"
            ? (caches as any).default
            : undefined;
      } catch {
        cache = undefined;
      }

      if (cache) {
        const cached = await cache.match(cacheKey);

        if (cached) {
          return cached;
        }
      }

      const index = await getSearchIndex();
      const matches = searchDocsWithScores(
        index.items,
        normalizedQ,
        limit,
      );

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

      const out = buildJSONResponse(req, response, 600);

      if (cache) {
        await cache.put(cacheKey, out.clone());
      }

      return out;
    }

    if (path.startsWith("/knowledge/")) {
      const id = decodeURIComponent(
        path.slice("/knowledge/".length),
      );

      if (!/^[a-z0-9:_-]{2,120}$/i.test(id)) {
        return badRequest(req, "Invalid id format");
      }

      let doc = (await getKnowledgeDocById(
        id,
      )) as KnowledgeDoc | null;

      if (!doc) {
        const knowledge = await getKnowledge();

        doc =
          knowledge.docs.find(
            (d: KnowledgeDoc) => d.id === id,
          ) ?? null;
      }

      if (!doc) {
        return notFound(req);
      }

      return buildJSONResponse(req, doc, 86400);
    }

    return notFound(req);
  } catch (err) {
    console.error(err);

    const message =
      err instanceof Error
        ? `${err.name}: ${err.message}`
        : String(err);

    return buildJSONResponse(
      req,
      {
        error: true,
        message: "Internal error",
        detail: message,
      },
      30,
      500,
    );
  }
}
