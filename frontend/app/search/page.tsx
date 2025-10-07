import React from 'react';

async function fetchJson<T>(url: string): Promise<T> {
	const res = await fetch(url, { cache: 'no-store' });
	if (!res.ok) throw new Error('Failed to fetch');
	return res.json();
}

function stripHtml(input: string): string {
	return (input || "").replace(/<[^>]+>/g, "");
}

export default async function SearchPage({ searchParams }: { searchParams: { q?: string } }) {
	const api = process.env.NEXT_SERVER_API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://backend:8000/api';
	const q = (searchParams?.q || '').trim();
	const qs = q ? `?q=${encodeURIComponent(q)}` : '';
	const [newsData, columnsData] = await Promise.all([
		fetchJson<{ results: any[] }>(`${api}/news/${qs}`),
		fetchJson<{ results: any[] }>(`${api}/columns/${qs}`),
	]);

	return (
		<div>
			<h1 className="section-title">Поиск{q ? `: "${q}"` : ''}</h1>
			<div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginTop: 12 }}>
				<section>
					<h2 className="section-title">Новости</h2>
					<div className="cards" style={{ marginTop: 8 }}>
						{newsData.results.map((n) => (
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
										{(() => { const text = stripHtml(n.description); return text.length > 220 ? text.slice(0, 220) + '…' : text; })()}
									</p>
								)}
							</a>
						))}
					</div>
				</section>

				<section>
					<h2 className="section-title">Колонки</h2>
					<div className="cards" style={{ marginTop: 8 }}>
						{columnsData.results.map((c) => (
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
										{(() => { const text = stripHtml(c.content_body); return text.length > 220 ? text.slice(0, 220) + '…' : text; })()}
									</p>
								)}
							</a>
						))}
					</div>
				</section>
			</div>
		</div>
	);
}
