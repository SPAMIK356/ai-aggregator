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

function stripContent(input: string): string {
  const raw = String(input || "");
  return raw
    // 1) drop HTML tags
    .replace(/<[^>]+>/g, " ")
    // 2) convert markdown links [text](url) -> text
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, "$1")
    // 3) remove bare URLs
    .replace(/https?:\/\/\S+/g, "")
    // 4) remove emphasis markers and backticks
    .replace(/[\*_`]+/g, "")
    // 5) collapse whitespace
    .replace(/\s+/g, " ")
    .trim();
}

type UnifiedItem = {
  id: number;
  type: 'news' | 'column';
  title: string;
  snippet: string;
  published_at: string;
  resolved_image?: string;
  theme: 'AI' | 'CRYPTO';
  hashtags: { slug: string; name: string }[];
};

export default async function HomePage() {
  const api = process.env.NEXT_SERVER_API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://backend:8000/api';
  const [newsData, columnsData] = await Promise.all([
    safeFetchList<any>(`${api}/news/?page=1`),
    safeFetchList<any>(`${api}/columns/?page=1`),
  ]);

  // Build a dynamic ticker date: real day/month, fixed year 2049
  const now = new Date();
  const datePrefix = now.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' });
  const tickerDate = `${datePrefix} 2049`;

  return (
    <>
      <section className="hero">
      <h1>News from the future that is already happening</h1>
        <p>
          2049.news is a media outlet about the future of technology, artificial intelligence, and cryptoeconomics. Here, content is created by developers and entrepreneurs themselves — the people who are driving progress.
        </p>
        <ul className="slogans">
          <li><em>AI, technology, crypto — a look into 2049</em></li>
          <li><em>A place where developers, entrepreneurs, and visionaries write the history of the future</em></li>
          <li><em>From cyberpunk to reality: analyzing what is changing the world right now</em></li>
          <li><em>2049 — not just a date, but a metaphor for the future</em></li>
        </ul>
      </section>

      <div className="ticker" aria-hidden>
        <div className="ticker-track">
          <span className="ticker-item">{tickerDate}</span>
          {newsData.results.slice(0, 8).map((n: any) => (
            <span key={`t1-${n.id}`} className="ticker-item">{stripContent(n.title)}</span>
          ))}
          <span className="ticker-item">{tickerDate}</span>
          {newsData.results.slice(0, 8).map((n: any) => (
            <span key={`t2-${n.id}`} className="ticker-item">{stripContent(n.title)}</span>
          ))}
        </div>
      </div>

      <div className="home-grid">
        <section>
          <h2 className="section-title">Новости будущего</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {newsData.results.map((n: any) => (
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
            {columnsData.results.map((c: any) => (
              <a key={c.id} href={`/columns/${c.id}`} className="card">
                {(c.resolved_image || c.image_url) && (
                  <div style={{ marginBottom: 8 }}>
                    <img src={c.resolved_image || c.image_url} alt="" className="thumb" />
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


