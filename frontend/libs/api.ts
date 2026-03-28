/**
 * lib/api.ts — API client for FastAPI backend.
 * All calls route to http://localhost:8000 (FastAPI with CORS enabled).
 * Extended timeouts are mandatory — local LLM inference is slow.
 */

import axios from "axios";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 600_000, // 10 minutes — local LLM pipelines can be slow
  headers: { "Content-Type": "application/json" },
});

export interface GenerateRequest {
  keyword: string;
  tone: "informative" | "persuasive" | "casual" | "professional";
}

export interface BlogMetrics {
  readability_score: number;
  flesch_reading_ease: number;
  flesch_kincaid_grade: number;
  gunning_fog: number;
  ai_detection_percentage: number;
  naturalness_score: number;
  detection_method: string;
  detection_confidence?: string;
  word_count: number;
  heading_count: number;
  seo_score?: number;
}

export interface BlogGenerationResponse {
  keyword: string;
  tone: string;
  outline: string;
  draft_blog: string;
  final_blog: string;
  metrics: BlogMetrics;
}

export interface SerpResponse {
  keyword: string;
  combined_text: string;
  headings: string[];
  source_urls: string[];
}

/** Phase 1 — scrape SERP only (useful for testing) */
export async function scrapeSerp(keyword: string): Promise<SerpResponse> {
  const { data } = await client.post<SerpResponse>("/api/scrape", { keyword });
  return data;
}

/** Full pipeline — scrape → agents → validate */
export async function generateBlog(
  payload: GenerateRequest
): Promise<BlogGenerationResponse> {
  const { data } = await client.post<BlogGenerationResponse>(
    "/api/generate",
    payload
  );
  return data;
}

/** Validate arbitrary text */
export async function validateText(text: string): Promise<BlogMetrics> {
  const { data } = await client.post<BlogMetrics>("/api/validate", { text });
  return data;
}

export default client;