'use client';

import http from '@/remote/http';
import { z } from 'zod';
import { normalizeSearchItems } from '@/features/search/lib/normalize';

// 검색 결과 아이템 스키마 및 타입
export const SearchItemSchema = z.object({
  id: z.string(),
  title: z.string(),
  description: z.string().optional().default(''),
  url: z.string().url().optional(),
  source: z.string().optional(),
  source_name: z.string().optional(),
  verified_at: z.string().datetime().optional(),
});

export const SearchResponseSchema = z.object({
  items: z.array(SearchItemSchema),
});

export type SearchItem = z.infer<typeof SearchItemSchema>;
export type SearchResponse = z.infer<typeof SearchResponseSchema>;

export async function fetchSearchResults(query: string): Promise<SearchResponse> {
  // Force same-origin call to Next.js API route to avoid CORS when a global baseURL is set
  const { data } = await http.get('/api/search', { params: { q: query }, baseURL: '' });
  // 런타임 검증 + 클라이언트 측 정제 수행
  const parsed = SearchResponseSchema.parse(data);
  return { items: normalizeSearchItems(parsed.items) };
}


