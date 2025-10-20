/* eslint-disable no-console */
import fs from 'node:fs';
import path from 'node:path';
import { createClient } from '@supabase/supabase-js';
import { PlacesArraySchema, Place } from '@/features/data/schemas';

function getEnv(name: string): string {
  const v = process.env[name];
  if (!v) throw new Error(`Missing env: ${name}`);
  return v;
}

async function main() {
  const SUPABASE_URL = getEnv('SUPABASE_URL');
  const SUPABASE_SERVICE_ROLE_KEY = getEnv('SUPABASE_SERVICE_ROLE_KEY');
  const filePath = process.argv[2] ?? path.join(process.cwd(), 'src/features/data/sample/places.sample.json');

  const text = fs.readFileSync(filePath, 'utf8');
  const json = JSON.parse(text);
  const places: Place[] = PlacesArraySchema.parse(json);

  const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
    auth: { persistSession: false },
  });

  const { error } = await supabase.from('places').insert(places);
  if (error) throw new Error(error.message);
  console.log(`Inserted ${places.length} places`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});


