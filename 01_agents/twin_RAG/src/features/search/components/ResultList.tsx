'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { SearchItem } from '@/features/search/api';
import Image from 'next/image';
import { ResultMeta } from '@/components/ui/ResultMeta';

export type ResultListProps = {
  items: SearchItem[];
};

export function ResultList({ items }: ResultListProps) {
  if (!items.length) {
    return (
      <div className="text-sm text-muted-foreground">검색 결과가 없습니다.</div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-3 w-full max-w-2xl">
      {items.map((item) => (
        <Card key={item.id} className="overflow-hidden">
          <CardHeader className="flex flex-row items-center gap-3">
            <Image
              src={`https://picsum.photos/seed/${encodeURIComponent(item.id)}/64/64`}
              alt={item.title}
              width={48}
              height={48}
              className="rounded-md"
            />
            <CardTitle className="text-base">
              {item.url ? (
                <a href={item.url} target="_blank" className="underline">
                  {item.title}
                </a>
              ) : (
                item.title
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{item.description || '설명이 없습니다.'}</p>
            <ResultMeta source={item.source} source_name={(item as any).source_name} verified_at={(item as any).verified_at} />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export default ResultList;


