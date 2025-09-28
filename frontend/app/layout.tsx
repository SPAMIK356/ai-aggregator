import React from 'react';
import './globals.css';

export const metadata = {
	title: 'AI-Aggregator',
	description: 'Новости и авторские колонки об искусственном интеллекте',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
	return (
		<html lang="ru">
			<body>
				<header className="site-header">
					<div className="container">
						<nav className="nav">
							<a href="/" className="brand">AI-Aggregator</a>
							<a href="/news">Новости</a>
							<a href="/columns">Авторские колонки</a>
							<span className="spacer" />
							<a href="/contact">Контакты</a>
						</nav>
					</div>
				</header>
				<main className="container">{children}</main>
			</body>
		</html>
	);
}


