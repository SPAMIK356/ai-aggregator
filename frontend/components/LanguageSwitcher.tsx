'use client';

import { usePathname } from 'next/navigation';

export default function LanguageSwitcher({ locale }: { locale: string }) {
  const pathname = usePathname();

  // Determine the target locale and path
  const isRussian = locale === 'ru';
  const targetLocale = isRussian ? 'en' : 'ru';

  // Calculate the new path
  let newPath: string;
  if (isRussian) {
    // Currently on Russian, switch to English (remove /ru prefix)
    newPath = pathname.replace(/^\/ru/, '') || '/';
  } else {
    // Currently on English, switch to Russian (add /ru prefix)
    newPath = `/ru${pathname}`;
  }

  return (
    <a
      href={newPath}
      className="lang-switch"
      title={isRussian ? 'Switch to English' : 'Переключить на русский'}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        padding: '4px 8px',
        borderRadius: '4px',
        background: 'var(--surface)',
        border: '1px solid var(--border)',
        color: 'var(--text)',
        fontSize: '0.875rem',
        textDecoration: 'none',
        transition: 'background 0.2s',
      }}
    >
      <span style={{ opacity: isRussian ? 0.5 : 1 }}>EN</span>
      <span style={{ opacity: 0.5 }}>/</span>
      <span style={{ opacity: isRussian ? 1 : 0.5 }}>RU</span>
    </a>
  );
}

