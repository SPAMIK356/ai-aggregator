async function fetchJson(url: string) {
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch');
  return res.json();
}

function stripHtml(input: string): string {
  return (input || "").replace(/<[^>]+>/g, "");
}

export default async function ColumnsListPage({ searchParams }: { searchParams: { page?: string } }) {
  const api = process.env.NEXT_SERVER_API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://backend:8000/api';
  const page = Number(searchParams?.page || 1);
  const data = await fetchJson(`${api}/columns/?page=${page}`);

  return (
    <div>
      <h1 className="section-title">Авторские колонки</h1>
      <div className="cards" style={{ marginTop: 12 }}>
        {data.results.map((c: any) => (
          <a key={c.id} href={`/columns/${c.id}`} className="card">
            {(c.resolved_image || c.image_url) && (
              <div style={{ marginBottom: 8 }}>
                <img src={c.resolved_image || c.image_url} alt="" className="thumb" />
              </div>
            )}
            <div className="card-title">{c.title}</div>
            <div className="meta">{c.author_name} · {new Date(c.published_at).toLocaleString('ru-RU')}</div>
            {c.content_body && (
              <p className="snippet">
                {(() => {
                  const text = stripHtml(c.content_body);
                  return text.length > 220 ? text.slice(0, 220) + '…' : text;
                })()}
              </p>
            )}
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


