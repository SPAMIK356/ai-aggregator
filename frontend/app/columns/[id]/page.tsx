interface ColumnDetail {
  id: number;
  title: string;
  author_name: string;
  published_at: string;
  content_body: string;
}

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url, { next: { revalidate: 60 } });
  if (!res.ok) throw new Error('Failed to fetch');
  return res.json();
}

export default async function ColumnDetailPage({ params }: { params: { id: string } }) {
  const api = process.env.NEXT_PUBLIC_API_BASE || '/api';
  const data = await fetchJson<ColumnDetail>(`${api}/columns/${params.id}/`);
  return (
    <article className="prose">
      <h1 style={{ marginBottom: 8 }}>{data.title}</h1>
      <div className="meta" style={{ marginBottom: 16 }}>{data.author_name} · {new Date(data.published_at).toLocaleString('ru-RU')}</div>
      <div dangerouslySetInnerHTML={{ __html: data.content_body }} />
    </article>
  );
}


