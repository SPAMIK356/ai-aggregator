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
  const withoutCode = raw
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/~~~[\s\S]*?~~~/g, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<pre[\s\S]*?<\/pre>/gi, " ")
    .replace(/<code[\s\S]*?<\/code>/gi, " ");
  return withoutCode
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/<[^>]+>/g, " ")
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, "$1")
    .replace(/https?:\/\/\S+/g, "")
    .replace(/[\*_`]+/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

type NewsItem = {
  id: number;
  title: string;
  title_ru?: string;
  description: string;
  description_ru?: string;
  published_at: string;
  resolved_image?: string;
  image_url?: string;
  source_name: string;
};

type ColumnItem = {
  id: number;
  title: string;
  title_ru?: string;
  published_at: string;
  resolved_image?: string;
  image_url?: string;
  author_name: string;
};

export default async function RuHomePage() {
  const api = process.env.NEXT_SERVER_API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://backend:8000/api';
  const [newsData, columnsData] = await Promise.all([
    safeFetchList<NewsItem>(`${api}/news/?page=1`),
    safeFetchList<ColumnItem>(`${api}/columns/?page=1`),
  ]);

  // Build a dynamic ticker date: real day/month, fixed year 2049
  const now = new Date();
  const datePrefix = now.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' });
  const tickerDate = `${datePrefix} 2049`;

  return (
    <>
      <section className="hero">
      <h1>Новости из будущего, которое уже наступает</h1>
        <p>
          2049.news — это медиа о будущем технологий, искусственного интеллекта и криптоэкономики. Здесь контент создают сами разработчики и предприниматели — люди, которые двигают прогресс.
        </p>
        <ul className="slogans">
          <li><em>ИИ, технологии, крипта — взгляд в 2049</em></li>
          <li><em>Место, где разработчики, предприниматели и визионеры пишут историю будущего</em></li>
          <li><em>От киберпанка к реальности: анализируем то, что меняет мир прямо сейчас</em></li>
          <li><em>2049 — не просто дата, а метафора будущего</em></li>
        </ul>
      </section>

      <div className="ticker" aria-hidden>
        <div className="ticker-track">
          <span className="ticker-item">{tickerDate}</span>
          {newsData.results.slice(0, 8).map((n) => (
            <span key={`t1-${n.id}`} className="ticker-item">{stripContent(n.title_ru || n.title)}</span>
          ))}
          <span className="ticker-item">{tickerDate}</span>
          {newsData.results.slice(0, 8).map((n) => (
            <span key={`t2-${n.id}`} className="ticker-item">{stripContent(n.title_ru || n.title)}</span>
          ))}
        </div>
      </div>

      <div className="home-grid">
        <section>
          <h2 className="section-title">Новости из будущего</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {newsData.results.map((n) => (
              <a key={n.id} href={`/ru/news/${n.id}`} className="card">
                {(n.resolved_image || n.image_url) && (
                  <div style={{ marginBottom: 8 }}>
                    <img src={n.resolved_image || n.image_url} alt="" className="thumb" />
                  </div>
                )}
                <div className="card-title">{n.title_ru || n.title}</div>
                <div className="meta">{n.source_name} · {new Date(n.published_at).toLocaleString('ru-RU')}</div>
                {(n.description_ru || n.description) && (
                  <p className="snippet">
                    {(() => {
                      const text = stripContent(n.description_ru || n.description);
                      return text.length > 220 ? text.slice(0, 220) + '…' : text;
                    })()}
                  </p>
                )}
              </a>
            ))}
          </div>
        </section>

        <section>
          <h2 className="section-title">Инсайдерские блоги</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {columnsData.results.map((c) => (
              <a key={c.id} href={`/ru/columns/${c.id}`} className="card">
                {(c.resolved_image || c.image_url) && (
                  <div style={{ marginBottom: 8 }}>
                    <img src={c.resolved_image || c.image_url} alt="" className="thumb" />
                  </div>
                )}
                <div className="card-title">{c.title_ru || c.title}</div>
                <div className="meta">{c.author_name} · {new Date(c.published_at).toLocaleString('ru-RU')}</div>
              </a>
            ))}
          </div>
        </section>
      </div>

    </>
  );
}

