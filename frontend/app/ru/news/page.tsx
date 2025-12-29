async function fetchJson(url: string) {
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch');
  return res.json();
}

function stripContent(input: string): string {
  const raw = String(input || "");
  const withoutCode = raw
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/~~~[\s\S]*?~~~/g, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<pre[\s\S]*?<\/pre>/gi, " ")
    .replace(/<code[\s\S]*?<\/code>/gi, " ");
  const decoded = withoutCode
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

import AdBanner from "../../../components/AdBanner";

export default async function RuNewsListPage({ searchParams }: { searchParams: { page?: string; theme?: string } }) {
  const api = process.env.NEXT_SERVER_API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://backend:8000/api';
  const page = Number(searchParams?.page || 1);
  const theme = (searchParams?.theme || '').toUpperCase();
  const themeParam = theme === 'AI' || theme === 'CRYPTO' ? `&theme=${theme}` : '';
  const data = await fetchJson(`${api}/news/?page=${page}${themeParam}`);
  const desc = theme === 'AI'
    ? 'Последние прорывы в области ИИ: модели, инструменты и примеры использования в индустрии. Мы отслеживаем безопасность, качество и то, как ИИ уже интегрируется в продукты.'
    : theme === 'CRYPTO'
    ? 'Главное из мира крипты: рынки, протоколы, регулирование и инфраструктура. От фундаментальных обновлений до практических применений.'
    : 'Мы собираем ключевые новости о технологиях будущего: ИИ, крипторынок и прорывы, которые меняют мир. Кратко, по делу и без лишнего шума.';

  return (
    <div>
      <section className="hero">
        <h1>Новости</h1>
        <p>{desc}</p>
      </section>
      <div className="cards" style={{ marginTop: 12 }}>
        {data.results.map((n: any, idx: number) => (
          <>
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
        {page > 1 && <a className="pill" href={`?page=${page - 1}${themeParam ? `&theme=${theme}` : ''}`}>&larr; Назад</a>}
        {data.next && <a className="pill" href={`?page=${page + 1}${themeParam ? `&theme=${theme}` : ''}`}>Далее &rarr;</a>}
      </div>
    </div>
  );
}

