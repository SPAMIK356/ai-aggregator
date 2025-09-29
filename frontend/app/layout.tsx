import React from 'react';
import './globals.css';
import Image from 'next/image';

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
							<a href="/news" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
								<Image src="/icons/News_site.png" alt="Новости" width={18} height={18} />
								News
							</a>
							<a href="/columns" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
								<Image src="/icons/Autors.png" alt="Авторские колонки" width={18} height={18} />
								Author columns
							</a>
							<span className="spacer" />
							<a href="/contact" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
								<Image src="/icons/Contact.png" alt="Контакты" width={18} height={18} />
								Contacts
							</a>
						</nav>
					</div>
				</header>
				<main className="container">{children}</main>
			</body>
		</html>
	);
}


