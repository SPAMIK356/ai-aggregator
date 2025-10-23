import React from 'react';
import './globals.css';
import Image from 'next/image';
import newsIcon from '../icons/News_site.png';
import authorsIcon from '../icons/Autors.png';
import contactIcon from '../icons/Contact.png';
import CryptoWidget from '../components/CryptoWidget';
import dynamic from 'next/dynamic';
const BurgerMenu = dynamic(() => import('../components/BurgerMenu'), { ssr: false });
const MobileHeaderScroll = dynamic(() => import('../components/MobileHeaderScroll'), { ssr: false });

export const metadata = {
	title: '2049.news',
	description: 'Новости будущего: AI, технологии, крипто',
};

export const viewport = {
	width: 'device-width',
	initialScale: 1,
	maximumScale: 1,
	viewportFit: 'cover',
	// @ts-ignore - Next allows 'no'|'yes'
	userScalable: 'no',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
	return (
		<html lang="ru">
			<body>
				<MobileHeaderScroll />
                <header className="site-header">
                    <div className="container">
					<nav className="nav">
						<a href="/" className="brand">2049.news</a>
						<div className="desktop-nav">
						<a href="/" className="nav-button">Home</a>
						<a href="/news?theme=CRYPTO" className="nav-button"><Image className="nav-ico" src={newsIcon} alt="" width={16} height={16} /> Crypto</a>
						<a href="/columns" className="nav-button"><Image className="nav-ico" src={authorsIcon} alt="" width={16} height={16} /> Insider Blogs</a>
						<a href="/contact" className="nav-button"><Image className="nav-ico" src={contactIcon} alt="" width={16} height={16} /> Contacts</a>
						</div>
						<span className="spacer" />
					{/* mobile search (hidden on desktop) */}
					<form className="mobile-search" action="/search" method="get">
						<input name="q" type="text" placeholder="Search…" aria-label="Search" />
					</form>
					<CryptoWidget />
						<BurgerMenu />
					</nav>
				{/* Mobile crypto strip under the nav */}
				<div className="mobile-crypto">
					<CryptoWidget />
				</div>
                    </div>
                </header>
				<main className="container">{children}</main>
                <footer className="site-footer">
                    <div className="container">
                        <p className="footer-about">
                            <strong>2049.news</strong> — a media about the future of technology, artificial intelligence, and the crypto economy. We publish news, opinion columns and analysis from practitioners — developers, founders and researchers.
                        </p>
					<nav className="footer-nav" style={{ justifyContent: 'center' }}>
						<a href="/" className="nav-button">Home</a>
						<a href="/news?theme=CRYPTO" className="nav-button">Crypto</a>
						<a href="/columns" className="nav-button">Insider Blogs</a>
						<a href="/contact" className="nav-button">Contacts</a>
					</nav>
						<div style={{ display: 'flex', justifyContent: 'center', marginTop: 12 }}>
							<BurgerMenu />
						</div>
					</div>
				</footer>
			</body>
		</html>
	);
}


