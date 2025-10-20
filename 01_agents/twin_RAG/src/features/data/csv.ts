import { PlacesArraySchema, Place, PlaceSchema } from './schemas';

function toStringOrUndefined(value: unknown): string | undefined {
  return value === undefined || value === null || value === ''
    ? undefined
    : String(value);
}

function toNumberOrUndefined(value: unknown): number | undefined {
  if (value === undefined || value === null || value === '') return undefined;
  const n = Number(value);
  return Number.isFinite(n) ? n : undefined;
}

export function serializePlacesToCsv(places: Place[]): string {
  const header = [
    'id',
    'name_ko',
    'name_en',
    'category',
    'latitude',
    'longitude',
    'address_ko',
    'address_en',
    'phone',
    'source_url',
    'source_name',
    'verified_at',
  ];

  const rows = places.map((p) => [
    p.id,
    p.name_ko,
    p.name_en ?? '',
    p.category,
    p.latitude ?? '',
    p.longitude ?? '',
    p.address_ko ?? '',
    p.address_en ?? '',
    p.phone ?? '',
    p.source_url ?? '',
    p.source_name ?? '',
    p.verified_at ?? '',
  ]);

  const escape = (v: unknown) => {
    const s = String(v);
    if (s.includes(',') || s.includes('"') || s.includes('\n')) {
      return '"' + s.replace(/"/g, '""') + '"';
    }
    return s;
  };

  return [header.join(','), ...rows.map((r) => r.map(escape).join(','))].join('\n');
}

export function parsePlacesCsv(csv: string): Place[] {
  const lines = csv.split(/\r?\n/).filter((l) => l.trim().length > 0);
  if (lines.length === 0) return [];
  const header = parseCsvLine(lines[0]);
  const idx = Object.fromEntries(header.map((h, i) => [h, i] as const));

  const records = lines.slice(1).map((line) => {
    const cols = parseCsvLine(line);
    const obj: Partial<Place> = {
      id: String(cols[idx['id']]),
      name_ko: String(cols[idx['name_ko']]),
      name_en: toStringOrUndefined(cols[idx['name_en']]),
      category: String(cols[idx['category']]) as Place['category'],
      latitude: toNumberOrUndefined(cols[idx['latitude']]),
      longitude: toNumberOrUndefined(cols[idx['longitude']]),
      address_ko: toStringOrUndefined(cols[idx['address_ko']]),
      address_en: toStringOrUndefined(cols[idx['address_en']]),
      phone: toStringOrUndefined(cols[idx['phone']]),
      source_url: toStringOrUndefined(cols[idx['source_url']]),
      source_name: toStringOrUndefined(cols[idx['source_name']]),
      verified_at: toStringOrUndefined(cols[idx['verified_at']]),
    };
    return PlaceSchema.parse(obj);
  });

  return PlacesArraySchema.parse(records);
}

function parseCsvLine(line: string): string[] {
  const result: string[] = [];
  let current = '';
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (inQuotes) {
      if (ch === '"') {
        if (line[i + 1] === '"') {
          current += '"';
          i++;
        } else {
          inQuotes = false;
        }
      } else {
        current += ch;
      }
    } else {
      if (ch === ',') {
        result.push(current);
        current = '';
      } else if (ch === '"') {
        inQuotes = true;
      } else {
        current += ch;
      }
    }
  }
  result.push(current);
  return result;
}


