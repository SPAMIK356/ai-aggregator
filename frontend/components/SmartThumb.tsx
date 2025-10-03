'use client';

import React from 'react';

type Props = {
  src: string;
  alt?: string;
};

export default function SmartThumb({ src, alt = '' }: Props) {
  const [bucket, setBucket] = React.useState<'wide' | 'square' | 'tall'>('wide');

  const onLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.currentTarget;
    const w = img.naturalWidth || 1;
    const h = img.naturalHeight || 1;
    const r = w / h;
    // Bucket by aspect ratio
    if (r >= 1.25) setBucket('wide');
    else if (r <= 0.9) setBucket('tall');
    else setBucket('square');
  };

  return (
    <div className={`thumb-wrap ${bucket}`}>
      <img src={src} alt={alt} className="thumb-img" onLoad={onLoad} />
    </div>
  );
}


