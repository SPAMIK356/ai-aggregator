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

type NewsItem = {
  id: number;
  title: string;
  description: string;
  published_at: string;
  source_name: string;
  image_url?: string;
  resolved_image?: string;
};

type ColumnItem = {
  id: number;
  title: string;
  author_name: string;
  published_at: string;
  image_url?: string;
  resolved_image?: string;
};

export default async function HomePage() {
  const api = process.env.NEXT_SERVER_API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://backend:8000/api';
  const [newsData, columnsData] = await Promise.all([
    safeFetchList<NewsItem>(`${api}/news/?page=1`),
    safeFetchList<ColumnItem>(`${api}/columns/?page=1`),
  ]);

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
          {newsData.results.slice(0, 8).map((n) => (
            <span key={`t1-${n.id}`} className="ticker-item">{n.title}</span>
          ))}
          <span className="ticker-item">{tickerDate}</span>
          {newsData.results.slice(0, 8).map((n) => (
            <span key={`t2-${n.id}`} className="ticker-item">{n.title}</span>
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
      <section>
        <h2 className="section-title">Новости будущего</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {newsData.results.map((n) => (
            <a key={n.id} href={`/news/${n.id}`} className="card">
              {(n.resolved_image || n.image_url) && (
                <div style={{ marginBottom: 8 }}>
                  <img src={n.resolved_image || n.image_url!} alt="" className="thumb" />
                </div>
              )}
              <div className="card-title">{n.title}</div>
              <div className="meta">{n.source_name} · {new Date(n.published_at).toLocaleString('ru-RU')}</div>
              {n.description && (
                <p className="snippet">
                  {(() => {
                    const text = stripHtml(n.description);
                    return text.length > 220 ? text.slice(0, 220) + '…' : text;
                  })()}
                </p>
              )}
            </a>
          ))}
        </div>
      </section>

      <section>
        <h2 className="section-title">Блоги от инсайдеров</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {columnsData.results.map((c) => (
            <a key={c.id} href={`/columns/${c.id}`} className="card">
              {(c.resolved_image || c.image_url) && (
                <div style={{ marginBottom: 8 }}>
                  <img src={c.resolved_image || c.image_url!} alt="" className="thumb" />
                </div>
              )}
              <div className="card-title">{c.title}</div>
              <div className="meta">{c.author_name} · {new Date(c.published_at).toLocaleString('ru-RU')}</div>
            </a>
          ))}
        </div>
      </section>
      </div>
    </>
  );
}


