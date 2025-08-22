import { NextRequest } from 'next/server';

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
    const resp = await fetch(url.toString(), { cache: 'no-store' });
    if (!resp.ok) {
      const text = await resp.text();
      return new Response(text || 'Upstream error', { status: 502 });
    }
    const data = await resp.json();
    const items = Array.isArray(data?.results)
      ? data.results.map((r: any, idx: number) => ({
          id: String(idx),
          title: String(r?.title ?? r?.metadata?.title ?? 'Result'),
          description: String(r?.snippet ?? r?.metadata?.summary ?? ''),
          url: typeof r?.url === 'string' ? r.url : undefined,
          source: r?.type === 'doc' ? 'doc' : 'web',
        }))
      : [];
    return Response.json({ items });
  } catch (e: any) {
    return new Response('Proxy error', { status: 502 });
  }
}


