import { serializePlacesToCsv, parsePlacesCsv } from '@/features/data/csv';

describe('csv serializer/parser', () => {
  const sample = [
    {
      id: '123e4567-e89b-12d3-a456-426614174000',
      name_ko: '서울병원',
      category: 'HOSPITAL' as const,
      latitude: 37.5,
      longitude: 127.0,
      address_ko: '서울시 어딘가',
      phone: '02-000-0000',
      source_url: 'https://example.com',
      source_name: 'EX',
      verified_at: '2025-01-01T00:00:00.000Z',
    },
  ];

  it('roundtrips places <-> csv', () => {
    const csv = serializePlacesToCsv(sample as any);
    const parsed = parsePlacesCsv(csv);
    expect(parsed[0].id).toBe(sample[0].id);
    expect(parsed[0].name_ko).toBe(sample[0].name_ko);
    expect(parsed[0].category).toBe('HOSPITAL');
  });
});


