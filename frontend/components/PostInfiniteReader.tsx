"use client";

import React, { useEffect, useRef, useState } from "react";

type PostType = "news" | "columns";

export default function PostInfiniteReader({ type, currentId }: { type: PostType; currentId: number }) {
	const [items, setItems] = useState<any[]>([]);
	const [loading, setLoading] = useState(false);
	const [finished, setFinished] = useState(false);
	const sentinelRef = useRef<HTMLDivElement | null>(null);
	const nextIdRef = useRef<number | null>(currentId);

	useEffect(() => {
		const el = sentinelRef.current;
		if (!el) return;
		const io = new IntersectionObserver((entries) => {
			const entry = entries[0];
			if (entry.isIntersecting) {
				loadNext();
			}
		}, { rootMargin: "200px" });
		io.observe(el);
		return () => io.disconnect();
	}, []);

	async function loadNext() {
		if (loading || finished) return;
		setLoading(true);
		try {
			const id = nextIdRef.current;
			if (id == null) {
				setFinished(true);
				return;
			}
			const url = `/api/next/${type}/${id}`;
			const res = await fetch(url, { cache: "no-store" });
			const data = await res.json();
			if (!data || !data.next) {
				setFinished(true);
				return;
			}
			setItems(prev => [...prev, data.next]);
			nextIdRef.current = data.next.id;
		} catch (e) {
			setFinished(true);
		} finally {
			setLoading(false);
		}
	}

	return (
		<div>
			{items.map((it) => (
				<article key={`${type}-${it.id}`} className="prose" style={{ marginTop: 32 }}>
					<h2 style={{ marginBottom: 8 }}>{it.title}</h2>
					<div className="meta" style={{ marginBottom: 16 }}>
						{type === "news" ? it.source_name : it.author_name} · {new Date(it.published_at).toLocaleString('ru-RU')}
					</div>
					{(it.resolved_image || it.image_url) && (
						<p><img src={it.resolved_image || it.image_url} alt="" className="thumb" /></p>
					)}
					<div dangerouslySetInnerHTML={{ __html: type === "news" ? (it.description || "") : (it.content_body || "") }} />
				</article>
			))}
			{!finished && (
				<div ref={sentinelRef} style={{ padding: 12, textAlign: 'center', opacity: .7 }}>
					{loading ? 'Загрузка…' : 'Прокрутите вниз для загрузки следующего материала'}
				</div>
			)}
		</div>
	);
}



