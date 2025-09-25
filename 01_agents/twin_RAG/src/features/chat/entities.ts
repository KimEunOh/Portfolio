import { Entities, PlaceCategory } from '@/features/chat/types';

const CATEGORY_KEYWORDS: Array<{ keyword: RegExp; category: PlaceCategory }> = [
  { keyword: /(병원|hospital)/i, category: 'HOSPITAL' },
  { keyword: /(은행|bank)/i, category: 'BANK' },
  { keyword: /(행사|event)/i, category: 'EVENT' },
  { keyword: /(학교|school)/i, category: 'SCHOOL' },
  { keyword: /(정부|구청|행정|government)/i, category: 'GOVERNMENT' },
];

export function extractEntities(text: string): Entities {
  const categories = CATEGORY_KEYWORDS.filter(({ keyword }) => keyword.test(text)).map(
    ({ category }) => category
  );
  const location = extractLocation(text);
  return { categories, location };
}

function extractLocation(text: string): string | null {
  // very naive: pick token ending with '역' (station) or containing common district names
  const candidates = text.match(/([가-힣A-Za-z]+)(역|구|동)/);
  if (candidates && candidates[0]) return candidates[0];
  return null;
}


