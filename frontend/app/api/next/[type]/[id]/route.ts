import { NextResponse } from 'next/server';

export async function GET(_req: Request, { params }: { params: { type: string; id: string } }) {
	const type = (params.type || '').toLowerCase();
	const id = parseInt(params.id || '0', 10);
	if (!id || (type !== 'news' && type !== 'columns')) {
		return NextResponse.json({ next: null });
	}
	const api = process.env.NEXT_SERVER_API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://backend:8000/api';
	const url = type === 'news' ? `${api}/news/${id}/next/` : `${api}/columns/${id}/next/`;
	const res = await fetch(url, { cache: 'no-store' });
	const data = await res.json();
	return NextResponse.json(data);
}


