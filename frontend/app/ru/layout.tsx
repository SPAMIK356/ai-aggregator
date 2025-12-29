import React from 'react';
import PageShell from '../../components/PageShell';

export const metadata = {
	title: '2049.news',
	description: 'Новости будущего: ИИ, технологии, крипта',
};

export default function RuLayout({ children }: { children: React.ReactNode }) {
	return <PageShell locale="ru">{children}</PageShell>;
}

