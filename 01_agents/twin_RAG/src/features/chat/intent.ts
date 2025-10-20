import { Intent } from '@/features/chat/types';

export interface IntentClassifier {
  classify(text: string): Promise<Intent>;
}

type ClassifyOptions = { classifier?: IntentClassifier };

export async function classifyIntent(text: string, opts: ClassifyOptions = {}): Promise<Intent> {
  const trimmed = text.trim();
  if (!trimmed) return 'UNKNOWN';
  if (opts.classifier) return opts.classifier.classify(trimmed);
  // Fallback simple rule-based for now; can be swapped with transformers later
  const t = trimmed.toLowerCase();
  if (/(안녕|hello|hi)/.test(t)) return 'GREETING';
  if (/(비자|visa|immigration|출입국)/.test(t)) return 'ASK_ADMIN';
  if (/(병원|hospital|은행|bank|학교|school)/.test(t)) return 'SEARCH_PLACE';
  return 'UNKNOWN';
}


