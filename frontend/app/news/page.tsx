import SmartThumb from "../../components/SmartThumb";
async function fetchJson(url: string) {
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch');
  return res.json();
}

export default async function NewsListPage({ searchParams }: { searchParams: { page?: string } }) {
  const api = process.env.NEXT_SERVER_API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://backend:8000/api';
  const page = Number(searchParams?.page || 1);
  const data = await fetchJson(`${api}/news/?page=${page}`);

  return (
    <div>
      <h1 className="section-title">Новости</h1>
      <div className="cards" style={{ marginTop: 12 }}>
        {data.results.map((n: any) => (
          <a key={n.id} href={`/news/${n.id}`} className="card">
            {(n.resolved_image || n.image_url) && (
              <div style={{ marginBottom: 8 }}>
                <SmartThumb src={n.resolved_image || n.image_url} />
              </div>
            )}
            <div className="card-title">{n.title}</div>
            <div className="meta">{n.source_name} · {new Date(n.published_at).toLocaleString('ru-RU')}</div>
            {n.description && <p className="snippet">{n.description.length > 300 ? n.description.slice(0, 300) + '…' : n.description}</p>}
          </a>
        ))}
      </div>

      <div className="pagination">
        {page > 1 && <a className="pill" href={`?page=${page - 1}`}>&larr; Назад</a>}
        {data.next && <a className="pill" href={`?page=${page + 1}`}>Далее &rarr;</a>}
      </div>
    </div>
  );
}


