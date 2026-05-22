import type { KnowledgePayload, ManifestPayload, Metadata, SearchIndexPayload } from "./types";

// Since no KV or Upstash, we could just read the files using Fetch or load them directly
// But Edge functions don't have fs. Let's assume we import the json directly or they are available via some remote fetch.
// Given the setup, maybe they are bundled. Let's just import them if possible.

import metadataJson from "../actions/data/metadata.json";
import manifestJson from "../actions/data/manifest.json";
import searchIndexJson from "../actions/data/search-index.json";
import knowledgeJson from "../actions/data/knowledge.json";

export async function getManifest(): Promise<ManifestPayload> {
  return manifestJson as unknown as ManifestPayload;
}

export async function getSearchIndex(): Promise<SearchIndexPayload> {
  return searchIndexJson as unknown as SearchIndexPayload;
}

export async function getKnowledge(): Promise<KnowledgePayload> {
  return knowledgeJson as unknown as KnowledgePayload;
}

export async function getKnowledgeDocById(id: string): Promise<unknown | null> {
  const knowledge = await getKnowledge();
  return knowledge.docs.find((d: any) => d.id === id) ?? null;
}

export async function getMetadata(): Promise<Metadata> {
  return metadataJson as unknown as Metadata;
}
