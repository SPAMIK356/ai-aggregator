import React from 'react';
import '../globals.css';
import Image from 'next/image';
import newsIcon from '../../icons/News_site.png';
import authorsIcon from '../../icons/Autors.png';
import contactIcon from '../../icons/Contact.png';
import CryptoWidget from '../../components/CryptoWidget';
import LanguageSwitcher from '../../components/LanguageSwitcher';
import dynamic from 'next/dynamic';
const BurgerMenu = dynamic(() => import('../../components/BurgerMenu'), { ssr: false });
const MobileHeaderScroll = dynamic(() => import('../../components/MobileHeaderScroll'), { ssr: false });

export const metadata = {
	title: '2049.news',
	description: 'Новости будущего: ИИ, технологии, крипта',
};

export const viewport = {
	width: 'device-width',
	initialScale: 1,
	maximumScale: 1,
	viewportFit: 'cover',
	// @ts-ignore - Next allows 'no'|'yes'
	userScalable: 'no',
};

export default function RuLayout({ children }: { children: React.ReactNode }) {
	return (
		<html lang="ru">
			<body>
				<MobileHeaderScroll />
                <header className="site-header">
                    <div className="container">
					<nav className="nav">
						<a href="/ru" className="brand">2049.news</a>
						<div className="desktop-nav">
						<a href="/ru" className="nav-button">Главная</a>
						<a href="/ru/news?theme=CRYPTO" className="nav-button"><Image className="nav-ico" src={newsIcon} alt="" width={16} height={16} /> Крипта</a>
						<a href="/ru/columns" className="nav-button"><Image className="nav-ico" src={authorsIcon} alt="" width={16} height={16} /> Инсайдерские блоги</a>
						<a href="/ru/contact" className="nav-button"><Image className="nav-ico" src={contactIcon} alt="" width={16} height={16} /> Контакты</a>
						</div>
						<span className="spacer" />
					{/* mobile search (hidden on desktop) */}
					<form className="mobile-search" action="/ru/search" method="get">
						<input name="q" type="text" placeholder="Поиск…" aria-label="Поиск" />
					</form>
					<CryptoWidget />
					<LanguageSwitcher locale="ru" />
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
                            <strong>2049.news</strong> — медиа о будущем технологий, искусственного интеллекта и криптоэкономики. Мы публикуем новости, авторские колонки и аналитику от практиков — разработчиков, основателей и исследователей.
                        </p>
					<nav className="footer-nav" style={{ justifyContent: 'center' }}>
						<a href="/ru" className="nav-button">Главная</a>
						<a href="/ru/news?theme=CRYPTO" className="nav-button">Крипта</a>
						<a href="/ru/columns" className="nav-button">Инсайдерские блоги</a>
						<a href="/ru/contact" className="nav-button">Контакты</a>
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

