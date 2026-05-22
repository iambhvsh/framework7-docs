import type { Env } from "./types";

export function withCORS(req: Request, headers: Headers, env: Env): void {
  const allowed = env.ALLOWED_ORIGIN || "*";
  const origin = req.headers.get("Origin") || "";
  const allowOrigin = allowed === "*" ? "*" : origin === allowed ? origin : "";
  if (allowOrigin) headers.set("Access-Control-Allow-Origin", allowOrigin);
  headers.set("Access-Control-Allow-Methods", "GET, OPTIONS");
  headers.set("Access-Control-Allow-Headers", "Content-Type, If-None-Match");
  headers.set("Access-Control-Max-Age", "86400");
}

export function etagFor(payload: string): string {
  // Weak ETag to avoid expensive canonicalization at edge.
  return `W/\"${payload.length.toString(16)}-${simpleHash(payload)}\"`;
}

function simpleHash(input: string): string {
  let h = 2166136261;
  for (let i = 0; i < input.length; i++) {
    h ^= input.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return (h >>> 0).toString(16);
}

export function buildJSONResponse(
  req: Request,
  env: Env,
  bodyObj: unknown,
  maxAgeSeconds: number,
  status = 200,
  etagOverride?: string,
): Response {
  const body = JSON.stringify(bodyObj);
  const headers = new Headers({
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": `public, max-age=${maxAgeSeconds}, s-maxage=${maxAgeSeconds}, stale-while-revalidate=86400`,
    Vary: "Accept-Encoding, If-None-Match, Origin",
    "X-Content-Type-Options": "nosniff",
  });

  withCORS(req, headers, env);

  const etag = etagOverride || etagFor(body);
  headers.set("ETag", etag);

  const inm = req.headers.get("If-None-Match");
  if (inm && inm === etag) {
    return new Response(null, { status: 304, headers });
  }

  return new Response(body, { status, headers });
}

export function sanitizeQuery(q: string | null): string {
  if (!q) return "";
  return q.replace(/[^a-zA-Z0-9_\-:.\s]/g, " ").replace(/\s+/g, " ").trim();
}

export async function enforceRateLimit(req: Request, env: Env): Promise<boolean> {
  const max = Number(env.RATE_LIMIT_MAX || "120");
  const windowSec = Number(env.RATE_LIMIT_WINDOW_SECONDS || "60");
  const ip = req.headers.get("CF-Connecting-IP") || "anon";
  const id = env.RATE_LIMITER.idFromName(ip);
  const stub = env.RATE_LIMITER.get(id);
  const res = await stub.fetch(`https://rate/check?max=${max}&windowSec=${windowSec}`);
  if (!res.ok) return false;
  const body = (await res.json()) as { allowed?: boolean };
  return !!body.allowed;
}
