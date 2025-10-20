import { Place, PlacesArraySchema } from './schemas';
import { mapSeoulHospitalToPlace } from './transformers';

export function transformSeoulHospitalsJsonToPlaces(records: unknown[]): Place[] {
  const places = (records as Record<string, unknown>[]).map((r) => mapSeoulHospitalToPlace(r));
  return PlacesArraySchema.parse(places);
}


