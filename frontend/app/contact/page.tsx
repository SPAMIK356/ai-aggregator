import React from 'react';

export default function ContactPage() {
	return (
		<article className="prose">
			<h1>Контакты</h1>
			<p>Напишите нам: <a href="mailto:hello@2049.news">hello@2049.news</a></p>
			<p>Мы открыты для предложений по сотрудничеству и публикациям.</p>
			<h2 style={{ marginTop: 16 }}>Опубликовать статью</h2>
			<p>
				Если вы хотите опубликовать статью, отправьте материал на
				{' '}<a href="mailto:email@example.com">email@example.com</a> со следующей информацией:
			</p>
			<ul>
				<li>Заголовок</li>
				<li>Имя автора</li>
				<li>Полный текст (HTML/Markdown) и изображения</li>
				<li>Контакт для связи</li>
			</ul>
		</article>
	);
}

