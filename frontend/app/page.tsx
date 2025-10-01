async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch');
  return res.json();
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
    fetchJson<{ results: NewsItem[] }>(`${api}/news/?page=1`),
    fetchJson<{ results: ColumnItem[] }>(`${api}/columns/?page=1`),
  ]);

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
      <section>
        <h2 className="section-title">Новости</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {newsData.results.map((n) => (
            <a key={n.id} href={`/news/${n.id}`} className="card">
              {(n.resolved_image || n.image_url) && (
                <div style={{ marginBottom: 8 }}>
                  <img src={n.resolved_image || n.image_url!} alt="" style={{ maxWidth: '100%', borderRadius: 6 }} />
                </div>
              )}
              <div className="card-title">{n.title}</div>
              <div className="meta">{n.source_name} · {new Date(n.published_at).toLocaleString('ru-RU')}</div>
              {n.description && <p className="snippet">{n.description.length > 300 ? n.description.slice(0, 300) + '…' : n.description}</p>}
            </a>
          ))}
        </div>
      </section>

      <section>
        <h2 className="section-title">Авторские колонки</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {columnsData.results.map((c) => (
            <a key={c.id} href={`/columns/${c.id}`} className="card">
              {(c.resolved_image || c.image_url) && (
                <div style={{ marginBottom: 8 }}>
                  <img src={c.resolved_image || c.image_url!} alt="" style={{ maxWidth: '100%', borderRadius: 6 }} />
                </div>
              )}
              <div className="card-title">{c.title}</div>
              <div className="meta">{c.author_name} · {new Date(c.published_at).toLocaleString('ru-RU')}</div>
            </a>
          ))}
        </div>
      </section>
    </div>
  );
}


