import { NextRequest } from 'next/server';
import { classifyIntent } from '@/features/chat/intent';
import { extractEntities } from '@/features/chat/entities';
import { createEmptyContext, updateContext } from '@/features/chat/state';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const message = String(body?.message ?? '').trim();
    const lang = (body?.lang === 'en' ? 'en' : 'ko') as 'ko' | 'en';
    if (!message) {
      return new Response('message is required', { status: 400 });
    }

    const intent = await classifyIntent(message);
    const entities = extractEntities(message);

    // very naive reply generator for MVP
    const reply = generateReply(intent, lang);

    const ctx0 = createEmptyContext(lang);
    const ctx1 = updateContext(ctx0, { userMessage: message, intent, entities, reply });

    return new Response(
      JSON.stringify({ reply: ctx1.history.at(-1)?.reply ?? reply, intent, entities }),
      { headers: { 'content-type': 'application/json' }, status: 200 }
    );
  } catch (e) {
    return new Response('Bad Request', { status: 400 });
  }
}

function generateReply(intent: string, lang: 'ko' | 'en'): string {
  if (intent === 'GREETING') return lang === 'ko' ? '안녕하세요! 무엇을 도와드릴까요?' : 'Hello! How can I help?';
  if (intent === 'ASK_ADMIN')
    return lang === 'ko'
      ? '행정 절차 관련 질문이군요. 구체적으로 알려주세요.'
      : 'Administrative question detected. Please provide more details.';
  if (intent === 'SEARCH_PLACE')
    return lang === 'ko' ? '어떤 지역에서 찾을까요?' : 'Which area should I search in?';
  return lang === 'ko' ? '질문을 이해하지 못했어요. 다시 말씀해 주세요.' : "I couldn't understand. Please rephrase.";
}


