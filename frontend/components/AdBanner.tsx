"use client";

import React, { useEffect, useState } from 'react';
import PromoBanner from './PromoBanner';

type BannerResp = { id: number; name: string; url: string; src: string } | null;

export default function AdBanner({ variant }: { variant?: 'post' | 'feed' }) {
  const [banner, setBanner] = useState<BannerResp>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch('/fe-ads', { cache: 'no-store' });
        if (!res.ok) return;
        const data = await res.json();
        if (!cancelled) setBanner(data && data.src ? data : null);
      } catch {
        // ignore
      }
    })();
    return () => { cancelled = true; };
  }, []);

  if (!banner) return null as any;
  return <PromoBanner src={banner.src} alt={banner.name} variant={variant} url={banner.url} />;
}




