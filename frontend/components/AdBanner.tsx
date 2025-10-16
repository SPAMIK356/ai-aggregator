async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch');
  return res.json();
}

type Banner = { id: number; name: string; url: string; image_url: string; weight: number };

export default async function AdBanner({ variant }: { variant?: 'post' | 'feed' }) {
  const api = process.env.NEXT_SERVER_API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://backend:8000/api';
  const backendOrigin = api.replace(/\/?api\/?$/, '');
  const data = await fetchJson<{ results: Banner[] }>(`${api}/ads/`);
  const items = data.results?.filter(b => b.image_url && b.url) || [];
  if (!items.length) return null;
  // Weighted random pick
  const total = items.reduce((s, b) => s + Math.max(1, Number(b.weight || 1)), 0);
  let r = Math.random() * total;
  let pick = items[0];
  for (const b of items) {
    r -= Math.max(1, Number(b.weight || 1));
    if (r <= 0) { pick = b; break; }
  }
  const absoluteImageUrl = (() => {
    const img = pick.image_url || '';
    if (/^https?:\/\//i.test(img)) return img;
    return `${backendOrigin}${img.startsWith('/') ? img : `/${img}`}`;
  })();
  const proxiedSrc = `/api/fe-media?u=${encodeURIComponent(absoluteImageUrl)}`;
  const PromoBanner = (await import('./PromoBanner')).default;
  return <PromoBanner src={proxiedSrc} alt={pick.name} variant={variant} url={pick.url} />;
}




