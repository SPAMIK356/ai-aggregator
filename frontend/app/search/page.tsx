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

	const ai = (aiData.results || []).slice(0, 10);
	const crypto = (cryptoData.results || []).slice(0, 10);

	return (
		<div>
			<h1 className="section-title" style={{ textAlign: 'center' }}>Поиск{q ? `: "${q}"` : ''}</h1>
			<div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginTop: 12, alignItems: 'start' }}>
				<section style={{ textAlign: 'center' }}>
					<h2 className="section-title">ИИ</h2>
					<div style={{ display: 'flex', flexDirection: 'column', gap: 12, alignItems: 'center' }}>
						{ai.length ? (
							ai.map(item => (
								<a key={`${item.type}-${item.id}`} href={item.type === 'news' ? `/news/${item.id}` : `/columns/${item.id}`} className="card" style={{ width: '100%' }}>
									{item.resolved_image && (
										<div style={{ marginBottom: 8 }}>
											<img src={item.resolved_image} alt="" className="thumb" />
										</div>
									)}
									<div className="card-title">{item.title}</div>
									{item.snippet && (
										<p className="snippet">{(() => { const t = stripHtml(item.snippet || ''); return t.length > 220 ? t.slice(0, 220) + '…' : t; })()}</p>
									)}
								</a>
							))
						) : (
							<p className="meta" style={{ opacity: .7 }}>Ничего не найдено</p>
						)}
					</div>
				</section>

				<section style={{ textAlign: 'center' }}>
					<h2 className="section-title">Крипта</h2>
					<div style={{ display: 'flex', flexDirection: 'column', gap: 12, alignItems: 'center' }}>
						{crypto.length ? (
							crypto.map(item => (
								<a key={`${item.type}-${item.id}`} href={item.type === 'news' ? `/news/${item.id}` : `/columns/${item.id}`} className="card" style={{ width: '100%' }}>
									{item.resolved_image && (
										<div style={{ marginBottom: 8 }}>
											<img src={item.resolved_image} alt="" className="thumb" />
										</div>
									)}
									<div className="card-title">{item.title}</div>
									{item.snippet && (
										<p className="snippet">{(() => { const t = stripHtml(item.snippet || ''); return t.length > 220 ? t.slice(0, 220) + '…' : t; })()}</p>
									)}
								</a>
							))
						) : (
							<p className="meta" style={{ opacity: .7 }}>Ничего не найдено</p>
						)}
					</div>
				</section>
			</div>
		</div>
	);
}
