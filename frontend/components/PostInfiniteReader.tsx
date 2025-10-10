"use client";

import React, { useEffect, useRef, useState } from "react";
import SmartThumb from "./SmartThumb";

type PostType = "news" | "columns";

type Loaded = any & { _similar?: any[]; _social?: any[] };

export default function PostInfiniteReader({ type, currentId }: { type: PostType; currentId: number }) {
	const [items, setItems] = useState<Loaded[]>([]);
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
			const url = `/fe-next/${type}/${id}`;
			const res = await fetch(url, { cache: "no-store" });
			const data = await res.json();
			if (!data || !data.next) {
				setFinished(true);
				return;
			}
			const nextItem: Loaded = { ...data.next, _similar: data.similar || [], _social: data.socialLinks || [] };
			setItems(prev => [...prev, nextItem]);
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
					<p><SmartThumb src={it.resolved_image || it.image_url} /></p>
				)}
					<div dangerouslySetInnerHTML={{ __html: type === "news" ? (it.description || "") : (it.content_body || "") }} />
					{/* Social links */}
					{(it._social && it._social.length > 0) && (
						<div className="meta" style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginTop: 12 }}>
							{it._social.map((s: any) => (
								<a key={s.id} href={s.url} target="_blank" rel="noopener noreferrer" aria-label={s.name} title={s.name} style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
									{s.icon_url ? (
										<img src={s.icon_url} alt="" width={24} height={24} style={{ objectFit: 'contain' }} />
									) : (
										<span style={{ width: 24, height: 24, display: 'inline-block', background: 'var(--border)', borderRadius: 6 }} />
									)}
									<span style={{ fontSize: 14 }}>{s.name}</span>
								</a>
							))}
						</div>
					)}
					<hr style={{ margin: '24px 0', borderColor: 'var(--border)' }} />
					<h3 style={{ marginBottom: 12 }}>Похожие материалы</h3>
					<div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
						{(it._similar || []).map((sp: any) => (
							<a key={sp.id} href={`/${sp.type === 'column' ? 'columns' : 'news'}/${sp.id}`} className="card">
								{sp.resolved_image && <img src={sp.resolved_image} alt="" className="thumb" />}
								<div className="card-title" style={{ marginTop: 8 }}>{sp.title}</div>
							</a>
						))}
					</div>
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



