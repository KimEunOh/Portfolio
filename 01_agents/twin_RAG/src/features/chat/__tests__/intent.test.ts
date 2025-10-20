import { classifyIntent, Intent, IntentClassifier } from '@/features/chat/intent';
import { extractEntities } from '@/features/chat/entities';

class MockClassifier implements IntentClassifier {
  async classify(text: string): Promise<Intent> {
    const t = text.toLowerCase();
    if (/(병원|hospital)/.test(t)) return 'SEARCH_PLACE';
    if (/(은행|bank)/.test(t)) return 'SEARCH_PLACE';
    if (/(안녕|hello|hi)/.test(t)) return 'GREETING';
    if (/(비자|visa|immigration|출입국)/.test(t)) return 'ASK_ADMIN';
    return 'UNKNOWN';
  }
}

describe('intent classification', () => {
  const mock = new MockClassifier();

  test('병원 찾아줘 → SEARCH_PLACE', async () => {
    const intent = await classifyIntent('병원 찾아줘', { classifier: mock });
    expect(intent).toBe('SEARCH_PLACE');
  });

  test('안녕 → GREETING', async () => {
    const intent = await classifyIntent('안녕', { classifier: mock });
    expect(intent).toBe('GREETING');
  });

  test('은행 알려줘 → entities includes BANK', () => {
    const ents = extractEntities('강남역 근처 은행 알려줘');
    expect(ents.categories).toContain('BANK');
  });
});


