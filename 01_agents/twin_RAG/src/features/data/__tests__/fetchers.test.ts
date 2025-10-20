import { transformSeoulHospitalsJsonToPlaces } from '@/features/data/fetchers';

describe('fetchers/transformSeoulHospitalsJsonToPlaces', () => {
  it('transforms array of records', () => {
    const input = [
      {
        ykiho: '123e4567-e89b-12d3-a456-426614174000',
        yadmNm: '서울병원',
      },
    ];
    const places = transformSeoulHospitalsJsonToPlaces(input as any);
    expect(places[0].name_ko).toBe('서울병원');
  });
});


