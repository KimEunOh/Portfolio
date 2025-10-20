'use client';

import React, { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchSearchResults, type SearchItem } from '@/features/search/api';
import { SearchBar } from '@/features/search/components/SearchBar';
import { ResultList } from '@/features/search/components/ResultList';
import { Separator } from '@/components/ui/separator';

export function SearchContainer() {
  const [query, setQuery] = useState('');
  const [submitted, setSubmitted] = useState('');

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['search', submitted],
    queryFn: async () => {
      if (!submitted) return { items: [] as SearchItem[] };
      return fetchSearchResults(submitted);
    },
    enabled: Boolean(submitted),
    staleTime: 60 * 1000,
    gcTime: 10 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 1,
    placeholderData: (prev) => prev,
    structuralSharing: true,
    keepPreviousData: true,
  });

  const items = useMemo(() => data?.items ?? [], [data]);
  const handleSubmit = () => {
    setSubmitted(query.trim());
    // react-query will automatically refetch on key change
    if (query.trim()) refetch();
  };

  return (
    <div className="w-full flex flex-col items-center gap-4">
      <SearchBar query={query} onQueryChange={setQuery} onSubmit={handleSubmit} isLoading={isLoading || isFetching} />

      <Separator className="max-w-2xl" />

      {isLoading || isFetching ? (
        <div className="text-sm text-muted-foreground">불러오는 중...</div>
      ) : isError ? (
        <div className="text-sm text-red-600">오류가 발생했습니다. {(error as Error)?.message}</div>
      ) : (
        <ResultList items={items} />
      )}
    </div>
  );
}

export default SearchContainer;


