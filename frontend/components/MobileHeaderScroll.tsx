"use client";

import React from 'react';

export default function MobileHeaderScroll() {
  React.useEffect(() => {
    const docEl = document.documentElement;
    const body = document.body;
    let lastY = window.scrollY;
    let ticking = false;

    const measure = () => {
      const header = document.querySelector<HTMLElement>('.site-header');
      const h = header?.offsetHeight || 64;
      docEl.style.setProperty('--mobileHeaderH', `${h}px`);
    };
    measure();

    const onResize = () => {
      measure();
    };
    window.addEventListener('resize', onResize, { passive: true });

    const update = () => {
      const y = window.scrollY;
      const headerH = parseInt(getComputedStyle(docEl).getPropertyValue('--mobileHeaderH') || '64', 10) || 64;
      const delta = y - lastY;
      // Hide on downward scroll beyond header height, show on upward scroll
      if (y > headerH + 20 && delta > 6) {
        body.classList.add('header-hidden');
      } else if (delta < -6 || y < 10) {
        body.classList.remove('header-hidden');
      }
      lastY = y;
      ticking = false;
    };

    const onScroll = () => {
      if (!ticking) {
        ticking = true;
        requestAnimationFrame(update);
      }
    };

    window.addEventListener('scroll', onScroll, { passive: true });
    return () => {
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', onResize);
      body.classList.remove('header-hidden');
      docEl.style.removeProperty('--mobileHeaderH');
    };
  }, []);

  return null;
}


