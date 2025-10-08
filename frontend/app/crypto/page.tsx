async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch');
  return res.json();
}

type UnifiedItem = {
  id: number;
  type: 'news' | 'column';
  title: string;
  snippet: string;
  published_at: string;
  resolved_image?: string;
  theme: 'AI' | 'CRYPTO';
  hashtags: { slug: string; name: string }[];
};

export default async function CryptoPage() {
  const api = process.env.NEXT_SERVER_API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://backend:8000/api';
  const data = await fetchJson<{ results: UnifiedItem[] }>(`${api}/posts/?theme=CRYPTO&page=1`);
  return (
    <section>
      <h2 className="section-title">Крипта</h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {data.results.map((p) => (
          <a key={`${p.type}-${p.id}`} href={p.type === 'news' ? `/news/${p.id}` : `/columns/${p.id}`} className="card">
            {p.resolved_image && (
              <div style={{ marginBottom: 8 }}>
                <img src={p.resolved_image} alt="" className="thumb" />
              </div>
            )}
            <div className="card-title">{p.title}</div>
            <div className="meta">
              {p.hashtags.slice(0, 3).map(h => (
                <span key={h.slug} style={{ marginRight: 6, opacity: .8, fontSize: 12 }}>#{h.name}</span>
              ))}
            </div>
            <p className="snippet">{p.snippet}</p>
          </a>
        ))}
      </div>
    </section>
  );
}


