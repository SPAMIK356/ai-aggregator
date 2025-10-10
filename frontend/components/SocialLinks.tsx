import React from "react";

async function fetchJson<T>(url: string): Promise<T> {
	const res = await fetch(url, { cache: 'no-store' });
	if (!res.ok) throw new Error('Failed to fetch');
	return res.json();
}

export default async function SocialLinks() {
	const api = process.env.NEXT_SERVER_API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://backend:8000/api';
	const data = await fetchJson<{ results: { id: number; name: string; url: string; icon_url?: string }[] }>(`${api}/social-links/`);
	const items = data.results || [];
	if (!items.length) return null as any;
	return (
		<div className="meta" style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginTop: 12 }}>
			{items.map(it => (
				<a key={it.id} href={it.url} target="_blank" rel="noopener noreferrer" aria-label={it.name} title={it.name} style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
					{it.icon_url ? (
						<img src={it.icon_url} alt="" width={24} height={24} style={{ objectFit: 'contain' }} />
					) : (
						<span style={{ width: 24, height: 24, display: 'inline-block', background: 'var(--border)', borderRadius: 6 }} />
					)}
					<span style={{ fontSize: 14 }}>{it.name}</span>
				</a>
			))}
		</div>
	);
}



