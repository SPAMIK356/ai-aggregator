import React from 'react';
import './globals.css';
import Image from 'next/image';
import newsIcon from '../icons/News_site.png';
import authorsIcon from '../icons/Autors.png';
import contactIcon from '../icons/Contact.png';
import localFont from 'next/font/local';

const digital = localFont({
	src: '../fonts/DIGITALPIXELV4-REGULAR.OTF',
	display: 'swap',
});

export const metadata = {
	title: '2049.news',
	description: 'Новости будущего: AI, технологии, крипто',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
	return (
		<html lang="ru">
			<body className={digital.className}>
				<header className="site-header">
					<div className="container">
					<nav className="nav">
						<a href="/" className="brand">2049.news</a>
						<a href="/news" className="nav-button" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
								<Image src={newsIcon} alt="News" width={18} height={18} />
							Новости будущего
							</a>
						<a href="/columns" className="nav-button" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
								<Image src={authorsIcon} alt="Author columns" width={18} height={18} />
							Блоги от инсайдеров
							</a>
							<span className="spacer" />
						<a href="/contact" className="nav-button" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
								<Image src={contactIcon} alt="Contacts" width={18} height={18} />
							Контакты
							</a>
						</nav>
					</div>
				</header>
				<main className="container">{children}</main>
			</body>
		</html>
	);
}


