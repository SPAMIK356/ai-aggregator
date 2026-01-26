"use client";

import React from 'react';
import { createPortal } from 'react-dom';
import { usePathname } from 'next/navigation';

type Locale = 'en' | 'ru';

const translations = {
    en: {
        menu: 'Menu',
        close: 'Close',
        search: 'Search…',
        home: 'Home',
        crypto: 'Crypto',
        blogs: 'Insider Blogs',
        contacts: 'Contacts',
        about: 'About',
        privacy: 'Privacy Policy',
        terms: 'Terms of Use',
        newsFilters: 'News filters',
        all: 'All',
        ai: 'AI',
        language: 'Language',
        switchLang: 'Переключить на русский',
    },
    ru: {
        menu: 'Меню',
        close: 'Закрыть',
        search: 'Поиск…',
        home: 'Главная',
        crypto: 'Крипта',
        blogs: 'Инсайдерские блоги',
        contacts: 'Контакты',
        about: 'О нас',
        privacy: 'Политика конфиденциальности',
        terms: 'Условия использования',
        newsFilters: 'Фильтры новостей',
        all: 'Все',
        ai: 'ИИ',
        language: 'Язык',
        switchLang: 'Switch to English',
    },
};

export default function BurgerMenu({ locale = 'en' }: { locale?: Locale }) {
    const [open, setOpen] = React.useState(false);
    const [mounted, setMounted] = React.useState(false);
    const pathname = usePathname();
    const t = translations[locale];
    const prefix = locale === 'ru' ? '/ru' : '';
    
    // Language switch path
    const isRussian = locale === 'ru';
    const langSwitchPath = isRussian 
        ? (pathname.replace(/^\/ru/, '') || '/') 
        : `/ru${pathname}`;

    React.useEffect(() => {
        setMounted(true);
        const onKey = (e: KeyboardEvent) => {
            if (e.key === 'Escape') setOpen(false);
        };
        window.addEventListener('keydown', onKey);
        return () => window.removeEventListener('keydown', onKey);
    }, []);

    React.useEffect(() => {
        if (!mounted) return;
        document.body.classList.toggle('menu-open', open);
        return () => { document.body.classList.remove('menu-open'); };
    }, [open, mounted]);

    return (
        <>
            <button className="burger-btn" aria-label={t.menu} onClick={() => setOpen(true)}>
                <span className="hb-line" />
                <span className="hb-line" />
                <span className="hb-line" />
            </button>
            {mounted && createPortal(
                <>
                    {open && <div className="backdrop" onClick={() => setOpen(false)} />}
                    <div className={"drawer" + (open ? " open" : "") } role="dialog" aria-modal="true">
                        <div className="drawer-header">
                            <strong>{t.menu}</strong>
                            <button className="drawer-close" aria-label={t.close} onClick={() => setOpen(false)}>×</button>
                        </div>
                        <div className="drawer-search">
                            <form action={`${prefix}/search`} method="get">
                                <input name="q" type="text" placeholder={t.search} aria-label={t.search} />
                            </form>
                        </div>
                        <div className="drawer-lang">
                            <a 
                                href={langSwitchPath} 
                                className="lang-switch-mobile"
                                title={t.switchLang}
                            >
                                <span className="lang-icon">🌐</span>
                                <span>{isRussian ? 'English' : 'Русский'}</span>
                            </a>
                        </div>
                        <nav className="drawer-nav">
                            <a href={`${prefix}/`} onClick={() => setOpen(false)} className="nav-button">{t.home}</a>
                            <a href={`${prefix}/news?theme=CRYPTO`} onClick={() => setOpen(false)} className="nav-button">{t.crypto}</a>
                            <a href={`${prefix}/columns`} onClick={() => setOpen(false)} className="nav-button">{t.blogs}</a>
                            <a href={`${prefix}/contact`} onClick={() => setOpen(false)} className="nav-button">{t.contacts}</a>
                            <a href={`${prefix}/about`} onClick={() => setOpen(false)} className="nav-button">{t.about}</a>
                            <a href={`${prefix}/privacy`} onClick={() => setOpen(false)} className="nav-button">{t.privacy}</a>
                            <a href={`${prefix}/terms`} onClick={() => setOpen(false)} className="nav-button">{t.terms}</a>
                            <div className="drawer-sep" />
                            <div className="drawer-section">{t.newsFilters}</div>
                            <a href={`${prefix}/news`} onClick={() => setOpen(false)} className="pill">{t.all}</a>
                            <a href={`${prefix}/news?theme=AI`} onClick={() => setOpen(false)} className="pill">{t.ai}</a>
                            <a href={`${prefix}/news?theme=CRYPTO`} onClick={() => setOpen(false)} className="pill">{t.crypto}</a>
                        </nav>
                    </div>
                </>, document.body)}
        </>
    );
}


