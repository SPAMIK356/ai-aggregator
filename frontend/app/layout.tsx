import React from 'react';
import dynamic from 'next/dynamic';
import './globals.css';

// Dynamic import with SSR disabled to avoid hydration issues with localStorage/window
const CookieConsent = dynamic(() => import('../components/CookieConsent'), {
	ssr: false,
});

export const metadata = {
	title: '2049.news',
	description: 'News from the future: AI, technology, crypto',
};

export const viewport = {
	width: 'device-width',
	initialScale: 1,
	maximumScale: 1,
	viewportFit: 'cover',
	// @ts-ignore - Next allows 'no'|'yes'
	userScalable: 'no',
};

// Minimal root layout - just html/body shell
// Header/footer are rendered by page-level or route-group layouts
export default function RootLayout({ children }: { children: React.ReactNode }) {
	return (
		<html lang="en">
			<body>
				{children}
				<CookieConsent />
			</body>
		</html>
	);
}


