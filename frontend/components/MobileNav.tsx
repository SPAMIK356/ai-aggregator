'use client';

import React from 'react';
import Image from 'next/image';
import newsIcon from '../icons/News_site.png';
import authorsIcon from '../icons/Autors.png';
import contactIcon from '../icons/Contact.png';

export default function MobileNav() {
  const [open, setOpen] = React.useState(false);
  const drawerRef = React.useRef<HTMLDivElement | null>(null);

  React.useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open]);

  return (
    <>
      <button
        className="hamburger"
        aria-label="Open menu"
        aria-expanded={open}
        aria-controls="mobile-drawer"
        onClick={() => setOpen(true)}
      >
        <span className="hb-line" />
        <span className="hb-line" />
        <span className="hb-line" />
      </button>

      {open && <div className="backdrop" onClick={() => setOpen(false)} aria-hidden="true" />}

      <div
        ref={drawerRef}
        id="mobile-drawer"
        className={`drawer${open ? ' open' : ''}`}
        role="dialog"
        aria-modal="true"
        aria-label="Navigation"
      >
        <div className="drawer-header">
          <a href="/" className="brand">2049.news</a>
          <button className="drawer-close" aria-label="Close menu" onClick={() => setOpen(false)}>×</button>
        </div>
        <nav className="drawer-nav">
          <a href="/news" className="nav-button" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Image src={newsIcon} alt="News" width={18} height={18} />
            Future News
          </a>
          <a href="/columns" className="nav-button" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Image src={authorsIcon} alt="Author columns" width={18} height={18} />
            Insider Blogs
          </a>
          <form action="/search" method="get" className="drawer-search">
            <input name="q" type="text" placeholder="Search…" aria-label="Search" />
          </form>
          <a href="/contact" className="nav-button" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Image src={contactIcon} alt="Contacts" width={18} height={18} />
            Contacts
          </a>
        </nav>
      </div>
    </>
  );
}



