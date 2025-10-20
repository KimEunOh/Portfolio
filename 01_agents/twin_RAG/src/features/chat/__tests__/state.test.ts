import { updateContext, createEmptyContext } from '@/features/chat/state';
import { Intent } from '@/features/chat/types';

describe('conversation state management', () => {
  test('appends turns and updates lastIntent', () => {
    const ctx0 = createEmptyContext('ko');
    const ctx1 = updateContext(ctx0, {
      userMessage: '안녕',
      intent: 'GREETING' as Intent,
      entities: { categories: [], location: null },
      reply: '안녕하세요!',
    });

    expect(ctx1.lastIntent).toBe('GREETING');
    expect(ctx1.history.length).toBe(1);
    expect(ctx1.history[0].userMessage).toBe('안녕');
  });
});


