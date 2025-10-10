import { NextResponse } from 'next/server';

export async function GET(_req: Request, { params }: { params: { type: string; id: string } }) {
	const type = (params.type || '').toLowerCase();
	const id = parseInt(params.id || '0', 10);
	if (!id || (type !== 'news' && type !== 'columns')) {
		return NextResponse.json({ next: null });
	}
	const api = process.env.NEXT_SERVER_API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://backend:8000/api';
	const nextUrl = type === 'news' ? `${api}/news/${id}/next/` : `${api}/columns/${id}/next/`;
	const res = await fetch(nextUrl, { cache: 'no-store' });
	const data = await res.json();
	let similar: any[] = [];
	let socialLinks: any[] = [];
	if (data && data.next && data.next.id) {
		const simType = type === 'columns' ? 'column' : 'news';
		try {
			const simRes = await fetch(`${api}/posts/similar/?type=${simType}&id=${data.next.id}&limit=2`, { cache: 'no-store' });
			const simJson = await simRes.json();
			similar = simJson.results || [];
		} catch {}
	}
	try {
		const slRes = await fetch(`${api}/social-links/`, { cache: 'no-store' });
		const slJson = await slRes.json();
		socialLinks = slJson.results || [];
	} catch {}
	return NextResponse.json({ ...data, similar, socialLinks });
}


