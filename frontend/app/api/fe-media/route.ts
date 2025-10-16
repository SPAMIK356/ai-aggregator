export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const u = searchParams.get('u');
  if (!u) return new Response('Missing u', { status: 400 });
  try {
    const res = await fetch(u, { cache: 'no-store' });
    if (!res.ok) return new Response('Upstream error', { status: res.status });
    const headers = new Headers();
    // Pass through content-type and caching hints
    const ct = res.headers.get('content-type');
    if (ct) headers.set('content-type', ct);
    headers.set('cache-control', 'public, max-age=60');
    const buf = await res.arrayBuffer();
    return new Response(buf, { status: 200, headers });
  } catch (e) {
    return new Response('Fetch failed', { status: 502 });
  }
}


