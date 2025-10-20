import type { Place } from './schemas';

type SupabaseInsertResult = { error: { message: string } | null };

type SupabaseClientLike = {
  from: (table: string) => {
    insert: (rows: unknown[]) => Promise<SupabaseInsertResult>;
  };
};

/**
 * Insert places into Supabase in chunks to avoid payload limits.
 */
export async function insertPlaces(
  client: SupabaseClientLike,
  places: Place[],
  options: { table?: string; chunkSize?: number } = {}
): Promise<void> {
  const table = options.table ?? 'places';
  const chunkSize = options.chunkSize ?? 500;
  for (let i = 0; i < places.length; i += chunkSize) {
    const chunk = places.slice(i, i + chunkSize);
    const { error } = await client.from(table).insert(chunk);
    if (error) {
      throw new Error(`Failed to insert places: ${error.message}`);
    }
  }
}


