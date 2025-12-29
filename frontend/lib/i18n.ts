export const locales = ['en', 'ru'] as const;
export type Locale = (typeof locales)[number];
export const defaultLocale: Locale = 'en';

// Simple dictionary type
export type Dictionary = {
  site: { name: string; description: string };
  nav: { home: string; crypto: string; blogs: string; contacts: string; search: string };
  hero: { title: string; description: string; slogans: string[] };
  sections: { news: string; blogs: string };
  footer: { about: string };
  common: { readMore: string; loading: string; noResults: string };
};

const dictionaries: Record<Locale, () => Promise<Dictionary>> = {
  en: () => import('../dictionaries/en.json').then((m) => m.default),
  ru: () => import('../dictionaries/ru.json').then((m) => m.default),
};

export async function getDictionary(locale: Locale): Promise<Dictionary> {
  return dictionaries[locale]();
}

export function isValidLocale(locale: string): locale is Locale {
  return locales.includes(locale as Locale);
}

