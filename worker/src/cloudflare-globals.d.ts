/* Minimal local Cloudflare Worker ambient types for editor/typecheck stability.
   If @cloudflare/workers-types is installed, these remain compatible. */

interface KVNamespaceGetOptions {
  type?: "text" | "json" | "arrayBuffer" | "stream";
  cacheTtl?: number;
}

interface KVNamespacePutOptions {
  expiration?: number;
  expirationTtl?: number;
  metadata?: unknown;
}

interface KVNamespace {
  get(key: string, options?: KVNamespaceGetOptions): Promise<string | null>;
  put(key: string, value: string, options?: KVNamespacePutOptions): Promise<void>;
}

interface DurableObjectId {
  toString(): string;
}

interface DurableObjectStub {
  fetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response>;
}

interface DurableObjectNamespace {
  idFromName(name: string): DurableObjectId;
  get(id: DurableObjectId): DurableObjectStub;
}

interface DurableObjectStorage {
  get<T = unknown>(key: string): Promise<T | undefined>;
  put<T = unknown>(key: string, value: T): Promise<void>;
  delete(key: string): Promise<boolean>;
  list<T = unknown>(options?: { prefix?: string }): Promise<Map<string, T>>;
  setAlarm(scheduledTime: number | Date): Promise<void>;
}

interface DurableObjectState {
  storage: DurableObjectStorage;
}

declare const caches: CacheStorage & {
  default: Cache;
};
