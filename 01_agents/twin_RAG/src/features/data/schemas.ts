import { z } from 'zod';

/**
 * Zod schemas for core datasets used in place search and content verification.
 */

export const PlaceCategorySchema = z.enum([
  'HOSPITAL',
  'BANK',
  'EVENT',
  'SCHOOL',
  'GOVERNMENT',
  'OTHER',
]);

export const OpeningHoursSchema = z
  .record(
    z
      .enum(['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']),
    z.array(
      z.object({
        open: z.string().regex(/^\d{2}:\d{2}$/),
        close: z.string().regex(/^\d{2}:\d{2}$/),
      })
    )
  )
  .optional();

export const PlaceSchema = z.object({
  id: z.string().uuid(),
  name_ko: z.string().min(1),
  name_en: z.string().optional(),
  category: PlaceCategorySchema,
  latitude: z.number().optional(),
  longitude: z.number().optional(),
  address_ko: z.string().optional(),
  address_en: z.string().optional(),
  phone: z.string().optional(),
  opening_hours: OpeningHoursSchema,
  source_url: z.string().url().optional(),
  source_name: z.string().optional(),
  verified_at: z.string().datetime().optional(),
  created_at: z.string().datetime().optional(),
  updated_at: z.string().datetime().optional(),
});

export type Place = z.infer<typeof PlaceSchema>;

export const PlacesArraySchema = z.array(PlaceSchema);


