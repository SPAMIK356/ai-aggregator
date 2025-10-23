async function fetchJson(url: string) {
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch');
  return res.json();
}

function stripContent(input: string): string {
  const raw = String(input || "");
  const decoded = raw
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");
  return decoded
    .replace(/<[^>]+>/g, " ")
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, "$1")
    .replace(/https?:\/\/\S+/g, "")
    .replace(/[\*_`]+/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

import AdBanner from "../../components/AdBanner";

export default async function NewsListPage({ searchParams }: { searchParams: { page?: string; theme?: string } }) {
  const api = process.env.NEXT_SERVER_API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://backend:8000/api';
  const page = Number(searchParams?.page || 1);
  const theme = (searchParams?.theme || '').toUpperCase();
  const themeParam = theme === 'AI' || theme === 'CRYPTO' ? `&theme=${theme}` : '';
  const data = await fetchJson(`${api}/news/?page=${page}${themeParam}`);
  const desc = theme === 'AI'
    ? 'The latest breakthroughs in AI: models, tools, and industry use cases. We track safety, quality, and how AI is already being integrated into products.'
    : theme === 'CRYPTO'
    ? 'Highlights from the crypto world: markets, protocols, regulations, and infrastructure. From fundamental updates to practical applications.'
    : 'We gather key news about future technologies: AI, the crypto market, and breakthroughs that are changing the world. Concise, to the point, and without the extra noise.';

  return (
    <div>
      <section className="hero">
        <h1>News</h1>
        <p>{desc}</p>
      </section>
      {/* filters moved to burger menu */}
      <div className="cards" style={{ marginTop: 12 }}>
        {data.results.map((n: any, idx: number) => (
          <>
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
                  const text = stripContent(n.description);
                  return text.length > 300 ? text.slice(0, 300) + '…' : text;
                })()}
              </p>
            )}
          </a>
          {(idx > 0 && idx % 6 === 0) ? <div key={`ad-${idx}`} className="feed-ad"><AdBanner variant="feed" /></div> : null}
          </>
        ))}
      </div>

      <div className="pagination">
        {page > 1 && <a className="pill" href={`?page=${page - 1}${themeParam ? `&theme=${theme}` : ''}`}>&larr; Prev</a>}
        {data.next && <a className="pill" href={`?page=${page + 1}${themeParam ? `&theme=${theme}` : ''}`}>Next &rarr;</a>}
      </div>
    </div>
  );
}


