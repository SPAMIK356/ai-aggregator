from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional

import feedparser
from celery import shared_task
import requests
from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import NewsItem, NewsSource
from .models import TelegramChannel, WebsiteSource
from bs4 import BeautifulSoup
import re
from html import escape
from .rewriter import rewrite_article
try:
	from telethon.tl.types import (
		MessageEntityBold,
		MessageEntityItalic,
		MessageEntityUnderline,
		MessageEntityCode,
		MessageEntityPre,
		MessageEntityBlockquote,
		MessageMediaPhoto,
	)
except Exception:
	MessageEntityBold = MessageEntityItalic = MessageEntityUnderline = None
	MessageEntityCode = MessageEntityPre = MessageEntityBlockquote = None
	MessageMediaPhoto = None

try:
	# Use synchronous helpers to avoid awaiting coroutines in Celery task
	from telethon.sync import TelegramClient
	from telethon.sessions import StringSession
except Exception:  # optional at import time
	TelegramClient = None
	StringSession = None


def _safe_dt(value) -> datetime:
	try:
		return datetime(*value[:6], tzinfo=timezone.utc) if value else timezone.now()
	except Exception:
		return timezone.now()


def _strip_html_tags(value: str) -> str:
	return re.sub(r"<[^>]+>", "", value)


def _format_telegram_html(text: str, entities) -> str:
	"""Render a subset of Telegram entities into HTML tags.

	Supports: bold, italic, underline, code/pre, blockquote.
	Falls back to escaping raw text if entities missing.
	"""
	if not text:
		return ""
	if not entities:
		return escape(text)
	# Build list of (start, end, tag_open, tag_close)
	wraps = []
	for e in entities:
		offset = getattr(e, "offset", None)
		length = getattr(e, "length", None)
		if offset is None or length is None:
			continue
		start = int(offset)
		end = int(offset + length)
		tag_open = tag_close = None
		if MessageEntityBold and isinstance(e, MessageEntityBold):
			tag_open, tag_close = "<b>", "</b>"
		elif MessageEntityItalic and isinstance(e, MessageEntityItalic):
			tag_open, tag_close = "<i>", "</i>"
		elif MessageEntityUnderline and isinstance(e, MessageEntityUnderline):
			tag_open, tag_close = "<u>", "</u>"
		elif MessageEntityCode and isinstance(e, MessageEntityCode):
			tag_open, tag_close = "<code>", "</code>"
		elif MessageEntityPre and isinstance(e, MessageEntityPre):
			tag_open, tag_close = "<pre>", "</pre>"
		elif MessageEntityBlockquote and isinstance(e, MessageEntityBlockquote):
			tag_open, tag_close = "<blockquote>", "</blockquote>"
		if tag_open:
			wraps.append((start, end, tag_open, tag_close))
	# Apply wraps from right to left to keep indices valid
	result = escape(text)
	for start, end, open_tag, close_tag in sorted(wraps, key=lambda x: x[0], reverse=True):
		# Map to escaped positions is non-trivial; as a simplification,
		# re-slice from original text and escape piecewise.
		orig_segment = text[start:end]
		result = (
			escape(text[:start])
			+ open_tag
			+ escape(orig_segment)
			+ close_tag
			+ escape(text[end:])
		)
	return result


@shared_task
def run_parser() -> dict:
	created = 0
	skipped = 0
	for source in NewsSource.objects.filter(is_active=True):
		feed = feedparser.parse(source.url)
		entries = feed.entries or []
		for entry in entries:
			title = getattr(entry, "title", "").strip()
			link = getattr(entry, "link", "").strip()
			description = getattr(entry, "summary", "").strip()
			published_parsed = getattr(entry, "published_parsed", None)
			published_at = _safe_dt(published_parsed)
			if not link:
				skipped += 1
				continue
			try:
				with transaction.atomic():
					NewsItem.objects.create(
						title=title or link,
						original_url=link,
						description=description[:2000],
						published_at=published_at,
						source_name=source.title or source.url,
					)
					created += 1
			except IntegrityError:
				skipped += 1
	return {"created": created, "skipped": skipped}


@shared_task
def deliver_outbox() -> dict:
	from .models import OutboxEvent

	webhook_url = getattr(settings, "WEBHOOK_URL", "")
	if not webhook_url:
		return {"delivered": 0, "skipped": 0, "reason": "no webhook"}

	delivered = 0
	skipped = 0
	for event in OutboxEvent.objects.filter(delivered_at__isnull=True).order_by("created_at")[:100]:
		try:
			resp = requests.post(webhook_url, json={
				"event_type": event.event_type,
				"payload": event.payload,
			})
			if 200 <= resp.status_code < 300:
				event.delivery_attempts += 1
				event.mark_delivered()
				delivered += 1
			else:
				event.delivery_attempts += 1
				event.last_error = f"HTTP {resp.status_code}: {resp.text[:500]}"
				event.save(update_fields=["delivery_attempts", "last_error"])
				skipped += 1
		except Exception as exc:
			event.delivery_attempts += 1
			event.last_error = str(exc)[:500]
			event.save(update_fields=["delivery_attempts", "last_error"])
			skipped += 1
	return {"delivered": delivered, "skipped": skipped}


