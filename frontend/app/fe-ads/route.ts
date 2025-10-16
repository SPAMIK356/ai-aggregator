import { NextResponse } from 'next/server';

type Banner = { id: number; name: string; url: string; image_url: string; weight: number };

export async function GET() {
  const api = process.env.NEXT_SERVER_API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://backend:8000/api';
  try {
    const backendOrigin = api.replace(/\/?api\/?$/, '');
    const res = await fetch(`${api}/ads/`, { cache: 'no-store' });
    if (!res.ok) return NextResponse.json(null);
    const data = await res.json();
    const items: Banner[] = (data?.results || []).filter((b: Banner) => b?.image_url && b?.url);
    if (!items.length) return NextResponse.json(null);
    // weighted pick
    const total = items.reduce((s, b) => s + Math.max(1, Number(b.weight || 1)), 0);
    let r = Math.random() * total;
    let pick = items[0];
    for (const b of items) { r -= Math.max(1, Number(b.weight || 1)); if (r <= 0) { pick = b; break; } }
    const absoluteImageUrl = (() => {
      const img = pick.image_url || '';
      if (/^https?:\/\//i.test(img)) return img;
      return `${backendOrigin}${img.startsWith('/') ? img : `/${img}`}`;
    })();
    const proxiedSrc = `/api/fe-media?u=${encodeURIComponent(absoluteImageUrl)}`;
    return NextResponse.json({ id: pick.id, name: pick.name, url: pick.url, src: proxiedSrc });
  } catch {
    return NextResponse.json(null);
  }
}


