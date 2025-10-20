import { z } from 'zod';
import { PlaceCategorySchema } from '@/features/data/schemas';

export type Intent = 'GREETING' | 'ASK_ADMIN' | 'SEARCH_PLACE' | 'UNKNOWN';

export type PlaceCategory = z.infer<typeof PlaceCategorySchema>;

export type Entities = {
  categories: PlaceCategory[];
  location: string | null;
};

export type ConversationTurn = {
  userMessage: string;
  reply: string;
  intent: Intent;
  entities: Entities;
  timestamp: number;
};

export type ConversationContext = {
  language: 'ko' | 'en';
  history: ConversationTurn[];
  lastIntent: Intent | null;
};


