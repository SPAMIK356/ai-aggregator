from __future__ import annotations

from datetime import datetime
from pathlib import Path
import os
from typing import Iterable, Optional

import feedparser
from celery import shared_task
from celery.utils.log import get_task_logger
import requests
from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import NewsItem, NewsSource
from .models import TelegramChannel, WebsiteSource, KeywordFilter, ParserConfig, Hashtag
from bs4 import BeautifulSoup
from PIL import Image, ImageOps
from urllib.parse import urlparse
import re
from html import escape
from .rewriter import rewrite_article
import json
try:
	from telegram import Bot, ParseMode
except Exception:
	Bot = None
	ParseMode = None
logger = get_task_logger(__name__)

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


def _to_plain_text(value: str) -> str:
	"""Convert HTML/Markdown-rich text into plain text for Telegram.

	Removes HTML tags/blocks, markdown links/emphasis/code, and bare URLs.
	"""
	try:
		if not value:
			return ""
		# Remove code/pre/style blocks entirely
		text = re.sub(r"<(pre|code|style)[\s\S]*?</\\1>", " ", value, flags=re.I)
		# Strip remaining HTML tags
		text = _strip_html_tags(text)
		# Markdown links: [text](url) -> text
		text = re.sub(r"\\[([^\\]]+)\\]\\((?:https?://|www\\.)[^\\s)]+\\)", r"\\1", text)
		# Remove emphasis/code markers: **, __, *, _, `, ```
		text = re.sub(r"```[\s\S]*?```", " ", text)
		text = re.sub(r"`+", "", text)
		text = re.sub(r"\\*\\*|__|\\*|_", "", text)
		# Remove bare URLs
		text = re.sub(r"https?://\\S+|www\\.\\S+", "", text)
		# Decode HTML entities and normalize whitespace
		import html as _html
		text = _html.unescape(text)
		text = re.sub(r"[ \t]+", " ", text)
		text = re.sub(r"\n{3,}", "\n\n", text)
		return text.strip()
	except Exception:
		return (value or "").strip()


