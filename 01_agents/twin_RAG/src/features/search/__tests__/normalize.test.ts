import { normalizeSearchItems } from '@/features/search/lib/normalize';

describe('normalizeSearchItems', () => {
  test('trims fields and drops items without title', () => {
    const input = [
      { id: '1', title: '  Hello  ', description: '  world  ', source: 'web' },
      { id: '2', title: '   ', description: 'desc', source: 'web' },
      { id: '3', description: 'no title', source: 'web' },
    ];
    const out = normalizeSearchItems(input);
    expect(out.length).toBe(1);
    expect(out[0].title).toBe('Hello');
    expect(out[0].description).toBe('world');
  });

  test('deduplicates by url when present and by title+source otherwise', () => {
    const input = [
      { id: 'a', title: 'Same', url: 'https://ex.com/1', source: 'web' },
      { id: 'b', title: 'Same other id', url: 'https://ex.com/1', source: 'web' },
      { id: 'c', title: 'Same', source: 'web' },
      { id: 'd', title: 'Same', source: 'web' },
      { id: 'e', title: 'Same', source: 'doc' },
    ];
    const out = normalizeSearchItems(input);
    // keeps first of same url, dedup title+source pair, but allows different source
    expect(out.find((i) => i.id === 'a')).toBeTruthy();
    expect(out.find((i) => i.id === 'b')).toBeFalsy();
    expect(out.find((i) => i.id === 'c')).toBeTruthy();
    expect(out.find((i) => i.id === 'd')).toBeFalsy();
    expect(out.find((i) => i.id === 'e')).toBeTruthy();
  });

  test('preserves metadata fields when present', () => {
    const now = new Date().toISOString();
    const input = [
      {
        id: '1',
        title: 'Item',
        url: 'https://ex.com',
        source: 'local',
        source_name: 'Supabase',
        verified_at: now,
      },
    ];
    const out = normalizeSearchItems(input);
    expect(out[0].source_name).toBe('Supabase');
    expect(out[0].verified_at).toBe(now);
  });

  test('handles large arrays efficiently', () => {
    const big = Array.from({ length: 5000 }, (_, i) => ({ id: String(i), title: `T${i}`, source: 'web' }));
    const start = Date.now();
    const out = normalizeSearchItems(big);
    const elapsed = Date.now() - start;
    expect(out.length).toBe(5000);
    expect(elapsed).toBeLessThan(1000); // should run within 1s in CI
  });
});


