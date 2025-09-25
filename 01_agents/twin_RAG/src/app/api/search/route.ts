import { NextRequest } from 'next/server';
import { createPureClient } from '@/lib/supabase/server';
import { normalizeSearchItems, RawSearchItem } from '@/features/search/lib/normalize';

const RAG_SEARCH_URL = process.env.RAG_SEARCH_URL || 'http://localhost:8000/search';

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const q = searchParams.get('q')?.trim() || '';
  if (!q) {
    return Response.json({ items: [] });
  }

  const url = new URL(RAG_SEARCH_URL);
  url.searchParams.set('q', q);
  // Optional passthroughs
  const docTopK = searchParams.get('doc_top_k');
  const webCount = searchParams.get('web_count');
  const alpha = searchParams.get('alpha');
  const beta = searchParams.get('beta');
  if (docTopK) url.searchParams.set('doc_top_k', docTopK);
  if (webCount) url.searchParams.set('web_count', webCount);
  if (alpha) url.searchParams.set('alpha', alpha);
  if (beta) url.searchParams.set('beta', beta);

  try {
    // 1) Upstream RAG results
    const resp = await fetch(url.toString(), { cache: 'no-store' });
    const ragItems: RawSearchItem[] = (() => {
      if (!resp.ok) return [];
      // tolerate non-json upstream
      return resp
        .json()
        .then((data) =>
          Array.isArray((data as any)?.results)
            ? (data as any).results.map((r: any, idx: number) => ({
                id: String(idx),
                title: String(r?.title ?? r?.metadata?.title ?? 'Result'),
                description: String(r?.snippet ?? r?.metadata?.summary ?? ''),
                url: typeof r?.url === 'string' ? r.url : undefined,
                source: r?.type === 'doc' ? 'doc' : 'web',
              }))
            : []
        )
        .catch(() => []) as any;
    })();

    // 2) Local DB results from places (simple ILIKE match on name/address/phone)
    const supabase = await createPureClient();
    const { data: local, error } = await supabase
      .from('places')
      .select('name_ko,name_en,address_ko,address_en,phone,source_url,source_name,verified_at')
      .or(`name_ko.ilike.%${q}%,name_en.ilike.%${q}%,address_ko.ilike.%${q}%,address_en.ilike.%${q}%,phone.ilike.%${q}%`)
      .limit(20);
    const localItems: RawSearchItem[] = Array.isArray(local)
      ? local.map((p: any) => ({
          id: p.source_url ?? `${p.name_ko}-${p.phone ?? ''}`,
          title: String(p.name_ko ?? p.name_en ?? '결과'),
          description: String(p.address_ko ?? p.address_en ?? ''),
          url: typeof p.source_url === 'string' ? p.source_url : undefined,
          source: 'local',
          source_name: typeof p.source_name === 'string' ? p.source_name : undefined,
          verified_at: typeof p.verified_at === 'string' ? p.verified_at : undefined,
        }))
      : [];

    const combined = normalizeSearchItems([...(await ragItems), ...localItems]);
    return Response.json({ items: combined });
  } catch (e: any) {
    return new Response('Proxy error', { status: 502 });
  }
}


