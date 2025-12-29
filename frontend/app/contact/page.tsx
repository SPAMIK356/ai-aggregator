import React from 'react';
import PageShell from '../../components/PageShell';

export default function ContactPage() {
	return (
		<PageShell locale="en">
		<article className="prose">
  <header>
    <h1>Contacts</h1>
    <p><strong>Write to us:</strong> 2049.news@gmail.com</p>
    <p>We’re open to collaboration, partnership proposals, content exchange, and joint publications. If you have ideas, news, analytical materials, or projects for our audience — reach out.</p>
  </header>

  <section>
    <h2>📩 Submit an Article</h2>
    <p>Send your material to <strong>2049.news.articles@gmail.com</strong> with the subject line: <span>Article Submission — [Title of the Material]</span></p>
    <p>Include in your email:</p>
    <ul>
      <li>Article title</li>
      <li>Author’s name (or pseudonym for anonymity)</li>
      <li>Short summary (2–3 sentences about the core idea)</li>
      <li>Full text (.docx, HTML, or Markdown)</li>
      <li>Images/graphics (.jpg, .png, or .webp, min. 1200×675 px)</li>
      <li>Contact details for follow-up (email, Telegram, or preferred channel)</li>
    </ul>
  </section>

  <section>
    <h2>📰 Article Requirements</h2>
    <ul>
      <li>Original work, not previously published elsewhere</li>
      <li>Focus areas: technology, AI, innovation, cryptocurrency, economy, the future of media, society</li>
      <li>Length: 1,000–10,000 characters (excluding spaces)</li>
      <li>External links are allowed if they point to reliable, verifiable sources</li>
      <li>We may edit grammar, punctuation, and structure without changing meaning</li>
    </ul>
  </section>

  <section>
    <h2>🤝 Collaboration &amp; Partnerships</h2>
    <p>We welcome new partners, experts, and contributors. Possible formats:</p>
    <ul>
      <li>Joint publications and collaborations</li>
      <li>Expert interviews</li>
      <li>Content exchange and reposts</li>
      <li>Special projects and advertising integrations</li>
    </ul>
    <p>For partnership inquiries: <strong>2049.news.partners@gmail.com</strong></p>
  </section>
</article>
		</PageShell>
	);
}

