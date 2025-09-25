import { POST } from '@/app/api/chat/route';

function makeRequest(body: any) {
  return { json: async () => body } as any;
}

describe('/api/chat', () => {
  test('400 when empty message', async () => {
    const res = await POST(makeRequest({ message: '' }));
    expect(res.status).toBe(400);
  });

  test('200 basic greeting flow', async () => {
    const res = await POST(makeRequest({ message: '안녕', lang: 'ko' }));
    expect(res.status).toBe(200);
    const json = await res.json();
    expect(typeof json.reply).toBe('string');
  });
});


