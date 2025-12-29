import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const locales = ['en', 'ru'];
const defaultLocale = 'en';

function getLocaleFromPathname(pathname: string): string | null {
  const segments = pathname.split('/');
  const maybeLocale = segments[1];
  if (locales.includes(maybeLocale)) {
    return maybeLocale;
  }
  return null;
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Skip for static files, api routes, and special paths
  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api') ||
    pathname.startsWith('/fe-') ||
    pathname.startsWith('/media') ||
    pathname.includes('.') // static files
  ) {
    return NextResponse.next();
  }

  const pathLocale = getLocaleFromPathname(pathname);

  // If we already have a locale in the path, continue
  if (pathLocale) {
    return NextResponse.next();
  }

  // For root paths without locale, treat as English (default)
  // No redirect needed - the page will handle it
  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next|api|fe-|media|.*\\..*).*)'],
};