@shared_task
def fetch_telegram_channels() -> dict:
	"""Fetch new posts from configured Telegram channels and save as NewsItem.

	Requires env vars:
	- TG_API_ID
	- TG_API_HASH
	- TG_STRING_SESSION (recommended) or TG_BOT_TOKEN (not used here)
	"""
	if TelegramClient is None:
		return {"error": "telethon not installed"}

	api_id = getattr(settings, "TG_API_ID", None)
	api_hash = getattr(settings, "TG_API_HASH", None)
	string_session = getattr(settings, "TG_STRING_SESSION", None)
	if not (api_id and api_hash and string_session):
		return {"error": "missing TG creds"}

	created = 0
	skipped = 0
	client = TelegramClient(StringSession(string_session), int(api_id), str(api_hash))
	# Use context manager to connect/disconnect synchronously
	with client:
		for ch in TelegramChannel.objects.filter(is_active=True):
			try:
				entity = ch.username if ch.username.startswith("@") else f"@{ch.username}"
				offset_id = ch.last_message_id or 0
				# Fetch latest messages (newest first), then process oldest->newest
				msgs = list(client.iter_messages(entity, limit=50))
				max_id = ch.last_message_id or 0
				for m in reversed(msgs):
					if m.id and m.id <= offset_id:
						continue
					raw_text = (getattr(m, "text", None) or getattr(m, "message", None) or "")
					html = _format_telegram_html(raw_text, getattr(m, "entities", None))
					if not (raw_text or html):
						skipped += 1
						continue
					url = f"https://t.me/{ch.username.lstrip('@')}/{m.id}"
					published_at = _safe_dt(getattr(m, "date", None).timetuple() if getattr(m, "date", None) else None)
					try:
						with transaction.atomic():
							orig_title = (_strip_html_tags(html).split("\n")[0] or raw_text.split("\n")[0] or url)[:200]
							orig_body = (html or escape(raw_text))[:5000]
							rew = rewrite_article(orig_title, orig_body) or {"title": orig_title, "content": orig_body}
							img_url = ""
							if MessageMediaPhoto and getattr(m, "media", None) and isinstance(m.media, MessageMediaPhoto):
								# Use public CDN path (Telegraph style) if available via m.photo; as a fallback, keep empty
								# For simplicity in MVP, set image_url to the t.me view path; real download needs file save
								img_url = f"https://t.me/{ch.username.lstrip('@')}/{m.id}?single"
							NewsItem.objects.create(
								title=(rew.get("title") or orig_title)[:500],
								original_url=url,
								description=(rew.get("content") or orig_body)[:10000],
								image_url=img_url,
								published_at=published_at,
								source_name=ch.title or ch.username,
							)
							created += 1
					except IntegrityError:
						skipped += 1
					max_id = max(max_id, m.id or 0)
				if max_id and max_id != (ch.last_message_id or 0):
					ch.last_message_id = max_id
					ch.save(update_fields=["last_message_id", "updated_at"])
			except Exception:
				skipped += 1
	return {"created": created, "skipped": skipped}


@shared_task
def fetch_websites() -> dict:
	"""Parse configured websites using CSS selectors and save as NewsItem."""
	created = 0
	skipped = 0
	for ws in WebsiteSource.objects.filter(is_active=True):
		try:
			resp = requests.get(ws.url, timeout=15)
			if resp.status_code != 200:
				skipped += 1
				continue
			soup = BeautifulSoup(resp.text, 'html.parser')
			containers = soup.select(ws.list_selector)
			for c in containers[:50]:
				title_el = c.select_one(ws.title_selector)
				url_el = c.select_one(ws.url_selector)
				if not title_el or not url_el:
					skipped += 1
					continue
				title = title_el.get_text(strip=True)
				link = url_el.get('href') or ''
				if link.startswith('/'):
					from urllib.parse import urljoin
					link = urljoin(ws.url, link)
				desc = ''
				if ws.desc_selector:
					desc_el = c.select_one(ws.desc_selector)
					desc = desc_el.get_text(strip=True) if desc_el else ''
				if not link:
					skipped += 1
					continue
					try:
					with transaction.atomic():
							rew = rewrite_article(title or link, desc or "") or {"title": title or link, "content": desc or ""}
							img = ""
							if ws.image_selector:
								img_el = c.select_one(ws.image_selector)
								if img_el and img_el.get('src'):
									img = img_el.get('src')
									if img.startswith('/'):
										from urllib.parse import urljoin
										img = urljoin(ws.url, img)
						NewsItem.objects.create(
							title=(rew.get("title") or title or link)[:500],
							original_url=link,
							description=(rew.get("content") or desc or "")[:10000],
								image_url=img,
							published_at=timezone.now(),
							source_name=ws.name,
						)
						created += 1
				except IntegrityError:
					skipped += 1
		except Exception:
			skipped += 1
	return {"created": created, "skipped": skipped}


