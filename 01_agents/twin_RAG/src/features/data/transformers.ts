import { Place, PlaceSchema, PlaceCategorySchema } from './schemas';

/**
 * Map a Seoul Open Data hospital record (or similar) into a Place.
 * Minimal fields are mapped; unknown fields are ignored.
 */
export function mapSeoulHospitalToPlace(input: Record<string, unknown>): Place {
  const id = String(input['ykiho'] ?? input['id'] ?? cryptoRandomUuid());
  const nameKo = String(input['yadmNm'] ?? input['YadmNm'] ?? input['name'] ?? '병원');
  const tel = input['telno'] ?? input['Telno'] ?? input['phone'];
  const lon = Number(input['XPos'] ?? input['x'] ?? input['lon'] ?? '');
  const lat = Number(input['YPos'] ?? input['y'] ?? input['lat'] ?? '');
  const addr = input['addr'] ?? input['Addr'] ?? input['address'];

  const place: Partial<Place> = {
    id,
    name_ko: nameKo,
    category: PlaceCategorySchema.Values.HOSPITAL,
    name_en: undefined,
    phone: typeof tel === 'string' ? tel : undefined,
    longitude: Number.isFinite(lon) ? lon : undefined,
    latitude: Number.isFinite(lat) ? lat : undefined,
    address_ko: typeof addr === 'string' ? addr : undefined,
  } as Partial<Place>;

  return PlaceSchema.parse(place);
}

function cryptoRandomUuid(): string {
  // Simple fallback for environments without crypto.randomUUID
  if (typeof (globalThis as any).crypto?.randomUUID === 'function') {
    return (globalThis as any).crypto.randomUUID();
  }
  // RFC4122 v4-ish fallback (not cryptographically strong)
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = (Math.random() * 16) | 0,
      v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}


