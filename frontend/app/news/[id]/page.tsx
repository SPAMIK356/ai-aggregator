import SmartThumb from "../../../components/SmartThumb";
interface NewsDetail {
  id: number;
  title: string;
  original_url: string;
  description: string;
  published_at: string;
  source_name: string;
  image_url?: string;
  resolved_image?: string;
  theme?: 'AI' | 'CRYPTO';
  hashtags?: { slug: string; name: string }[];
}

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch');
  return res.json();
}

export default async function NewsDetailPage({ params }: { params: { id: string } }) {
  const api = process.env.NEXT_SERVER_API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://backend:8000/api';
  const data = await fetchJson<NewsDetail>(`${api}/news/${params.id}/`);
  const similar = await fetchJson<{ results: { id: number; type: 'news'; title: string; resolved_image?: string }[] }>(`${api}/posts/similar/?type=news&id=${params.id}&limit=2`);
  return (
    <article className="prose">
      <h1 style={{ marginBottom: 8 }}>{data.title}</h1>
      <div className="meta" style={{ marginBottom: 16 }}>{data.source_name} · {new Date(data.published_at).toLocaleString('ru-RU')}</div>
      {(data.resolved_image || data.image_url) && (
        <p><SmartThumb src={data.resolved_image || data.image_url!} /></p>
      )}
      <div dangerouslySetInnerHTML={{ __html: data.description }} />
      {(data.hashtags && data.hashtags.length > 0) && (
        <p className="meta" style={{ marginTop: 12 }}>{data.hashtags.map(h => <span key={h.slug} style={{ marginRight: 8 }}>#{h.name}</span>)}</p>
      )}
      <hr style={{ margin: '24px 0', borderColor: 'var(--border)' }} />
      <h3 style={{ marginBottom: 12 }}>Похожие материалы</h3>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        {similar.results.map(item => (
          <a key={item.id} href={`/news/${item.id}`} className="card">
            {item.resolved_image && <img src={item.resolved_image} alt="" className="thumb" />}
            <div className="card-title" style={{ marginTop: 8 }}>{item.title}</div>
          </a>
        ))}
      </div>
    </article>
  );
}



