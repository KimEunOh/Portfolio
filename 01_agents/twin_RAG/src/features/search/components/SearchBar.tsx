'use client';

import React from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Search } from 'lucide-react';

export type SearchBarProps = {
  query: string;
  onQueryChange: (value: string) => void;
  onSubmit: () => void;
  isLoading?: boolean;
};

export function SearchBar({ query, onQueryChange, onSubmit, isLoading }: SearchBarProps) {
  return (
    <div className="flex gap-2 w-full max-w-2xl">
      <Input
        placeholder="검색어를 입력하세요"
        value={query}
        onChange={(e) => onQueryChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') onSubmit();
        }}
      />
      <Button onClick={onSubmit} disabled={isLoading}>
        <Search className="w-4 h-4 mr-1" /> 검색
      </Button>
    </div>
  );
}

export default SearchBar;


