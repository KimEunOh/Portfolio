import { mapSeoulHospitalToPlace } from '@/features/data/transformers';

describe('transformers/mapSeoulHospitalToPlace', () => {
  it('maps minimal fields', () => {
    const input = {
      ykiho: '123e4567-e89b-12d3-a456-426614174000',
      yadmNm: '서울병원',
      XPos: '127.0',
      YPos: '37.5',
      telno: '02-000-0000',
      addr: '서울시 어딘가',
    };
    const place = mapSeoulHospitalToPlace(input);
    expect(place.name_ko).toBe('서울병원');
    expect(place.category).toBe('HOSPITAL');
  });
});


