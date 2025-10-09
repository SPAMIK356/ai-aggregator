async function fetchJson(url: string) {
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch');
  return res.json();
}

function stripHtml(input: string): string {
  return (input || "").replace(/<[^>]+>/g, "");
}

export default async function NewsListPage({ searchParams }: { searchParams: { page?: string; theme?: string } }) {
  const api = process.env.NEXT_SERVER_API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://backend:8000/api';
  const page = Number(searchParams?.page || 1);
  const theme = (searchParams?.theme || '').toUpperCase();
  const themeParam = theme === 'AI' || theme === 'CRYPTO' ? `&theme=${theme}` : '';
  const data = await fetchJson(`${api}/news/?page=${page}${themeParam}`);

  return (
    <div>
      <h1 className="section-title">Новости</h1>
      <div className="meta" style={{ display: 'flex', gap: 8, marginTop: 8 }}>
        <a href={`/news`} className="pill">Все</a>
        <a href={`/news?theme=AI`} className="pill">ИИ</a>
        <a href={`/news?theme=CRYPTO`} className="pill">Крипта</a>
      </div>
      <div className="cards" style={{ marginTop: 12 }}>
        {data.results.map((n: any) => (
          <a key={n.id} href={`/news/${n.id}`} className="card">
            {(n.resolved_image || n.image_url) && (
              <div style={{ marginBottom: 8 }}>
                <img src={n.resolved_image || n.image_url} alt="" className="thumb" />
              </div>
            )}
            <div className="card-title">{n.title}</div>
            <div className="meta">{n.source_name} · {new Date(n.published_at).toLocaleString('ru-RU')}</div>
            {n.description && (
              <p className="snippet">
                {(() => {
                  const text = stripHtml(n.description);
                  return text.length > 300 ? text.slice(0, 300) + '…' : text;
                })()}
              </p>
            )}
          </a>
        ))}
      </div>

      <div className="pagination">
        {page > 1 && <a className="pill" href={`?page=${page - 1}${themeParam ? `&theme=${theme}` : ''}`}>&larr; Назад</a>}
        {data.next && <a className="pill" href={`?page=${page + 1}${themeParam ? `&theme=${theme}` : ''}`}>Далее &rarr;</a>}
      </div>
    </div>
  );
}


