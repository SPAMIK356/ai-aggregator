async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch');
  return res.json();
}

type Banner = { id: number; name: string; url: string; image_url: string; weight: number };

export default async function AdBanner() {
  const api = process.env.NEXT_SERVER_API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://backend:8000/api';
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
  return (
    <div className="ad-wrap">
      <a href={pick.url} target="_blank" rel="noopener noreferrer" title={pick.name}>
        <img src={pick.image_url} alt={pick.name} />
      </a>
    </div>
  );
}




