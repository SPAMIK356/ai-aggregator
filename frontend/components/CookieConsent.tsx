'use client';

import { useState, useEffect } from 'react';

const COOKIE_CONSENT_KEY = 'cookie_consent_accepted';

// Inline translations for client component (avoids async dictionary loading)
const translations = {
	en: {
		title: 'We use cookies',
		description: 'This site uses cookies to enhance your browsing experience and analyze traffic. By clicking "Accept", you consent to our use of cookies.',
		privacy: 'Privacy Policy',
		accept: 'Accept',
		privacyLink: '/privacy',
	},
	ru: {
		title: 'Мы используем cookies',
		description: 'Этот сайт использует файлы cookie для улучшения вашего опыта и анализа трафика. Нажимая «Принять», вы соглашаетесь с использованием cookies.',
		privacy: 'Политика конфиденциальности',
		accept: 'Принять',
		privacyLink: '/ru/privacy',
	},
};

type Locale = 'en' | 'ru';

export default function CookieConsent() {
	const [visible, setVisible] = useState(false);
	const [closing, setClosing] = useState(false);
	const [locale, setLocale] = useState<Locale>('en');

	useEffect(() => {
		// Detect locale from URL path
		const path = window.location.pathname;
		const detectedLocale: Locale = path.startsWith('/ru') ? 'ru' : 'en';
		setLocale(detectedLocale);

		// Check if user has already accepted cookies
		const accepted = localStorage.getItem(COOKIE_CONSENT_KEY);
		if (!accepted) {
			// Small delay for smoother page load
			const timer = setTimeout(() => setVisible(true), 800);
			return () => clearTimeout(timer);
		}
	}, []);

	const handleAccept = () => {
		setClosing(true);
		localStorage.setItem(COOKIE_CONSENT_KEY, 'true');
		// Wait for animation to complete before hiding
		setTimeout(() => setVisible(false), 300);
	};

	if (!visible) return null;

	const t = translations[locale];

	return (
		<div className={`cookie-banner ${closing ? 'closing' : ''}`}>
			<div className="cookie-content">
				<div className="cookie-icon">🍪</div>
				<div className="cookie-text">
					<p className="cookie-title">{t.title}</p>
					<p className="cookie-desc">{t.description}</p>
				</div>
				<div className="cookie-actions">
					<a href={t.privacyLink} className="cookie-link">{t.privacy}</a>
					<button onClick={handleAccept} className="cookie-accept">
						{t.accept}
					</button>
				</div>
			</div>

			<style jsx>{`
				.cookie-banner {
					position: fixed;
					bottom: 0;
					left: 0;
					right: 0;
					z-index: 9999;
					padding: 16px;
					animation: slideUp 0.4s ease-out;
				}

				.cookie-banner.closing {
					animation: slideDown 0.3s ease-in forwards;
				}

				@keyframes slideUp {
					from {
						transform: translateY(100%);
						opacity: 0;
					}
					to {
						transform: translateY(0);
						opacity: 1;
					}
				}

				@keyframes slideDown {
					from {
						transform: translateY(0);
						opacity: 1;
					}
					to {
						transform: translateY(100%);
						opacity: 0;
					}
				}

				.cookie-content {
					max-width: 980px;
					margin: 0 auto;
					display: flex;
					align-items: center;
					gap: 16px;
					padding: 18px 22px;
					background: linear-gradient(180deg, #12121a 0%, #0d0d14 100%);
					border: 1px solid #242436;
					border-radius: 12px;
					box-shadow: 0 -10px 40px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.03) inset;
					backdrop-filter: blur(10px);
				}

				.cookie-icon {
					font-size: 32px;
					flex-shrink: 0;
				}

				.cookie-text {
					flex: 1;
					min-width: 0;
				}

				.cookie-title {
					margin: 0 0 4px;
					font-size: 16px;
					font-weight: 700;
					color: #e6e9ef;
				}

				.cookie-desc {
					margin: 0;
					font-size: 14px;
					color: #9aa1aa;
					line-height: 1.5;
				}

				.cookie-actions {
					display: flex;
					align-items: center;
					gap: 16px;
					flex-shrink: 0;
				}

				.cookie-link {
					color: #9aa1aa;
					font-size: 14px;
					text-decoration: underline;
					text-underline-offset: 2px;
					transition: color 0.2s;
				}

				.cookie-link:hover {
					color: #ff6b3d;
				}

				.cookie-accept {
					padding: 10px 24px;
					font-size: 14px;
					font-weight: 600;
					color: #fff;
					background: linear-gradient(135deg, #ff6b3d 0%, #ff2b50 100%);
					border: none;
					border-radius: 8px;
					cursor: pointer;
					transition: transform 0.15s ease, box-shadow 0.15s ease;
					font-family: inherit;
					letter-spacing: 0.3px;
				}

				.cookie-accept:hover {
					transform: translateY(-2px);
					box-shadow: 0 8px 20px rgba(255, 107, 61, 0.35);
				}

				.cookie-accept:active {
					transform: translateY(0);
				}

				/* Mobile responsive */
				@media (max-width: 767px) {
					.cookie-banner {
						padding: 12px;
					}

					.cookie-content {
						flex-direction: column;
						text-align: center;
						padding: 16px;
						gap: 12px;
					}

					.cookie-icon {
						font-size: 28px;
					}

					.cookie-actions {
						flex-direction: column;
						width: 100%;
						gap: 12px;
					}

					.cookie-accept {
						width: 100%;
						padding: 12px 24px;
					}
				}
			`}</style>
		</div>
	);
}
