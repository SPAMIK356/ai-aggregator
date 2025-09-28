async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch');
  return res.json();
}

type NewsItem = {
  id: number;
  title: string;
  original_url: string;
  description: string;
  published_at: string;
  source_name: string;
};

type ColumnItem = {
  id: number;
  title: string;
  author_name: string;
  published_at: string;
};

export default async function HomePage() {
  const api = process.env.NEXT_SERVER_API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://backend:8000/api';
  const [newsData, columnsData] = await Promise.all([
    fetchJson<{ results: NewsItem[] }>(`${api}/news/?page=1`),
    fetchJson<{ results: ColumnItem[] }>(`${api}/columns/?page=1`),
  ]);

  return (
    <div className="cards" style={{ gap: 24 }}>
      <section>
        <h2 className="section-title">Новости</h2>
        <div className="cards">
          {newsData.results.map((n) => (
            <a key={n.id} href={n.original_url} target="_blank" rel="noopener noreferrer" className="card">
              <div className="card-title">{n.title}</div>
              <div className="meta">{n.source_name} · {new Date(n.published_at).toLocaleString('ru-RU')}</div>
              {n.description && <p className="snippet">{n.description}</p>}
            </a>
          ))}
        </div>
      </section>

      <section>
        <h2 className="section-title">Авторские колонки</h2>
        <div className="cards">
          {columnsData.results.map((c) => (
            <a key={c.id} href={`/columns/${c.id}`} className="card">
              <div className="card-title">{c.title}</div>
              <div className="meta">{c.author_name} · {new Date(c.published_at).toLocaleString('ru-RU')}</div>
            </a>
          ))}
        </div>
      </section>
    </div>
  );
}


