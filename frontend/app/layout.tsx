import React from 'react';
import './globals.css';
import Image from 'next/image';
import newsIcon from '../icons/News_site.png';
import authorsIcon from '../icons/Autors.png';
import contactIcon from '../icons/Contact.png';

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
							<a href="/news" className="nav-button" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
								<Image src={newsIcon} alt="News" width={18} height={18} />
								News
							</a>
							<a href="/columns" className="nav-button" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
								<Image src={authorsIcon} alt="Author columns" width={18} height={18} />
								Author columns
							</a>
							<span className="spacer" />
							<a href="/contact" className="nav-button" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
								<Image src={contactIcon} alt="Contacts" width={18} height={18} />
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


