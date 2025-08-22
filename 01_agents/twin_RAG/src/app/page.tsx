'use client';

import { Button } from '@/components/ui/button';
import { CheckCircle, Github, Copy, Sparkles } from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { useToast } from '@/hooks/use-toast';
import axios from 'axios';
import { SearchContainer } from '@/features/search/components/SearchContainer';

const PACKAGE_NAME = '@easynext/cli';
const CURRENT_VERSION = 'v0.1.35';

function latestVersion(packageName: string) {
  return axios
    .get('https://registry.npmjs.org/' + packageName + '/latest')
    .then((res) => res.data.version);
}

export default function Home() {
  const { toast } = useToast();
  const [latest, setLatest] = useState<string | null>(null);

  useEffect(() => {
    const fetchLatestVersion = async () => {
      try {
        const version = await latestVersion(PACKAGE_NAME);
        setLatest(`v${version}`);
      } catch (error) {
        console.error('Failed to fetch version info:', error);
      }
    };
    fetchLatestVersion();
  }, []);

  const handleCopyCommand = () => {
    navigator.clipboard.writeText(`npm install -g ${PACKAGE_NAME}@latest`);
    toast({
      description: 'Update command copied to clipboard',
    });
  };

  const needsUpdate = latest && latest !== CURRENT_VERSION;

  return (
    <div className="min-h-screen flex flex-col items-center justify-start gap-8 py-10">
      <div className="flex flex-col items-center text-center gap-2">
        <h1 className="text-3xl md:text-5xl font-semibold tracking-tighter !leading-tight">
          Korea Assist 검색
        </h1>
        <p className="text-muted-foreground">행정·생활·문화 정보를 검색해 보세요.</p>
        <p className="text-xs text-muted-foreground">
          Current: {CURRENT_VERSION} · Latest: {latest || 'Loading...'}
          {needsUpdate && (
            <button onClick={handleCopyCommand} className="ml-2 underline">
              업데이트 명령 복사
            </button>
          )}
        </p>
      </div>

      <SearchContainer />
    </div>
  );
}

function Section() {
  const items = [
    { href: 'https://nextjs.org/', label: 'Next.js' },
    { href: 'https://ui.shadcn.com/', label: 'shadcn/ui' },
    { href: 'https://tailwindcss.com/', label: 'Tailwind CSS' },
    { href: 'https://www.framer.com/motion/', label: 'framer-motion' },
    { href: 'https://zod.dev/', label: 'zod' },
    { href: 'https://date-fns.org/', label: 'date-fns' },
    { href: 'https://ts-pattern.dev/', label: 'ts-pattern' },
    { href: 'https://es-toolkit.dev/', label: 'es-toolkit' },
    { href: 'https://zustand.docs.pmnd.rs/', label: 'zustand' },
    { href: 'https://supabase.com/', label: 'supabase' },
    { href: 'https://react-hook-form.com/', label: 'react-hook-form' },
  ];

  return (
    <div className="flex flex-col py-5 md:py-8 space-y-2 opacity-75">
      <p className="font-semibold">What&apos;s Included</p>

      <div className="flex flex-col space-y-1 text-muted-foreground">
        {items.map((item) => (
          <SectionItem key={item.href} href={item.href}>
            {item.label}
          </SectionItem>
        ))}
      </div>
    </div>
  );
}

function SectionItem({ children, href }: { children: React.ReactNode; href: string }) {
  return (
    <a href={href} className="flex items-center gap-2 underline" target="_blank">
      <CheckCircle className="w-4 h-4" />
      <p>{children}</p>
    </a>
  );
}
