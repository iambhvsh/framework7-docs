export interface ManifestItem {
  id: string;
  slug: string;
  title: string;
  category: string;
  summary: string;
  keywords: string[];
}

export interface SearchItem extends ManifestItem {
  aliases: string[];
  url: string;
  retrieval_text?: string;
  boost?: number;
}

export interface KnowledgeDoc extends SearchItem {
  props: Array<Record<string, unknown>>;
  events: Array<Record<string, unknown>>;
  notes: string[];
  tsx_example: string;
  content: string;
}

export interface Metadata {
  version: string;
  generatedAt: string;
  documentCount: number;
  checksum: string;
  buildId: string;
  stats: Record<string, unknown>;
  // Backward-compatible optional fields.
  generated_at?: string;
  checksums?: Record<string, string>;
}

export interface ManifestPayload {
  version: string;
  generatedAt: string;
  documentCount: number;
  componentCount: number;
  coreCount: number;
  count: number;
  items: ManifestItem[];
  generated_at?: string;
}

export interface SearchIndexPayload {
  version: string;
  generatedAt: string;
  count: number;
  items: SearchItem[];
  generated_at?: string;
}

export interface KnowledgePayload {
  version: string;
  generatedAt: string;
  count: number;
  docs: KnowledgeDoc[];
  generated_at?: string;
}

export interface Env {
  DOCS_KV: KVNamespace;
  RATE_LIMITER: DurableObjectNamespace;
  ALLOWED_ORIGIN?: string;
  RATE_LIMIT_MAX?: string;
  RATE_LIMIT_WINDOW_SECONDS?: string;
}
