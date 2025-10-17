import React from 'react';
import './globals.css';
import Image from 'next/image';
import newsIcon from '../icons/News_site.png';
import authorsIcon from '../icons/Autors.png';
import contactIcon from '../icons/Contact.png';
import CryptoWidget from '../components/CryptoWidget';

export const metadata = {
	title: '2049.news',
	description: 'Новости будущего: AI, технологии, крипто',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
	return (
		<html lang="ru">
			<body>
                <header className="site-header">
                    <div className="container">
                    <nav className="nav">
                        <a href="/" className="brand">2049.news</a>
                        <a href="/news" className="nav-button" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                <Image src={newsIcon} alt="News" width={18} height={18} />
                            Future News
                            </a>
                        <a href="/columns" className="nav-button" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                <Image src={authorsIcon} alt="Author columns" width={18} height={18} />
                            Insider Blogs
                            </a>
                            <span className="spacer" />
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <CryptoWidget />
                        <form action="/search" method="get" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <input name="q" type="text" placeholder="Search…" aria-label="Search" style={{ padding: '6px 10px', borderRadius: 8, border: '1px solid var(--border)', background: 'var(--bg-elev)', color: '#fff' }} />
                        </form>
                        <a href="/contact" className="nav-button" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                <Image src={contactIcon} alt="Contacts" width={18} height={18} />
                            Contacts
                            </a>
                    </div>
                    </nav>
                    </div>
                </header>
				<main className="container">{children}</main>
				<footer className="site-footer">
					<div className="container">
                        <p className="footer-about">
                            <strong>2049.news</strong> — a media about the future of technology, artificial intelligence, and the crypto economy. We publish news, opinion columns and analysis from practitioners — developers, founders and researchers.
                        </p>
						<nav className="footer-nav">
                            <a href="/news" className="nav-button">Future News</a>
                            <a href="/columns" className="nav-button">Insider Blogs</a>
                            <a href="/contact" className="nav-button">Contacts</a>
                            <a href="/about" className="nav-button">About</a>
                            <a href="/privacy" className="nav-button">Privacy Policy</a>
                            <a href="/terms" className="nav-button">Terms of Use</a>
						</nav>
					</div>
				</footer>
			</body>
		</html>
	);
}


