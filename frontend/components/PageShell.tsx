import React from 'react';
import Image from 'next/image';
import newsIcon from '../icons/News_site.png';
import authorsIcon from '../icons/Autors.png';
import contactIcon from '../icons/Contact.png';
import CryptoWidget from './CryptoWidget';
import LanguageSwitcher from './LanguageSwitcher';
import dynamic from 'next/dynamic';

const BurgerMenu = dynamic(() => import('./BurgerMenu'), { ssr: false });
const MobileHeaderScroll = dynamic(() => import('./MobileHeaderScroll'), { ssr: false });

type Locale = 'en' | 'ru';

const translations = {
  en: {
    home: 'Home',
    crypto: 'Crypto',
    blogs: 'Insider Blogs',
    contacts: 'Contacts',
    search: 'Search…',
    footer: '2049.news — a media about the future of technology, artificial intelligence, and the crypto economy. We publish news, opinion columns and analysis from practitioners — developers, founders and researchers.',
  },
  ru: {
    home: 'Главная',
    crypto: 'Крипта',
    blogs: 'Инсайдерские блоги',
    contacts: 'Контакты',
    search: 'Поиск…',
    footer: '2049.news — медиа о будущем технологий, искусственного интеллекта и криптоэкономики. Мы публикуем новости, авторские колонки и аналитику от практиков — разработчиков, основателей и исследователей.',
  },
};

export default function PageShell({ 
  children, 
  locale = 'en' 
}: { 
  children: React.ReactNode; 
  locale?: Locale;
}) {
  const t = translations[locale];
  const prefix = locale === 'ru' ? '/ru' : '';

  return (
    <>
      <MobileHeaderScroll />
      <header className="site-header">
        <div className="container">
          <nav className="nav">
            <a href={`${prefix}/`} className="brand">2049.news</a>
            <div className="desktop-nav">
              <a href={`${prefix}/`} className="nav-button">{t.home}</a>
              <a href={`${prefix}/news?theme=CRYPTO`} className="nav-button">
                <Image className="nav-ico" src={newsIcon} alt="" width={16} height={16} /> {t.crypto}
              </a>
              <a href={`${prefix}/columns`} className="nav-button">
                <Image className="nav-ico" src={authorsIcon} alt="" width={16} height={16} /> {t.blogs}
              </a>
              <a href={`${prefix}/contact`} className="nav-button">
                <Image className="nav-ico" src={contactIcon} alt="" width={16} height={16} /> {t.contacts}
              </a>
            </div>
            <span className="spacer" />
            <form className="mobile-search" action={`${prefix}/search`} method="get">
              <input name="q" type="text" placeholder={t.search} aria-label={t.search} />
            </form>
            <CryptoWidget />
            <LanguageSwitcher locale={locale} />
            <BurgerMenu />
          </nav>
          <div className="mobile-crypto">
            <CryptoWidget />
          </div>
        </div>
      </header>
      <main className="container">{children}</main>
      <footer className="site-footer">
        <div className="container">
          <p className="footer-about">
            <strong>2049.news</strong> — {t.footer.replace('2049.news — ', '')}
          </p>
          <nav className="footer-nav" style={{ justifyContent: 'center' }}>
            <a href={`${prefix}/`} className="nav-button">{t.home}</a>
            <a href={`${prefix}/news?theme=CRYPTO`} className="nav-button">{t.crypto}</a>
            <a href={`${prefix}/columns`} className="nav-button">{t.blogs}</a>
            <a href={`${prefix}/contact`} className="nav-button">{t.contacts}</a>
          </nav>
          <div style={{ display: 'flex', justifyContent: 'center', marginTop: 12 }}>
            <BurgerMenu />
          </div>
        </div>
      </footer>
    </>
  );
}

