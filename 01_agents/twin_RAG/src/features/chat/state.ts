import { ConversationContext, ConversationTurn, Entities, Intent } from '@/features/chat/types';

export function createEmptyContext(language: 'ko' | 'en' = 'ko'): ConversationContext {
  return { language, history: [], lastIntent: null };
}

type UpdateArgs = {
  userMessage: string;
  intent: Intent;
  entities: Entities;
  reply: string;
};

export function updateContext(ctx: ConversationContext, args: UpdateArgs): ConversationContext {
  const turn: ConversationTurn = {
    userMessage: args.userMessage,
    intent: args.intent,
    entities: args.entities,
    reply: args.reply,
    timestamp: Date.now(),
  };
  return {
    ...ctx,
    history: [...ctx.history, turn],
    lastIntent: args.intent,
  };
}


