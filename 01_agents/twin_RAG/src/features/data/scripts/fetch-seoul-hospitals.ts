/* eslint-disable no-console */
import axios from 'axios';
import fs from 'node:fs';
import path from 'node:path';
import { transformSeoulHospitalsJsonToPlaces } from '@/features/data/fetchers';

function getArg(idx: number, fallback?: string): string | undefined {
  return process.argv[idx] ?? fallback;
}

async function main() {
  const url = getArg(2) ?? process.env.SEOUL_HOSPITALS_URL;
  if (!url) {
    throw new Error('Usage: npx ts-node fetch-seoul-hospitals.ts <url> [out.json]');
  }
  const outPath = getArg(3) ?? path.join(process.cwd(), 'src/features/data/sample/places.from_api.json');

  const { data } = await axios.get(url);
  const records: unknown[] = Array.isArray(data) ? data : data?.data ?? [];
  const places = transformSeoulHospitalsJsonToPlaces(records);

  fs.writeFileSync(outPath, JSON.stringify(places, null, 2), 'utf8');
  console.log(`Wrote ${places.length} places -> ${outPath}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});


