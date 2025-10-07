import React from 'react';

async function fetchJson<T>(url: string): Promise<T> {
	const res = await fetch(url, { cache: 'no-store' });
	if (!res.ok) throw new Error('Failed to fetch');
	return res.json();
}

export default async function AboutPage() {
	const api = process.env.NEXT_SERVER_API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://backend:8000/api';
	let content = { title: 'О нас', body: '' } as any;
	try {
		content = await fetchJson<any>(`${api}/pages/about/`);
	} catch {}
	return (
		<article className="prose">
			<h1>{content.title || 'О нас'}</h1>
			<div dangerouslySetInnerHTML={{ __html: content.body || '<p>Добавьте текст в админке (SitePage slug=about).</p>' }} />
		</article>
	);
}


