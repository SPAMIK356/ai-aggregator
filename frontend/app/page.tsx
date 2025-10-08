async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch');
  return res.json();
}

async function safeFetchList<T>(url: string): Promise<{ results: T[] }> {
  try {
    return await fetchJson<{ results: T[] }>(url);
  } catch {
    return { results: [] };
  }
}

function stripHtml(input: string): string {
  return (input || "").replace(/<[^>]+>/g, "");
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

export default async function HomePage() {
  const api = process.env.NEXT_SERVER_API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://backend:8000/api';
  const unified = await safeFetchList<UnifiedItem>(`${api}/posts/?page=1`);

  // Build a dynamic ticker date: real day/month, fixed year 2049
  const now = new Date();
  const datePrefix = now.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' });
  const tickerDate = `${datePrefix} 2049`;

  return (
    <>
      <section className="hero">
        <h1>Новости из будущего, которое уже наступает</h1>
        <p>
          2049.news — это медиа о будущем технологий, искусственного интеллекта и криптоэкономики. Здесь создают контент сами разработчики и предприниматели — люди, которые двигают прогресс.
        </p>
        <ul className="slogans">
          <li><em>AI, технологии, крипто — взгляд в 2049</em></li>
          <li><em>Место, где разработчики, предприниматели и визионеры пишут историю будущего</em></li>
          <li><em>От киберпанка к реальности: разбор того, что меняет мир прямо сейчас</em></li>
          <li><em>2049 — не просто дата, а метафора будущего</em></li>
        </ul>
      </section>

      <div className="ticker" aria-hidden>
        <div className="ticker-track">
          <span className="ticker-item">{tickerDate}</span>
          {unified.results.slice(0, 8).map((n) => (
            <span key={`t1-${n.id}`} className="ticker-item">{n.title}</span>
          ))}
          <span className="ticker-item">{tickerDate}</span>
          {unified.results.slice(0, 8).map((n) => (
            <span key={`t2-${n.id}`} className="ticker-item">{n.title}</span>
          ))}
        </div>
      </div>

      <section>
        <h2 className="section-title">Лента</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {unified.results.map((p) => (
            <a key={`${p.type}-${p.id}`} href={p.type === 'news' ? `/news/${p.id}` : `/columns/${p.id}`} className="card">
              {p.resolved_image && (
                <div style={{ marginBottom: 8 }}>
                  <img src={p.resolved_image} alt="" className="thumb" />
                </div>
              )}
              <div className="card-title">{p.title}</div>
              <div className="meta">
                <span style={{ marginRight: 8, padding: '2px 6px', border: '1px solid var(--border)', borderRadius: 6, fontSize: 12 }}>{p.theme}</span>
                {p.hashtags.slice(0, 3).map(h => (
                  <span key={h.slug} style={{ marginRight: 6, opacity: .8, fontSize: 12 }}>#{h.name}</span>
                ))}
              </div>
              {p.snippet && (
                <p className="snippet">
                  {(() => {
                    const text = stripHtml(p.snippet);
                    return text.length > 220 ? text.slice(0, 220) + '…' : text;
                  })()}
                </p>
              )}
            </a>
          ))}
        </div>
      </section>

    </>
  );
}


