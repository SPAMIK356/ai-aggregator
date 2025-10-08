import React from 'react';

async function fetchJson<T>(url: string): Promise<T> {
	const res = await fetch(url, { cache: 'no-store' });
	if (!res.ok) throw new Error('Failed to fetch');
	return res.json();
}

function stripHtml(input: string): string {
	return (input || "").replace(/<[^>]+>/g, "");
}

type UnifiedItem = {
	id: number;
	type: 'news' | 'column';
	title: string;
	snippet?: string;
	resolved_image?: string;
	published_at: string;
};

export default async function SearchPage({ searchParams }: { searchParams: { q?: string } }) {
	const api = process.env.NEXT_SERVER_API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://backend:8000/api';
	const q = (searchParams?.q || '').trim();
	const param = q ? `&q=${encodeURIComponent(q)}` : '';
	const [aiData, cryptoData] = await Promise.all([
		fetchJson<{ results: UnifiedItem[] }>(`${api}/posts/?theme=AI${param}`),
		fetchJson<{ results: UnifiedItem[] }>(`${api}/posts/?theme=CRYPTO${param}`),
	]);

	const ai = aiData.results?.[0];
	const crypto = cryptoData.results?.[0];

	return (
		<div>
			<h1 className="section-title" style={{ textAlign: 'center' }}>Поиск{q ? `: "${q}"` : ''}</h1>
			<div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginTop: 12, alignItems: 'start' }}>
				<section style={{ textAlign: 'center' }}>
					<h2 className="section-title">ИИ</h2>
					<div style={{ display: 'flex', flexDirection: 'column', gap: 12, alignItems: 'center' }}>
						{ai ? (
							<a href={ai.type === 'news' ? `/news/${ai.id}` : `/columns/${ai.id}`} className="card" style={{ width: '100%' }}>
								{ai.resolved_image && (
									<div style={{ marginBottom: 8 }}>
										<img src={ai.resolved_image} alt="" className="thumb" />
									</div>
								)}
								<div className="card-title">{ai.title}</div>
								{ai.snippet && (
									<p className="snippet">{(() => { const t = stripHtml(ai.snippet || ''); return t.length > 220 ? t.slice(0, 220) + '…' : t; })()}</p>
								)}
							</a>
						) : (
							<p className="meta" style={{ opacity: .7 }}>Ничего не найдено</p>
						)}
					</div>
				</section>

				<section style={{ textAlign: 'center' }}>
					<h2 className="section-title">Крипта</h2>
					<div style={{ display: 'flex', flexDirection: 'column', gap: 12, alignItems: 'center' }}>
						{crypto ? (
							<a href={crypto.type === 'news' ? `/news/${crypto.id}` : `/columns/${crypto.id}`} className="card" style={{ width: '100%' }}>
								{crypto.resolved_image && (
									<div style={{ marginBottom: 8 }}>
										<img src={crypto.resolved_image} alt="" className="thumb" />
									</div>
								)}
								<div className="card-title">{crypto.title}</div>
								{crypto.snippet && (
									<p className="snippet">{(() => { const t = stripHtml(crypto.snippet || ''); return t.length > 220 ? t.slice(0, 220) + '…' : t; })()}</p>
								)}
							</a>
						) : (
							<p className="meta" style={{ opacity: .7 }}>Ничего не найдено</p>
						)}
					</div>
				</section>
			</div>
		</div>
	);
}
