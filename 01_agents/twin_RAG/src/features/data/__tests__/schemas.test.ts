import { PlaceSchema, PlacesArraySchema } from '@/features/data/schemas';

describe('schemas/PlaceSchema', () => {
  it('validates a correct place object', () => {
    const valid = {
      id: '123e4567-e89b-12d3-a456-426614174000',
      name_ko: '서울병원',
      category: 'HOSPITAL',
    };
    expect(() => PlaceSchema.parse(valid)).not.toThrow();
  });

  it('fails when id is not a uuid', () => {
    const invalid = {
      id: 'not-uuid',
      name_ko: '서울병원',
      category: 'HOSPITAL',
    } as any;
    expect(() => PlaceSchema.parse(invalid)).toThrow();
  });

  it('validates an array of places', () => {
    const arr = [
      { id: '123e4567-e89b-12d3-a456-426614174000', name_ko: 'A', category: 'BANK' },
      { id: '123e4567-e89b-12d3-a456-426614174001', name_ko: 'B', category: 'SCHOOL' },
    ];
    expect(() => PlacesArraySchema.parse(arr)).not.toThrow();
  });
});


