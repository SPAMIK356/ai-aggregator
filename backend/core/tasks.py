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
	from telegram import Bot
except Exception:
	Bot = None
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
			# Prefer webhook if configured
			if webhook_url:
				resp = requests.post(webhook_url, json={
					"event_type": event.event_type,
					"payload": event.payload,
				})
				ok = 200 <= resp.status_code < 300
            # Fallback to Telegram bot
			if (not ok) and bot_token and channel and Bot:
				try:
					bot = Bot(token=bot_token)
					payload = event.payload or {}
                    t = (payload.get("title") or "New post").strip()
                    body = (payload.get("body") or "").strip()
                    img = (payload.get("image_url") or "").strip()

                    # If this is a NewsItem event, re-fetch from DB and skip Telegram-origin items
                    try:
                        if event.event_type == OutboxEvent.EVENT_NEWS_CREATED:
                            nid = payload.get("id")
                            if nid:
                                ni = NewsItem.objects.filter(pk=int(nid)).only("title", "description", "image_url", "image_file", "original_url").first()
                                if ni:
                                    orig = (ni.original_url or "").lower()
                                    if "t.me/" in orig or "telegram." in orig:
                                        # Skip Telegram-origin items for bot posting
                                        raise RuntimeError("skip_telegram_origin")
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
					text = f"<b>{t}</b>\n\n{body}".strip()
					if img:
						try:
							bot.send_photo(chat_id=channel, photo=img, caption=text[:1024], parse_mode="HTML")
							ok = True
						except Exception:
							bot.send_message(chat_id=channel, text=text[:4096], parse_mode="HTML", disable_web_page_preview=True)
							ok = True
					else:
						bot.send_message(chat_id=channel, text=text[:4096], parse_mode="HTML", disable_web_page_preview=True)
						ok = True
				except Exception as _tg_exc:
					ok = False
			if ok:
				event.delivery_attempts += 1
				event.mark_delivered()
				delivered += 1
			else:
				event.delivery_attempts += 1
				event.last_error = (f"Webhook failed" if webhook_url else "")
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
					max_id = max(max_id, m.id or 0)
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
							rew = rewrite_article(title or link, desc or "")
						except Exception:
							rew = None
						if not rew:
							rew = {"title": title or link, "content": desc or ""}
						# Skip too-short per config
						effective_body = (rew.get("content") or desc or "")
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


