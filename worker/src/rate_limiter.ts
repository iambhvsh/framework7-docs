export class RateLimiter {
  private state: DurableObjectState;

  constructor(state: DurableObjectState) {
    this.state = state;
  }

  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);
    const max = Math.max(1, Number(url.searchParams.get("max") || "120"));
    const windowSec = Math.max(1, Number(url.searchParams.get("windowSec") || "60"));
    const bucket = Math.floor(Date.now() / (windowSec * 1000));
    const key = `b:${bucket}`;

    const currentRaw = await this.state.storage.get<number>(key);
    const current = Number(currentRaw || 0);
    if (current >= max) {
      return json({ allowed: false, remaining: 0 });
    }

    await this.state.storage.put(key, current + 1);
    await this.state.storage.setAlarm(Date.now() + (windowSec + 5) * 1000);
    return json({ allowed: true, remaining: Math.max(0, max - (current + 1)) });
  }

  async alarm(): Promise<void> {
    // Keep storage bounded by pruning stale buckets.
    const nowSec = Math.floor(Date.now() / 1000);
    const keepAfter = nowSec - 3600;
    const list = await this.state.storage.list<number>({ prefix: "b:" });
    for (const [k] of list) {
      const bucket = Number(k.slice(2));
      if (Number.isFinite(bucket) && bucket < keepAfter) {
        await this.state.storage.delete(k);
      }
    }
  }
}

function json(payload: unknown): Response {
  return new Response(JSON.stringify(payload), {
    headers: { "Content-Type": "application/json; charset=utf-8" },
  });
}