def _to_telegram_html(value: str) -> str:
	"""Sanitize to Telegram HTML subset: allow <b>, <i>, <u>, <s>, <code>, <pre>, <a>.

	- Drops scripts/styles and unsupported tags
	- Normalizes synonyms (strong->b, em->i, ins->u, del/strike->s)
	- Keeps only href on <a> and only http/https links
	- Converts block tags to newlines
	"""
	try:
		if not value:
			return ""
		allowed = {"b", "i", "u", "s", "code", "pre", "a", "br"}
		block_newline = {"p", "div", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote"}
		soup = BeautifulSoup(value, "html.parser")
		# Remove dangerous blocks
		for t in soup.find_all(["script", "style"]):
			t.decompose()
		# Normalize synonyms first
		for tag in soup.find_all(True):
			name = tag.name.lower()
			if name == "strong":
				tag.name = "b"
			elif name == "em":
				tag.name = "i"
			elif name == "ins":
				tag.name = "u"
			elif name in ("del", "strike"):
				tag.name = "s"
		# Convert block tags to newline boundaries and unwrap
		for tag in list(soup.find_all(block_newline)):
			tag.insert_before("\n")
			tag.insert_after("\n")
			tag.unwrap()
		# Clean all tags, keeping only the allowed subset and safe attributes
		for tag in soup.find_all(True):
			name = tag.name.lower()
			if name == "a":
				href = tag.get("href", "")
				if not href.startswith("http://") and not href.startswith("https://"):
					# Drop unsafe links
					tag.unwrap()
					continue
				# Keep only href
				for attr in list(tag.attrs.keys()):
					if attr != "href":
						del tag.attrs[attr]
			elif name in allowed:
				# Allowed tag, drop all attributes
				for attr in list(tag.attrs.keys()):
					del tag.attrs[attr]
			else:
				# Replace unsupported tags with their text
				tag.unwrap()
		# Build cleaned HTML string
		html = "".join(str(c) for c in soup.contents)
		# Normalize multiple newlines
		html = re.sub(r"\n{3,}", "\n\n", html)
		return html.strip()
	except Exception:
		# Fallback to plain text if sanitization fails
		return _to_plain_text(value)


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


def _compress_image_at_path(path: Path, cfg: Optional[ParserConfig]) -> None:
	"""Resize/compress image in-place if it exceeds cfg max dimensions.

	Safe no-op on errors or if cfg has limits disabled.
	"""
	try:
		if not cfg:
			return
		max_w = int(getattr(cfg, "max_image_width", 0) or 0)
		max_h = int(getattr(cfg, "max_image_height", 0) or 0)
		quality = int(getattr(cfg, "image_quality", 85) or 85)
		if not (max_w or max_h):
			return
		if not path.exists():
			return
		with Image.open(path) as im:
			im = ImageOps.exif_transpose(im)
			w, h = im.size
			# Compute scale preserving aspect
			scale_w = (max_w / w) if (max_w and w > max_w) else 1.0
			scale_h = (max_h / h) if (max_h and h > max_h) else 1.0
			scale = min(scale_w, scale_h)
			if scale < 1.0:
				new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
				im = im.resize(new_size, Image.LANCZOS)
			ext = path.suffix.lower()
			params = {}
			if ext in (".jpg", ".jpeg"):
				params = {"format": "JPEG", "quality": quality, "optimize": True, "progressive": True}
			elif ext == ".webp":
				params = {"format": "WEBP", "quality": quality, "method": 6}
			elif ext == ".png":
				params = {"format": "PNG", "optimize": True}
			if params:
				im.save(path, **params)
			else:
				# Fallback keep original format
				im.save(path)
	except Exception:
		# Best-effort; ignore compression failures
		logger.exception("Image compression failed for %s", str(path))


@shared_task
def run_parser() -> dict:
	# Global parser toggle
	cfg = ParserConfig.objects.order_by("-updated_at").first()
	if cfg and not cfg.is_enabled:
		logger.info("RSS parser disabled by admin")
		return {"created": 0, "skipped": 0, "disabled": True}
	min_chars = int(getattr(cfg, "min_chars", 0) or 0) if cfg else 0
	created = 0
	skipped = 0
	# Load active keyword phrases once
	phrases = list(KeywordFilter.objects.filter(is_active=True).values_list("phrase", flat=True))
	phrases_lc = [p.lower() for p in phrases if p]
	for source in NewsSource.objects.filter(is_active=True):
		logger.info("RSS parse start url=%s", source.url)
		feed = feedparser.parse(source.url)
		entries = feed.entries or []
		logger.info("RSS entries=%d", len(entries))
		for entry in entries:
			title = getattr(entry, "title", "").strip()
			link = getattr(entry, "link", "").strip()
			description = getattr(entry, "summary", "").strip()
			published_parsed = getattr(entry, "published_parsed", None)
			published_at = _safe_dt(published_parsed)
			if not link:
				skipped += 1
				continue
			# Keyword filter (pre-rewrite)
			orig_title = title or link
			orig_body = description or ""
			full_text = f"{orig_title}\n{orig_body}".lower()
			if phrases_lc and any(kw in full_text for kw in phrases_lc):
				logger.info("RSS keyword skip url=%s", link)
				skipped += 1
				continue
			try:
				with transaction.atomic():
					# Skip too-short items per admin config
					if min_chars and len((title or "") + "\n" + (description or "")) < min_chars:
						skipped += 1
						continue
					# Pick theme from source.default_theme (fallback to AI)
					theme_val = source.default_theme or NewsItem.Theme.AI
					NewsItem.objects.create(
						title=title or link,
						original_url=link,
						description=description[:2000],
						published_at=published_at,
						source_name=source.title or source.url,
						theme=theme_val,
					)
					created += 1
			except IntegrityError:
				skipped += 1
				logger.info("RSS duplicate skip url=%s", link)
	logger.info("RSS done created=%d skipped=%d", created, skipped)
	return {"created": created, "skipped": skipped}


@shared_task
def deliver_outbox() -> dict:
	from .models import OutboxEvent, NewsItem

	webhook_url = getattr(settings, "WEBHOOK_URL", "")
	bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
	channel = getattr(settings, "TELEGRAM_CHANNEL", "")
	if not webhook_url:
		# If webhook not configured, we can still deliver to Telegram if configured
		if not (bot_token and channel and Bot):
			return {"delivered": 0, "skipped": 0, "reason": "no delivery configured"}

	delivered = 0
	skipped = 0
	for event in OutboxEvent.objects.filter(delivered_at__isnull=True).order_by("created_at")[:100]:
		try:
			ok = False
			last_err = ""
			# Drop legacy events without id (pre-payload schema) to avoid infinite retries
			try:
				if event.event_type == OutboxEvent.EVENT_NEWS_CREATED:
					pl = event.payload or {}
					if not pl.get("id"):
						event.delivery_attempts += 1
						event.mark_delivered()
						skipped += 1
						continue
			except Exception:
				pass
			# Prefer webhook if configured
			if webhook_url:
				resp = requests.post(webhook_url, json={
					"event_type": event.event_type,
					"payload": event.payload,
				})
				ok = 200 <= resp.status_code < 300
				if not ok:
					last_err = f"WEBHOOK HTTP {resp.status_code}"
			# Fallback to Telegram bot
			if (not ok) and bot_token and channel and Bot:
				try:
					bot = Bot(token=bot_token)
					payload = event.payload or {}
					t = (payload.get("title") or "New post").strip()
					body = (payload.get("body") or "").strip()
					img = (payload.get("image_url") or "").strip()

					# If this is a NewsItem event, re-fetch from DB to get latest data
					try:
						if event.event_type == OutboxEvent.EVENT_NEWS_CREATED:
							nid = payload.get("id")
							if nid:
								ni = NewsItem.objects.filter(pk=int(nid)).only("title", "description", "image_url", "image_file", "original_url").first()
								if ni:
									t = (ni.title or t).strip()
									body = (ni.description or body or "").strip()
									if not img:
										img = (ni.image_url or "").strip()
										if not img and getattr(ni, "image_file", None):
											try:
												img = ni.image_file.url  # type: ignore[attr-defined]
											except Exception:
												img = ""
					except RuntimeError as _skip:
						# Mark as delivered to avoid retry loop on skipped items
						event.delivery_attempts += 1
						event.mark_delivered()
						skipped += 1
						continue
					except Exception:
						pass
					# Optionally rewrite specifically for Telegram if enabled
					try:
						from .rewriter import get_active_telegram_config, rewrite_article_tg
						_tg_cfg = get_active_telegram_config()
						if _tg_cfg:
							rew = rewrite_article_tg(t, body)
							if rew and isinstance(rew, dict):
								t = (rew.get("title") or t).strip()
								body = (rew.get("content") or body or "").strip()
					except Exception:
						pass
					# Prefer Telegram HTML formatting with safe subset; fallback to plain text
					text = f"{t}\n\n{body}".strip()
					text_html = _to_telegram_html(text)
					text_plain = _to_plain_text(text)
					if img:
						try:
							pm = (ParseMode.HTML if 'ParseMode' in globals() and ParseMode else 'HTML')
							bot.send_photo(chat_id=channel, photo=img, caption=text_html[:1024], parse_mode=pm)
							ok = True
						except Exception:
							# Fallback to photo+plain caption; if that fails, try message HTML, then plain
							try:
								bot.send_photo(chat_id=channel, photo=img, caption=text_plain[:1024])
								ok = True
							except Exception:
								try:
									pm = (ParseMode.HTML if 'ParseMode' in globals() and ParseMode else 'HTML')
									bot.send_message(chat_id=channel, text=text_html[:4096], parse_mode=pm, disable_web_page_preview=True)
									ok = True
								except Exception:
									bot.send_message(chat_id=channel, text=text_plain[:4096], disable_web_page_preview=True)
									ok = True
					else:
						try:
							pm = (ParseMode.HTML if 'ParseMode' in globals() and ParseMode else 'HTML')
							bot.send_message(chat_id=channel, text=text_html[:4096], parse_mode=pm, disable_web_page_preview=True)
							ok = True
						except Exception:
							bot.send_message(chat_id=channel, text=text_plain[:4096], disable_web_page_preview=True)
							ok = True
				except Exception as _tg_exc:
					ok = False
					last_err = f"TG {type(_tg_exc).__name__}: {str(_tg_exc)[:300]}"
			if ok:
				event.delivery_attempts += 1
				event.mark_delivered()
				delivered += 1
			else:
				event.delivery_attempts += 1
				event.last_error = last_err or ("Webhook failed" if webhook_url else "Delivery failed")
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

	# Global parser toggle
	cfg = ParserConfig.objects.order_by("-updated_at").first()
	if cfg and not cfg.is_enabled:
		logger.info("TG parser disabled by admin")
		return {"created": 0, "skipped": 0, "disabled": True}
	min_chars = int(getattr(cfg, "min_chars", 0) or 0) if cfg else 0

	created = 0
	skipped = 0
	# Load active keyword phrases once
	phrases = list(KeywordFilter.objects.filter(is_active=True).values_list("phrase", flat=True))
	phrases_lc = [p.lower() for p in phrases if p]
	logger.info("TG fetch start")
	client = TelegramClient(StringSession(string_session), int(api_id), str(api_hash))
	# Use context manager to connect/disconnect synchronously
	with client:
		for ch in TelegramChannel.objects.filter(is_active=True):
			try:
				entity = ch.username if ch.username.startswith("@") else f"@{ch.username}"
				# Skip invite links or invalid entities
				if entity.startswith("@http") or "+" in entity:
					logger.error("TG channel error: Invalid entity '%s'. Use public @username, not invite link.", entity)
					skipped += 1
					continue
				offset_id = ch.last_message_id or 0
				logger.info("TG channel=%s offset_id=%s", entity, offset_id)
				# Fetch latest messages (newest first), then process oldest->newest
				msgs = list(client.iter_messages(entity, limit=50))
				logger.info("TG messages fetched=%d", len(msgs))
				max_id = ch.last_message_id or 0
				for m in reversed(msgs):
					if m.id and m.id <= offset_id:
						continue
					# Track max_id early so skips still advance checkpoint
					max_id = max(max_id, m.id or 0)
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
							# Keyword filter (pre-rewrite)
							if phrases_lc:
								full_text = f"{orig_title}\n{orig_body}".lower()
								if any(kw in full_text for kw in phrases_lc):
									logger.info("TG keyword skip url=%s", url)
									skipped += 1
									continue
							# Rewrite with AI (best-effort)
							try:
								rew = rewrite_article(orig_title, orig_body)
							except Exception:
								rew = None
							if not rew:
								rew = {"title": orig_title, "content": orig_body}
							# Skip too-short per config (check rewritten/body)
							effective_body = (rew.get("content") or orig_body) or ""
							if min_chars and len((_strip_html_tags(effective_body) or effective_body)) < min_chars:
								skipped += 1
								continue
						# Try to build image URL
						img_url = ""
						try:
							if ch.parse_images and getattr(m, "photo", None):
								target_dir = Path(getattr(settings, "MEDIA_ROOT", Path("media"))) / "telegram" / ch.username.lstrip("@")
								target_dir.mkdir(parents=True, exist_ok=True)
								saved = client.download_media(m, file=str(target_dir))
								if saved:
									saved_path = Path(saved)
									# Normalize filename to avoid spaces/parentheses in URLs
									try:
										orig_name = saved_path.name
										safe_name = re.sub(r"\s+", "_", orig_name)
										safe_name = safe_name.replace("(", "").replace(")", "")
										if safe_name != orig_name:
											new_path = saved_path.with_name(safe_name)
											saved_path.rename(new_path)
											saved_path = new_path
									except Exception:
										pass
								media_root = Path(getattr(settings, "MEDIA_ROOT", Path("media")))
								# Compress if exceeds limits
								try:
									cfg2 = ParserConfig.objects.order_by("-updated_at").first()
									_compress_image_at_path(saved_path, cfg2)
								except Exception:
									logger.exception("Compress failed")
								rel = saved_path.relative_to(media_root)
								media_url = getattr(settings, "MEDIA_URL", "/media/")
								img_url = f"{media_url}{rel.as_posix()}"
								logger.info("TG image saved path=%s url=%s", str(saved_path), img_url)
						except Exception:
							# If anything fails, fall back to t.me permalink
							img_url = f"https://t.me/{ch.username.lstrip('@')}/{m.id}?single"
							logger.exception("TG image download failed; using permalink url=%s", img_url)
						# Final fallback if no local image was produced but message includes a photo entity
						if ch.parse_images and (not img_url) and MessageMediaPhoto and getattr(m, "media", None) and isinstance(m.media, MessageMediaPhoto):
							img_url = f"https://t.me/{ch.username.lstrip('@')}/{m.id}?single"
							logger.info("TG image fallback to permalink url=%s", img_url)
						# Determine theme: use AI output if present else channel default else AI
						theme_val = None
						try:
							t = (rew or {}).get("theme") if isinstance(rew, dict) else None
							if isinstance(t, str) and t.strip().upper() in (NewsItem.Theme.AI, NewsItem.Theme.CRYPTO):
								theme_val = t.strip().upper()
						except Exception:
							theme_val = None
						n = NewsItem.objects.create(
							title=(rew.get("title") or orig_title)[:500],
							original_url=url,
							description=(rew.get("content") or orig_body)[:10000],
							image_url=img_url,
							published_at=published_at,
							source_name=ch.title or ch.username,
							theme=(theme_val or ch.default_theme or NewsItem.Theme.AI),
						)
						# Attach hashtags if provided and valid
						try:
							tags = rew.get("hashtags") if isinstance(rew, dict) else None
							if isinstance(tags, list) and tags:
								slugs = [str(s).strip().lower() for s in tags if s]
								objs = list(Hashtag.objects.filter(slug__in=slugs, is_active=True))
								if objs:
									n.hashtags.add(*objs)
						except Exception:
							logger.exception("Attach hashtags failed (TG)")
						logger.info("TG created NewsItem url=%s image_url=%s", url, img_url)
						created += 1
					except IntegrityError:
						skipped += 1
						logger.info("TG duplicate skip url=%s", url)
				if max_id and max_id != (ch.last_message_id or 0):
					ch.last_message_id = max_id
					ch.save(update_fields=["last_message_id", "updated_at"])
			except Exception:
				skipped += 1
				logger.exception("TG channel error")
	logger.info("TG done created=%d skipped=%d", created, skipped)
	return {"created": created, "skipped": skipped}


@shared_task
def fetch_websites() -> dict:
	"""Parse configured websites using CSS selectors and save as NewsItem."""
	# Global parser toggle
	cfg = ParserConfig.objects.order_by("-updated_at").first()
	if cfg and not cfg.is_enabled:
		logger.info("WEB parser disabled by admin")
		return {"created": 0, "skipped": 0, "disabled": True}
	min_chars = int(getattr(cfg, "min_chars", 0) or 0) if cfg else 0

	created = 0
	skipped = 0
	# Load active keyword phrases once
	phrases = list(KeywordFilter.objects.filter(is_active=True).values_list("phrase", flat=True))
	phrases_lc = [p.lower() for p in phrases if p]
	for ws in WebsiteSource.objects.filter(is_active=True):
		try:
			logger.info("WEB parse start name=%s url=%s", ws.name, ws.url)
			resp = requests.get(ws.url, timeout=15, headers={"User-Agent": "Mozilla/5.0 (compatible; ai-aggregator/1.0)"})
			if resp.status_code != 200:
				skipped += 1
				logger.info("WEB non-200 status=%s", resp.status_code)
				continue
			soup = BeautifulSoup(resp.text, 'html.parser')
			containers = soup.select(ws.list_selector)
			logger.info("WEB containers=%d selector=%s", len(containers), ws.list_selector)
			for c in containers[:50]:
				title_el = c.select_one(ws.title_selector)
				url_el = c.select_one(ws.url_selector)
				if not title_el or not url_el:
					skipped += 1
					logger.info("WEB missing title/url")
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
				# Fetch full article body from detail page
				full_body = desc
				try:
					resp_detail = requests.get(link, timeout=20, headers={"User-Agent": "Mozilla/5.0 (compatible; ai-aggregator/1.0)"})
					if resp_detail.status_code == 200:
						from bs4 import BeautifulSoup as _BS
						detail = _BS(resp_detail.text, 'html.parser')
						# Heuristic: prefer article tag, else main, else body text
						art = detail.select_one('article') or detail.select_one('main') or detail.body
						if art:
							full_body = art.get_text("\n", strip=True)
							# Trim excessively long bodies
							if full_body and len(full_body) > 12000:
								full_body = full_body[:12000]
				except Exception:
					pass
				if not link:
					skipped += 1
					logger.info("WEB empty link")
					continue
				# Keyword filter (pre-rewrite)
				if phrases_lc:
					full_text = f"{title}\n{desc}".lower()
					if any(kw in full_text for kw in phrases_lc):
						logger.info("WEB keyword skip url=%s", link)
						skipped += 1
						continue
				try:
					with transaction.atomic():
						try:
							rew = rewrite_article(title or link, full_body or desc or "")
						except Exception:
							rew = None
						if not rew:
							rew = {"title": title or link, "content": (full_body or desc or "")}
						# Skip too-short per config
						effective_body = (rew.get("content") or full_body or desc or "")
						if min_chars and len((_strip_html_tags(effective_body) or effective_body)) < min_chars:
							skipped += 1
							continue
						img = ""
						if ws.parse_images and ws.image_selector:
							img_el = c.select_one(ws.image_selector)
							if img_el and (img_el.get('src') or img_el.get('data-src')):
								img = img_el.get('src') or img_el.get('data-src')
								if img and img.startswith('/'):
									from urllib.parse import urljoin
									img = urljoin(ws.url, img)
								# Download image into MEDIA and compress
								try:
									if img:
										media_root = Path(getattr(settings, "MEDIA_ROOT", Path("media")))
										target_dir = media_root / "web" / urlparse(ws.url).hostname.replace('.', '_')
										target_dir.mkdir(parents=True, exist_ok=True)
										resp_img = requests.get(img, timeout=20)
										if resp_img.status_code == 200:
											import hashlib
											hash_name = hashlib.sha1(img.encode('utf-8')).hexdigest()[:16]
											ext = ".jpg"
											ct = resp_img.headers.get("Content-Type", "").lower()
											if "png" in ct:
												ext = ".png"
											elif "webp" in ct:
												ext = ".webp"
											elif "jpeg" in ct or "jpg" in ct:
												ext = ".jpg"
											local_path = target_dir / f"{hash_name}{ext}"
											with open(local_path, "wb") as f:
												f.write(resp_img.content)
											# Compress per config
											try:
												cfg2 = ParserConfig.objects.order_by("-updated_at").first()
												_compress_image_at_path(local_path, cfg2)
											except Exception:
												logger.exception("Compress failed (web)")
											media_url = getattr(settings, "MEDIA_URL", "/media/")
											rel = local_path.relative_to(media_root)
											img = f"{media_url}{rel.as_posix()}"
								except Exception:
									logger.exception("WEB image download failed")
						# Determine theme: use AI output if present else website default else AI
						theme_val = None
						try:
							t = (rew or {}).get("theme") if isinstance(rew, dict) else None
							if isinstance(t, str) and t.strip().upper() in (NewsItem.Theme.AI, NewsItem.Theme.CRYPTO):
								theme_val = t.strip().upper()
						except Exception:
							theme_val = None
						n = NewsItem.objects.create(
								title=(rew.get("title") or title or link)[:500],
								original_url=link,
								description=(rew.get("content") or desc or "")[:10000],
								image_url=img,
								published_at=timezone.now(),
								source_name=ws.name,
								theme=(theme_val or ws.default_theme or NewsItem.Theme.AI),
							)
						# Attach hashtags if provided and valid
						try:
							tags = rew.get("hashtags") if isinstance(rew, dict) else None
							if isinstance(tags, list) and tags:
								slugs = [str(s).strip().lower() for s in tags if s]
								objs = list(Hashtag.objects.filter(slug__in=slugs, is_active=True))
								if objs:
									n.hashtags.add(*objs)
						except Exception:
							logger.exception("Attach hashtags failed (WEB)")
						created += 1
				except IntegrityError:
					skipped += 1
					logger.info("WEB duplicate skip url=%s", link)
		except Exception:
			skipped += 1
			logger.exception("WEB source error name=%s", ws.name)
	logger.info("WEB done created=%d skipped=%d", created, skipped)
	return {"created": created, "skipped": skipped}


@shared_task
def poll_and_post_latest_news(limit: int = 10) -> dict:
	"""Every run, read last posted NewsItem ID from a file, pull new items, and post to Telegram.

	Uses plain text, no HTML, and posts photos if URLs are present.
	"""
	bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
	channel = getattr(settings, "TELEGRAM_CHANNEL", "")
	if not (bot_token and channel and Bot):
		logger.info("TG poll: no telegram configured; skip")
		return {"posted": 0, "skipped": 0, "reason": "no telegram configured"}

	media_root = Path(getattr(settings, "MEDIA_ROOT", Path("media")))
	state_dir = media_root / "state"
	state_dir.mkdir(parents=True, exist_ok=True)
	state_file = state_dir / "tg_last_posted_id.txt"
	# Determine current max id in DB to seed checkpoint on first run
	try:
		current_max_id = int(NewsItem.objects.order_by("-id").values_list("id", flat=True).first() or 0)
	except Exception:
		current_max_id = 0

	last_id = 0
	seeded = False
	try:
		if state_file.exists():
			val = (state_file.read_text() or "").strip()
			last_id = int(val) if val else 0
		else:
			# Seed: start from current max id so we only post new content going forward
			state_file.write_text(str(current_max_id))
			return {"posted": 0, "skipped": 0, "last_id": current_max_id, "seeded": True}
	except Exception:
		# If parsing checkpoint failed, reset to current max id to avoid posting old backlog
		last_id = current_max_id
		try:
			state_file.write_text(str(current_max_id))
		except Exception:
			pass
		return {"posted": 0, "skipped": 0, "last_id": current_max_id, "seeded": True}

	qs = NewsItem.objects.order_by("id").filter(id__gt=last_id)[:max(1, int(limit))]
	posted = 0
	skipped = 0
	if not qs:
		logger.info("TG poll: no new items last_id=%d", last_id)
		return {"posted": 0, "skipped": 0, "last_id": last_id}
	bot = Bot(token=bot_token)
	new_last = last_id
	for n in qs:
		try:
			title = (n.title or "New post").strip()
			body = (n.description or "").strip()
			# TG-specific rewrite if enabled
			try:
				from .rewriter import get_active_telegram_config, rewrite_article_tg
				_tg_cfg = get_active_telegram_config()
				if _tg_cfg:
					rew = rewrite_article_tg(title, body)
					if rew and isinstance(rew, dict):
						title = (rew.get("title") or title).strip()
						body = (rew.get("content") or body or "").strip()
			except Exception:
				pass
			text_html = _to_telegram_html(f"{title}\n\n{body}")[:4096]
			text_plain = _to_plain_text(f"{title}\n\n{body}")[:4096]
			img = (n.image_url or "").strip()
			# Resolve local file path if available
			local_path = ""
			try:
				if getattr(n, "image_file", None) and getattr(n.image_file, "path", ""):
					if os.path.exists(n.image_file.path):  # type: ignore[attr-defined]
						local_path = n.image_file.path  # type: ignore[attr-defined]
			except Exception:
				local_path = ""
			# If URL is relative, map to MEDIA_ROOT correctly (strip MEDIA_URL prefix if present)
			if not local_path and img:
				try:
					from urllib.parse import urlparse
					p = urlparse(img)
					if not p.scheme:
						media_url_prefix = getattr(settings, "MEDIA_URL", "/media/") or "/media/"
						candidate = None
						if img.startswith(media_url_prefix):
							rel = img[len(media_url_prefix):].lstrip("/")
							candidate = media_root / rel
						elif img.startswith("/"):
							candidate = media_root / img.lstrip("/")
						else:
							candidate = media_root / img
						if candidate and candidate.exists():
							local_path = str(candidate)
				except Exception:
					pass
			# Build absolute URL only if PUBLIC_BASE_URL provided; otherwise keep relative so we try local mapping or file upload
			try:
				base = getattr(settings, "PUBLIC_BASE_URL", "").strip()
				if img and img.startswith("/") and base:
					img = base.rstrip("/") + img
			except Exception:
				pass
			# Prefer uploading local file when available, else try downloading remote to temp, else send by URL, else text
			if local_path:
				try:
					logger.info("TG poll: sending local image path=%s id=%d", local_path, n.id)
					with open(local_path, "rb") as f:
							pm = (ParseMode.HTML if 'ParseMode' in globals() and ParseMode else 'HTML')
							bot.send_photo(chat_id=channel, photo=f, caption=text_html[:1024], parse_mode=pm)
					posted += 1
				except Exception:
					logger.exception("TG poll: local image send failed id=%d", n.id)
					# Fallbacks
					try:
						with open(local_path, "rb") as f:
							bot.send_photo(chat_id=channel, photo=f, caption=text_plain[:1024])
						posted += 1
					except Exception:
						try:
							pm = (ParseMode.HTML if 'ParseMode' in globals() and ParseMode else 'HTML')
							bot.send_message(chat_id=channel, text=text_html)
							posted += 1
						except Exception:
							bot.send_message(chat_id=channel, text=text_plain)
							posted += 1
			elif img:
				# Try downloading the remote image so Telegram receives a clean file upload
				try:
					logger.info("TG poll: trying remote download url=%s id=%d", img, n.id)
					resp = requests.get(img, timeout=20, headers={"User-Agent": "Mozilla/5.0 (compatible; ai-aggregator/1.0)"})
					if resp.status_code == 200 and resp.content:
						import tempfile
						with tempfile.NamedTemporaryFile(suffix=".jpg") as tf:
							tf.write(resp.content)
							tf.flush()
							with open(tf.name, "rb") as f:
								pm = (ParseMode.HTML if 'ParseMode' in globals() and ParseMode else 'HTML')
								bot.send_photo(chat_id=channel, photo=f, caption=text_html[:1024], parse_mode=pm)
								posted += 1
								new_last = max(new_last, n.id)
								continue
				except Exception:
					logger.exception("TG poll: remote download/send failed url=%s id=%d", img, n.id)
				try:
					logger.info("TG poll: sending by URL url=%s id=%d", img, n.id)
					pm = (ParseMode.HTML if 'ParseMode' in globals() and ParseMode else 'HTML')
					bot.send_photo(chat_id=channel, photo=img, caption=text_html[:1024], parse_mode=pm)
					posted += 1
				except Exception:
					logger.exception("TG poll: URL photo send failed url=%s id=%d", img, n.id)
					# Fallback message: try HTML then plain
					try:
						pm = (ParseMode.HTML if 'ParseMode' in globals() and ParseMode else 'HTML')
						bot.send_message(chat_id=channel, text=text_html, parse_mode=pm, disable_web_page_preview=True)
						posted += 1
					except Exception:
						bot.send_message(chat_id=channel, text=text_plain, disable_web_page_preview=True)
						posted += 1
			else:
				try:
					pm = (ParseMode.HTML if 'ParseMode' in globals() and ParseMode else 'HTML')
					bot.send_message(chat_id=channel, text=text_html, parse_mode=pm, disable_web_page_preview=True)
					posted += 1
				except Exception:
					bot.send_message(chat_id=channel, text=text_plain, disable_web_page_preview=True)
					posted += 1
			new_last = max(new_last, n.id)
		except Exception:
			skipped += 1
	try:
		if new_last > last_id:
			state_file.write_text(str(new_last))
	except Exception:
		pass
	logger.info("TG poll: done posted=%d skipped=%d last_id=%d", posted, skipped, new_last)
	return {"posted": posted, "skipped": skipped, "last_id": new_last}


