"use client";

import React from 'react';
import { createPortal } from 'react-dom';

export default function BurgerMenu() {
    const [open, setOpen] = React.useState(false);
    const [mounted, setMounted] = React.useState(false);

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
            <button className="burger-btn" aria-label="Menu" onClick={() => setOpen(true)}>
                <span className="hb-line" />
                <span className="hb-line" />
                <span className="hb-line" />
            </button>
            {mounted && createPortal(
                <>
                    {open && <div className="backdrop" onClick={() => setOpen(false)} />}
                    <div className={"drawer" + (open ? " open" : "") } role="dialog" aria-modal="true">
                        <div className="drawer-header">
                            <strong>Menu</strong>
                            <button className="drawer-close" aria-label="Close" onClick={() => setOpen(false)}>×</button>
                        </div>
                        <div className="drawer-search">
                            <form action="/search" method="get">
                                <input name="q" type="text" placeholder="Search…" aria-label="Search" />
                            </form>
                        </div>
                        <nav className="drawer-nav">
                            <a href="/" onClick={() => setOpen(false)} className="nav-button">Home</a>
                            <a href="/news?theme=CRYPTO" onClick={() => setOpen(false)} className="nav-button">Crypto</a>
                            <a href="/columns" onClick={() => setOpen(false)} className="nav-button">Insider Blogs</a>
                            <a href="/contact" onClick={() => setOpen(false)} className="nav-button">Contacts</a>
                            <a href="/about" onClick={() => setOpen(false)} className="nav-button">About</a>
                            <a href="/privacy" onClick={() => setOpen(false)} className="nav-button">Privacy Policy</a>
                            <a href="/terms" onClick={() => setOpen(false)} className="nav-button">Terms of Use</a>
                            <div className="drawer-sep" />
                            <div className="drawer-section">News filters</div>
                            <a href="/news" onClick={() => setOpen(false)} className="pill">All</a>
                            <a href="/news?theme=AI" onClick={() => setOpen(false)} className="pill">AI</a>
                            <a href="/news?theme=CRYPTO" onClick={() => setOpen(false)} className="pill">Crypto</a>
                        </nav>
                    </div>
                </>, document.body)}
        </>
    );
}


