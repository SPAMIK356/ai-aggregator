"use client";

import React, { useEffect, useState } from "react";

type LinkItem = { id: number; name: string; url: string; icon_url?: string };

export default function SocialLinks() {
	const [items, setItems] = useState<LinkItem[]>([]);
	useEffect(() => {
		const api = process.env.NEXT_PUBLIC_API_BASE || "http://backend:8000/api";
		fetch(`${api}/social-links/`, { cache: "no-store" })
			.then(r => r.json())
			.then(d => setItems(d.results || []))
			.catch(() => setItems([]));
	}, []);

	if (!items.length) return null;
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



