"use client";

type Props = { src: string; alt: string; variant?: 'post' | 'feed'; url: string };

export default function PromoBanner({ src, alt, variant, url }: Props) {
  const cls = variant === 'feed' ? 'promo-wrap feed' : 'promo-wrap post';
  return (
    <div
      className={cls}
      role="button"
      tabIndex={0}
      onClick={() => {
        try { window.open(url, '_blank', 'noopener'); } catch {}
      }}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          try { window.open(url, '_blank', 'noopener'); } catch {}
        }
      }}
      style={{ cursor: 'pointer' }}
      aria-label={alt}
      title={alt}
    >
      <div className="promo-frame">
        <img src={src} alt={alt} />
      </div>
    </div>
  );
}


