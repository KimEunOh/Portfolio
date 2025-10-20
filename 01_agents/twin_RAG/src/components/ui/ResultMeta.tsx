'use client';

import React from 'react';
import { format } from 'date-fns';

export type ResultMetaProps = {
  source?: string;
  source_name?: string;
  verified_at?: string;
};

export function ResultMeta({ source, source_name, verified_at }: ResultMetaProps) {
  const verified = verified_at ? safeFormat(verified_at) : undefined;
  return (
    <div className="mt-2 text-xs text-gray-500 flex flex-wrap gap-2">
      {source && <span>출처: {source}</span>}
      {source_name && <span>({source_name})</span>}
      {verified && <span>검증일: {verified}</span>}
    </div>
  );
}

function safeFormat(iso: string): string | undefined {
  try {
    return format(new Date(iso), 'yyyy-MM-dd');
  } catch {
    return undefined;
  }
}

export default ResultMeta;


