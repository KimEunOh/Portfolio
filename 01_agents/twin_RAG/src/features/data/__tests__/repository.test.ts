import { insertPlaces } from '@/features/data/repository';

describe('repository/insertPlaces', () => {
  it('inserts in chunks and throws on error', async () => {
    const calls: any[] = [];
    const client = {
      from: (_table: string) => ({
        insert: async (rows: unknown[]) => {
          calls.push(rows.length);
          return { error: null };
        },
      }),
    } as any;

    const rows = Array.from({ length: 1200 }).map((_, i) => ({
      id: `123e4567-e89b-12d3-a456-42661417${(1000 + i).toString().slice(-4)}`,
      name_ko: 'X',
      category: 'OTHER' as const,
    }));

    await insertPlaces(client, rows as any, { chunkSize: 500 });
    expect(calls).toEqual([500, 500, 200]);
  });
});


