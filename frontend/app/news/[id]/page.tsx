interface NewsDetail {
  id: number;
  title: string;
  original_url: string;
  description: string;
  published_at: string;
  source_name: string;
  image_url?: string;
  resolved_image?: string;
}

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch');
  return res.json();
}

export default async function NewsDetailPage({ params }: { params: { id: string } }) {
  const api = process.env.NEXT_SERVER_API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://backend:8000/api';
  const data = await fetchJson<NewsDetail>(`${api}/news/${params.id}/`);
  return (
    <article className="prose">
      <h1 style={{ marginBottom: 8 }}>{data.title}</h1>
      <div className="meta" style={{ marginBottom: 16 }}>{data.source_name} · {new Date(data.published_at).toLocaleString('ru-RU')}</div>
      {(data.resolved_image || data.image_url) && (
        <p><img src={data.resolved_image || data.image_url!} alt="" className="thumb" /></p>
      )}
      <div dangerouslySetInnerHTML={{ __html: data.description }} />
    </article>
  );
}



