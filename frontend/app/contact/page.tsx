import React from 'react';

async function fetchJson<T>(url: string): Promise<T> {
	const res = await fetch(url, { cache: 'no-store' });
	if (!res.ok) throw new Error('Failed to fetch');
	return res.json();
}

export default async function ContactPage() {
	const api = process.env.NEXT_SERVER_API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://backend:8000/api';
	let content = { title: 'Контакты', body: '' } as any;
	try {
		content = await fetchJson<any>(`${api}/pages/contact/`);
	} catch {}
	return (
		<article className="prose">
			<h1>{content.title || 'Контакты'}</h1>
			<div dangerouslySetInnerHTML={{ __html: content.body || '<p>Добавьте текст в админке (SitePage slug=contact).</p>' }} />
		</article>
	);
}

export default function ContactPage() {
  return (
    <div className="prose">
      <h1>Контакты / Опубликовать статью</h1>
      <p>
        Если вы хотите опубликовать статью, пожалуйста, отправьте материал на почту
        {' '}<a href="mailto:email@example.com">email@example.com</a> со следующей информацией:
      </p>
      <ul>
        <li>Заголовок</li>
        <li>Имя автора</li>
        <li>Полный текст (можно в формате HTML/Markdown) и изображения</li>
        <li>Контакт для связи</li>
      </ul>
    </div>
  );
}


